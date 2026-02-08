from dearlog import logger  # isort: split

import os
from importlib.metadata import metadata

__meta__:   dict = metadata(__package__)
__about__:   str = __meta__["Summary"]
__author__:  str = __meta__["Author"]
__version__: str = __meta__["Version"]

from broken.project import BrokenProject

# macOS: Enable CPU fallback for unsupported operations in MPS
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Make telemetries opt-in instead of opt-out
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    ABOUT=__about__,
)

from broken.pytorch import BrokenTorch

BrokenTorch.install(exists_ok=True)
