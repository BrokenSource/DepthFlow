from enum import Enum
from typing import Annotated, Any

import numpy as np
import xxhash
from cyclopts import Parameter
from pydantic import PrivateAttr

from depthflow import logger
from depthflow.estimators import DepthEstimator

# ---------------------------------------------------------------------------- #

class DepthAnythingBase(DepthEstimator):

    class Model(str, Enum):
        Small = "small"
        Base  = "base"
        Large = "large"
        Giant = "giant"

    model: Model = Model.Small
    """The model of DepthAnything to use"""

    _processor: Annotated[
        dict[Model, Any],
        Parameter(show=False)
    ] = PrivateAttr(default_factory=dict)

    _pipelines: Annotated[
        dict[Model, Any],
        Parameter(show=False)
    ] = PrivateAttr(default_factory=dict)

    def __hash__(self) -> int:
        hasher = xxhash.xxh3_64()
        hasher.update(type(self).__name__)
        hasher.update(self.model.value)
        return hasher.intdigest()

# ---------------------------------------------------------------------------- #

class DepthAnythingV1(DepthAnythingBase):
    """Wrapper for https://github.com/LiheYoung/Depth-Anything"""

    _model: Annotated[Any, Parameter(show=False)] = PrivateAttr(None)

    def load_model(self) -> None:
        if self.model not in self._pipelines:
            import torch
            from transformers import AutoImageProcessor, AutoModelForDepthEstimation
            logger.info(f"Loading {type(self).__name__} {self.model}")
            huggingface = f"LiheYoung/depth-anything-{self.model.value}-hf"
            self._pipelines.setdefault(self.model, AutoModelForDepthEstimation.from_pretrained(huggingface))
            self._processor.setdefault(self.model, AutoImageProcessor.from_pretrained(huggingface))
            self._pipelines[self.model].to(torch.accelerator.current_accelerator() or "cpu")

    def _estimate(self, image: np.ndarray) -> np.ndarray:
        import torch
        with torch.no_grad():
            image = self._processor[self.model](images=image, return_tensors="pt")
            image.to(torch.accelerator.current_accelerator() or "cpu")
            depth = self._pipelines[self.model](**image)
            return depth.predicted_depth.cpu().numpy()[0]

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter, maximum_filter
        depth = gaussian_filter(input=depth, sigma=0.3)
        depth = maximum_filter(input=depth, size=5)
        return depth

# ---------------------------------------------------------------------------- #

class DepthAnythingV2(DepthAnythingBase):
    """Wrapper for https://github.com/DepthAnything/Depth-Anything-V2"""

    def load_model(self) -> None:
        if self.model not in self._pipelines:
            import torch
            from transformers import AutoImageProcessor, AutoModelForDepthEstimation
            logger.info(f"Loading {type(self).__name__} {self.model}")
            huggingface = f"depth-anything/Depth-Anything-V2-{self.model.value}-hf"
            self._pipelines.setdefault(self.model, AutoModelForDepthEstimation.from_pretrained(huggingface))
            self._processor.setdefault(self.model, AutoImageProcessor.from_pretrained(huggingface))
            self._pipelines[self.model].to(torch.accelerator.current_accelerator() or "cpu")

    def _estimate(self, image: np.ndarray) -> np.ndarray:
        import torch
        with torch.no_grad():
            image = self._processor[self.model](images=image, return_tensors="pt")
            image.to(torch.accelerator.current_accelerator() or "cpu")
            depth = self._pipelines[self.model](**image)
            return depth.predicted_depth.cpu().numpy()[0]

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter, maximum_filter
        depth = gaussian_filter(input=depth, sigma=0.6)
        depth = maximum_filter(input=depth, size=5)
        return depth
