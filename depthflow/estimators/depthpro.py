# pyright: reportMissingImports=false
import copy
import subprocess
import sys
from typing import Any

import numpy as np
from PIL import Image
from pydantic import PrivateAttr

from broken import logger
from broken.path import BrokenPath
from broken.resolution import BrokenResolution
from depthflow.estimators import DepthEstimator


class DepthPro(DepthEstimator):
    """Configure and use DepthPro estimator"""
    # https://github.com/apple/ml-depth-pro

    _model: Any = PrivateAttr(None)
    _transform: Any = PrivateAttr(None)

    def _load_model(self) -> None:
        subprocess.run((
            sys.executable, "-m", "uv", "pip", "install",
            "git+https://github.com/apple/ml-depth-pro"
        ))

        # Download external checkpoint model
        logger.info("Loading Depth Estimator model (DepthPro)")
        checkpoint = BrokenPath.get_external("https://ml-site.cdn-apple.com/models/depth-pro/depth_pro.pt")

        import torch
        from depth_pro import create_model_and_transforms
        from depth_pro.depth_pro import DEFAULT_MONODEPTH_CONFIG_DICT

        # Change the checkpoint URI to the downloaded checkpoint
        config = copy.deepcopy(DEFAULT_MONODEPTH_CONFIG_DICT)
        config.checkpoint_uri = checkpoint

        self._model, self._transform = create_model_and_transforms(
            precision=torch.float16,
            device=self.device,
            config=config
        )
        self._model.eval()

    def _estimate(self, image: np.ndarray) -> np.ndarray:

        # Infer, transfer to CPU, invert depth values
        depth = self._model.infer(self._transform(image))["depth"]
        depth = depth.detach().cpu().numpy().squeeze()
        depth = (np.max(depth) - depth)

        # Limit resolution to 1024 as there's no gains in interpoilation
        depth = np.array(Image.fromarray(depth).resize(BrokenResolution.fit(
            old=depth.shape, max=(1024, 1024),
            ar=(depth.shape[1]/depth.shape[0]),
        ), resample=Image.LANCZOS))

        return depth

    def _post(self, depth: np.ndarray) -> np.ndarray:
        from scipy.ndimage import maximum_filter
        depth = maximum_filter(input=depth, size=5)
        return depth
