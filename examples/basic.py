"""
(c) CC BY-SA 4.0, Tremeschin

This file is the same as running `python -m depthflow (args)`,
or simply `depthflow (args)` from within a venv.
"""
import sys

from depthflow.scene import DepthScene

if __name__ == "__main__":
    scene = DepthScene()
    scene.cli(*sys.argv[1:])
