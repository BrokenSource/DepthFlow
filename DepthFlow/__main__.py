import sys

from Broken.Base import BrokenProfiler
from DepthFlow import DEPTHFLOW
from DepthFlow.DepthFlow import DepthFlowScene


def main():
    with BrokenProfiler("DEPTHFLOW"):
        DEPTHFLOW.welcome()
        depthflow = DepthFlowScene()
        depthflow.cli(sys.argv[1:])

if __name__ == "__main__":
    main()
