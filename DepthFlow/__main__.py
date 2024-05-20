import sys

from Broken import BrokenProfiler
from DepthFlow.DepthFlow import DepthFlowScene


def main():
    with BrokenProfiler("DEPTHFLOW"):
        depthflow = DepthFlowScene()
        depthflow.cli(sys.argv[1:])

if __name__ == "__main__":
    main()
