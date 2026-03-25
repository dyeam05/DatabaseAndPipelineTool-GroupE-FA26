from cvat_sdk import make_client
from cvat_sdk.models import PatchedLabelRequest, TaskWriteRequest
from cvat_sdk.core.proxies.tasks import ResourceType
from dotenv import load_dotenv
import os

load_dotenv()

# UPLOAD A DATASET, creates tasks in batches of 100

CVAT_HOST = os.environ.get("CVAT_HOST", "http://localhost:8080")
CVAT_EMAIL = os.environ["CVAT_EMAIL"]
CVAT_PASSWORD = os.environ["CVAT_PASSWORD"]

BATCH_SIZE = 100

AV_LABELS = {
    0: 'person',
    1: 'bicycle',
    2: 'car',
    3: 'motorbike',
    5: 'bus',
    6: 'train',
    7: 'truck',
    9: 'traffic light',
    11: 'stop sign',
}

AV_LABEL_REQUESTS = [PatchedLabelRequest(name=name) for name in AV_LABELS.values()]


# helper to group elements into batches
def batch_list(lst: list, batch_size:int) -> list:
    return [lst[i:i + batch_size] for i in range(0, len(lst), batch_size)]


def create_task(task_name: str, 
                file_names: list[str], 
                resource_type: ResourceType = ResourceType.SHARE) -> int:
    
    if not file_names:
        raise ValueError("file_names must not be empty")
    
    # create a single cvat task for # of images
    with make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD)) as client:
        task_spec = TaskWriteRequest(
            name=task_name,
            labels=AV_LABEL_REQUESTS,
        )

        print(f"Creating task '{task_name}' with {len(file_names)} images")

        # this is same as upload image, resources=[list of filenames, not paths]
        task = client.tasks.create_from_data(
            spec=task_spec,
            resource_type=resource_type,
            resources=file_names,
        )
        print(f"Task created: {task.id}")
        return task.id



def create_tasks_from_folder(local_image_dir: str = "raw_images",
                             task_title: str = "av_dataset",
                             resource_type: ResourceType = ResourceType.SHARE,
                             share_subdir: str | None = None) -> list[int]:
    # upload all images in a dir to a CVAT task in batches
    # one task per batch

    # SHARE: image list only needs file names. CVAT reads from the volume
    #   the share_root passes subfolders
    # LOCAL: image list needs path/filename CVAT reads from local storage



    # store image files locally into list
    file_names = sorted([
        f for f in os.listdir(local_image_dir)
        if f.lower().endswith((".png"))
    ])

    if not file_names:
        print(f"No images found in {local_image_dir}")
        return []


    # build full paths for LOCAL
    if resource_type == ResourceType.LOCAL:
        file_names = [os.path.join(local_image_dir, f) for f in file_names]

    # Share only needs filenames, if in subfolder, segment1/image1.png
    elif resource_type == ResourceType.SHARE:
        file_names = [
            f"{share_subdir}/{f}" if share_subdir else f for f in file_names
        ]



    # from file_names split into batches
    batches = batch_list(file_names, BATCH_SIZE)
    task_ids = []

    # for each file, place into a task
    for i, batch in enumerate(batches, start=1):
        task_name = f"{task_title}_batch_{i}"
        task_id = create_task(task_name=task_name, file_names=batch, resource_type=resource_type)
        task_ids.append(task_id)

    print(f"Created {len(task_ids)} tasks: {task_ids}")
    return task_ids


if __name__ == "__main__":
    create_tasks_from_folder("cvat_share/images", "av_dataset", share_subdir="images")