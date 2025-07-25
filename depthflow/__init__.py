from broken import BrokenProject, __version__

DEPTHFLOW_ABOUT = "🌊 Images to 3D Parallax effect video"

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    ABOUT=DEPTHFLOW_ABOUT,
)

from broken.core.pytorch import BrokenTorch

BrokenTorch.install(exists_ok=True)
