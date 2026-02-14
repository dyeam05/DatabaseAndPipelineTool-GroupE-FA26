#!/usr/bin/env python3
from openpilot.tools.lib.route import Route
from openpilot.tools.lib.logreader import LogReader
from openpilot.tools.lib.framereader import FrameReader
from openpilot.selfdrive.test.process_replay.migration import migrate_all
import argparse
import json
import sys
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROUTE_CAMERAS = ("front", "wide", "driver")
DEFAULT_SIGNAL_FIELDS = [
    "carState.vEgo",
    "carState.aEgo",
    "carState.steeringAngleDeg",
    "carState.steeringRateDeg",
    "carState.steeringTorque",
    "carState.steeringTorqueEps",
    "carState.steeringPressed",
    "carState.gasPressed",
    "carState.brakePressed",
    "carState.leftBlinker",
    "carState.rightBlinker",
    "carState.cruiseState.speed",
    "carState.wheelSpeeds.fl",
    "carState.wheelSpeeds.fr",
    "carState.wheelSpeeds.rl",
    "carState.wheelSpeeds.rr",
]


def nv12_to_bgr(raw_nv12: bytes | np.ndarray, width: int, height: int, stride: int, uv_offset: int) -> np.ndarray:

    raw = np.frombuffer(raw_nv12, dtype=np.uint8)
    y_plane = raw[0:height * stride].reshape((height, stride))[:, :width]
    uv_plane = raw[uv_offset:uv_offset + (height // 2) * stride].reshape((height // 2, stride))[:, :width]

    nv12 = np.vstack((y_plane, uv_plane))
    return cv2.cvtColor(nv12, cv2.COLOR_YUV2BGR_NV12)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Save route camera frames and per-frame metadata")
    parser.add_argument("--route", required=True, help="Route ID (e.g. dongle|timestamp or dongle/timestamp)")
    parser.add_argument("--data-dir", help="Optional local route data dir (instead of cloud)")
    parser.add_argument("--include-log-signals", action="store_true",
                        help="Attach log signals (speed/steering/etc.) to each frame")
    parser.add_argument("--signal-fields", default=",".join(DEFAULT_SIGNAL_FIELDS),
                        help="Comma-separated log fields to include (e.g. carState.vEgo,carState.steeringAngleDeg)")

    # Output
    parser.add_argument("--out", default="tools/camerastream/captures", help="Output directory")
    parser.add_argument("--format", choices=["raw", "jpg", "png"], default="raw", help="Frame output format")
    parser.add_argument("--jpeg-quality", type=int, default=95, help="JPEG quality (1-100)")
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 2), help="Number of worker processes")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0 = unlimited, per camera)")
    parser.add_argument("--max-seconds", type=float, default=0.0, help="Stop after N seconds (0 = unlimited)")
    return parser.parse_args()


def route_camera_paths(route, camera: str) -> list[str | None]:
    if camera == "front":
        return route.camera_paths()
    if camera == "wide":
        return route.ecamera_paths()
    return route.dcamera_paths()


def get_available_cameras(route) -> list[str]:
    camera_map = {
        "front": route.camera_paths(),
        "wide": route.ecamera_paths(),
        "driver": route.dcamera_paths(),
    }
    available = [name for name, paths in camera_map.items() if any(paths)]
    if not available:
        raise ValueError("No camera data found for route")
    return available


def parse_signal_fields(spec: str) -> list[str]:
    return [f.strip() for f in spec.split(",") if f.strip()]


def _to_jsonable(v):
    if isinstance(v, (bool, int, float, str)) or v is None:
        return v
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    try:
        return float(v)
    except Exception:
        return str(v)


def _get_nested_field(obj, field_path: list[str]):
    cur = obj
    for name in field_path:
        cur = getattr(cur, name)
    return _to_jsonable(cur)


