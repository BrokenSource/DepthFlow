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

def server() -> None:
    """🌐 Run DepthFlow's [bold green]API Server[/]"""
    log.minor("Launching the DepthFlow API Server")
    from DepthFlow.Server import DepthServer
    DepthServer().cli(*sys.argv[1:])

def main() -> None:
    with BrokenProfiler("DEPTHFLOW"):
        BrokenTyper.complex(
            main=depthflow,
            nested=(depthflow, gradio, server),
            simple=BrokenTorch.install,
        )

if __name__ == "__main__":
    main()
