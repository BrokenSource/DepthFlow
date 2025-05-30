import sys

from broken import (
    BrokenTorch,
    BrokenTyper,
    log,
)

# -----------------------------------------------|

def depthflow() -> None:
    """🚀 Run DepthFlow's [bold green]Command line interface[/]"""
    from depthflow.scene import DepthScene
    DepthScene().cli(*sys.argv[1:])

def gradio() -> None:
    """🎓 Run DepthFlow's [bold green]Gradio user interface[/]"""
    log.minor("Launching the DepthFlow WebUI")
    from depthflow.webui import DepthGradio
    BrokenTyper.simple(DepthGradio().launch)

def estimator() -> None:
    """🔎 Estimate depthmaps of general images"""
    from broken.externals.depthmap import (
        DepthAnythingV1,
        DepthAnythingV2,
        DepthPro,
        Marigold,
        ZoeDepth,
    )
    cli = BrokenTyper(description=estimator.__doc__)
    DepthAnythingV2.cli(cli, name="anything2")
    DepthAnythingV1.cli(cli, name="anything1")
    DepthPro.cli(cli, name="depthpro")
    Marigold.cli(cli, name="marigold")
    ZoeDepth.cli(cli, name="zoedepth")
    cli(*sys.argv[1:])

def upscaler() -> None:
    """✨ Upscale images to higher resolutions"""
    from broken.externals.upscaler import Realesr, Upscayl, Waifu2x
    cli = BrokenTyper(description=upscaler.__doc__)
    Realesr.cli(cli, name="realesr")
    Upscayl.cli(cli, name="upscayl")
    Waifu2x.cli(cli, name="waifu2x")
    cli(*sys.argv[1:])

# -----------------------------------------------|

def main() -> None:
    cli = BrokenTyper.toplevel()

    with cli.panel("Commands"):
        cli.command(depthflow, default=True)
        cli.command(gradio)
        cli.direct_script()

    with cli.panel("Tools"):
        cli.command(BrokenTorch.install)
        cli.command(estimator)
        cli.command(upscaler)

    cli(*sys.argv[1:])

if __name__ == "__main__":
    main()
