import cvat_sdk.models as models
import cvat_sdk.auto_annotation as cvataa

import torch
from PIL import Image
from transformers import (
    AutoImageProcessor,
    AutoModelForObjectDetection,
    DetrImageProcessor,
)

from cvat_annotation_functions.i_cvat_detection import ICVATDetection

class CVATDetrDetection(ICVATDetection):
    """
    Docs [here](https://docs.cvat.ai/docs/api_sdk/sdk/auto-annotation/)

    Model that should allow the usage of an arbitrary hugging face DETR model.
    """

    def __init__(self, model_name: str = "PekingU/rtdetr_v2_r50vd"):
        self.processor: DetrImageProcessor = AutoImageProcessor.from_pretrained(model_name) # type: ignore
        self.model = AutoModelForObjectDetection.from_pretrained(model_name)
        self.raw_labels: dict[int, str] = dict(self.model.config.id2label)
        self.model.eval()

    @property
    def labels(self) -> dict[int, str]:
        return self.raw_labels

    @property
    def spec(self) -> cvataa.DetectionFunctionSpec:
        return cvataa.DetectionFunctionSpec(
            labels=[
                cvataa.label_spec(name, id=idx) for idx, name in self.raw_labels.items()
            ]
        )

    def detect(
        self, 
        context: cvataa.DetectionFunctionContext,
        image: Image.Image
    ) -> list[models.LabeledShapeRequest]:
        conf_threshold = context.conf_threshold or 0.5

        with torch.no_grad():
            inputs = self.processor(images=[image], return_tensors="pt")
            outputs = self.model(**inputs)
            target_sizes = torch.tensor([[image.size[1], image.size[0]]])
            results = self.processor.post_process_object_detection(
                outputs=outputs,
                threshold=conf_threshold,
                target_sizes=target_sizes, # type: ignore
            )[0]

        return [
            cvataa.rectangle(
                label.item(),
                [
                    box[0].item(),
                    box[1].item(),
                    box[2].item(),
                    box[3].item(),
                ],
            )
            for box, label, score in zip(
                results["boxes"], results["labels"], results["scores"]
            )
            if score >= conf_threshold and label.item() in self.raw_labels
        ]
