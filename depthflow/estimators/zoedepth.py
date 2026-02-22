# pyright: reportMissingImports=false
import subprocess
import sys
from enum import Enum
from typing import TYPE_CHECKING, Annotated

import numpy as np
from PIL import Image
from pydantic import Field
from shaderflow.resolution import Resolution
from typer import Option

from depthflow import logger
from depthflow.estimators import DepthEstimator

if TYPE_CHECKING:
    import torch

class ZoeDepth(DepthEstimator):
    """Configure and use ZoeDepth estimator"""
    # https://github.com/isl-org/ZoeDepth

    class Model(str, Enum):
        N  = "n"
        K  = "k"
        NK = "nk"

    model: Annotated[Model, Option("--model", "-m")] = Field(Model.N)
    """Model of ZoeDepth to use"""

    def model_post_init(self) -> None:
        subprocess.run((
            sys.executable, "-m", "uv", "pip", "install",
            "timm==0.6.7", "torchvision==0.15.2",
            "--no-deps",
        ))

        logger.info(f"Loading Depth Estimator model (ZoeDepth-{self.model.value})")
        self._model = torch.hub.load(
            "isl-org/ZoeDepth", f"ZoeD_{self.model.value.upper()}",
            pretrained=True, trust_repo=True
        ).to(self.device)

    # Downscale for the largest component to be 512 pixels (Zoe precision), invert for 0=infinity
    def _estimate(self, image: np.ndarray) -> np.ndarray:
        depth = Image.fromarray(1 - DepthEstimator.normalize(self._model.infer_pil(image)))
        new = Resolution.fit(old=depth.size, max=(512, 512), ar=depth.size[0]/depth.size[1])
        return np.array(depth.resize(new, resample=Image.LANCZOS)).astype(np.float32)
