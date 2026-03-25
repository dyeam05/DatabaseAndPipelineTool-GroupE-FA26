import os
from dotenv import load_dotenv

from transformers import AutoImageProcessor, AutoModelForObjectDetection
from PIL import Image as PIL
import torch

from cvat_sdk import make_client
import cvat_sdk.models as models
import cvat_sdk.auto_annotation as cvataa

# auto annotate all images in a given task. assumes model is trained

load_dotenv()

# Constants
CVAT_HOST = os.environ.get("CVAT_HOST", "http://localhost:8080")
CVAT_EMAIL = os.environ["CVAT_EMAIL"]
CVAT_PASSWORD = os.environ["CVAT_PASSWORD"]
MODEL = "PekingU/rtdetr_v2_r50vd"

# these labels are already trained in the RTDetr
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

class AVDetectionFunction():
    def __init__(self, model_name: str = MODEL):
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModelForObjectDetection.from_pretrained(model_name)
        self.model.eval() # set to evaluation mode

    @property
    def spec(self) -> cvataa.DetectionFunctionSpec:
        # define the labels
        return cvataa.DetectionFunctionSpec(
            labels=[
                cvataa.label_spec(name, id=idx)
                for idx, name in AV_LABELS.items()
            ]
        )
    
    def detect(self, context: cvataa.DetectionFunctionContext, image: PIL.Image) -> list[models.LabeledShapeRequest]:
        # Determine the confidence threshold (default 0.5 if not set)
        conf_threshold = context.conf_threshold or 0.5

        with torch.no_grad():
            # tranform image into a pytorch tensor that the model expects as an input
            inputs = self.processor(images=[image], return_tensors='pt')
            outputs = self.model(**inputs)

            target_sizes = torch.tensor([[image.size[1], image.size[0]]])
            results = self.processor.post_process_object_detection(
                outputs=outputs,
                threshold=conf_threshold,
                target_sizes=target_sizes
            )[0]


            print(f"Total detections before filtering: {len(results['boxes'])}")
            print(f"Labels detected: {[l.item() for l in results['labels']]}")
            print(f"Scores: {[round(s.item(), 3) for s in results['scores']]}")

        # convert back to CVAT SDK format
        return [
            cvataa.rectangle(label.item(), [
                box[0].item(), # xmin
                box[1].item(), # ymin
                box[2].item(), # xmax
                box[3].item(), # ymax
            ])
            for box, label, score in zip(results["boxes"], results["labels"], results["scores"])
            if score >= conf_threshold and label.item() in AV_LABELS

        ]

# reusable function for pipeline.py to call, conf_threshold is included for potential future use but idk if we will need it
def annotate_task(task_id: int, conf_threshold: float = 0.5) -> None:
    with make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD)) as client:
        func = AVDetectionFunction()
        cvataa.annotate_task(client, task_id, func)

if __name__ == '__main__':
    # log into the CVAT server
    with make_client(CVAT_HOST, credentials=(CVAT_EMAIL, CVAT_PASSWORD)) as client:
        func = AVDetectionFunction()

        # annotate task 12345 using the function
        cvataa.annotate_task(client, 1, func) # client, task_id, function