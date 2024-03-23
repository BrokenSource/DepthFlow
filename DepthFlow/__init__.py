from ShaderFlow import *

import Broken
from Broken import *

_spinner = yaspin(text="Loading Library: DepthFlow")
_spinner.start()

import DepthFlow.Resources as DepthFlowResources
import transformers

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
from ShaderFlow.Optional.Monocular import Monocular
from .DepthFlow import *

_spinner.stop()
