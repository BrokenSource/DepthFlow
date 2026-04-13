import sys
from typing import Annotated

import cyclopts
from cyclopts import App, Parameter


def scene(*ctx: Annotated[str, Parameter(
    allow_leading_hyphen=True,
    show=False,
)]) -> None:
    """🟢 Run depthflow's command line interface"""
    from depthflow.scene import DepthScene
    DepthScene().cli.meta(ctx)

def main() -> None:
    cli = App(help_flags=[])
    cli.default(scene)
    cli(sys.argv[1:])

if __name__ == "__main__":
    main()
