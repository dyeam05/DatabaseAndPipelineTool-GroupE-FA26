from enum import StrEnum

from sqlalchemy import Enum


class ArtifactKind(StrEnum):
    IMAGE = "image"
    JSON = "json"
    PARQUET = "parquet"

artifact_kind_enum = Enum(
    ArtifactKind,
    name="artifact_kind_enum",
    native_enum=True,
    validate_strings=True
)

class ArtifactRole(StrEnum):
    FRAME_IMAGE = "frame_image"
    SEGMENT_LOG = "segment_log"
    COCO_EXPORT = "coco_export"
    DETECTION_JSON = "detection_json"
    SEGMENTATION_MASK = "segmentation_mask"
    SEGMENTATION_MAP = "segmentation_map"
    DEPTH_MAP = "depth_map"

artifact_role_enum = Enum(
    ArtifactRole,
    name="artifact_role_enum",
    native_enum=True,
    validate_strings=True
)

class CameraType(StrEnum):
    FRONT_REGULAR = "front_regular"
    FRONT_WIDE = "front_wide"
    DRIVER = "driver"

camera_type_enum =  Enum(
    CameraType,
    name="camer_type_num",
    native_enum=True,
    validate_strings=True
)


class JobType(StrEnum):
    OBJECT_DETECTION = "object_detection"
    SEGMENTATION = "segmentation"
    DEPTH = "depth"
    ANNOTATION = "annotation"

job_type_enum = Enum(
    JobType,
    name="job_type_enum",
    native_enum=True,
    validate_strings=True
)

class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

job_status_enum = Enum(
    JobStatus,
    name="job_status_enum",
    native_enum=True,
    validate_strings=True
)

class RouteStatus(StrEnum):
    DOWNLOAD_QUEUE = "download queue"
    DOWNLOADING = "downloading"
    UPLOAD_QUEUE = "upload queue"
    UPLOADING = "uploading"
    FAILED = "failed"

route_status_enum = Enum(
    RouteStatus,
    name="route_status_enum",
    native_enum=True,
    validate_strings=True
)

class SegmentStatus(StrEnum):
    DOWNLOAD_QUEUE = "download queue"
    DOWNLOADING = "downloading"
    UPLOAD_QUEUE = "upload queue"
    UPLOADING = "uploading"
    FAILED = "failed"

segment_status_enum = Enum(
    SegmentStatus,
    name="segment_status_enum",
    native_enum=True,
    validate_strings=True
)
