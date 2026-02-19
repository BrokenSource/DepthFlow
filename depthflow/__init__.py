from dearlog import logger  # isort: split

from importlib.metadata import metadata

__meta__:   dict = metadata(__package__)
__about__:   str = __meta__.get("Summary")
__author__:  str = __meta__.get("Author")
__version__: str = __meta__.get("Version")

from pathlib import Path

RESOURCES: Path = Path(__file__).parent/"resources"

import os

# macOS: Enable CPU fallback for unsupported operations in MPS
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Make telemetries opt-in
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from broken.pytorch import BrokenTorch

BrokenTorch.install(exists_ok=True)
