import sys

from Broken import BrokenProfiler
from DepthFlow import DepthScene


def main():
    with BrokenProfiler("DEPTHFLOW"):
        depthflow = DepthScene()
        depthflow.cli(sys.argv[1:])

if __name__ == "__main__":
    main()
