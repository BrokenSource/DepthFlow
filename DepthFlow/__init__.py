import DepthFlow.Resources as DepthFlowResources
import torch
import transformers
from ShaderFlow import *

from Broken import *

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
)

from .DepthFlowMDE import *
from .DepthFlowScene import *
