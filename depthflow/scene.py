from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

from attrs import Factory, define
from imgui_bundle import imgui
from shaderflow.message import ShaderMessage
from shaderflow.scene import ShaderScene
from shaderflow.texture import ShaderTexture
from shaderflow.variable import ShaderVariable
from typer import Option

import depthflow
from broken.loaders import LoadImage
from depthflow import logger
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

DEFAULT_IMAGE: str = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
DEPTH_SHADER: Path = (depthflow.resources/"depthflow.glsl")

@define
class DepthScene(ShaderScene):
    state:     DepthState     = Factory(DepthState)
    estimator: DepthEstimator = Factory(DepthAnythingV2)
    animation: DepthAnimation = Factory(DepthAnimation)

    # ------------------------------------------------------------------------ #
    # Command line interface

    def commands(self):
        self.cli.description = depthflow.__about__

        with self.cli.panel(self.scene_panel):
            self.cli.command(self.input)

        with self.cli.panel("🌊 Depth estimator"):
            self.cli.command(DepthAnythingV1, post=self.set_estimator, name="da1")
            self.cli.command(DepthAnythingV2, post=self.set_estimator, name="da2")
            self.cli.command(DepthAnythingV3, post=self.set_estimator, name="da3")
            self.cli.command(DepthPro, post=self.set_estimator)
            self.cli.command(ZoeDepth, post=self.set_estimator)
            self.cli.command(Marigold, post=self.set_estimator)

        with self.cli.panel("🔮 Animation presets"):
            self.cli.command(self.animation.clear)
            for preset in Animation.members():
                if issubclass(preset, PresetBase):
                    self.cli.command(preset, post=self.animation.add)

        with self.cli.panel("🎨 Post-processing"):
            for post in Animation.members():
                if issubclass(post, FilterBase):
                    self.cli.command(post, post=self.animation.add)

    def input(self,
        image: Annotated[str, Option("--image", "-i", help="Input image from Path, URL or Directory")]=DEFAULT_IMAGE,
        depth: Annotated[str, Option("--depth", "-d", help="Input depthmap of the image (None to estimate)")]=None,
    ) -> None:
        """Use the given image(s) and depthmap(s) as the input of the scene"""
        logger.info(f"Loading image: {image}")
        logger.info(f"Loading depth: {depth or 'Estimating from image'}")

        # Load, estimate, upscale input image
        image = LoadImage(image)
        depth = LoadImage(depth) or self.estimator.estimate(image)

        self.image.from_image(image)
        self.depth.from_image(depth)

        # Match rendering resolution to image
        if (image is not DEFAULT_IMAGE):
            self.resolution = (image.width,image.height)
        else:
            self.resolution = (1920, 1080)

    # ------------------------------------------------------------------------ #
    # Module implementation

    def build(self) -> None:
        self.depth = ShaderTexture(scene=self, name="depth", anisotropy=1).repeat(False)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.shader.fragment = DEPTH_SHADER
        self.subsample = 2
        self.runtime = 5.0
        self.ssaa = 1.2

    def setup(self) -> None:
        if (not self.animation.steps):
            self.animation.add(Animation.Orbital())
        if self.image.is_empty():
            self.input(image=DEFAULT_IMAGE)

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
    # Proxy methods

    # # Estimators

    def set_estimator(self, estimator: DepthEstimator) -> DepthEstimator:
        self.estimator = estimator
        return self.estimator

    def depth_anything1(self, **options) -> DepthAnythingV1:
        return self.set_estimator(DepthAnythingV1(**options))
    def depth_anything2(self, **options) -> DepthAnythingV2:
        return self.set_estimator(DepthAnythingV2(**options))
    def depth_pro(self, **options) -> DepthPro:
        return self.set_estimator(DepthPro(**options))
    def zoe_depth(self, **options) -> ZoeDepth:
        return self.set_estimator(ZoeDepth(**options))
    def marigold(self, **options) -> Marigold:
        return self.set_estimator(Marigold(**options))

    # # Animations

    # Constant
    def set(self, **options) -> Animation.Set:
        return self.animation.add(Animation.Set(**options))
    def add(self, **options) -> Animation.Add:
        return self.animation.add(Animation.Add(**options))

    # Basic
    def linear(self, **options) -> Animation.Linear:
        return self.animation.add(Animation.Linear(**options))
    def sine(self, **options) -> Animation.Sine:
        return self.animation.add(Animation.Sine(**options))
    def cosine(self, **options) -> Animation.Cosine:
        return self.animation.add(Animation.Cosine(**options))
    def triangle(self, **options) -> Animation.Triangle:
        return self.animation.add(Animation.Triangle(**options))

    # Presets
    def vertical(self, **options) -> Animation.Vertical:
        return self.animation.add(Animation.Vertical(**options))
    def horizontal(self, **options) -> Animation.Horizontal:
        return self.animation.add(Animation.Horizontal(**options))
    def zoom(self, **options) -> Animation.Zoom:
        return self.animation.add(Animation.Zoom(**options))
    def circle(self, **options) -> Animation.Circle:
        return self.animation.add(Animation.Circle(**options))
    def dolly(self, **options) -> Animation.Dolly:
        return self.animation.add(Animation.Dolly(**options))
    def orbital(self, **options) -> Animation.Orbital:
        return self.animation.add(Animation.Orbital(**options))

    # Post-processing
    def vignette(self, **options) -> Animation.Vignette:
        return self.animation.add(Animation.Vignette(**options))
    def blur(self, **options) -> Animation.Blur:
        return self.animation.add(Animation.Blur(**options))
    def inpaint(self, **options) -> Animation.Inpaint:
        return self.animation.add(Animation.Inpaint(**options))
    def colors(self, **options) -> Animation.Colors:
        return self.animation.add(Animation.Colors(**options))

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
