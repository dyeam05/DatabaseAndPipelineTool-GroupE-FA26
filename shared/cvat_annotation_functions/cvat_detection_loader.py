from cvat_annotation_functions.cvat_detr_detection import CVATDetrDetection


BUILTIN_CVAT_DETECTION_PLUGINS = (
    CVATDetrDetection,
)


def load_builtin_cvat_detection_plugins() -> None:
    for _plugin in BUILTIN_CVAT_DETECTION_PLUGINS:
        _ = _plugin
        pass
