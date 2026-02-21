# pyright: reportMissingImports=false
import contextlib
import os
from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from typing import TYPE_CHECKING, Annotated, Optional

import numpy as np
import xxhash
from diskcache import Cache as DiskCache
from pydantic import BaseModel, Field
from typer import Option

import depthflow
from broken.loaders import LoadableImage, LoadImage

if TYPE_CHECKING:
    import torch

# Shared cache for estimations
DEPTHMAPS: DiskCache = DiskCache(
    directory=depthflow.dirs.user_cache_path.joinpath("depthmaps"),
    size_limit=int(os.getenv("DEPTHMAP_CACHE_SIZE_MB", 20))*(1024**2),
)

class DepthEstimator(BaseModel, ABC):

    class DTypeEnum(str, Enum):
        float64 = "float64"
        float32 = "float32"
        float16 = "float16"
        uint16  = "uint16"
        uint8   = "uint8"

    dtype: Annotated[DTypeEnum, Option("--dtype", "-d")] = Field(DTypeEnum.uint16)
    """The final data format to work, save the depthmap with"""

    @property
    def np_dtype(self) -> np.dtype:
        return getattr(np, self.dtype.value)

    @staticmethod
    def normalize(
        array: np.ndarray,
        dtype: np.dtype=np.float32,
        lerp: np.dtype=np.float64,
        min: Optional[float]=None,
        max: Optional[float]=None,
    ) -> np.ndarray:

        # Get the dtype information
        if np.issubdtype(dtype, np.integer):
            info = np.iinfo(dtype)
        else:
            info = np.finfo(dtype)

        info = (np.iinfo if np.issubdtype(dtype, np.integer) else np.finfo)(dtype)

        # Optionally override target dtype min and max
        min = (info.min if (min is None) else min)
        max = (info.max if (max is None) else max)

        # Work with float64 as array might be low precision
        return np.interp(
            x=array.astype(lerp),
            xp=(np.min(array), np.max(array)),
            fp=(min, max),
        ).astype(dtype)

    def estimate(self,
        image: LoadableImage,
        cache: bool=True,
    ) -> np.ndarray[np.float32]:
        import zlib

        image = LoadImage(image).convert("RGB")

        # Uniquely identify the image and current parameters
        key: int = xxhash.xxh3_64_intdigest(
            self.model_dump_json().encode() +
            image.tobytes()
        )

        # Estimate if not on cache
        if (not cache) or (depth := DEPTHMAPS.get(key)) is None:
            import torch

            # Estimate and convert to target dtype
            depth = self._estimate(image)
            depth = self.normalize(depth, dtype=self.np_dtype)

            # Save the array as a compressed numpy file
            np.save(buffer := BytesIO(), depth, allow_pickle=False)
            DEPTHMAPS.set(key, zlib.compress(
                buffer.getvalue(),
                level=9
            ))
        else:
            # Load the compressed lzma numpy file from cache
            depth = np.load(BytesIO(zlib.decompress(depth)))

        # Optionally thicken the depth map array
        depth = self.normalize(depth, dtype=np.float32, min=0, max=1)
        depth = (self._post(depth) if self.post else depth)
        return depth

    @property
    def device(self) -> str:
        import torch
        with contextlib.suppress(AttributeError):
            return torch.accelerator.current_accelerator().type
        return "cpu"

    @abstractmethod
    def _estimate(self, image: np.ndarray) -> np.ndarray:
        """Proper estimation logic"""
        ...

    post: Annotated[bool, Option("--post", " /--raw")] = Field(True, exclude=True)
    """Apply post-processing to mitigate artifacts"""

    @abstractmethod
    def _post(self, depth: np.ndarray) -> np.ndarray:
        """Post-processing to mitigate artifacts"""
        return depth

    # ------------------------------------------------------------------------ #

    @staticmethod
    def lstsq_masked(
        base: np.ndarray,
        fill: np.ndarray,
        mask: np.ndarray=None,
    ) -> np.ndarray:
        """
        Find the linear system coefficients (A, B) that minimizes
        MSE(base, A*(fill + B)) for the masked pixels
        """

        # Use whole image by default
        if mask is None:
            mask = np.ones_like(base, dtype=bool)

        # Make linear, apply mask
        mask = mask.ravel()
        x = base.ravel()[mask]
        y = fill.ravel()[mask]

        # Fit least squares linear regression
        A = np.column_stack((x, np.ones_like(x)))
        (a, b), *_ = np.linalg.lstsq(A, y)

        # Return opposite effects
        return (fill - b) / (a or 1)
