"""
Simple example of running DepthFlow defaults

Note: This file is the same as running `python -m DepthFlow` or just `depthflow` with the pyproject
    scripts entry points when on the venv. You can also run this directly with `python Base.py`

For more documentation, visit https://brokensrc.dev/depthflow
"""
from DepthFlow import DepthScene

if __name__ == "__main__":
    scene = DepthScene()
    scene.cli()
