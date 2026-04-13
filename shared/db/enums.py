from enum import StrEnum

from sqlalchemy import Enum


class ArtifactKind(StrEnum):
    IMAGE = "image"
    JSON = "json"
    PARQUET = "parquet"
    ZIP = "zip"

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
    name="camera_type_enum",
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

class JobSegmentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

job_segment_run_enum = Enum(
    JobSegmentRunStatus,
    name="job_segment_run_enum",
    native_enum=True,
    validate_strings=True
)

class JobSegmentRunImportStatus(StrEnum):
    QUEUED_FOR_LOADING = "queued_for_loading"
    LOADING = "loading"
    LOADED = "loaded"
    QUEUED_FOR_REMOVAL = "queued_for_removal"
    REMOVING = "removing"
    REMOVED = "removed"
    FAILED = "failed"

job_segment_run_import_status_enum = Enum(
    JobSegmentRunImportStatus,
    name="job_segment_run_review_status_enum",
    native_enum=True,
    validate_strings=True
)

class DatasetExportStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

dataset_export_status_enum = Enum(
    DatasetExportStatus,
    name="dataset_export_status_enum",
    native_enum=True,
    validate_strings=True
)

class RouteStatus(StrEnum):
    DOWNLOAD_QUEUE = "download queue"
    DOWNLOADING = "downloading"
    UPLOAD_QUEUE = "upload queue"
    UPLOADING = "uploading"
    FAILED = "failed"
    UPLOADED = "uploaded"

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
    UPLOADED = "uploaded"

segment_status_enum = Enum(
    SegmentStatus,
    name="segment_status_enum",
    native_enum=True,
    validate_strings=True
)
