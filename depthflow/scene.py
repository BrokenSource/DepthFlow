import contextlib
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, Optional

import numpy as np
from attrs import Factory, define, field
from cyclopts import Parameter
from PIL.Image import Image as PilImage
from shaderflow.message import ShaderMessage
from shaderflow.scene import ShaderScene
from shaderflow.texture import ShaderTexture
from shaderflow.variable import ShaderVariable

import depthflow
from depthflow.estimators import DepthEstimator
from depthflow.estimators.anything import (
    DepthAnythingV1,
    DepthAnythingV2,
)
from depthflow.state import DepthState


@define
class DepthScene(ShaderScene):

    state: DepthState = Factory(DepthState)
    """Parallax shader uniform values"""

    estimator: DepthEstimator = Factory(DepthAnythingV2)
    """Model used to estimate depthmaps from input images"""

    def smartset(self, object: Any) -> Any:
        if isinstance(object, DepthEstimator):
            self.estimator = object
        elif isinstance(object, DepthState):
            self.state = object
        return object

    # ------------------------------------------------------------------------ #

    def commands(self):
        self.cli.help = depthflow.__about__
        self.cli.version = depthflow.__version__
        self.cli.command(self.input)
        self.cli.command(DepthState, name="state", result_action=self.smartset)

        with contextlib.nullcontext("🌊 Depth Estimator") as group:
            self.cli.command(DepthAnythingV1, name="da1", group=group, result_action=self.smartset)
            self.cli.command(DepthAnythingV2, name="da2", group=group, result_action=self.smartset)

    def input(self,
        image: Annotated[Optional[Path | PilImage | np.ndarray | str | BytesIO | bytes], Parameter(
            help="Input image from Path, NumPy, URL (None to default)",
            name=("--image", "-i"))],
        depth: Annotated[Optional[Path | PilImage |np.ndarray | str | BytesIO | bytes], Parameter(
            help="Input depthmap of the image (None to estimate)",
            name=("--depth", "-d"))] = None,
    ) -> None:
        """Use the given image and depthmap on the scene"""
        self.initialize()

        # Default image, property of the original owners
        if (image is None):
            import pooch
            image = Path(pooch.retrieve(
                url="https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png",
                known_hash="xxh128:6fe8d585cfc4b8fc623b5450d06bcdc4",
                path=depthflow.dirs.user_cache_path,
                fname="wallhaven-pkz5r9.png",
                progressbar=True,
            ))

        import imageio.v3 as imageio

        # Load estimate input image
        if isinstance(image, PilImage):
            image = np.array(image)
        elif not isinstance(image, np.ndarray):
            image = imageio.imread(image)

        if depth is None:
            depth = self.estimator.estimate(image)
        elif isinstance(depth, PilImage):
            depth = np.array(depth)
        elif not isinstance(depth, np.ndarray):
            depth = imageio.imread(depth)

        self.image.from_numpy(image)
        self.depth.from_numpy(depth)

        # Match rendering resolution to image
        self.resolution = self.image.size

    # ------------------------------------------------------------------------ #

    image: ShaderTexture = field(init=False)
    depth: ShaderTexture = field(init=False)

    def build(self) -> None:
        self.depth = ShaderTexture(scene=self, name="depth", anisotropy=1).repeat(False)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.shader.fragment = (depthflow.resources/"depthflow.glsl")
        self.runtime = 5.0

    def setup(self) -> None:
        if self.image.is_empty():
            self.input(None)

    def update(self) -> None:
        # Animation code here!
        ...

    def handle(self, message: ShaderMessage) -> None:
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            self.input(image=message.first, depth=message.second)

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()
