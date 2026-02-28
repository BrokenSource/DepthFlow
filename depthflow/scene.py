import contextlib
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Any

import imageio.v3 as imageio
import pooch
from attrs import Factory, define
from cyclopts import Parameter
from imgui_bundle import imgui
from shaderflow.message import ShaderMessage
from shaderflow.scene import ShaderScene
from shaderflow.texture import ShaderTexture
from shaderflow.variable import ShaderVariable

import depthflow
from depthflow.animation import (
    Animation,
    DepthAnimation,
    FilterBase,
    PresetBase,
)
from depthflow.estimators import DepthEstimator
from depthflow.estimators.anything import (
    DepthAnythingV1,
    DepthAnythingV2,
    DepthAnythingV3,
)
from depthflow.estimators.depthpro import DepthPro
from depthflow.estimators.marigold import Marigold
from depthflow.estimators.zoedepth import ZoeDepth
from depthflow.state import DepthState


class Assets:
    """Copyright property of the original owners"""

    def background() -> Path:
        return pooch.retrieve(
            url="https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png",
            known_hash="xxh128:6fe8d585cfc4b8fc623b5450d06bcdc4",
            path=depthflow.directories.user_data_path,
            fname="wallhaven-pkz5r9.png",
            progressbar=True,
        )

# ---------------------------------------------------------------------------- #

@define
class DepthScene(ShaderScene):
    state:     DepthState     = Factory(DepthState)
    estimator: DepthEstimator = Factory(DepthAnythingV2)
    animation: DepthAnimation = Factory(DepthAnimation)

    def smartset(self, object: Any) -> Any:
        if isinstance(object, DepthEstimator):
            self.estimator = object
        return object

    # ------------------------------------------------------------------------ #
    # Command line interface

    def commands(self):
        self.cli.help = depthflow.__about__
        self.cli.version = depthflow.__version__
        self.cli.command(self.input)

        with contextlib.nullcontext("🌊 Depth Estimator") as group:
            options = dict(group=group, result_action=self.smartset)
            self.cli.command(DepthAnythingV1, name="da1",      **options)
            self.cli.command(DepthAnythingV2, name="da2",      **options)
            self.cli.command(DepthAnythingV3, name="da3",      **options)
            self.cli.command(DepthPro,        name="depthpro", **options)
            self.cli.command(ZoeDepth,        name="zoedepth", **options)
            self.cli.command(Marigold,        name="marigold", **options)

        with contextlib.nullcontext("🎬 Animation presets") as group:
            for preset in Animation.members():
                if issubclass(preset, PresetBase):
                    self.cli.command(preset, group=group, result_action=self.animation.add)

        with contextlib.nullcontext("🎨 Post-processing") as group:
            for post in Animation.members():
                if issubclass(post, FilterBase):
                    self.cli.command(post, group=group, result_action=self.animation.add)

    def input(self,
        image: Annotated[str, Parameter(
            help="Input image from Path, NumPy, URL (None to default)",
            name=("--image", "-i"))] = None,
        depth: Annotated[str, Parameter(
            help="Input depthmap of the image (None to estimate)",
            name=("--depth", "-d"))] = None,
    ) -> None:
        """Use the given image(s) and depthmap(s) as the input of the scene"""
        if (image is None):
            image = Assets.background()

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
        if (not self.animation.steps):
            self.animation.add(Animation.Orbital())
        if self.image.is_empty():
            self.input()

    def update(self) -> None:
        self.animation.apply(self)

    def handle(self, message: ShaderMessage) -> None:
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            self.input(image=message.first, depth=message.second)
            self._load_inputs()

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()

    # ------------------------------------------------------------------------ #

    def ui(self) -> None:
        if (state := imgui.slider_float("Height", self.state.height, 0, 1, "%.2f"))[0]:
            self.state.height = state[1]
        if (state := imgui.slider_float("Steady", self.state.steady, 0, 1, "%.2f"))[0]:
            self.state.steady = state[1]
        if (state := imgui.slider_float("Focus", self.state.focus, 0, 1, "%.2f"))[0]:
            self.state.focus = state[1]
        if (state := imgui.slider_float("Invert", self.state.invert, 0, 1, "%.2f"))[0]:
            self.state.invert = state[1]
        if (state := imgui.slider_float("Zoom", self.state.zoom, 0, 2, "%.2f"))[0]:
            self.state.zoom = state[1]
        if (state := imgui.slider_float("Isometric", self.state.isometric, 0, 1, "%.2f"))[0]:
            self.state.isometric = state[1]
        if (state := imgui.slider_float("Dolly", self.state.dolly, 0, 5, "%.2f"))[0]:
            self.state.dolly = state[1]

        imgui.text("- True camera position")
        if (state := imgui.slider_float("Center X", self.state.center_x, -self.aspect_ratio, self.aspect_ratio, "%.2f"))[0]:
            self.state.center_x = state[1]
        if (state := imgui.slider_float("Center Y", self.state.center_y, -1, 1, "%.2f"))[0]:
            self.state.center_y = state[1]

        imgui.text("- Fixed point at height changes")
        if (state := imgui.slider_float("Origin X", self.state.origin_x, -self.aspect_ratio, self.aspect_ratio, "%.2f"))[0]:
            self.state.origin_x = state[1]
        if (state := imgui.slider_float("Origin Y", self.state.origin_y, -1, 1, "%.2f"))[0]:
            self.state.origin_y = state[1]

        imgui.text("- Parallax offset")
        if (state := imgui.slider_float("Offset X", self.state.offset_x, -2, 2, "%.2f"))[0]:
            self.state.offset_x = state[1]
        if (state := imgui.slider_float("Offset Y", self.state.offset_y, -2, 2, "%.2f"))[0]:
            self.state.offset_y = state[1]
