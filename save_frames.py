from openpilot.tools.lib.route import Route, Segment
from openpilot.tools.lib.logreader import LogReader
from openpilot.tools.lib.framereader import FrameReader

import matplotlib.pyplot as plt
import cv2 as cv

from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import os
import argparse


class CameraView(Enum):
    FRONT_NARROW = "FRONT_NARROW"  # fcamera
    FRONT_WIDE = "FRONT_WIDE"  # ecamera
    DRIVER = "DRIVER"  # dcamera


def save_frames_from_hevc_url(hevc_url: str, output_path: Path, verbose: bool = False):
    os.makedirs(name=output_path, exist_ok=True)
    frame_reader = FrameReader(hevc_url)
    frame_idx = 0
    while True:
        try:
            frame = frame_reader.get(frame_idx)
        except StopIteration:
            break

        output_file_name = output_path / f"{frame_idx}.png"
        is_image_save_success = cv.imwrite(filename=output_file_name, img=cv.cvtColor(frame, cv.COLOR_RGB2BGR))
        if not is_image_save_success:
            raise Exception(f"Image save failed for output {output_file_name}")

        if verbose:
            print(f"Saved image {frame_idx} to {output_file_name.absolute()}")

        frame_idx += 1

    if verbose:
        print("No more frames")


def save_segment_frames_for_camera_view(segment: Segment, camera_view: CameraView, output_path: Path, verbose: bool = False):
    if camera_view == CameraView.FRONT_NARROW:
        save_frames_from_hevc_url(hevc_url=segment.camera_path, output_path=output_path / "front_narrow", verbose=verbose)
    elif camera_view == CameraView.FRONT_WIDE:
        save_frames_from_hevc_url(hevc_url=segment.ecamera_path, output_path=output_path / "front_wide", verbose=verbose)
    elif camera_view == CameraView.DRIVER:
        save_frames_from_hevc_url(hevc_url=segment.dcamera_path, output_path=output_path / "driver", verbose=verbose)


def save_segment_frames_for_camera_views(segment: Segment, camera_views: list[CameraView], output_path: Path, verbose: bool = False):
    for camera_view in camera_views:
        save_segment_frames_for_camera_view(
            segment=segment,
            camera_view=camera_view,
            output_path=output_path,
            verbose=verbose
        )

def save_route_frames_for_camer_views(
    route_name: str,
    camera_views: list[CameraView],
    output_path: Path,
    verbose: bool =False
):
    route = Route(name=route_name)
    for segment_idx in range(len(route.segments)):
        segment = route.segments[segment_idx]
        save_segment_frames_for_camera_views(
            segment=segment,
            camera_views=camera_views,
            output_path=output_path / f"{segment_idx}",
            verbose=verbose
        )


def main():
    parser = argparse.ArgumentParser(
        description="Save images from CommaVQ Cloud based on route name."
    )

    parser.add_argument(
        "route_name",
        help="Name of the route."
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output Directory",
        default="./output_directory"
    )

    parser.add_argument(
        "--camera_views",
        nargs="+",
        choices=[camera_view.value for camera_view in CameraView],
        help=f"List of camera views to download."
    )

    args = parser.parse_args()

    route_name = args.route_name
    output_dir = Path(args.output)
    camera_views = [CameraView(camera_view_string) for camera_view_string in args.camera_views]

    print("Route Name:", route_name)
    print("Output Dir:", output_dir)
    print("Camera Views:", camera_views)

    save_route_frames_for_camer_views(
        route_name=route_name,
        camera_views=camera_views,
        output_path=output_dir
    )

    print("Completed")


if __name__ == "__main__":
    main()
