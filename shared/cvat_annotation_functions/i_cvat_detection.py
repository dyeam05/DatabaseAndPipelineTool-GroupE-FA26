from abc import ABC, abstractmethod

import cvat_sdk.models as models
import cvat_sdk.auto_annotation as cvataa

from PIL import Image
    
class ICVATDetection(ABC):
    """
    Docs [here](https://docs.cvat.ai/docs/api_sdk/sdk/auto-annotation/)

    Abstract interface for CVAT detection auto-annotation functions.
    """


    @property
    @abstractmethod
    def labels(self) -> dict[int, str]:
        ...

    @property
    @abstractmethod
    def spec(self) -> cvataa.DetectionFunctionSpec:
        ...

    @abstractmethod
    def detect(
        self, 
        context: cvataa.DetectionFunctionContext,
        image: Image.Image
    ) -> list[models.LabeledShapeRequest]:
        ...
