import os

import DepthFlow.Resources as DepthFlowResources

# -------------------------------------------------------------------------------------------------|
# Hack to install path dependencies at runtime.
while bool(os.environ.get("PYAPP", False)):
    try:
        import Broken
        break
    except ImportError:
        print("Installing path dependencies... (Any errors should be ok to ignore)")

    import importlib.resources
    import subprocess
    import sys

    # Fixme: Why PYAPP_PASS_LOCATION isn't passed on Linux?
    if os.name != "nt":
        sys.argv = sys.argv[1:]
        sys.argv.insert(0, sys.executable)

    # Pip acronym and install maybe required packages
    PIP = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--quiet"]

    # Install bundled wheels.. in our wheel
    for wheel in (importlib.resources.files(DepthFlowResources)/"Wheels").glob("*.whl"):
        subprocess.run(PIP + [str(wheel)])
    break
# -------------------------------------------------------------------------------------------------|

import gradio
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
from .Modules import *
from .DepthFlow import *
