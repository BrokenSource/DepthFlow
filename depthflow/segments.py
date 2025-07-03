# pyright: reportMissingImports=false
from abc import ABC, abstractmethod
from io import BytesIO
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Iterable,
    TypeAlias,
    Union,
)

import numpy as np
import xxhash
from diskcache import Cache as DiskCache
from pydantic import Field, PrivateAttr
from typer import Option

import broken
from broken import (
    BrokenEnum,
    Environment,
    install,
    log,
)
from broken.core.extra.loaders import LoadableImage, LoadImage
from broken.core.path import BrokenPath
from broken.core.vectron import Vectron
from broken.externals import ExternalModelsBase, ExternalTorchBase
from broken.types import MiB

if TYPE_CHECKING:
    import torch

# ------------------------------------------------------------------------------------------------ #

class SegmenterBase(
    ExternalTorchBase,
    ExternalModelsBase,
    ABC
):
    _cache: DiskCache = PrivateAttr(default_factory=lambda: DiskCache(
        directory=BrokenPath.mkdir(broken.PROJECT.DIRECTORIES.CACHE/"segments"),
        size_limit=int(Environment.float("SEGMENTER_CACHE_SIZE_MB", 50)*MiB),
    ))

    def split(self,
        image: LoadableImage,
        cache: bool=True,
    ) -> np.ndarray:
        import gzip

        # Uniquely identify the image and current parameters
        image = np.array(LoadImage(image).convert("RGB"))
        key: str = f"{hash(self)}{Vectron.image_hash(image)}"
        key: int = xxhash.xxh3_64_intdigest(key)

        # Process input if not on cache
        if (not cache) or (segments := self._cache.get(key)) is None:
            self.load_torch()
            self.load_model()
            segments = np.array(list(self._split(image)))
            np.save(buffer := BytesIO(), segments, allow_pickle=False)
            self._cache.set(key, gzip.compress(buffer.getvalue()))
        else:
            segments = np.load(BytesIO(gzip.decompress(segments)))

        return segments

    @abstractmethod
    def _split(image: LoadableImage) -> Iterable[np.ndarray]:
        """The implementation shall return a bool-like array of the same shape"""
        ...

# ------------------------------------------------------------------------------------------------ #

# Fixme: How to make it output masks that covers the whole image?
# Fixme: SAM2 has no depth or contiguous object awareness, and we kinda need it.
class SegmentAnything2(SegmenterBase):
    class Model(str, BrokenEnum):
        Tiny  = "tiny"
        Small = "small"
        Base  = "base-plus"
        Large = "large"

    model: Annotated[Model, Option("--model", "-m")] = Field(Model.Large)
    """The model of SegmentAnything2 to use"""

    _processor: Any = PrivateAttr(None)

    def _load_model(self) -> None:
        Environment.setdefault("SAM2_BUILD_CUDA", 0)
        install(package="sam2", pypi="git+https://github.com/facebookresearch/sam2@2b90b9")
        log.info(f"Loading SegmentAnything2 model ({self.model})")
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
        self._processor = SAM2AutomaticMaskGenerator.from_pretrained(
            f"facebook/sam2-hiera-{self.model.value}",
            device=self.device,
            points_per_side=16,
            points_per_batch=2,
            # pred_iou_thresh=0.9,
            # stability_score_thresh=0.5,
            # stability_score_offset=0.7,
            # crop_n_layers=1,
            # box_nms_thresh=0.7,
            # crop_n_points_downscale_factor=2,
            # min_mask_region_area=25000,
            # use_m2m=True,
        )

    def _split(self, image: np.ndarray) -> Iterable[np.ndarray]:

        # with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        with torch.inference_mode():
            for data in self._processor.generate(image):
                yield data["segmentation"]

# ------------------------------------------------------------------------------------------------ #

Segmenter: TypeAlias = Union[
    SegmentAnything2,
]
