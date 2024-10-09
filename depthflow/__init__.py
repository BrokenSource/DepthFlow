import depthflow.resources as resources
from broken import BrokenProject

DEPTHFLOW_ABOUT = """
🌊 Image to → 2.5D Parallax Effect Video. A Free and Open Source ImmersityAI alternative.\n

Usage: All commands have a --help option with extensible configuration, and are chained together.
→ See the [blue link=https://brokensrc.dev/depthflow/]Website[/blue link] for examples and more information!\n
"""

DEPTHFLOW = BrokenProject(
    package=__file__,
    name="DepthFlow",
    author="BrokenSource",
    resources=resources,
    about=DEPTHFLOW_ABOUT,
)

from broken import BrokenTorch
from depthflow.scene import DepthScene

BrokenTorch.install()
