from enum import StrEnum
# this role tell segment_log for which segment belong to
# only server as a reference for now

class ArtifactRole(StrEnum):
    FRAME_IMAGE = "frame_image"
    SEGMENT_LOG = "segment_log"
    COCO_EXPORT = "coco_export"
    DETECTION_JSON = "detection_json"
    SEGMENTATION_MASK = "segmentation_mask"
    SEGMENTATION_MAP = "segmentation_map"
    DEPTH_MAP = "depth_map"