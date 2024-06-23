from __future__ import annotations

import functools
import math
from abc import ABC, abstractmethod
from typing import Annotated, Any, Iterable, Tuple

import imgui
import typer
from attr import define, field
from pydantic import BaseModel, Field, PrivateAttr
from ShaderFlow.Message import ShaderMessage
from ShaderFlow.Scene import ShaderScene
from ShaderFlow.Texture import ShaderTexture
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken import pydantic_cli
from Broken.Externals.Depthmap import (
    DepthAnything,
    DepthAnythingV2,
    DepthEstimator,
    Marigold,
    ZoeDepth,
)
from Broken.Externals.Upscaler import BrokenUpscaler, NoUpscaler, Realesr, Waifu2x
from Broken.Loaders import LoaderImage
from DepthFlow import DEPTHFLOW

DEPTHFLOW_ABOUT = """
🌊 Image to → 2.5D Parallax Effect Video. High quality, user first.\n

Usage: Chain commands, at minimum just [green]main[/green] for a realtime window, drag and drop images
• The --main command is used for exporting videos, setting quality, resolution
• All commands have a --help option with extensible configuration

Examples:
• Upscaler:    (depthflow realesr --scale 2 input -i ~/image.png main -o ./output.mp4 --ssaa 1.5)
• Convenience: (depthflow input -i ~/image16x9.png main -h 1440) [bright_black]# Auto calculates w=2560[/bright_black]
• Estimator:   (depthflow anything2 --model large input -i ~/image.png main)
• Post FX:     (depthflow dof -e vignette -e main)

Notes:
• The rendered video loops perfectly, the duration is the main's --time
• The last two commands must be --input and --main in order to work
"""

