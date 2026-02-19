# pyright: reportMissingImports=false
import subprocess
import sys
from enum import Enum
from typing import TYPE_CHECKING, Annotated

import numpy as np
from PIL import Image
from pydantic import Field
from typer import Option

from depthflow import logger
from depthflow.estimators import DepthEstimator

if TYPE_CHECKING:
    import diffusers
    import torch

class Marigold(DepthEstimator):
    """Configure and use Marigold estimator"""
    # https://github.com/prs-eth/Marigold

    class Variant(str, Enum):
        FP16 = "fp16"
        FP32 = "fp32"

    variant: Annotated[Variant, Option("--variant", "-v",
        help="What variant of Marigold to use")] = \
        Field(Variant.FP16)

    def model_post_init(self) -> None:
        subprocess.run((
            sys.executable, "-m", "uv", "pip", "install",
            "accelerate", "diffusers", "matplotlib",
        ))

        from diffusers import DiffusionPipeline

        logger.info("Loading Depth Estimator model (Marigold)")

        self._model = DiffusionPipeline.from_pretrained(
            "prs-eth/marigold-depth-lcm-v1-0",
            custom_pipeline="marigold_depth_estimation",
            torch_dtype=dict(
                fp16=torch.float16,
                fp32=torch.float32,
            )[self.variant.value],
            variant=self.variant.value,
        ).to(self.device)

    def _estimate(self, image: np.ndarray) -> np.ndarray:
        return (1 - self._model(
            Image.fromarray(image),
            match_input_res=False,
            show_progress_bar=True,
            color_map=None,
        ).depth_np)

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import gaussian_filter, maximum_filter
        depth = gaussian_filter(input=depth, sigma=0.6)
        depth = maximum_filter(input=depth, size=5)
        return depth
