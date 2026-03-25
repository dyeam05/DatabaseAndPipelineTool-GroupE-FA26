#!/usr/bin/env python3
import json
import os
import sys
from typing import Any
from openpilot.system.hardware import TICI
from tinygrad.tensor import Tensor
from tinygrad.dtype import dtypes
if TICI:
    from openpilot.selfdrive.modeld.runners.tinygrad_helpers import qcom_tensor_from_opencl_address
    os.environ['QCOM'] = '1'
else:
    os.environ['LLVM'] = '1'
import time
import pickle
import numpy as np
import cereal.messaging as messaging
from cereal import car, log
from pathlib import Path
from setproctitle import setproctitle
from cereal.messaging import PubMaster, SubMaster
from msgq.visionipc import VisionIpcClient, VisionStreamType, VisionBuf
from opendbc.car.car_helpers import get_demo_car_params
from openpilot.common.swaglog import cloudlog
from openpilot.common.params import Params
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.realtime import config_realtime_process
from openpilot.common.transformations.camera import DEVICE_CAMERAS
from openpilot.common.transformations.model import get_warp_matrix
from openpilot.system import sentry
from openpilot.selfdrive.controls.lib.desire_helper import DesireHelper
from openpilot.selfdrive.modeld.parse_model_outputs import Parser
from openpilot.selfdrive.modeld.fill_model_msg import fill_model_msg, fill_pose_msg, PublishState
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.selfdrive.modeld.models.commonmodel_pyx import DrivingModelFrame, CLContext

import cv2

PROCESS_NAME = "selfdrive.modeld.modeld"
SEND_RAW_PRED = os.getenv('SEND_RAW_PRED')

VISION_CONNECT_TIMEOUT_SECONDS = float(os.getenv("VISION_CONNECT_TIMEOUT_SECONDS", "30"))
NO_FRAME_RECONNECT_SECONDS = float(os.getenv("NO_FRAME_RECONNECT_SECONDS", "3"))
EXTRACT_STALL_TIMEOUT_SECONDS = float(os.getenv("EXTRACT_STALL_TIMEOUT_SECONDS", "60"))
HEALTH_LOG_INTERVAL_SECONDS = float(os.getenv("HEALTH_LOG_INTERVAL_SECONDS", "10"))
RECONNECT_COOLDOWN_SECONDS = float(os.getenv("RECONNECT_COOLDOWN_SECONDS", "5"))
MAX_EXTRA_CAMERA_RECONNECT_ATTEMPTS = int(os.getenv("MAX_EXTRA_CAMERA_RECONNECT_ATTEMPTS", "3"))

VISION_PKL_PATH = Path(__file__).parent / 'models/driving_vision_tinygrad.pkl'
POLICY_PKL_PATH = Path(__file__).parent / 'models/driving_policy_tinygrad.pkl'
VISION_METADATA_PATH = Path(__file__).parent / 'models/driving_vision_metadata.pkl'
POLICY_METADATA_PATH = Path(__file__).parent / 'models/driving_policy_metadata.pkl'


class FrameMeta:
    frame_id: int = 0
    timestamp_sof: int = 0
    timestamp_eof: int = 0

    def __init__(self, vipc=None):
        if vipc is not None:
            self.frame_id, self.timestamp_sof, self.timestamp_eof = vipc.frame_id, vipc.timestamp_sof, vipc.timestamp_eof


