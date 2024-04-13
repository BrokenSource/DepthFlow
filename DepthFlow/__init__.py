
import Broken
import DepthFlow.Resources as DepthFlowResources
from Broken import BrokenProject, BrokenTorch

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
)

Broken.set_project(DEPTHFLOW)
BrokenTorch.manage(DEPTHFLOW.RESOURCES)
