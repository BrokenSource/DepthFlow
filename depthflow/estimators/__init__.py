# pyright: reportMissingImports=false
import contextlib
import multiprocessing
import os
import tempfile
from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import numpy as np
import xxhash
from diskcache import Cache as DiskCache
from pydantic import BaseModel, Field
from typer import Option

from broken.loaders import LoadableImage, LoadImage
from broken.vectron import Vectron

if TYPE_CHECKING:
    import torch

# Shared cache for estimations
DEPTHMAPS: DiskCache = DiskCache(
    directory=Path(tempfile.gettempdir()).joinpath("depthflow.sqlite"),
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

    def estimate(self,
        image: LoadableImage,
        cache: bool=True,
    ) -> np.ndarray[np.float32]:
        import lzma

        image = LoadImage(image).convert("RGB")

        # Uniquely identify the image and current parameters
        key: int = xxhash.xxh3_64_intdigest(
            self.model_dump_json().encode() +
            image.tobytes()
        )

        # Estimate if not on cache
        if (not cache) or (depth := DEPTHMAPS.get(key)) is None:
            import torch
            torch.set_num_threads(multiprocessing.cpu_count())

            # Estimate and convert to target dtype
            depth = self._estimate(image)
            depth = Vectron.normalize(depth, dtype=self.np_dtype)

            # Save the array as a compressed numpy file
            np.save(buffer := BytesIO(), depth, allow_pickle=False)
            DEPTHMAPS.set(key, lzma.compress(buffer.getvalue()))
        else:
            # Load the compressed lzma numpy file from cache
            depth = np.load(BytesIO(lzma.decompress(depth)))

        # Optionally thicken the depth map array
        depth = Vectron.normalize(depth, dtype=np.float32, min=0, max=1)
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
