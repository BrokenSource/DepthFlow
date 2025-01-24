import DepthFlow.Resources as DepthFlowResources
from Broken import BrokenProject, __version__

__version__ = __version__

DEPTHFLOW_ABOUT = """
🌊 Images to → 2.5D Parallax Effect Video. A Free and Open Source ImmersityAI alternative.\n\n
→ See the [blue link=https://brokensrc.dev/depthflow/]Website[/] for examples and more information!\n
"""

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
    ABOUT=DEPTHFLOW_ABOUT,
)

from Broken import BrokenTorch

BrokenTorch.install(exists_ok=True)
