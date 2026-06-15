import os
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import xxhash
from diskcache import Cache as DiskCache
from numpy.typing import DTypeLike
from pydantic import BaseModel

import depthflow

DEPTHMAPS: DiskCache = DiskCache(
    directory=depthflow.dirs.user_cache_path.joinpath("depthmaps"),
    size_limit=int(os.getenv("DEPTHMAP_CACHE_SIZE_MB", 32))*(1024**2),
)

class DepthEstimator(BaseModel, ABC):

    @abstractmethod
    def __hash__(self) -> int:
        """Deterministic hash for current settings"""
        ...

    def estimate(self, image: np.ndarray) -> np.ndarray:
        hasher = xxhash.xxh3_64()
        hasher.update(str(self.__hash__()))
        hasher.update(image.tobytes())
        key: int = hasher.intdigest()

        # Grab only rgb channels
        if (image.shape[-1] == 4):
            image = image[..., :3]

        # Avoid expensive methods when cached
        if (depth := DEPTHMAPS.get(key)) is None:
            self.load_model()
            depth = self._estimate(image)
            depth = self.normalize(depth)
            DEPTHMAPS.set(key, depth)

        # Normalized f32 for GPU
        depth = self.normalize(
            array=depth,
            dtype=np.float32,
            min=0.0, max=1.0
        )

        return self._post(depth)

    @abstractmethod
    def load_model(self) -> None:
        ...

    @abstractmethod
    def _estimate(self, image: np.ndarray) -> np.ndarray:
        """Proper estimation logic"""
        ...

    def _post(self, depth: np.ndarray) -> np.ndarray:
        """Post-processing to mitigate artifacts"""
        return depth

    @staticmethod
    def normalize(
        array: np.ndarray,
        dtype: DTypeLike=np.float32,
        lerp: DTypeLike=np.float64,
        min: Optional[float]=None,
        max: Optional[float]=None,
    ) -> np.ndarray:

        # Get the dtype information
        if np.issubdtype(dtype, np.integer):
            info = np.iinfo(dtype) # type: ignore
        else:
            info = np.finfo(dtype) # type: ignore

        # Optionally override target dtype min and max
        min = (info.min if (min is None) else min) # type: ignore
        max = (info.max if (max is None) else max) # type: ignore

        # Work with float64 as array might be low precision
        return np.interp(
            x=array.astype(lerp),
            xp=(np.min(array), np.max(array)),
            fp=(min, max),
        ).astype(dtype) # type: ignore
