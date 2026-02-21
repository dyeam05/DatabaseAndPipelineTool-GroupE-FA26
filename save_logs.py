from openpilot.tools.lib.route import Route
from openpilot.tools.lib.logreader import _LogFileReader, LogReader
from openpilot.selfdrive.test.process_replay.migration import migrate_all
from tools.jotpluggler.data import msgs_to_time_series
import pandas as pd
import numpy as np
import pyarrow

from typing import Any
from pathlib import Path
import os
import argparse


def process_segment_logs(segment_url: str, fields_to_track: list[tuple[str, ...]]):
    log_file_reader = _LogFileReader(fn=segment_url, sort_by_time=True)
    # the dict of log timeseries has a dict where each entry is a service, and each services has fields, and each fields
    dict_of_log_timeseries, time_min, time_max = time_seriess = msgs_to_time_series(log_file_reader)

    camera_encoder_time_series = dict_of_log_timeseries['roadEncodeIdx']
    frame_time_stamps: np.ndarray = camera_encoder_time_series['timestampSof']['values'] / 1e9 # get the timestamps of the start of each frame so we know when we need sensor values
    frame_ids = camera_encoder_time_series['frameId']['values']

    def extract_data_nested_dict(nested_dict, dict_path: tuple[str, ...]):
        for key in dict_path:
            nested_dict = nested_dict[key]
        return nested_dict

    def create_key_from_field_tuple(field_tuple: tuple[str, ...]):
        return ".".join(field_tuple)

    def generate_data_stream_for_time_stamps(
        target_time_stamps: np.ndarray,
        data_time_stamps: np.ndarray,
        data: list | np.ndarray
    ) -> list | np.ndarray :
        def _py_primitive(x: Any) -> Any:
            # NumPy scalar -> Python scalar (float/int/bool/...)
            if isinstance(x, np.generic):
                return x.item()

            # 0-d ndarray -> Python scalar
            if isinstance(x, np.ndarray) and x.ndim == 0:
                return x.item()

            # Plain Python types (bool/int/float/str/None) just pass through
            return x

        indices = np.searchsorted(data_time_stamps, target_time_stamps, side="right") - 1
        indices = np.clip(indices, 0, len(data) - 1)
        return [_py_primitive(data[i]) for i in indices]

    tracked_data = {
        "timestamps": frame_time_stamps.tolist(),
        "frameIds": (frame_ids - np.min(frame_ids)).tolist() # 0-align the frame ids and convert to regular list
    }
    for field_to_track in fields_to_track:
        field_output_key = create_key_from_field_tuple(field_to_track) # create unique key to store in output dict

        service_name: str = field_to_track[0] # the highest level entry chooses the service
        service_time_stamps = dict_of_log_timeseries[service_name]['t'] # extract the timestamps for when these services messages were generated

        field_time_series_data = extract_data_nested_dict(nested_dict=dict_of_log_timeseries, dict_path=field_to_track)['values'] # actual entries are stored in the values key
        time_stamp_aligned_data = generate_data_stream_for_time_stamps(
            target_time_stamps=frame_time_stamps,
            data_time_stamps=service_time_stamps,
            data=field_time_series_data
        )

        tracked_data[field_output_key] = time_stamp_aligned_data

    return tracked_data

def process_route_logs(
    route_name: str,
    fields_to_track: list[tuple[str, ...]],
    output_dir: Path
):
    os.makedirs(output_dir, exist_ok=True)

    log_reader = LogReader(identifier=route_name, sort_by_time=True, only_union_types=True)

    for segment_index in range(len(log_reader.logreader_identifiers)):
        segment_url = log_reader.logreader_identifiers[segment_index]
        data_dict = process_segment_logs(segment_url=segment_url, fields_to_track=fields_to_track)
        dataframe = pd.DataFrame(data_dict)
        dataframe.to_parquet(output_dir / f"{segment_index}.parquet", engine='pyarrow')

def main():
    parser = argparse.ArgumentParser(
        description="Save log files from CommaVQ Cloud based on a route name."
    )

    parser.add_argument(
        "route_name",
        help="Name of the route."
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output Directory",
        default="./log_output_directory"
    )

    fields_to_track = [("carState", "steeringAngleDeg")]

    args = parser.parse_args()

    route_name = args.route_name
    output_dir = Path(args.output)

        fields_to_track=fields_to_track,
        output_dir=output_dir
    )

if __name__ == "__main__":
    main()