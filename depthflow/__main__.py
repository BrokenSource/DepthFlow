import sys

from broken.pytorch import BrokenTorch
from broken.typerx import BrokenTyper
from depthflow import logger


def depthflow() -> None:
    """🚀 Run DepthFlow's Command Line Interface"""
    from depthflow.scene import DepthScene
    DepthScene().cli(*sys.argv[1:])

def gradio() -> None:
    """🎓 Run DepthFlow's Gradio user interface"""
    logger.note("Launching the DepthFlow WebUI")
    from depthflow.webui import DepthGradio
    BrokenTyper.simple(DepthGradio().launch)

def main() -> None:
    cli = BrokenTyper.toplevel()

    with cli.panel("Commands"):
        cli.command(depthflow, default=True)
        cli.command(gradio)
        cli.direct_script()

    with cli.panel("Tools"):
        cli.command(BrokenTorch.install)

    cli(*sys.argv[1:])

if __name__ == "__main__":
    main()
