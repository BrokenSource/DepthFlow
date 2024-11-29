import functools
import os
from pathlib import Path
from typing import Annotated, Generator, Iterable, List, Optional, Set, Tuple, Union

import numpy
import validators
from attr import Factory, define
from imgui_bundle import imgui
from PIL.Image import Image
from ShaderFlow.Exceptions import ShaderBatchStop
from ShaderFlow.Message import ShaderMessage
from ShaderFlow.Scene import ShaderScene
from ShaderFlow.Texture import ShaderTexture
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken import BrokenPath, flatten, list_get
from Broken.Externals.Depthmap import (
    BaseEstimator,
    DepthAnythingV1,
    DepthAnythingV2,
    DepthPro,
    Marigold,
    ZoeDepth,
)
from Broken.Externals.Upscaler import (
    BrokenUpscaler,
    NoUpscaler,
    Realesr,
    Upscayl,
    Waifu2x,
)
from Broken.Loaders import LoadableImage, LoaderImage
from Broken.Types import FileExtensions
from DepthFlow import DEPTHFLOW, DEPTHFLOW_ABOUT
from DepthFlow.Animation import (
    Actions,
    ComponentBase,
    DepthAnimation,
    FilterBase,
    PresetBase,
)
from DepthFlow.State import DepthState

# -------------------------------------------------------------------------------------------------|

