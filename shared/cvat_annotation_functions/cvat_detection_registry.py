from dataclasses import dataclass
from pydantic import BaseModel
from cvat_annotation_functions.i_cvat_detection import ICVATDetection

@dataclass(frozen=True)
class CVATDetectionPluginDefinition:
    key: str
    implementation_cls: type["ICVATDetection"]
    config_model: type[BaseModel]
    display_name: str
    description: str | None = None

CVAT_DETECTION_REGISTRY: dict[str, CVATDetectionPluginDefinition] = {}

def register_cvat_detection_plugin(
    *,
    key: str,
    config_model: type[BaseModel],
    display_name: str,
    description: str | None = None
):
    def decorator(cls: type["ICVATDetection"]):
        if key in CVAT_DETECTION_REGISTRY:
            raise ValueError(f"Duplictate CVAT detection pluging key: {key}")

        CVAT_DETECTION_REGISTRY[key] = CVATDetectionPluginDefinition(
            key=key,
            implementation_cls=cls,
            config_model=config_model,
            display_name=display_name,
            description=description
        )
        return cls
    return decorator


def get_cvat_detection_plugin_definition(key: str) -> CVATDetectionPluginDefinition:
    try:
        return CVAT_DETECTION_REGISTRY[key]
    except KeyError as exc:
        raise KeyError(f"Unknown CVAT detection implementation_key: {key}") from exc


def build_cvat_detection_from_key(key: str, config: dict) -> ICVATDetection:
    plugin_definition = get_cvat_detection_plugin_definition(key)
    validated_config = plugin_definition.config_model.model_validate(config)
    return plugin_definition.implementation_cls(validated_config)
