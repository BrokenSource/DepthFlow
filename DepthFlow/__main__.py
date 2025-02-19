import sys

from Broken import BrokenProfiler, BrokenTorch, BrokenTyper, log


def depthflow() -> None:
    """🚀 Run DepthFlow's [bold green]Command line interface[/]"""
    from DepthFlow.Scene import DepthScene
    DepthScene().cli(*sys.argv[1:])

def gradio() -> None:
    """🎓 Run DepthFlow's [bold green]Gradio user interface[/]"""
    log.minor("Launching the DepthFlow WebUI")
    from DepthFlow.Webui import DepthGradio
    BrokenTyper.simple(DepthGradio().launch)

def main() -> None:
    with BrokenProfiler("DEPTHFLOW"):
        cli = BrokenTyper.toplevel()

        with cli.panel("Commands"):
            cli.command(depthflow, default=True)
            cli.command(gradio)
            cli.command(BrokenTorch.install)

        with cli.panel("Depth Estimators"):
            ...

        with cli.panel("Upscalers"):
            ...

        cli(*sys.argv[1:])

if __name__ == "__main__":
    main()
