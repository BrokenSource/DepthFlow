from ShaderFlow import *

import Broken
from Broken import *

_spinner = yaspin(text="Loading Library: DepthFlow")
_spinner.start()

import DepthFlow.Resources as DepthFlowResources

DEPTHFLOW = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="DepthFlow",
    APP_AUTHOR="BrokenSource",
    RESOURCES=DepthFlowResources,
)

Broken.PROJECT = DEPTHFLOW

_spinner.stop()
BrokenTorch.manage(DEPTHFLOW.RESOURCES)
_spinner.start()

# isort: off
import torch
from .Modules import *
from .DepthFlow import *

_spinner.stop()
