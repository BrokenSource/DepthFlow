from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Optional

import numpy as np
from attr import Factory, define
from imgui_bundle import imgui
from shaderflow.message import ShaderMessage
from shaderflow.scene import ShaderScene
from shaderflow.texture import ShaderTexture
from shaderflow.variable import ShaderVariable
from typer import Option

from broken import Environment, log
from broken.core.vectron import Vectron
from broken.externals.depthmap import (
    DepthAnythingV1,
    DepthAnythingV2,
    DepthEstimator,
    DepthPro,
    Marigold,
    ZoeDepth,
)
from broken.externals.upscaler import (
    BrokenUpscaler,
    NoUpscaler,
    Realesr,
    Upscayl,
    Waifu2x,
)
from depthflow import DEPTHFLOW, DEPTHFLOW_ABOUT
from depthflow.animation import (
    Animation,
    ComponentBase,
    DepthAnimation,
    FilterBase,
    PresetBase,
)
from depthflow.segments import SegmentAnything2, Segmenter
from depthflow.state import DepthState

# -------------------------------------------------------------------------------------------------|

DEFAULT_IMAGE: str = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
DEPTH_SHADER: Path = (DEPTHFLOW.RESOURCES.SHADERS/"depthflow.glsl")

@define
class DepthScene(ShaderScene):
    state:     DepthState     = Factory(DepthState)
    animation: DepthAnimation = Factory(DepthAnimation)
    estimator: DepthEstimator = Factory(DepthAnythingV2)
    segmenter: Segmenter      = Factory(SegmentAnything2)
    upscaler:  BrokenUpscaler = Factory(NoUpscaler)

    # -------------------------------------------------------------------------------------------- #
    # Command line interface

    def commands(self):
        self.cli.description = DEPTHFLOW_ABOUT

        with self.cli.panel(self.scene_panel):
            self.cli.command(self.input)

        with self.cli.panel("🔧 Preloading"):
            self.cli.command(self.load_estimator, hidden=True)
            self.cli.command(self.load_upscaler,  hidden=True)

        with self.cli.panel("🌊 Depth estimator"):
            self.cli.command(DepthAnythingV1, post=self.set_estimator, name="da1")
            self.cli.command(DepthAnythingV2, post=self.set_estimator, name="da2")
            self.cli.command(DepthPro, post=self.set_estimator)
            self.cli.command(ZoeDepth, post=self.set_estimator)
            self.cli.command(Marigold, post=self.set_estimator)

        with self.cli.panel("⭐️ Upscaler"):
            self.cli.command(Realesr, post=self.set_upscaler)
            self.cli.command(Upscayl, post=self.set_upscaler)
            self.cli.command(Waifu2x, post=self.set_upscaler)

        with self.cli.panel("🚀 Animation components"):
            _hidden = Environment.flag("ADVANCED", 0)
            for animation in Animation.members():
                if issubclass(animation, ComponentBase):
                    self.cli.command(animation, post=self.animation.add, hidden=_hidden)

        with self.cli.panel("🔮 Animation presets"):
            for preset in Animation.members():
                if issubclass(preset, PresetBase):
                    self.cli.command(preset, post=self.animation.add)
            self.cli.command(self.animation.clear)

        with self.cli.panel("🎨 Post-processing"):
            for post in Animation.members():
                if issubclass(post, FilterBase):
                    self.cli.command(post, post=self.animation.add)

    def input(self,
        image: Annotated[str, Option("--image", "-i",
            help="[bold green](🟢 Basic)[/] Input image from Path, URL or Directory"
        )]=DEFAULT_IMAGE,
    ) -> None:
        """Use the given image and depthmap as the input of the scene"""
        from scipy.ndimage import gaussian_filter, maximum_filter
        from skimage.transform import resize

        # Get and load the main image, update resolution
        image = np.array(self.upscaler.upscale(image))
        height, width, _  = (image.shape )
        self.resolution   = (width,height)
        self.aspect_ratio = (width/height)
        self.image.from_numpy(image)
        dtype = image.dtype

        # Estimate the base depthmap
        depth = self.estimator.estimate(image)
        depth = resize(depth, (height, width))
        self.depth.from_numpy(depth)
        self.masks.from_numpy(depth)

        # Simple classic mode
        if (self.layers == 1):
            pass

        # Advanced inpainting mode
        # Fixme: Work with float32? But then texture access is hard, improve LoadImage
        elif (self.layers > 1):
            log.info(f"Segmenting the image into {self.layers} layers")
            cutoffs  = np.linspace(1, 0, self.layers, endpoint=0)
            segments = self.segmenter.split(image)
            mask     = np.zeros_like(depth)

            # For each depth cutoff defining a layer
            for layer, (A, B) in enumerate(zip(cutoffs - (1/self.layers), cutoffs)):
                log.info(f"Estimating depthmap for layer {layer}")
                other = self.estimator.estimate(image, cache=False)
                other = resize(other, (height, width))

                # Calculate average depth for the layer
                for segment in segments:
                    average = (np.sum(depth * segment) / np.sum(segment))

                    if (A <= average <= B):
                        segment = maximum_filter(input=segment, size=7)
                        mask = np.where(segment, 1, mask)

                # Apply the mask to the image
                image = np.where(mask[..., None], 0.0, image)
                image = image.astype(dtype)

                # Fixme: Force local consistency in all parts of the depthmap
                # Fit the depthmap to the reference one
                other = Vectron.lstq_masked(
                    base=depth, fill=other,
                    mask=mask.astype(bool)
                )

                # Fixme: Improve .from_numpy to accept a layer and not recreate stuff? or is fine?
                self.image.write(data=np.flipud(image).tobytes(), layer=layer)
                self.depth.write(data=np.flipud(other).tobytes(), layer=layer)
                self.masks.write(data=np.flipud(mask ).tobytes(), layer=layer)

    # -------------------------------------------------------------------------------------------- #
    # Module implementation

    image: ShaderTexture = None
    depth: ShaderTexture = None
    masks: ShaderTexture = None
    layers: int = 6

    def build(self) -> None:
        self.image = ShaderTexture(scene=self, name="image", layers=self.layers).repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth", layers=self.layers).repeat(False)
        self.masks = ShaderTexture(scene=self, name="masks", layers=self.layers).repeat(False)
        self.shader.fragment = DEPTH_SHADER
        self.subsample = 2
        self.runtime = 5.0
        self.ssaa = 1.2

    def setup(self) -> None:
        if (not self.animation):
            self.animation.add(Animation.Orbital())
        self.input()

    def update(self) -> None:
        # self.animation.apply(self)
        ...


    def handle(self, message: ShaderMessage) -> None:
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            self.input(image=message.first, depth=message.second)

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()

    # -------------------------------------------------------------------------------------------- #
    # Proxy methods

    # # Upscalers

    def set_upscaler(self, upscaler: Optional[BrokenUpscaler]=None) -> BrokenUpscaler:
        self.upscaler = (upscaler or NoUpscaler())
        return self.upscaler
    def clear_upscaler(self) -> None:
        self.upscaler = NoUpscaler()
    def load_upscaler(self) -> None:
        self.upscaler.download()

    def realesr(self, **options) -> Realesr:
        return self.set_upscaler(Realesr(**options))
    def upscayl(self, **options) -> Upscayl:
        return self.set_upscaler(Upscayl(**options))
    def waifu2x(self, **options) -> Waifu2x:
        return self.set_upscaler(Waifu2x(**options))

    # # Estimators

    def set_estimator(self, estimator: DepthEstimator) -> DepthEstimator:
        self.estimator = estimator
        return self.estimator
    def load_estimator(self) -> None:
        self.estimator.load_model()

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
