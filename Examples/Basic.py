"""
(c) CC BY-SA 4.0, Tremeschin

Simple example of running DepthFlow default implementation

Note: This file is the same as running `python -m DepthFlow` or just `depthflow` with the pyproject
    scripts entry points when on the venv. You can also run this directly with `python Basic.py`

• For more information, visit https://brokensrc.dev/depthflow
"""
import sys

from DepthFlow.Scene import DepthScene

if __name__ == "__main__":
    scene = DepthScene()
    scene.cli(sys.argv[1:])
