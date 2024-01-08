from DepthFlow import *


def main():
    with BrokenProfiler("DEPTHFLOW"):
        DEPTHFLOW.welcome()
        depthflow = DepthFlowScene()
        depthflow.cli(sys.argv[1:])

if __name__ == "__main__":
    main()
