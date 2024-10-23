import DepthFlow.Resources as DepthFlowResources
from Broken import BrokenProject

DEPTHFLOW_ABOUT = """
🌊 Images to → 2.5D Parallax Effect Video. A Free and Open Source ImmersityAI alternative.\n\n
→ See the [blue link=https://brokensrc.dev/depthflow/]Website[/blue link] for examples and more information!\n
"""

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
    ABOUT=DEPTHFLOW_ABOUT,
)

from Broken import BrokenTorch
from DepthFlow.Scene import DepthScene

BrokenTorch.install(exists_ok=True)