class DepthFlowState(BaseModel):
    """Set parallax parameter values on the state [green](See 'config --help' for options)[/green]"""

    height: Annotated[float, typer.Option("--height", "-h", min=0, max=1,
        help="[bold][red](🔴 Basic   )[/red][/bold] Depthmap's peak value, the effect [bold][cyan]intensity[/cyan][/bold] [medium_purple3](The camera is 1 distance away from depth=0 at the z=1 plane)[/medium_purple3]")] = \
        Field(default=0.35)

    static: Annotated[float, typer.Option("--static", "-s", min=0, max=1,
        help="[bold][red](🔴 Basic   )[/red][/bold] Focal depth plane of [bold][cyan]offsets[/cyan][/bold] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[/medium_purple3]")] = \
        Field(default=0.25)

    focus: Annotated[float, typer.Option("--focus", "-f", min=0, max=1,
        help="[bold][red](🔴 Basic   )[/red][/bold] Focal depth plane of [bold][cyan]perspective[/cyan][/bold] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[/medium_purple3]")] = \
        Field(default=0.5)

    zoom: Annotated[float, typer.Option("--zoom", "-z", min=0,
        help="[bold][red](🔴 Basic   )[/red][/bold] Camera [bold][cyan]zoom factor[/cyan][/bold] [medium_purple3](2 means a quarter of the image is visible)[/medium_purple3]")] = \
        Field(default=1.0)

    isometric: Annotated[float, typer.Option("--isometric", "-iso", min=0, max=1,
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Isometric factor of [bold][cyan]camera projections[/cyan][/bold] [medium_purple3](Zero is fully perspective, 1 is orthographic)[/medium_purple3]")] = \
        Field(default=0.0)

    dolly: Annotated[float, typer.Option("--dolly", "-d", min=0, max=1,
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Same effect as --isometric, dolly zoom [medium_purple3](Move back ray projection origins by this amount)[/medium_purple3]")] = \
        Field(default=0.0)

    invert: Annotated[float, typer.Option("--invert", "-inv", min=0, max=1,
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Interpolate depth values between (0=far, 1=near) and vice-versa, as in [bold][cyan]mix(height, 1-height, invert)[/bold][/cyan]")] = \
        Field(default=0.0)

    mirror: Annotated[bool, typer.Option("--mirror", "-m", " /-n",
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Apply [bold][cyan]GL_MIRRORED_REPEAT[/cyan][/bold] to the image [medium_purple3](The image is mirrored out of bounds on the respective edge)[/medium_purple3]")] = \
        Field(default=True)

    # # Center

    center_x: Annotated[float, typer.Option("--center-x", "-cex", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Horizontal 'true' offset of the camera [medium_purple3](The camera *is* above this point)[/medium_purple3]")] = \
        Field(default=0)

    center_y: Annotated[float, typer.Option("--center-y", "-cey", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Vertical   'true' offset of the camera [medium_purple3](The camera *is* above this point)[/medium_purple3]")] = \
        Field(default=0)

    @property
    def center(self) -> Tuple[float, float]:
        """'True' offset of the camera, the camera *is* above this point"""
        return (self.center_x, self.center_y)

    @center.setter
    def center(self, value: Tuple[float, float]):
        self.center_x, self.center_y = value

    # # Origin

    origin_x: float = Field(default=0)
    """Hozirontal focal point of the offsets, *as if* the camera was above this point"""

    origin_x: Annotated[float, typer.Option("--origin-x", "-orx", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Horizontal focal point of the offsets [medium_purple3](*As if* the camera was above this point)[/medium_purple3]")] = \
        Field(default=0)

    origin_y: Annotated[float, typer.Option("--origin-y", "-ory", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Vertical   focal point of the offsets [medium_purple3](*As if* the camera was above this point)[/medium_purple3]")] = \
        Field(default=0)

    @property
    def origin(self) -> Tuple[float, float]:
        """Focal point of the offsets, *as if* the camera was above this point"""
        return (self.origin_x, self.origin_y)

    @origin.setter
    def origin(self, value: Tuple[float, float]):
        self.origin_x, self.origin_y = value

    # # Parallax

    offset_x: Annotated[float, typer.Option("--offset-x", "-ofx", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Horizontal parallax displacement [medium_purple3](Change this over time for the 3D effect)[/medium_purple3]")] = \
        Field(default=0)

    offset_y: Annotated[float, typer.Option("--offset-y", "-ofy", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Vertical   parallax displacement [medium_purple3](Change this over time for the 3D effect)[/medium_purple3]")] = \
        Field(default=0)

    @property
    def offset(self) -> Tuple[float, float]:
        """Parallax displacement, change this over time for the 3D effect"""
        return (self.offset_x, self.offset_y)

    @offset.setter
    def offset(self, value: Tuple[float, float]):
        self.offset_x, self.offset_y = value

    # # Special

    def reset(self) -> None:
        for name, field in self.model_fields.items(): # noqa
            setattr(self, name, field.default)

    class _PFX_DOF(BaseModel):
        """Set depth of field parameters [green](See 'dof --help' for options)[/green]"""
        enable: Annotated[bool, typer.Option("--enable", "-e",
            help="[bold][blue](🔵 Special )[/blue][/bold] Enable the Depth of field effect")] = \
            Field(default=False)

        start: Annotated[float, typer.Option("--start", "-a",
            help="[green](🟢 Advanced)[/green] Effect starts at this depth distance")] = \
            Field(default=0.6)

        end: Annotated[float, typer.Option("--end", "-b",
            help="[green](🟢 Advanced)[/green] Effect ends at this depth distance")] = \
            Field(default=1.0)

        exponent: Annotated[float, typer.Option("--exponent", "-t", min=0, max=10,
            help="[green](🟢 Advanced)[/green] Effect depth exponent")] = \
            Field(default=2.0)

        intensity: Annotated[float, typer.Option("--intensity", "-i", min=0, max=2,
            help="[green](🟢 Advanced)[/green] Effect blur intensity")] = \
            Field(default=1.0)

        quality: Annotated[int, typer.Option("--quality", "-q", min=1, max=16,
            help="[green](🟢 Advanced)[/green] Effect blur quality (radial steps)")] = \
            Field(default=4)

        directions: Annotated[int, typer.Option("--directions", "-d",
            help="[green](🟢 Advanced)[/green] Effect blur quality (directions)")] = \
            Field(default=16)

        def pipeline(self) -> Iterable[ShaderVariable]:
            yield ShaderVariable("uniform", "bool",  "iDofEnable",     self.enable)
            yield ShaderVariable("uniform", "float", "iDofStart",      self.start)
            yield ShaderVariable("uniform", "float", "iDofEnd",        self.end)
            yield ShaderVariable("uniform", "float", "iDofExponent",   self.exponent)
            yield ShaderVariable("uniform", "float", "iDofIntensity",  self.intensity/100)
            yield ShaderVariable("uniform", "int",   "iDofQuality",    self.quality)
            yield ShaderVariable("uniform", "int",   "iDofDirections", self.directions)

    _dof: _PFX_DOF = PrivateAttr(default_factory=_PFX_DOF)
    """Depth of Field Post-Processing configuration"""

    class _PFX_Vignette(BaseModel):
        """Set vignette parameters [green](See 'vignette --help' for options)[/green]"""
        enable: Annotated[bool, typer.Option("--enable", "-e",
            help="[bold][blue](🔵 Special )[/blue][/bold] Enable the Vignette effect")] = \
            Field(default=False)

        intensity: Annotated[float, typer.Option("--intensity", "-i", min=0, max=100,
            help="[green](🟢 Advanced)[/green] Intensity of the Vignette effect")] = \
            Field(default=30)

        decay: Annotated[float, typer.Option("--decay", "-d", min=0, max=1,
            help="[green](🟢 Advanced)[/green] Decay of the Vignette effect")] = \
            Field(default=0.1)

        def pipeline(self) -> Iterable[ShaderVariable]:
            yield ShaderVariable("uniform", "bool",  "iVignetteEnable",    self.enable)
            yield ShaderVariable("uniform", "float", "iVignetteIntensity", self.intensity)
            yield ShaderVariable("uniform", "float", "iVignetteDecay",     self.decay)

    _vignette: _PFX_Vignette = PrivateAttr(default_factory=_PFX_Vignette)
    """Vignette Post-Processing configuration"""

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield ShaderVariable("uniform", "float", "iDepthHeight",    self.height)
        yield ShaderVariable("uniform", "float", "iDepthStatic",    self.static)
        yield ShaderVariable("uniform", "float", "iDepthFocus",     self.focus)
        yield ShaderVariable("uniform", "float", "iDepthInvert",    self.invert)
        yield ShaderVariable("uniform", "float", "iDepthZoom",      self.zoom)
        yield ShaderVariable("uniform", "float", "iDepthIsometric", self.isometric)
        yield ShaderVariable("uniform", "float", "iDepthDolly",     self.dolly)
        yield ShaderVariable("uniform", "vec2",  "iDepthCenter",    self.center)
        yield ShaderVariable("uniform", "vec2",  "iDepthOrigin",    self.origin)
        yield ShaderVariable("uniform", "vec2",  "iDepthOffset",    self.offset)
        yield ShaderVariable("uniform", "bool",  "iDepthMirror",    self.mirror)
        yield from self._dof.pipeline()
        yield from self._vignette.pipeline()

# -------------------------------------------------------------------------------------------------|

class DepthFlowAnimation(BaseModel, ABC):

    @abstractmethod
    def update(self, scene: DepthFlowScene) -> None:
        pass

# -------------------------------------------------------------------------------------------------|

@define
class DepthFlowScene(ShaderScene):
    __name__ = "DepthFlow"

    # Constants
    DEFAULT_IMAGE = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
    DEPTH_SHADER  = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.glsl")

    # DepthFlow objects
    estimator: DepthEstimator = field(factory=DepthAnything)
    upscaler: BrokenUpscaler = field(factory=NoUpscaler)
    state: DepthFlowState = field(factory=DepthFlowState)

    def input(self,
        image: Annotated[str, Option("--image", "-i", help="Background Image [green](Path, URL, NumPy, PIL)[/green]")],
        depth: Annotated[str, Option("--depth", "-d", help="Depthmap of the Image [medium_purple3](None to estimate)[/medium_purple3]")]=None,
    ) -> None:
        """Load an Image from Path, URL and its estimated Depthmap [green](See 'input --help' for options)[/green]"""
        image = self.upscaler.upscale(LoaderImage(image))
        depth = LoaderImage(depth) or self.estimator.estimate(image)
        self.aspect_ratio = (image.width/image.height)
        self.image.from_image(image)
        self.depth.from_image(depth)

    def set_upscaler(self, upscaler: BrokenUpscaler) -> None:
        self.upscaler = upscaler

    def set_estimator(self, estimator: DepthEstimator) -> None:
        self.estimator = estimator

    def commands(self):
        self.typer.description = DEPTHFLOW_ABOUT
        self.typer.command(self.input)
        self.typer.command(self.state, name="config", requires=True)

        with self.typer.panel("🌊 Depth estimators"):
            self.typer.command(pydantic_cli(DepthAnything(), post=self.set_estimator), name="anything1")
            self.typer.command(pydantic_cli(DepthAnythingV2(), post=self.set_estimator), name="anything2")
            self.typer.command(pydantic_cli(ZoeDepth(), post=self.set_estimator), name="zoedepth")
            self.typer.command(pydantic_cli(Marigold(), post=self.set_estimator), name="marigold")

        with self.typer.panel("⭐️ Upscalers"):
            self.typer.command(pydantic_cli(Realesr(), post=self.set_upscaler), name="realesr", requires=True)
            self.typer.command(pydantic_cli(Waifu2x(), post=self.set_upscaler), name="waifu2x", requires=True)

        with self.typer.panel("✨ Post processing"):
            self.typer.command(self.state._vignette, name="vignette", requires=True)
            self.typer.command(self.state._dof, name="dof", requires=True)

    def setup(self):
        if self.image.is_empty():
            self.input(image=DepthFlowScene.DEFAULT_IMAGE)
        self.ssaa = 1.2
        self.time = 0

    def build(self):
        ShaderScene.build(self)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.shader.fragment = self.DEPTH_SHADER
        self.aspect_ratio = (16/9)

    def update(self):

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
        # self.camera.rotate2d(1.5*math.sin(self.cycle))

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
