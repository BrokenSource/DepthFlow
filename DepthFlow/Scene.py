import copy
import os
from pathlib import Path
from typing import Annotated, Generator, Iterable, List, Optional, Set, Tuple, Union

import numpy
import validators
from attr import define, field
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
    DepthAnythingV1,
    DepthAnythingV2,
    DepthEstimator,
    DepthPro,
    Marigold,
    ZoeDepth,
)
from Broken.Externals.Upscaler import BrokenUpscaler, NoUpscaler, Realesr, Waifu2x
from Broken.Loaders import LoadableImage, LoaderImage
from Broken.Types import FileExtensions
from DepthFlow import DEPTHFLOW, DEPTHFLOW_ABOUT
from DepthFlow.Motion import Animation, Components, Preset, Presets
from DepthFlow.State import DepthState

# -------------------------------------------------------------------------------------------------|

@define
class DepthScene(ShaderScene):
    __name__ = "DepthFlow"

    # Constants
    DEFAULT_IMAGE = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
    DEPTH_SHADER  = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.glsl")

    # DepthFlow objects
    animation: List[Union[Animation, Preset, DepthState]] = field(factory=list)
    estimator: DepthEstimator = field(factory=DepthAnythingV2)
    upscaler: BrokenUpscaler = field(factory=NoUpscaler)
    state: DepthState = field(factory=DepthState)
    _image: Union[LoadableImage, Iterable] = DEFAULT_IMAGE
    _depth: Union[LoadableImage, Iterable] = None

    # -------------------------------------------------------------------------------------------- #
    # Proxy methods

    def add_animation(self, animation: Union[Animation, Preset]) -> object:
        self.animation.append(animation := copy.deepcopy(animation))
        return animation

    def clear_animations(self) -> None:
        self.animation.clear()

    def set_upscaler(self, upscaler: Optional[BrokenUpscaler]) -> None:
        self.upscaler = upscaler or NoUpscaler()

    def clear_upscaler(self) -> None:
        self.upscaler = NoUpscaler()

    def set_estimator(self, estimator: DepthEstimator) -> None:
        self.estimator = estimator

    def load_model(self) -> None:
        self.estimator.load_model()

    # -------------------------------------------------------------------------------------------- #
    # User commands

    def commands(self):
        self.typer.description = DEPTHFLOW_ABOUT
        self.typer.command(self.load_model, hidden=True)

        with self.typer.panel(self.scene_panel):
            self.typer.command(self.input)

        with self.typer.panel("🌊 Depth estimator"):
            self.typer.command(DepthAnythingV1, post=self.set_estimator, name="dav1")
            self.typer.command(DepthAnythingV2, post=self.set_estimator, name="dav2")
            self.typer.command(DepthPro, post=self.set_estimator)
            self.typer.command(ZoeDepth, post=self.set_estimator)
            self.typer.command(Marigold, post=self.set_estimator)

        with self.typer.panel("⭐️ Upscaler"):
            self.typer.command(Realesr, post=self.set_upscaler)
            self.typer.command(Waifu2x, post=self.set_upscaler)

        with self.typer.panel("🚀 Animation (Components, advanced)"):
            hidden = (not eval(os.getenv("ADVANCED", "0")))
            for animation in Components.members():
                self.typer.command(animation, post=self.add_animation, hidden=hidden)

        with self.typer.panel("🔮 Animation presets"):
            for preset in Presets.members():
                self.typer.command(preset, post=self.add_animation)

    def input(self,
        image: Annotated[List[str], Option("--image", "-i",
            help="[bold green](🟢 Basic)[/] Background Image [green](Path, URL, NumPy, PIL)[/]"
        )],
        depth: Annotated[List[str], Option("--depth", "-d",
            help="[bold green](🟢 Basic)[/] Depthmap of the Image [medium_purple3](None to estimate)[/]"
        )]=None,
    ) -> None:
        """Input images from Path, URL, Directories and its estimated Depthmap"""
        self._image = image
        self._depth = depth

    # -------------------------------------------------------------------------------------------- #
    # ShaderFlow Scene implementation

    def build(self):
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.normal = ShaderTexture(scene=self, name="normal")
        self.shader.fragment = self.DEPTH_SHADER
        self.ssaa = 1.2

    def setup(self):
        if (not self.animation):
            self.add_animation(Presets.Orbital())
        self._load_inputs()
        self.time = 0

    # Todo: Overhaul this function
    def animate(self):
        if not self.animation:
            return

        self.state.reset()

        for item in self.animation:
            if issubclass(type(item), DepthState):
                self.state = copy.deepcopy(item)

        for item in self.animation:
            if issubclass(type(item), DepthState):
                continue
            if issubclass(type(item), Preset):
                for animation in item.animation():
                    animation(self)
            else:
                item(self)

    def update(self):
        self.animate()

    def handle(self, message: ShaderMessage):
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            files = iter(message.files)
            self.input(image=next(files), depth=next(files, None))

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()

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
        self.normal.from_numpy(self.estimator.normal_map(depth))
        self.resolution   = (image.width,image.height)
        self.aspect_ratio = (image.width/image.height)
        self.image.from_image(image)
        self.depth.from_image(depth)

        # Default to 1920x1080 on base image
        if (self._image is self.DEFAULT_IMAGE):
            self.resolution   = (1920, 1080)
            self.aspect_ratio = 16/9

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