@define
class DepthScene(ShaderScene):
    __name__ = "DepthFlow"

    # Constants
    DEFAULT_IMAGE = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
    DEPTH_SHADER  = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.glsl")

    # DepthFlow objects
    animation: DepthAnimation = Factory(DepthAnimation)
    estimator: BaseEstimator = Factory(DepthAnythingV2)
    upscaler: BrokenUpscaler = Factory(NoUpscaler)
    state: DepthState = Factory(DepthState)
    _image: Iterable[LoadableImage] = DEFAULT_IMAGE
    _depth: Iterable[Iterable] = None

    # -------------------------------------------------------------------------------------------- #
    # User commands

    def commands(self):
        self.cli.description = DEPTHFLOW_ABOUT
        self.cli.command(self.load_model, hidden=True)

        with self.cli.panel(self.scene_panel):
            self.cli.command(self.input)

        with self.cli.panel("🌊 Depth estimator"):
            self.cli.command(DepthAnythingV1, post=self.set_estimator, name="any1")
            self.cli.command(DepthAnythingV2, post=self.set_estimator, name="any2")
            self.cli.command(DepthPro, post=self.set_estimator)
            self.cli.command(ZoeDepth, post=self.set_estimator)
            self.cli.command(Marigold, post=self.set_estimator)

        with self.cli.panel("⭐️ Upscaler"):
            self.cli.command(Realesr, post=self.set_upscaler)
            self.cli.command(Upscayl, post=self.set_upscaler)
            self.cli.command(Waifu2x, post=self.set_upscaler)

        with self.cli.panel("🚀 Animation components"):
            _hidden = (not eval(os.getenv("ADVANCED", "0")))
            for animation in Actions.members():
                if issubclass(animation, ComponentBase):
                    self.cli.command(animation, post=self.animation.add, hidden=_hidden)

        with self.cli.panel("🔮 Animation presets"):
            for preset in Actions.members():
                if issubclass(preset, PresetBase):
                    self.cli.command(preset, post=self.animation.add)

        with self.cli.panel("🎨 Post-processing"):
            for post in Actions.members():
                if issubclass(post, FilterBase):
                    self.cli.command(post, post=self.animation.add)

    def input(self,
        image: Annotated[List[str], Option("--image", "-i",
            help="[bold green](🟢 Basic)[/] Background Image [green](Path, URL, NumPy, PIL)[/]"
        )],
        depth: Annotated[List[str], Option("--depth", "-d",
            help="[bold green](🟢 Basic)[/] Depthmap of the Image [medium_purple3](None to estimate)[/]"
        )]=None,
    ) -> None:
        """Input images from Path, URL, Directories and its estimated Depthmap (Lazy load)"""
        self._image = image
        self._depth = depth

    # -------------------------------------------------------------------------------------------- #
    # ShaderFlow Scene implementation

    def build(self) -> None:
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.shader.fragment = self.DEPTH_SHADER
        self.ssaa = 1.2

    def setup(self) -> None:
        if (not self.animation):
            self.animation.add(Actions.Orbital())
        self._load_inputs()

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

    # -------------------------------------------------------------------------------------------- #
    # Proxy methods

    # # Upscalers

    def set_upscaler(self, upscaler: Optional[BrokenUpscaler]=None) -> BrokenUpscaler:
        self.upscaler = (upscaler or NoUpscaler())
        return self.upscaler
    def clear_upscaler(self) -> None:
        self.upscaler = NoUpscaler()

    # Options
    def realesr(self, **options) -> Realesr:
        return self.set_upscaler(Realesr(**options))
    def upscayl(self, **options) -> Upscayl:
        return self.set_upscaler(Upscayl(**options))
    def waifu2x(self, **options) -> Waifu2x:
        return self.set_upscaler(Waifu2x(**options))

    # # Estimators

    def set_estimator(self, estimator: BaseEstimator) -> BaseEstimator:
        self.estimator = estimator
        return self.estimator
    def load_model(self) -> None:
        self.estimator.load_model()

    # Options
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
    def set(self, **options) -> Actions.Set:
        return self.animation.add(Actions.Set(**options))
    def add(self, **options) -> Actions.Add:
        return self.animation.add(Actions.Add(**options))

    # Basic
    def linear(self, **options) -> Actions.Linear:
        return self.animation.add(Actions.Linear(**options))
    def sine(self, **options) -> Actions.Sine:
        return self.animation.add(Actions.Sine(**options))
    def cosine(self, **options) -> Actions.Cosine:
        return self.animation.add(Actions.Cosine(**options))
    def triangle(self, **options) -> Actions.Triangle:
        return self.animation.add(Actions.Triangle(**options))

    # Presets
    def vertical(self, **options) -> Actions.Vertical:
        return self.animation.add(Actions.Vertical(**options))
    def horizontal(self, **options) -> Actions.Horizontal:
        return self.animation.add(Actions.Horizontal(**options))
    def zoom(self, **options) -> Actions.Zoom:
        return self.animation.add(Actions.Zoom(**options))
    def circle(self, **options) -> Actions.Circle:
        return self.animation.add(Actions.Circle(**options))
    def dolly(self, **options) -> Actions.Dolly:
        return self.animation.add(Actions.Dolly(**options))
    def orbital(self, **options) -> Actions.Orbital:
        return self.animation.add(Actions.Orbital(**options))

    # Post-processing
    def vignette(self, **options) -> Actions.Vignette:
        return self.animation.add(Actions.Vignette(**options))
    def blur(self, **options) -> Actions.Blur:
        return self.animation.add(Actions.Blur(**options))
    def inpaint(self, **options) -> Actions.Inpaint:
        return self.animation.add(Actions.Inpaint(**options))
    def colors(self, **options) -> Actions.Colors:
        return self.animation.add(Actions.Colors(**options))

    # -------------------------------------------------------------------------------------------- #
    # Internal batch exporting

    def _load_inputs(self) -> None:
        """Load inputs: single or batch exporting"""
        image = self._get_batch_input(self._image)
        depth = self._get_batch_input(self._depth)
        if (image is None):
            raise ShaderBatchStop()
        self.log_info(f"Loading image: {image}")
        self.log_info(f"Loading depth: {depth or 'Estimating from image'}")
        image = self.upscaler.upscale(LoaderImage(image))
        depth = LoaderImage(depth) or self.estimator.estimate(image)
        self.resolution   = (image.width,image.height)
        self.aspect_ratio = (image.width/image.height)
        self.image.from_image(image)
        self.depth.from_image(depth)

        # Default to 1920x1080 on base image
        if (self._image is self.DEFAULT_IMAGE):
            self.resolution   = (1920, 1080)
            self.aspect_ratio = (16/9)

    def export_name(self, path: Path) -> Path:
        """Modifies the output path if on batch exporting mode"""
        options = list(self._itr_batch_input(self._image))

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

    def _itr_batch_input(self, item: Optional[LoadableImage]) -> Generator[LoadableImage, None, None]:
        if (item is None):
            return None

        # Recurse on multiple inputs
        if isinstance(item, (List, Tuple, Set)):
            for part in item:
                yield from self._itr_batch_input(part)

        # Return known valid inputs as is
        elif isinstance(item, (bytes, Image, numpy.ndarray)):
            yield item
        elif validators.url(item):
            yield item

        # Valid directory on disk
        elif (path := BrokenPath.get(item)).exists():
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
        return list_get(list(self._itr_batch_input(item)), self.index)

    def ui(self) -> None:
        if (state := imgui.slider_float("Height", self.state.height, 0, 1, "%.2f"))[0]:
            self.state.height = max(0, state[1])
        if (state := imgui.slider_float("Steady", self.state.steady, 0, 1, "%.2f"))[0]:
            self.state.steady = max(0, state[1])
        if (state := imgui.slider_float("Focus", self.state.focus, 0, 1, "%.2f"))[0]:
            self.state.focus = max(0, state[1])
        if (state := imgui.slider_float("Invert", self.state.invert, 0, 1, "%.2f"))[0]:
            self.state.invert = max(0, state[1])
        if (state := imgui.slider_float("Zoom", self.state.zoom, 0, 2, "%.2f"))[0]:
            self.state.zoom = max(0, state[1])
        if (state := imgui.slider_float("Isometric", self.state.isometric, 0, 1, "%.2f"))[0]:
            self.state.isometric = max(0, state[1])
        if (state := imgui.slider_float("Dolly", self.state.dolly, 0, 5, "%.2f"))[0]:
            self.state.dolly = max(0, state[1])

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
