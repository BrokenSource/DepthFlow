# pyright: reportMissingImports=false
import subprocess
import sys
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Annotated

import numpy as np
from pydantic import Field
from typer import Option

from depthflow import logger
from depthflow.estimators import DepthEstimator

if TYPE_CHECKING:
    import torch

# ---------------------------------------------------------------------------- #

class DepthAnythingBase(DepthEstimator):

    class Model(str, Enum):
        Small = "small"
        Base  = "base"
        Large = "large"

    model: Annotated[Model, Option("--model", "-m")] = Field(Model.Small)
    """The model of DepthAnything to use"""

    @property
    @abstractmethod
    def _huggingface_model(self) -> str:
        ...

    def load_model(self) -> None:
        import transformers
        logger.info(f"Loading Depth Estimator model ({self._huggingface_model})")
        if (self.model != self.Model.Small):
            logger.warn("[bold light_coral]• This depth estimator model is licensed under CC BY-NC 4.0 (non-commercial)[/]")
        self._processor = transformers.AutoImageProcessor.from_pretrained(self._huggingface_model, use_fast=False)
        self._model = transformers.AutoModelForDepthEstimation.from_pretrained(self._huggingface_model)
        self._model.to(self.device)

    def _estimate(self, image: np.ndarray) -> np.ndarray:
        import torch
        self.load_model()
        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.no_grad():
            depth = self._model(**inputs).predicted_depth
        return depth.squeeze(1).cpu().numpy()[0]

# ---------------------------------------------------------------------------- #
# https://github.com/LiheYoung/Depth-Anything

class DepthAnythingV1(DepthAnythingBase):
    """Configure and use DepthAnythingV1"""

    sigma: Annotated[float, Option("--sigma", "-s")] = Field(0.3)
    """Gaussian blur intensity to smoothen the depthmap"""

    thicken: Annotated[int, Option("--thicken", "-t")] = Field(5)
    """Maximum-kernel size to thicken the depthmap edges"""

    @property
    def _huggingface_model(self) -> str:
        return f"LiheYoung/depth-anything-{self.model.value}-hf"

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter, maximum_filter
        depth = gaussian_filter(input=depth, sigma=self.sigma)
        depth = maximum_filter(input=depth, size=self.thicken)
        return depth

# ---------------------------------------------------------------------------- #
# https://github.com/DepthAnything/Depth-Anything-V2

class DepthAnythingV2(DepthAnythingBase):
    """Configure and use DepthAnythingV2"""

    sigma: Annotated[float, Option("--sigma", "-s")] = Field(0.6)
    """Gaussian blur intensity to smoothen the depthmap"""

    thicken: Annotated[int, Option("--thicken", "-t")] = Field(5)
    """Maximum-kernel size to thicken the depthmap edges"""

    @property
    def _huggingface_model(self) -> str:
        return f"depth-anything/Depth-Anything-V2-{self.model.value}-hf"

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter, maximum_filter
        depth = gaussian_filter(input=depth, sigma=self.sigma)
        depth = maximum_filter(input=depth, size=self.thicken)
        return depth

# ---------------------------------------------------------------------------- #
# https://github.com/ByteDance-Seed/depth-anything-3

class DepthAnythingV3(DepthEstimator):
    """Configure and use DepthAnythingV3"""

    class Model(str, Enum):
        Small = "small"
        Base  = "base"
        Large = "large"
        Giant = "giant"

    model: Annotated[Model, Option("--model", "-m")] = Field(Model.Small)
    """The model of DepthAnything3 to use"""

    resolution: Annotated[int, Option("--resolution", "-r")] = Field(1024)
    """Resolution of the depthmap, better results but slower and memory intensive"""

    sigma: Annotated[float, Option("--sigma", "-s")] = Field(0.3)
    """Gaussian blur intensity to smoothen the depthmap"""

    thicken: Annotated[int, Option("--thicken", "-t")] = Field(5)
    """Maximum-kernel size to thicken the depthmap edges"""

    def _load_model(self) -> None:
        try:
            import depth_anything_3
        except ImportError:
            subprocess.run((
                sys.executable, "-m", "uv", "pip", "install",
                "git+https://github.com/BrokenSource/Depth-Anything-3",
            ))
        if (self.model != self.Model.Small):
            logger.warn("[bold light_coral]• This depth estimator model is licensed under CC BY-NC 4.0 (non-commercial)[/]")
        from depth_anything_3.api import DepthAnything3
        self._model = DepthAnything3.from_pretrained(f"depth-anything/da3-{self.model.value}")
        self._model.to(self.device)

    def _estimate(self, image: np.ndarray) -> np.ndarray:
        prediction = self._model.inference(
            image=[image],
            process_res=self.resolution,
            export_format="npz",
            use_ray_pose=True,
        )
        depth = prediction.depth[0]
        depth = 1.0 / depth
        return depth

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter, maximum_filter
        depth = gaussian_filter(input=depth, sigma=self.sigma)
        depth = maximum_filter(input=depth, size=self.thicken)
        return depth
