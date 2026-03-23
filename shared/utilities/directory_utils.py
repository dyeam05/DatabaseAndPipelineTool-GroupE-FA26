from pathlib import Path
import os

def get_subdirectories(path: Path) -> list[Path]:
    return [p for p in path.iterdir() if p.is_dir()]

def does_directory_have_more_than_n_items(path: Path, n: int):
    counter = 0
    stack = [path]
    while stack:
        current = stack.pop()
        with os.scandir(current) as it:
            for entry in it:
                counter += 1
                if counter >= n:
                    return True
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))

    return False

