from cvat_sdk import make_client
from dotenv import load_dotenv
import os
import zipfile

# export annotations JSON to a directory. 

load_dotenv()

CVAT_HOST = os.environ.get("CVAT_HOST", "http://localhost:8080")
CVAT_USER = os.environ["CVAT_USER"]
CVAT_PASS = os.environ["CVAT_PASS"]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "annotations")
COCO_FORMAT = "COCO 1.0"


def export_task_coco(task_id: int, output_dir: str = OUTPUT_DIR) -> str:

    # create a place for the annotations to be stored (will be changed once we get a db)
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, f"task_{task_id}.zip")
    out_path = os.path.join(output_dir, f"task_{task_id}.json")

    # create a cvat client to use proxys
    with make_client(CVAT_HOST, credentials=(CVAT_USER, CVAT_PASS)) as client:
        task = client.tasks.retrieve(task_id)
        # model_proxy.py in cvat repo
        task.export_dataset(
            format_name=COCO_FORMAT,
            filename=zip_path,
            include_images=False,
        )

    # Extract the COCO instances JSON from the zip
    with zipfile.ZipFile(zip_path, "r") as zf:
        # CVAT COCO zips contain annotations/instances_default.json
        coco_files = [f for f in zf.namelist() if f.endswith(".json")]
        if not coco_files:
            raise FileNotFoundError(f"No JSON found in export zip for task {task_id}")
        with zf.open(coco_files[0]) as src, open(out_path, "wb") as dst:
            dst.write(src.read())

    os.remove(zip_path)
    print(f"Saved COCO annotations to {out_path}")
    return out_path

# export every task currently in cvat
def export_all_tasks(output_dir: str = OUTPUT_DIR):
    with make_client(CVAT_HOST, credentials=(CVAT_USER, CVAT_PASS)) as client:
        tasks = client.tasks.list()


    for task in tasks:
        export_task_coco(task.id, output_dir)


if __name__ == "__main__":
    export_task_coco(6, "annotations")