from Broken import BrokenProfiler
from DepthFlow import DepthScene


def main():
    with BrokenProfiler("DEPTHFLOW"):
        DepthScene().cli()

if __name__ == "__main__":
    main()
