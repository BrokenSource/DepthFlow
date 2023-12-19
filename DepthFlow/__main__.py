from DepthFlow import *


def main():
    depthflow = DepthFlowScene()
    depthflow.cli(sys.argv[1:])

if __name__ == "__main__":
    main()
