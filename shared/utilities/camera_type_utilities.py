from db.enums import CameraType


def folder_name_to_camera_type(folder_name: str) -> CameraType:
    conversion: dict[str, CameraType] = {
        "front": CameraType.FRONT_REGULAR,
        "front_wide": CameraType.FRONT_WIDE
    }

    if folder_name not in conversion:
        raise ValueError(f"Folder name {folder_name} not supported.")

    return conversion[folder_name]