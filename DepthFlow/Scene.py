import copy
import math
import os
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
from DepthFlow.Motion import Animation, Components, Preset, Presets
from DepthFlow.State import DepthState

DEPTHFLOW_ABOUT = """
🌊 Image to → 2.5D Parallax Effect Video. A Free and Open Source LeiaPix/ImmersityAI alternative.\n

Usage: All commands have a --help option with extensible configuration, and are chained together

[yellow]Examples:[/yellow]
• Simplest:    [bold blue]depthflow[/bold blue] [blue]main[/blue] [bright_black]# Realtime window, drag and drop images![/bright_black]
• Your image:  [bold blue]depthflow[/bold blue] [blue]input[/blue] -i ./image.png [blue]main[/blue]
• Exporting:   [bold blue]depthflow[/bold blue] [blue]input[/blue] -i ./image.png [blue]main[/blue] -o ./output.mp4
• Upscaler:    [bold blue]depthflow[/bold blue] [blue]realesr[/blue] --scale 2 [blue]input[/blue] -i ./image.png [blue]main[/blue] -o ./output.mp4
• Convenience: [bold blue]depthflow[/bold blue] [blue]input[/blue] -i ./image16x9.png [blue]main[/blue] -h 1440 [bright_black]# Auto calculates w=2560[/bright_black]
• Estimator:   [bold blue]depthflow[/bold blue] [blue]dav2[/blue] --model large [blue]input[/blue] -i ~/image.png [blue]main[/blue]
• Post FX:     [bold blue]depthflow[/bold blue] [blue]dof[/blue] -e [blue]vignette[/blue] -e [blue]main[/blue]

[yellow]Notes:[/yellow]
• A --ssaa value of 1.5+ is recommended for final exports, real time uses 1.2
• The [bold blue]main[/bold blue]'s --quality preset gives little improvement for small movements
• The rendered video loops perfectly, the period is the main's --time
• The last two commands must be [bold blue]input[/bold blue] and [bold blue]main[/bold blue] (in order) to work
"""

# -------------------------------------------------------------------------------------------------|

@define
class DepthScene(ShaderScene):
    __name__ = "DepthFlow"

    # Constants
    DEFAULT_IMAGE = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
    DEPTH_SHADER  = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.glsl")

    # DepthFlow objects
    animation: List[Animation] = field(factory=list)
    estimator: DepthEstimator = field(factory=DepthAnythingV2)
    upscaler: BrokenUpscaler = field(factory=NoUpscaler)
    state: DepthState = field(factory=DepthState)

    def add_animation(self, animation: Union[Animation, Preset]) -> None:
        if issubclass(type(animation), Preset):
            self.animation.extend(animation.animation())
            return
        self.animation.append(copy.deepcopy(animation))

    def set_upscaler(self, upscaler: BrokenUpscaler) -> None:
        self.upscaler = upscaler

    def set_estimator(self, estimator: DepthEstimator) -> None:
        self.estimator = estimator

    def load_model(self) -> None:
        self.estimator.load_model()

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

    def webui(self):
        """Launch a Gradio WebUI for DepthFlow in the browser"""
        from DepthFlow.Webui import DepthFlowWebui
        DepthFlowWebui().launch()

    def commands(self):
        self.typer.description = DEPTHFLOW_ABOUT
        self.typer.command(self.load_model, hidden=True)

        with self.typer.panel(self.scene_panel):
            self.typer.command(self.state, name="config")
            self.typer.command(self.webui)
            self.typer.command(self.input)

        with self.typer.panel("🌊 Depth estimators"):
            self.typer.command(DepthAnythingV1, post=self.set_estimator, name="dav1")
            self.typer.command(DepthAnythingV2, post=self.set_estimator, name="dav2")
            self.typer.command(ZoeDepth, post=self.set_estimator)
            self.typer.command(Marigold, post=self.set_estimator)

        with self.typer.panel("⭐️ Upscalers"):
            self.typer.command(Realesr, post=self.set_upscaler)
            self.typer.command(Waifu2x, post=self.set_upscaler)

        with self.typer.panel("🔮 Animation (Components)"):
            for animation in Components.members():
                self.typer.command(animation, post=self.add_animation)

        with self.typer.panel("🔮 Animation (Presets)"):
            for preset in Presets.members():
                self.typer.command(preset, post=self.add_animation)

    def setup(self):
        if self.image.is_empty():
            self.input(image=DepthScene.DEFAULT_IMAGE)
        if (not self.animation):
            self.add_animation(Presets.Orbital())
        self.time = 0

    def build(self):
        ShaderScene.build(self)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.normal = ShaderTexture(scene=self, name="normal").repeat(False)
        self.shader.fragment = self.DEPTH_SHADER
        self.aspect_ratio = (16/9)
        self.ssaa = 1.2

    def update(self):
        self.state.reset()

        for item in self.animation:
            item.update(self)

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
