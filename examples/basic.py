"""
(c) CC BY-SA 4.0, Tremeschin

This file is the same as running `python -m DepthFlow (args)` or just `depthflow (args)`
from within a venv. You can also run this directly with `python Basic.py (args)`
"""
import sys

from depthflow.scene import DepthScene

if __name__ == "__main__":
    scene = DepthScene()
    scene.cli(sys.argv[1:])
