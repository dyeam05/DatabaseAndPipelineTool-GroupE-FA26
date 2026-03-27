from pathlib import Path

def get_pngs_in_directory(dir: Path):
    if not dir.is_dir():
        raise ValueError(f"{dir} is not a directory")

    return list(dir.glob("*.png"))
