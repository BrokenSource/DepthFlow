import sys

from Broken import BrokenProfiler, BrokenTyper


def gradio():
    """Run the DepthFlow [bold red]Gradio user interface[reset]"""
    from DepthFlow.Webui import DepthGradio

    with BrokenProfiler("DEPTHFLOW"):
        BrokenTyper.simple(DepthGradio().launch)


def depthflow():
    """Run the DepthFlow [bold red]Command line interface[reset]"""
    from DepthFlow import DepthScene

    with BrokenProfiler("DEPTHFLOW"):
        DepthScene().cli(*sys.argv[1:])

def main():
    BrokenTyper.release(depthflow, gradio)

if __name__ == "__main__":
    main()