class ModelState:
    frames: dict[str, DrivingModelFrame]
    inputs: dict[str, np.ndarray]
    output: np.ndarray
    prev_desire: np.ndarray  # for tracking the rising edge of the pulse

    def __init__(self, context: CLContext):
        self.frames = {
            'input_imgs': DrivingModelFrame(context, ModelConstants.TEMPORAL_SKIP),
            'big_input_imgs': DrivingModelFrame(context, ModelConstants.TEMPORAL_SKIP)
        }
        self.prev_desire = np.zeros(ModelConstants.DESIRE_LEN, dtype=np.float32)

        self.full_features_buffer = np.zeros((1, ModelConstants.FULL_HISTORY_BUFFER_LEN,  ModelConstants.FEATURE_LEN), dtype=np.float32)
        self.full_desire = np.zeros((1, ModelConstants.FULL_HISTORY_BUFFER_LEN, ModelConstants.DESIRE_LEN), dtype=np.float32)
        self.full_prev_desired_curv = np.zeros((1, ModelConstants.FULL_HISTORY_BUFFER_LEN, ModelConstants.PREV_DESIRED_CURV_LEN), dtype=np.float32)
        self.temporal_idxs = slice(-1-(ModelConstants.TEMPORAL_SKIP*(ModelConstants.INPUT_HISTORY_BUFFER_LEN-1)), None, ModelConstants.TEMPORAL_SKIP)

        # policy inputs
        self.numpy_inputs = {
            'desire': np.zeros((1, ModelConstants.INPUT_HISTORY_BUFFER_LEN, ModelConstants.DESIRE_LEN), dtype=np.float32),
            'traffic_convention': np.zeros((1, ModelConstants.TRAFFIC_CONVENTION_LEN), dtype=np.float32),
            'lateral_control_params': np.zeros((1, ModelConstants.LATERAL_CONTROL_PARAMS_LEN), dtype=np.float32),
            'prev_desired_curv': np.zeros((1, ModelConstants.INPUT_HISTORY_BUFFER_LEN, ModelConstants.PREV_DESIRED_CURV_LEN), dtype=np.float32),
            'features_buffer': np.zeros((1, ModelConstants.INPUT_HISTORY_BUFFER_LEN,  ModelConstants.FEATURE_LEN), dtype=np.float32),
        }

        with open(VISION_METADATA_PATH, 'rb') as f:
            vision_metadata = pickle.load(f)
            self.vision_input_shapes = vision_metadata['input_shapes']
            self.vision_output_slices = vision_metadata['output_slices']
            vision_output_size = vision_metadata['output_shapes']['outputs'][1]

        with open(POLICY_METADATA_PATH, 'rb') as f:
            policy_metadata = pickle.load(f)
            self.policy_input_shapes = policy_metadata['input_shapes']
            self.policy_output_slices = policy_metadata['output_slices']
            policy_output_size = policy_metadata['output_shapes']['outputs'][1]

        # img buffers are managed in openCL transform code
        self.vision_inputs: dict[str, Tensor] = {}
        self.vision_output = np.zeros(vision_output_size, dtype=np.float32)
        self.policy_inputs = {k: Tensor(v, device='NPY').realize() for k, v in self.numpy_inputs.items()}
        self.policy_output = np.zeros(policy_output_size, dtype=np.float32)
        self.parser = Parser()

        with open(VISION_PKL_PATH, "rb") as f:
            self.vision_run = pickle.load(f)

        with open(POLICY_PKL_PATH, "rb") as f:
            self.policy_run = pickle.load(f)

    def slice_outputs(self, model_outputs: np.ndarray, output_slices: dict[str, slice]) -> dict[str, np.ndarray]:
        parsed_model_outputs = {k: model_outputs[np.newaxis, v] for k, v in output_slices.items()}
        return parsed_model_outputs

    def run(self, buf: VisionBuf, wbuf: VisionBuf, transform: np.ndarray, transform_wide: np.ndarray,
            inputs: dict[str, np.ndarray], prepare_only: bool) -> dict[str, np.ndarray] | None:
        # Model decides when action is completed, so desire input is just a pulse triggered on rising edge
        inputs['desire'][0] = 0
        new_desire = np.where(inputs['desire'] - self.prev_desire > .99, inputs['desire'], 0)
        self.prev_desire[:] = inputs['desire']

        self.full_desire[0, :-1] = self.full_desire[0, 1:]
        self.full_desire[0, -1] = new_desire
        self.numpy_inputs['desire'][:] = self.full_desire.reshape(
            (1, ModelConstants.INPUT_HISTORY_BUFFER_LEN, ModelConstants.TEMPORAL_SKIP, -1)).max(axis=2)

        self.numpy_inputs['traffic_convention'][:] = inputs['traffic_convention']
        self.numpy_inputs['lateral_control_params'][:] = inputs['lateral_control_params']
        imgs_cl = {'input_imgs': self.frames['input_imgs'].prepare(buf, transform.flatten()),
                   'big_input_imgs': self.frames['big_input_imgs'].prepare(wbuf, transform_wide.flatten())}

        if TICI:
            # The imgs tensors are backed by opencl memory, only need init once
            for key in imgs_cl:
                if key not in self.vision_inputs:
                    self.vision_inputs[key] = qcom_tensor_from_opencl_address(
                        imgs_cl[key].mem_address, self.vision_input_shapes[key], dtype=dtypes.uint8)
        else:
            for key in imgs_cl:
                frame_input = self.frames[key].buffer_from_cl(imgs_cl[key]).reshape(self.vision_input_shapes[key])
                self.vision_inputs[key] = Tensor(frame_input, dtype=dtypes.uint8).realize()

        if prepare_only:
            return None

        self.vision_output = self.vision_run(**self.vision_inputs).numpy().flatten()
        vision_outputs_dict = self.parser.parse_vision_outputs(self.slice_outputs(self.vision_output, self.vision_output_slices))

        self.full_features_buffer[0, :-1] = self.full_features_buffer[0, 1:]
        self.full_features_buffer[0, -1] = vision_outputs_dict['hidden_state'][0, :]
        self.numpy_inputs['features_buffer'][:] = self.full_features_buffer[0, self.temporal_idxs]

        self.policy_output = self.policy_run(**self.policy_inputs).numpy().flatten()
        policy_outputs_dict = self.parser.parse_policy_outputs(self.slice_outputs(self.policy_output, self.policy_output_slices))

        # TODO model only uses last value now
        self.full_prev_desired_curv[0, :-1] = self.full_prev_desired_curv[0, 1:]
        self.full_prev_desired_curv[0, -1, :] = policy_outputs_dict['desired_curvature'][0, :]
        self.numpy_inputs['prev_desired_curv'][:] = self.full_prev_desired_curv[0, self.temporal_idxs]

        combined_outputs_dict = {**vision_outputs_dict, **policy_outputs_dict}
        if SEND_RAW_PRED:
            combined_outputs_dict['raw_pred'] = np.concatenate([self.vision_output.copy(), self.policy_output.copy()])

        return combined_outputs_dict


