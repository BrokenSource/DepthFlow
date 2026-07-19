from dearlog import logger  # isort: split

__about__   = "🌊 Images to 3D parallax effect videos"
__package__ = "depthflow"
__version__ = "1.0.0"
__license__ = "AGPL-3.0"

from pathlib import Path

from platformdirs import PlatformDirs

resources = Path(__file__).parent/"resources"

dirs = PlatformDirs(
    appname=__package__,
    ensure_exists=True,
    opinion=True,
)

import os

# macOS: Enable CPU fallback for unsupported operations in MPS
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Make telemetries opt-in
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

# Note: We don't import DepthScene for pure estimators usage,
#   to avoid importing shaderflow, moderngl, imgui, etc.
