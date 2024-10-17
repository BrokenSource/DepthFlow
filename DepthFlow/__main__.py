import sys

from Broken import BrokenProfiler, BrokenTorch, BrokenTyper
from DepthFlow import DepthScene


def gradio():
    """🎓 Run the DepthFlow [bold green]Gradio user interface[/]"""
    from DepthFlow.Webui import DepthGradio
    BrokenTyper.simple(DepthGradio().launch)

def cli():
    """🚀 Run the DepthFlow [bold green]Command line interface[/]"""
    DepthScene().cli(*sys.argv[1:])

def main():
    with BrokenProfiler("DEPTHFLOW"):
        BrokenTyper.complex(
            main=cli,
            nested=(cli, gradio),
            direct=BrokenTorch.install,
        )

if __name__ == "__main__":
    main()