def build_route_signal_chunks(log_paths: list[str | None], fps: int, signal_fields: list[str]) -> list[dict[str, object | None]]:

    valid_log_paths = [p for p in log_paths if p]
    if not valid_log_paths:
        return []

    msgs = migrate_all(list(LogReader(valid_log_paths, sort_by_time=True)))
    if not msgs:
        return []

    services = {f.split(".", 1)[0] for f in signal_fields}
    dt_ns = 1e9 / fps
    chunks: list[dict[str, object]] = []
    current: dict[str, object] = {}
    next_time = msgs[0].logMonoTime + dt_ns

    for msg in msgs:
        msg_time = msg.logMonoTime
        while msg_time >= next_time:
            chunks.append(current)
            current = {}
            next_time += dt_ns

        which = msg.which()
        if which in services:
            current[which] = getattr(msg, which)
    if current:
        chunks.append(current)

    out: list[dict[str, object | None]] = []
    split_paths = [(f, f.split(".")) for f in signal_fields]
    for chunk in chunks:
        frame_signals: dict[str, object | None] = {}
        for field, parts in split_paths:
            service, rest = parts[0], parts[1:]
            if service not in chunk:
                frame_signals[field] = None
                continue
            try:
                frame_signals[field] = _get_nested_field(chunk[service], rest)
            except Exception:
                frame_signals[field] = None
        out.append(frame_signals)
    return out


_WORKER_FRAMES_DIR: Path | None = None
_WORKER_META_DIR: Path | None = None
_WORKER_FORMAT: str | None = None
_WORKER_JPEG_QUALITY: int | None = None
_WORKER_SIGNAL_CHUNKS: list[dict[str, object | None]] | None = None
_WORKER_MAX_FRAMES: int | None = None
_WORKER_DEADLINE: float | None = None


def _init_worker(frames_dir: Path, meta_dir: Path, output_format: str, jpeg_quality: int,
                 signal_chunks: list[dict[str, object | None]] | None, max_frames: int, deadline: float | None) -> None:
    global _WORKER_FRAMES_DIR, _WORKER_META_DIR, _WORKER_FORMAT, _WORKER_JPEG_QUALITY
    global _WORKER_SIGNAL_CHUNKS, _WORKER_MAX_FRAMES, _WORKER_DEADLINE

    _WORKER_FRAMES_DIR = frames_dir
    _WORKER_META_DIR = meta_dir
    _WORKER_FORMAT = output_format
    _WORKER_JPEG_QUALITY = jpeg_quality
    _WORKER_SIGNAL_CHUNKS = signal_chunks
    _WORKER_MAX_FRAMES = max_frames if max_frames > 0 else None
    _WORKER_DEADLINE = deadline


def _process_segment(task: tuple[str, int, str, int]) -> tuple[str, int, int]:
    camera_name, seg_idx, seg_path, start_frame_id = task
    seg_reader = FrameReader(seg_path, pix_fmt="nv12")
    assert _WORKER_META_DIR is not None
    assert _WORKER_FRAMES_DIR is not None
    assert _WORKER_FORMAT is not None
    meta_path = _WORKER_META_DIR / f"metadata.{camera_name}.seg{seg_idx}.jsonl"

    frames_written = 0
    with meta_path.open("w") as mf:
        for local_idx in range(seg_reader.frame_count):
            if _WORKER_DEADLINE is not None and time.monotonic() >= _WORKER_DEADLINE:
                break

            frame_id = start_frame_id + local_idx
            if _WORKER_MAX_FRAMES is not None and frame_id >= _WORKER_MAX_FRAMES:
                break

            nv12_flat = seg_reader.get(local_idx)
            raw_nv12 = nv12_flat.tobytes()
            width = int(seg_reader.w)
            height = int(seg_reader.h)
            stride = int(seg_reader.w)
            uv_offset = int(seg_reader.w * seg_reader.h)

            if _WORKER_FORMAT == "raw":
                frame_name = f"{frame_id:08d}_fid{frame_id:010d}.nv12"
                (_WORKER_FRAMES_DIR / camera_name / frame_name).write_bytes(raw_nv12)
            else:
                img_bgr = nv12_to_bgr(raw_nv12, width, height, stride, uv_offset)
                ext = ".jpg" if _WORKER_FORMAT == "jpg" else ".png"
                frame_name = f"{frame_id:08d}_fid{frame_id:010d}{ext}"
                frame_path = _WORKER_FRAMES_DIR / camera_name / frame_name
                if _WORKER_FORMAT == "jpg":
                    assert _WORKER_JPEG_QUALITY is not None
                    cv2.imwrite(str(frame_path), img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), _WORKER_JPEG_QUALITY])
                else:
                    cv2.imwrite(str(frame_path), img_bgr)

            source_meta: dict[str, object | None] = {
                "camera": camera_name,
                "segment_idx": seg_idx,
                "segment_local_idx": local_idx,
                "source_path": seg_path,
            }
            if _WORKER_SIGNAL_CHUNKS is not None:
                if 0 <= frame_id < len(_WORKER_SIGNAL_CHUNKS):
                    source_meta["signals"] = _WORKER_SIGNAL_CHUNKS[frame_id]
                else:
                    source_meta["signals"] = None

            meta: dict[str, object | None] = {
                "frame_idx": frame_id,
                "filename": frame_name,
                "frame_id": frame_id,
                "width": width,
                "height": height,
                "stride": stride,
                "uv_offset": uv_offset,
                "buffer_len": int(len(raw_nv12)),
            }
            meta.update(source_meta)
            mf.write(json.dumps(meta) + "\n")
            frames_written += 1

    return camera_name, seg_idx, frames_written


