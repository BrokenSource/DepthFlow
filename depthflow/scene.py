from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Optional

import numpy as np
import validators
from attr import Factory, define
from imgui_bundle import imgui
from PIL.Image import Image as ImageType
from pydantic import Field
from shaderflow.exceptions import ShaderBatchStop
from shaderflow.message import ShaderMessage
from shaderflow.scene import ShaderScene
from shaderflow.texture import ShaderTexture
from shaderflow.variable import ShaderVariable
from typer import Option

from broken import BrokenPath, Environment, flatten, list_get
from broken.core.extra.loaders import LoadableImage, LoadImage
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
from broken.types import FileExtensions, PydanticImage
from depthflow import DEPTHFLOW, DEPTHFLOW_ABOUT
from depthflow.animation import (
    Animation,
    ComponentBase,
    DepthAnimation,
    FilterBase,
    PresetBase,
)
from depthflow.state import DepthState

# -------------------------------------------------------------------------------------------------|

DEFAULT_IMAGE: str = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
DEPTH_SHADER: Path = (DEPTHFLOW.RESOURCES.SHADERS/"depthflow.glsl")

@define
class DepthScene(ShaderScene):
    state: DepthState = Factory(DepthState)

    class Config(ShaderScene.Config):
        image:     Iterable[PydanticImage] = DEFAULT_IMAGE
        depth:     Iterable[PydanticImage] = None
        estimator: DepthEstimator = Field(default_factory=DepthAnythingV2)
        animation: DepthAnimation = Field(default_factory=DepthAnimation)
        upscaler:  BrokenUpscaler = Field(default_factory=NoUpscaler)

    # Redefinition for type hinting
    config: Config = Factory(Config)

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
                    self.cli.command(animation, post=self.config.animation.add, hidden=_hidden)

        with self.cli.panel("🔮 Animation presets"):
            for preset in Animation.members():
                if issubclass(preset, PresetBase):
                    self.cli.command(preset, post=self.config.animation.add)

        with self.cli.panel("🎨 Post-processing"):
            for post in Animation.members():
                if issubclass(post, FilterBase):
                    self.cli.command(post, post=self.config.animation.add)

    def input(self,
        image: Annotated[list[str], Option("--image", "-i",
            help="[bold green](🟢 Basic)[/] Input image from Path, URL or Directory"
        )],
        depth: Annotated[list[str], Option("--depth", "-d",
            help="[bold green](🟢 Basic)[/] Input depthmap of the image [medium_purple3](None to estimate)[/]"
        )]=None,
    ) -> None:
        """Use the given image(s) and depthmap(s) as the input of the scene"""
        self.config.image = image
        self.config.depth = depth

    # -------------------------------------------------------------------------------------------- #
    # Module implementation

    def build(self) -> None:
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.shader.fragment = DEPTH_SHADER
        self.subsample = 2
        self.runtime = 5.0
        self.ssaa = 1.2

    def setup(self) -> None:
        if (not self.config.animation):
            self.config.animation.add(Animation.Orbital())
        self._load_inputs()

    def update(self) -> None:
        self.config.animation.apply(self)

    def handle(self, message: ShaderMessage) -> None:
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            self.input(image=message.first, depth=message.second)
            self._load_inputs()

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()

    # -------------------------------------------------------------------------------------------- #
    # Proxy methods

    # # Upscalers

    def set_upscaler(self, upscaler: Optional[BrokenUpscaler]=None) -> BrokenUpscaler:
        self.config.upscaler = (upscaler or NoUpscaler())
        return self.config.upscaler
    def clear_upscaler(self) -> None:
        self.config.upscaler = NoUpscaler()
    def load_upscaler(self) -> None:
        self.config.upscaler.download()

    def realesr(self, **options) -> Realesr:
        return self.set_upscaler(Realesr(**options))
    def upscayl(self, **options) -> Upscayl:
        return self.set_upscaler(Upscayl(**options))
    def waifu2x(self, **options) -> Waifu2x:
        return self.set_upscaler(Waifu2x(**options))

    # # Estimators

    def set_estimator(self, estimator: DepthEstimator) -> DepthEstimator:
        self.config.estimator = estimator
        return self.config.estimator
    def load_estimator(self) -> None:
        self.config.estimator.load_model()

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
        return self.config.animation.add(Animation.Set(**options))
    def add(self, **options) -> Animation.Add:
        return self.config.animation.add(Animation.Add(**options))

    # Basic
    def linear(self, **options) -> Animation.Linear:
        return self.config.animation.add(Animation.Linear(**options))
    def sine(self, **options) -> Animation.Sine:
        return self.config.animation.add(Animation.Sine(**options))
    def cosine(self, **options) -> Animation.Cosine:
        return self.config.animation.add(Animation.Cosine(**options))
    def triangle(self, **options) -> Animation.Triangle:
        return self.config.animation.add(Animation.Triangle(**options))

    # Presets
    def vertical(self, **options) -> Animation.Vertical:
        return self.config.animation.add(Animation.Vertical(**options))
    def horizontal(self, **options) -> Animation.Horizontal:
        return self.config.animation.add(Animation.Horizontal(**options))
    def zoom(self, **options) -> Animation.Zoom:
        return self.config.animation.add(Animation.Zoom(**options))
    def circle(self, **options) -> Animation.Circle:
        return self.config.animation.add(Animation.Circle(**options))
    def dolly(self, **options) -> Animation.Dolly:
        return self.config.animation.add(Animation.Dolly(**options))
    def orbital(self, **options) -> Animation.Orbital:
        return self.config.animation.add(Animation.Orbital(**options))

    # Post-processing
    def vignette(self, **options) -> Animation.Vignette:
        return self.config.animation.add(Animation.Vignette(**options))
    def blur(self, **options) -> Animation.Blur:
        return self.config.animation.add(Animation.Blur(**options))
    def inpaint(self, **options) -> Animation.Inpaint:
        return self.config.animation.add(Animation.Inpaint(**options))
    def colors(self, **options) -> Animation.Colors:
        return self.config.animation.add(Animation.Colors(**options))

    # -------------------------------------------------------------------------------------------- #
    # Internal batch exporting

    def _load_inputs(self, echo: bool=True) -> None:
        """Load inputs: single or batch exporting"""

        # Batch exporting implementation
        image = self._get_batch_input(self.config.image)
        depth = self._get_batch_input(self.config.depth)

        if (image is None):
            raise ShaderBatchStop()

        self.log_info(f"Loading image: {image}", echo=echo)
        self.log_info(f"Loading depth: {depth or 'Estimating from image'}", echo=echo)

        # Load, estimate, upscale input image
        image = self.config.upscaler.upscale(LoadImage(image))
        depth = LoadImage(depth) or self.config.estimator.estimate(image)

        # Match rendering resolution to image
        self.resolution   = (image.width,image.height)
        self.aspect_ratio = (image.width/image.height)
        self.image.from_image(image)
        self.depth.from_image(depth)

        # Default to 1920x1080 on base image
        if (self.config.image is DEFAULT_IMAGE):
            self.resolution   = (1920, 1080)
            self.aspect_ratio = (16/9)

    def export_name(self, path: Path) -> Path:
        """Modifies the output path if on batch exporting mode"""
        options = list(self._iter_batch_input(self.config.image))

        # Single file mode, return as-is
        if (len(options) == 1):
            return path

        # Assume it's a local path
        image = Path(options[self.index])
        original = image.stem

        # Use the URL filename as base
        if validators.url(image):
            original = BrokenPath.url_filename(image)

        # Build the batch filename: 'file' + -'custom stem'
        return path.with_stem(original + "-" + path.stem)

    def _iter_batch_input(self, item: Optional[LoadableImage]) -> Iterable[LoadableImage]:
        if (item is None):
            return None

        # Recurse on multiple inputs
        if isinstance(item, (list, tuple, set)):
            for part in item:
                yield from self._iter_batch_input(part)

        # Return known valid inputs as is
        elif isinstance(item, (bytes, ImageType, np.ndarray)):
            yield item
        elif validators.url(item):
            yield item

        # Valid directory on disk
        elif (path := BrokenPath.get(item, exists=True)):
            if (path.is_dir()):
                files = (path.glob("*" + x) for x in FileExtensions.Image)
                yield from sorted(flatten(files))
            else:
                yield path

        # Interpret as a glob pattern
        elif ("*" in str(item)):
            yield from sorted(path.parent.glob(path.name))
        else:
            self.log_minor(f"Assuming {item} is an iterable, could go wrong..")
            yield from item

    def _get_batch_input(self, item: LoadableImage) -> Optional[LoadableImage]:
        return list_get(list(self._iter_batch_input(item)), self.index)

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
