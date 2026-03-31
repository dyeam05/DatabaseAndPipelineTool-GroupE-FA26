from pathlib import Path
import os


def get_pngs_in_directory(dir: Path):
    if not dir.is_dir():
        raise ValueError(f"{dir} is not a directory")

    return list(dir.glob("*.png"))


def does_dir_exist(dir: Path) -> bool:
    return os.path.isdir(dir)