def main(output_path: Path, demo=False):
    # Helper functions
    def to_json_compatible(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: to_json_compatible(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [to_json_compatible(v) for v in value]
        if isinstance(value, np.ndarray):
            return to_json_compatible(value.tolist())
        if isinstance(value, np.generic):
            return to_json_compatible(value.item())
        if isinstance(value, float) and not np.isfinite(value):
            return None
        return value

    def save_logs_as_json(frame_logs: list[dict[str, Any]], dir: Path):
        with open(dir / "logs.json", "w", encoding="utf-8") as file:
            json.dump(frame_logs, file, allow_nan=False)

    def flush_logs(frame_logs: list[dict[str, Any]], dir: Path):
        if len(frame_logs) == 0:
            return
        frame_logs.sort(key=lambda entry: entry["timestamp_sof"])
        save_logs_as_json(frame_logs, dir)
        frame_logs.clear()

    def decode_nv12_to_bgr(buf: VisionBuf) -> np.ndarray:
        h = buf.height
        w = buf.width
        s = buf.stride  # bytes per row in both Y & UV planes
        uv_off = buf.uv_offset  # byte offset where UV plane starts in buf.data

        # 2. View the entire buffer as one flat uint8 array
        raw = np.frombuffer(buf.data, dtype=np.uint8)

        # 3. Extract & reshape the Y plane (h rows × s bytes), then crop to actual width
        y_plane = raw[0: h * s] \
            .reshape((h, s))[:, :w]

        # 4. Extract & reshape the UV plane ((h/2) rows × s bytes), then crop
        uv_plane = raw[uv_off: uv_off + (h // 2) * s] \
            .reshape((h // 2, s))[:, :w]

        # 5. Stack into NV12 layout and convert to BGR
        nv12 = np.vstack((y_plane, uv_plane))
        return cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)

    def recover_img(buf: VisionBuf, saved_path: Path) -> np.ndarray:
        bgr = decode_nv12_to_bgr(buf)
        is_success = cv2.imwrite(str(saved_path), bgr)
        if not is_success:
            raise ValueError("Did not sucessfully save image")
        return bgr

    def ensure_output_dirs(base_path: Path) -> tuple[Path, Path]:
        front_path = base_path / "front"
        front_wide_path = base_path / "front_wide"
        front_path.mkdir(parents=True, exist_ok=True)
        front_wide_path.mkdir(parents=True, exist_ok=True)
        return front_path, front_wide_path

    def connect_vision_clients(context: CLContext) -> tuple[VisionIpcClient, VisionIpcClient, bool, bool]:
        start_wait = time.monotonic()
        while True:
            available_streams = VisionIpcClient.available_streams("camerad", block=False)
            if available_streams:
                use_extra = VisionStreamType.VISION_STREAM_WIDE_ROAD in available_streams and VisionStreamType.VISION_STREAM_ROAD in available_streams
                main_wide = VisionStreamType.VISION_STREAM_ROAD not in available_streams
                break

            if time.monotonic() - start_wait > VISION_CONNECT_TIMEOUT_SECONDS:
                raise RuntimeError("Timed out waiting for camerad streams")
            time.sleep(0.1)

        main_stream = VisionStreamType.VISION_STREAM_WIDE_ROAD if main_wide else VisionStreamType.VISION_STREAM_ROAD
        vipc_main = VisionIpcClient("camerad", main_stream, True, context)
        vipc_extra = VisionIpcClient("camerad", VisionStreamType.VISION_STREAM_WIDE_ROAD, False, context)
        cloudlog.warning(f"vision stream set up, main_wide_camera: {main_wide}, use_extra_client: {use_extra}")

        start_connect = time.monotonic()
        while not vipc_main.connect(False):
            if time.monotonic() - start_connect > VISION_CONNECT_TIMEOUT_SECONDS:
                raise RuntimeError("Timed out connecting to main camerad VisionIPC stream")
            time.sleep(0.1)

        while use_extra and not vipc_extra.connect(False):
            if time.monotonic() - start_connect > VISION_CONNECT_TIMEOUT_SECONDS:
                raise RuntimeError("Timed out connecting to extra camerad VisionIPC stream")
            time.sleep(0.1)

        cloudlog.warning(f"connected main cam with buffer size: {vipc_main.buffer_len} ({vipc_main.width} x {vipc_main.height})")
        if use_extra:
            cloudlog.warning(
                f"connected extra cam with buffer size: {vipc_extra.buffer_len} ({vipc_extra.width} x {vipc_extra.height})")

        return vipc_main, vipc_extra, use_extra, main_wide

    if output_path.parent == output_path or not output_path.name.isdigit():
        raise ValueError("--output_dir must point to a segment path like <uuid>/<segment_num>")

    logs: list[dict[str, Any]] = []
    seen_frame_ids: set[int] = set()
    current_front_dir, current_front_wide_dir = ensure_output_dirs(output_path)
    should_exit_after_flush = False

    print(f"Creating output director: {output_path}")
    os.makedirs(output_path, exist_ok=True)

    cloudlog.warning("modeld init")

    sentry.set_tag("daemon", PROCESS_NAME)
    cloudlog.bind(daemon=PROCESS_NAME)
    setproctitle(PROCESS_NAME)
    config_realtime_process(7, 54)

    cloudlog.warning("setting up CL context")
    cl_context = CLContext()
    cloudlog.warning("CL context ready; loading model")
    model = ModelState(cl_context)
    cloudlog.warning("models loaded, modeld starting")

    vipc_client_main, vipc_client_extra, use_extra_client, main_wide_camera = connect_vision_clients(cl_context)

    # messaging
    pm = PubMaster(["modelV2", "drivingModelData", "cameraOdometry"])
    sm = SubMaster([
        "deviceState",
        "carState",
        "roadCameraState",
        "liveCalibration",
        "driverMonitoringState",
        "carControl",
        "controlsState",
        "liveLocationKalmanDEPRECATED",
        "clocks",
        "roadEncodeIdx"
    ])

    publish_state = PublishState()
    params = Params()

    # setup filter to track dropped frames
    frame_dropped_filter = FirstOrderFilter(0., 10., 1. / ModelConstants.MODEL_FREQ)
    frame_id = 0
    last_vipc_frame_id = 0
    run_count = 0

    model_transform_main = np.zeros((3, 3), dtype=np.float32)
    model_transform_extra = np.zeros((3, 3), dtype=np.float32)
    live_calib_seen = False
    buf_main, buf_extra = None, None
    meta_main = FrameMeta()
    meta_extra = FrameMeta()

    if demo:
        CP = get_demo_car_params()
    else:
        CP = messaging.log_from_bytes(params.get("CarParams", block=True), car.CarParams)
    cloudlog.info("modeld got CarParams: %s", CP.brand)

    # TODO this needs more thought, use .2s extra for now to estimate other delays
    steer_delay = CP.steerActuatorDelay + .2

    DH = DesireHelper()

    last_main_frame_time = time.monotonic()
    last_progress_time = time.monotonic()
    last_health_log_time = time.monotonic()
    consecutive_main_empty_reads = 0
    consecutive_extra_empty_reads = 0
    last_main_reconnect_time = 0.0
    last_extra_reconnect_time = 0.0
    extra_camera_reconnect_attempts = 0

    try:
        while True:
            now = time.monotonic()
            if now - last_health_log_time >= HEALTH_LOG_INTERVAL_SECONDS:
                cloudlog.info(
                    f"health frame_id={last_vipc_frame_id} seg={output_path.name} "
                    f"main_empty_reads={consecutive_main_empty_reads} extra_empty_reads={consecutive_extra_empty_reads} "
                    f"seconds_since_main_frame={now - last_main_frame_time:.2f} "
                    f"seconds_since_progress={now - last_progress_time:.2f}")
                last_health_log_time = now

            if now - last_progress_time > EXTRACT_STALL_TIMEOUT_SECONDS:
                raise RuntimeError(
                    f"Extraction stalled for {EXTRACT_STALL_TIMEOUT_SECONDS}s without frame progress")

            # Keep receiving frames until we are at least 1 frame ahead of previous extra frame

            while meta_main.timestamp_sof < meta_extra.timestamp_sof + 25000000:
                buf_main = vipc_client_main.recv()
                if buf_main is None:
                    consecutive_main_empty_reads += 1
                    break

                meta_main = FrameMeta(vipc_client_main)
                consecutive_main_empty_reads = 0
                last_main_frame_time = time.monotonic()

                if meta_main.frame_id in seen_frame_ids:
                    cloudlog.warning(
                        f"Replay loop detected by repeated frame_id={meta_main.frame_id}. Flushing logs and exiting")
                    should_exit_after_flush = True
                    break

                seen_frame_ids.add(meta_main.frame_id)

            if should_exit_after_flush:
                flush_logs(logs, output_path)
                sys.exit(0)

            if buf_main is None:
                no_main_frame_for = time.monotonic() - last_main_frame_time
                if no_main_frame_for > NO_FRAME_RECONNECT_SECONDS:
                    now = time.monotonic()
                    if now - last_main_reconnect_time > RECONNECT_COOLDOWN_SECONDS:
                        cloudlog.warning(
                            f"No main camera frames for {no_main_frame_for:.2f}s, reconnecting VisionIPC clients")
                        vipc_client_main, vipc_client_extra, use_extra_client, main_wide_camera = connect_vision_clients(cl_context)
                        meta_main = FrameMeta()
                        meta_extra = FrameMeta()
                        consecutive_main_empty_reads = 0
                        consecutive_extra_empty_reads = 0
                        last_main_frame_time = time.monotonic()
                        last_main_reconnect_time = now
                        extra_camera_reconnect_attempts = 0

                cloudlog.debug("vipc_client_main no frame")
                continue

            if use_extra_client:
                # Keep receiving extra frames until frame id matches main camera
                while True:
                    buf_extra = vipc_client_extra.recv()
                    if buf_extra is None:
                        consecutive_extra_empty_reads += 1
                        break
                    meta_extra = FrameMeta(vipc_client_extra)
                    consecutive_extra_empty_reads = 0
                    if meta_main.timestamp_sof < meta_extra.timestamp_sof + 25000000:
                        break

                if buf_extra is None:
                    no_main_frame_for = time.monotonic() - last_main_frame_time
                    if no_main_frame_for > NO_FRAME_RECONNECT_SECONDS:
                        now = time.monotonic()
                        if now - last_extra_reconnect_time > RECONNECT_COOLDOWN_SECONDS:
                            extra_camera_reconnect_attempts += 1
                            if extra_camera_reconnect_attempts > MAX_EXTRA_CAMERA_RECONNECT_ATTEMPTS:
                                cloudlog.warning(
                                    f"Extra camera unavailable for {no_main_frame_for:.2f}s after {extra_camera_reconnect_attempts} reconnect attempts; falling back to main camera only")
                                use_extra_client = False
                                extra_camera_reconnect_attempts = 0
                            else:
                                cloudlog.warning(
                                    f"No extra camera frames while main stream active for {no_main_frame_for:.2f}s, reconnecting VisionIPC clients (attempt {extra_camera_reconnect_attempts}/{MAX_EXTRA_CAMERA_RECONNECT_ATTEMPTS})")
                                vipc_client_main, vipc_client_extra, use_extra_client, main_wide_camera = connect_vision_clients(cl_context)
                                meta_main = FrameMeta()
                                meta_extra = FrameMeta()
                                consecutive_main_empty_reads = 0
                                consecutive_extra_empty_reads = 0
                                last_main_frame_time = time.monotonic()
                                last_extra_reconnect_time = now
                        else:
                            skip_secs = RECONNECT_COOLDOWN_SECONDS - (now - last_extra_reconnect_time)
                            cloudlog.debug(f"extra camera reconnect on cooldown, trying again in {skip_secs:.2f}s")

                    cloudlog.debug("vipc_client_extra no frame")
                    if not use_extra_client:
                        buf_extra = buf_main
                        meta_extra = meta_main
                    else:
                        continue

                if abs(meta_main.timestamp_sof - meta_extra.timestamp_sof) > 10000000:
                    cloudlog.error(f"frames out of sync! main: {meta_main.frame_id} ({meta_main.timestamp_sof / 1e9:.5f}),\
                             extra: {meta_extra.frame_id} ({meta_extra.timestamp_sof / 1e9:.5f})")
            else:
                # Use single camera
                buf_extra = buf_main
                meta_extra = meta_main

            sm.update(0)
            desire = DH.desire
            is_rhd = sm["driverMonitoringState"].isRHD
            frame_id = sm["roadCameraState"].frameId
            v_ego = max(sm["carState"].vEgo, 0.)
            lateral_control_params = np.array([v_ego, steer_delay], dtype=np.float32)
            if sm.updated["liveCalibration"] and sm.seen['roadCameraState'] and sm.seen['deviceState']:
                device_from_calib_euler = np.array(sm["liveCalibration"].rpyCalib, dtype=np.float32)
                dc = DEVICE_CAMERAS[(str(sm['deviceState'].deviceType), str(sm['roadCameraState'].sensor))]
                model_transform_main = get_warp_matrix(
                    device_from_calib_euler, dc.ecam.intrinsics if main_wide_camera else dc.fcam.intrinsics, False).astype(np.float32)
                model_transform_extra = get_warp_matrix(device_from_calib_euler, dc.ecam.intrinsics, True).astype(np.float32)
                live_calib_seen = True

            traffic_convention = np.zeros(2)
            traffic_convention[int(is_rhd)] = 1

            vec_desire = np.zeros(ModelConstants.DESIRE_LEN, dtype=np.float32)
            if desire >= 0 and desire < ModelConstants.DESIRE_LEN:
                vec_desire[desire] = 1

            # tracked dropped frames
            vipc_dropped_frames = max(0, meta_main.frame_id - last_vipc_frame_id - 1)
            frames_dropped = frame_dropped_filter.update(min(vipc_dropped_frames, 10))
            if run_count < 10:  # let frame drops warm up
                frame_dropped_filter.x = 0.
                frames_dropped = 0.
            run_count = run_count + 1

            frame_drop_ratio = frames_dropped / (1 + frames_dropped)
            prepare_only = vipc_dropped_frames > 0
            if prepare_only:
                cloudlog.error(f"skipping model eval. Dropped {vipc_dropped_frames} frames")

            inputs: dict[str, np.ndarray] = {
                'desire': vec_desire,
                'traffic_convention': traffic_convention,
                'lateral_control_params': lateral_control_params,
            }
            logged_model_inputs = to_json_compatible(inputs)

            mt1 = time.perf_counter()
            model_output = model.run(buf_main, buf_extra, model_transform_main, model_transform_extra, inputs, prepare_only)
            mt2 = time.perf_counter()
            model_execution_time = mt2 - mt1

            if model_output is not None:
                modelv2_send = messaging.new_message('modelV2')
                drivingdata_send = messaging.new_message('drivingModelData')
                posenet_send = messaging.new_message('cameraOdometry')
                fill_model_msg(drivingdata_send, modelv2_send, model_output, v_ego, steer_delay,
                               publish_state, meta_main.frame_id, meta_extra.frame_id, frame_id,
                               frame_drop_ratio, meta_main.timestamp_eof, model_execution_time, live_calib_seen)

                desire_state = modelv2_send.modelV2.meta.desireState
                l_lane_change_prob = desire_state[log.Desire.laneChangeLeft]
                r_lane_change_prob = desire_state[log.Desire.laneChangeRight]
                lane_change_prob = l_lane_change_prob + r_lane_change_prob
                DH.update(sm['carState'], sm['carControl'].latActive, lane_change_prob)
                modelv2_send.modelV2.meta.laneChangeState = DH.lane_change_state
                modelv2_send.modelV2.meta.laneChangeDirection = DH.lane_change_direction
                drivingdata_send.drivingModelData.meta.laneChangeState = DH.lane_change_state
                drivingdata_send.drivingModelData.meta.laneChangeDirection = DH.lane_change_direction

                fill_pose_msg(posenet_send, model_output, meta_main.frame_id, vipc_dropped_frames, meta_main.timestamp_eof, live_calib_seen)
                pm.send('modelV2', modelv2_send)
                pm.send('drivingModelData', drivingdata_send)
                pm.send('cameraOdometry', posenet_send)
            last_vipc_frame_id = meta_main.frame_id
            last_progress_time = time.monotonic()

            vipc_frame_id = meta_main.frame_id

            # raise Exception
            logs.append({
                "frame_id": vipc_frame_id,
                "timestamp_sof": meta_main.timestamp_sof,
                "vehicle_state": to_json_compatible(sm['liveLocationKalmanDEPRECATED'].to_dict()),
                "car_control": to_json_compatible(sm['carControl'].to_dict()),
                "car_state": to_json_compatible(sm['carState'].to_dict()),
                "model_inputs": logged_model_inputs,
                "model_output": to_json_compatible(model_output) if model_output is not None else None,
            })

            try:
                recover_img(
                    buf=buf_main,
                    saved_path=current_front_dir / f"{vipc_frame_id}.png"
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to write front frame image for segment={output_path.name} frame={vipc_frame_id}") from exc

            if use_extra_client:
                try:
                    recover_img(
                        buf=buf_extra,
                        saved_path=current_front_wide_dir / f"{vipc_frame_id}.png"
                    )
                except Exception as exc:
                    raise RuntimeError(
                        f"Failed to write wide frame image for segment={output_path.name} frame={vipc_frame_id}") from exc

            # logs['vehicle_states'].append(sm["carState"].to_dict())
            # logs['carControls'].append(sm["carControl"].to_dict())
            # logs['controlsStates'].append(sm['controlsState'].to_dict())
            # logs['model_inputs'].append(inputs)
            # logs['liveLocationKalmanDEPRECATED'].append(sm['liveLocationKalmanDEPRECATED'].to_dict())

            # print(logs)

            # raise Exception
    finally:
        flush_logs(logs, output_path)


if __name__ == "__main__":
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--demo', action='store_true', help='A boolean for demo mode.')
        parser.add_argument('--output_dir', required=True, help='Segment output directory in the form <uuid>/<segment_num>')
        args = parser.parse_args()
        output_path: Path = Path(args.output_dir)
        main(demo=args.demo, output_path=output_path)
    except KeyboardInterrupt:
        cloudlog.warning(f"child {PROCESS_NAME} got SIGINT")
    except Exception:
        sentry.capture_exception()
        raise
