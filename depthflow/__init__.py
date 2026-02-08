from dearlog import logger  # isort: split

import importlib.metadata

from broken.project import BrokenProject

__version__ = importlib.metadata.version(__package__)

DEPTHFLOW_ABOUT = "🌊 Images to 3D Parallax effect video"

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    ABOUT=DEPTHFLOW_ABOUT,
)

from broken.pytorch import BrokenTorch

BrokenTorch.install(exists_ok=True)
