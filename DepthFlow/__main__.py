import sys

from Broken import BrokenProfiler, BrokenTyper
from DepthFlow import DepthScene


def main_webui():
    from DepthFlow.Webui import DepthWebui

    with BrokenProfiler("DEPTHFLOW"):
        DepthWebui().launch()

def main_cli():
    with BrokenProfiler("DEPTHFLOW"):
        DepthScene().cli(sys.argv[1:])

def main():
    BrokenTyper.release(main_cli)

if __name__ == "__main__":
    main()
