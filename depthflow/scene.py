import contextlib
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Any, Optional

import imageio.v3 as imageio
import pooch
from attrs import Factory, define
from cyclopts import Parameter
from shaderflow.message import ShaderMessage
from shaderflow.scene import ShaderScene
from shaderflow.texture import ShaderTexture
from shaderflow.variable import ShaderVariable

import depthflow
from depthflow.animation import Action, DepthAnimation
from depthflow.estimators import DepthEstimator
from depthflow.estimators.anything import (
    DepthAnythingV1,
    DepthAnythingV2,
    DepthAnythingV3,
)
from depthflow.state import DepthState


@define
class DepthScene(ShaderScene):
    state:     DepthState     = Factory(DepthState)
    estimator: DepthEstimator = Factory(DepthAnythingV2)
    animation: DepthAnimation = Factory(DepthAnimation)

    def smartset(self, object: Any) -> Any:
        if isinstance(object, DepthEstimator):
            self.estimator = object
        elif isinstance(object, DepthState):
            self.state = object
        return object

    # ------------------------------------------------------------------------ #
    # Command line interface

    def commands(self):
        self.cli.help = depthflow.__about__
        self.cli.version = depthflow.__version__
        self.cli.command(self.input)
        self.cli.command(DepthState, name="state", result_action=self.smartset)

        with contextlib.nullcontext("🌊 Depth Estimator") as group:
            self.cli.command(DepthAnythingV1, name="da1", group=group, result_action=self.smartset)
            self.cli.command(DepthAnythingV2, name="da2", group=group, result_action=self.smartset)
            self.cli.command(DepthAnythingV3, name="da3", group=group, result_action=self.smartset)

        with contextlib.nullcontext("Animation") as group:
            for cls in Action.__subclasses__():
                self.cli.command(cls, group=group, result_action=self.animation.steps.append)

    def input(self,
        image: Annotated[Optional[Path | str], Parameter(
            help="Input image from Path, NumPy, URL (None to default)",
            name=("--image", "-i"))],
        depth: Annotated[Optional[str], Parameter(
            help="Input depthmap of the image (None to estimate)",
            name=("--depth", "-d"))] = None,
    ) -> None:
        """Use the given image(s) and depthmap(s) as the input of the scene"""

        # Default image, property of the original owners
        if (image is None):
            image = Path(pooch.retrieve(
                url="https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png",
                known_hash="xxh128:6fe8d585cfc4b8fc623b5450d06bcdc4",
                path=depthflow.directories.user_data_path,
                fname="wallhaven-pkz5r9.png",
                progressbar=True,
            ))

        # Load estimate input image
        image = imageio.imread(image)
        depth = imageio.imread(depth) \
            if (depth is not None) else \
            self.estimator.estimate(image)

        self.image.from_numpy(image)
        self.depth.from_numpy(depth)

        # Match rendering resolution to image
        self.resolution = self.image.size

    # ------------------------------------------------------------------------ #
    # Module implementation

    def build(self) -> None:
        self.depth = ShaderTexture(scene=self, name="depth", anisotropy=1).repeat(False)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.shader.fragment = (depthflow.resources/"depthflow.glsl")
        self.runtime = 5.0

    def setup(self) -> None:
        if self.image.is_empty():
            self.input(None)

    def update(self) -> None:
        self.animation.apply(self.state, self.tau)

    def handle(self, message: ShaderMessage) -> None:
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            self.input(image=message.first, depth=message.second)

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()
