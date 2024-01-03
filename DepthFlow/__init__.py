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

# isort: off
from .DepthFlowMDE import *
from .DepthFlow import *
