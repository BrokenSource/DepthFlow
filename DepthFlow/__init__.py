from ShaderFlow import *

import Broken
from Broken import *

_spinner = yaspin(text="Initializing Library: DepthFlow")
_spinner.start()

import DepthFlow.Resources as DepthFlowResources
import torch
import transformers

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

_spinner.stop()
