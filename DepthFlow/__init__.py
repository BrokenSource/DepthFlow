import DepthFlow.Resources as DepthFlowResources
import torch
import transformers
from ShaderFlow import *

import Broken
from Broken import *

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
)

Broken.PROJECT = DEPTHFLOW

# isort: off
from .Modules import *
from .DepthFlow import *