def main() -> int:
    args = parse_args()
    if not (1 <= args.jpeg_quality <= 100):
        print("jpeg-quality must be in [1, 100]", file=sys.stderr)
        return 2

    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    out_dir = Path(args.out) / f"route_all_{ts}"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / "metadata.jsonl"
    run_path = out_dir / "run.json"

    route_obj = Route(args.route, data_dir=args.data_dir)
    cameras = get_available_cameras(route_obj)
    camera_paths_map = {
        "front": route_obj.camera_paths(),
        "wide": route_obj.ecamera_paths(),
        "driver": route_obj.dcamera_paths(),
    }
    for camera_name in cameras:
        (frames_dir / camera_name).mkdir(exist_ok=True)

    signal_chunks = None
    signal_fields: list[str] = []
    if args.include_log_signals:
        signal_fields = parse_signal_fields(args.signal_fields)
        if signal_fields:
            log_paths = route_obj.log_paths()
            print("Loading route logs for signal extraction...")
            # Assume 20 fps for signal-to-frame alignment
            signal_chunks = build_route_signal_chunks(log_paths, 20, signal_fields)
            print(f"Loaded signal chunks: {len(signal_chunks)}")

    run_info = {
        "format": args.format,
        "start_unix_time_s": time.time(),
        "route": route_obj.name.canonical_name,
        "cameras": cameras,
        "data_dir": args.data_dir,
        "include_log_signals": args.include_log_signals,
        "signal_fields": signal_fields,
    }
    run_path.write_text(json.dumps(run_info, indent=2) + "\n")

    print(f"Writing frames to {frames_dir}")
    print(f"Writing metadata to {meta_path}")
    print(f"Using {args.workers} worker processes")

    first_mono = time.monotonic()
    deadline = (first_mono + args.max_seconds) if args.max_seconds > 0 else None

    meta_segments_dir = out_dir / "metadata_segments"
    meta_segments_dir.mkdir(exist_ok=True)

    segment_tasks: list[tuple[str, int, str, int]] = []
    for camera_name in cameras:
        camera_paths = camera_paths_map[camera_name]
        next_frame_id = 0
        for seg_idx, seg_path in enumerate(camera_paths):
            if not seg_path:
                continue
            if args.max_frames > 0 and next_frame_id >= args.max_frames:
                break

            seg_reader = FrameReader(seg_path, pix_fmt="nv12")
            segment_tasks.append((camera_name, seg_idx, seg_path, next_frame_id))
            next_frame_id += seg_reader.frame_count

    frames_done = 0
    with Pool(processes=args.workers,
              initializer=_init_worker,
              initargs=(frames_dir, meta_segments_dir, args.format, args.jpeg_quality,
                        signal_chunks, args.max_frames, deadline)) as pool:
        for camera_name, seg_idx, seg_frames in pool.imap_unordered(_process_segment, segment_tasks):
            frames_done += seg_frames
            elapsed = time.monotonic() - first_mono
            fps = frames_done / elapsed if elapsed > 0 else 0.0
            print(f"camera={camera_name} segment={seg_idx} frames={frames_done} avg_fps={fps:.2f}")

    with meta_path.open("w") as mf:
        for camera_name, seg_idx, _, _ in sorted(segment_tasks, key=lambda t: (t[0], t[1])):
            seg_meta_path = meta_segments_dir / f"metadata.{camera_name}.seg{seg_idx}.jsonl"
            if not seg_meta_path.exists():
                continue
            mf.write(seg_meta_path.read_text())
            seg_meta_path.unlink()

    elapsed = time.monotonic() - first_mono
    fps = frames_done / elapsed if elapsed > 0 else 0.0
    print(f"done frames={frames_done} elapsed_s={elapsed:.2f} avg_fps={fps:.2f}")
    print(f"output={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
