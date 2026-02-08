from dearlog import logger  # isort: split

import importlib.metadata
import os

from broken.project import BrokenProject

__version__: str = importlib.metadata.version(__package__)
__about__:   str = "🌊 Images to 3D Parallax effect video"

# macOS: Enable CPU fallback for unsupported operations in MPS
# - https://pytorch.org/docs/stable/mps_environment_variables.html
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
