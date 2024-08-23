import DepthFlow.Resources as DepthFlowResources
from Broken import BrokenProject

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
)

from DepthFlow.Scene import DepthScene
