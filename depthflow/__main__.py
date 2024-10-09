import sys

from broken import BrokenProfiler, BrokenTerminal


def gradio():
    """Run the DepthFlow [bold red]Gradio user interface[/]"""
    from depthflow.webui import DepthGradio

    with BrokenProfiler("DEPTHFLOW"):
        BrokenTerminal.simple(DepthGradio().launch)


def depthflow():
    """Run the DepthFlow [bold red]Command line interface[/]"""
    from depthflow import DepthScene

    with BrokenProfiler("DEPTHFLOW"):
        DepthScene().cli(*sys.argv[1:])

def main():
    BrokenTerminal.release(depthflow, gradio)

if __name__ == "__main__":
    main()
