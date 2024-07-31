from __future__ import annotations

import copy
import math
from typing import Annotated, Iterable, List, Union

import imgui
from attr import define, field
from ShaderFlow.Message import ShaderMessage
from ShaderFlow.Scene import ShaderScene
from ShaderFlow.Texture import ShaderTexture
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken.Externals.Depthmap import (
    DepthAnythingV1,
    DepthAnythingV2,
    DepthEstimator,
    Marigold,
    ZoeDepth,
)
from Broken.Externals.Upscaler import BrokenUpscaler, NoUpscaler, Realesr, Waifu2x
from Broken.Loaders import LoaderImage
from DepthFlow import DEPTHFLOW
from DepthFlow.Animation import (
    Constant,
    DepthAnimation,
    DepthPreset,
    Linear,
    Sine,
)
from DepthFlow.State import DepthState

DEPTHFLOW_ABOUT = """
🌊 Image to → 2.5D Parallax Effect Video. High quality, user first.\n

Usage: Chain commands, at minimum just [green]main[/green] for a realtime window, drag and drop images
• The --main command is used for exporting videos, setting quality, resolution
• All commands have a --help option with extensible configuration

Examples:
• Upscaler:    (depthflow realesr --scale 2 input -i ~/image.png main -o ./output.mp4 --ssaa 1.5)
• Convenience: (depthflow input -i ~/image16x9.png main -h 1440) [bright_black]# Auto calculates w=2560[/bright_black]
• Estimator:   (depthflow dav2 --model large input -i ~/image.png main)
• Post FX:     (depthflow dof -e vignette -e main)

Notes:
• The rendered video loops perfectly, the duration is the main's --time
• The last two commands must be --input and --main in order to work
"""

# -------------------------------------------------------------------------------------------------|

@define
class DepthScene(ShaderScene):
    __name__ = "DepthFlow"

    # Constants
    DEFAULT_IMAGE = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
    DEPTH_SHADER  = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.glsl")

    # DepthFlow objects
    animation: List[Union[DepthAnimation, DepthPreset]] = field(factory=list)
    estimator: DepthEstimator = field(factory=DepthAnythingV2)
    upscaler: BrokenUpscaler = field(factory=NoUpscaler)
    state: DepthState = field(factory=DepthState)

    def add_animation(self, animation: DepthAnimation) -> None:
        self.animation.append(copy.deepcopy(animation))

    def set_upscaler(self, upscaler: BrokenUpscaler) -> None:
        self.upscaler = upscaler

    def set_estimator(self, estimator: DepthEstimator) -> None:
        self.estimator = estimator

    def input(self,
        image: Annotated[str, Option("--image", "-i", help="Background Image [green](Path, URL, NumPy, PIL)[/green]")],
        depth: Annotated[str, Option("--depth", "-d", help="Depthmap of the Image [medium_purple3](None to estimate)[/medium_purple3]")]=None,
    ) -> None:
        """Load an Image from Path, URL and its estimated Depthmap [green](See 'input --help' for options)[/green]"""
        image = self.upscaler.upscale(LoaderImage(image))
        depth = LoaderImage(depth) or self.estimator.estimate(image)
        self.aspect_ratio = (image.width/image.height)
        self.normal.from_numpy(self.estimator.normal_map(depth))
        self.image.from_image(image)
        self.depth.from_image(depth)

    def commands(self):
        self.typer.description = DEPTHFLOW_ABOUT
        self.typer.command(self.input)
        self.typer.command(self.state, name="config")

        with self.typer.panel("🌊 Depth estimators"):
            self.typer.command(DepthAnythingV1, post=self.set_estimator, name="dav1")
            self.typer.command(DepthAnythingV2, post=self.set_estimator, name="dav2")
            self.typer.command(ZoeDepth, post=self.set_estimator)
            self.typer.command(Marigold, post=self.set_estimator)

        with self.typer.panel("⭐️ Upscalers"):
            self.typer.command(Realesr, post=self.set_upscaler)
            self.typer.command(Waifu2x, post=self.set_upscaler)

        with self.typer.panel("🔮 Animation (Components)"):
            self.typer.command(Linear,   post=self.add_animation)
            self.typer.command(Constant, post=self.add_animation)
            self.typer.command(Sine,     post=self.add_animation)

        with self.typer.panel("🔮 Animation (Presets)"):
            ...

        with self.typer.panel("✨ Post processing"):
            self.typer.command(self.state._vignette, name="vignette")
            self.typer.command(self.state._dof, name="dof")

    def setup(self):
        if self.image.is_empty():
            self.input(image=DepthScene.DEFAULT_IMAGE)
        self.ssaa = 1.2
        self.time = 0

    def build(self):
        ShaderScene.build(self)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.normal = ShaderTexture(scene=self, name="normal").repeat(False)
        self.shader.fragment = self.DEPTH_SHADER
        self.aspect_ratio = (16/9)

    def update(self):
        # self.state.reset()
        # for item in self.animation:
        #     item.update(self)
        # return

        # In and out dolly zoom
        self.state.dolly = (0.5 + 0.5*math.cos(self.cycle))

        # Infinite 8 loop shift
        self.state.offset_x = (0.2 * math.sin(1*self.cycle))
        self.state.offset_y = (0.2 * math.sin(2*self.cycle))

        # Integral rotation (better for realtime)
        self.camera.rotate(
            direction=self.camera.base_z,
            angle=math.cos(self.cycle)*self.dt*0.4
        )

        # Fixed known rotation
        self.camera.rotate2d(1.5*math.sin(self.cycle))

        # Zoom in on the start
        # self.config.zoom = 1.2 - 0.2*(2/math.pi)*math.atan(self.time)

    def handle(self, message: ShaderMessage):
        ShaderScene.handle(self, message)

        if isinstance(message, ShaderMessage.Window.FileDrop):
            files = iter(message.files)
            self.input(image=next(files), depth=next(files, None))

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield from self.state.pipeline()

    def ui(self) -> None:
        if (state := imgui.slider_float("Height", self.state.height, 0, 1, "%.2f"))[0]:
            self.state.height = max(0, state[1])
        if (state := imgui.slider_float("Static", self.state.static, 0, 1, "%.2f"))[0]:
            self.state.static = max(0, state[1])
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
