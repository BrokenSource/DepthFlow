import sys

from Broken import BrokenProfiler, BrokenTyper
from DepthFlow import DepthScene


def gradio():
    """Run the DepthFlow [bold red]Gradio user interface[reset]"""
    from DepthFlow.Webui import DepthWebui

    with BrokenProfiler("DEPTHFLOW"):
        DepthWebui().launch()

def depthflow():
    """Run the DepthFlow [bold red]Command line interface[reset]"""
    with BrokenProfiler("DEPTHFLOW"):
        DepthScene().cli(*sys.argv[1:])

def main():
    BrokenTyper.release(depthflow, gradio)

if __name__ == "__main__":
    main()
