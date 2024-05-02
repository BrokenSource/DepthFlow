import math
from typing import Annotated, Iterable, Tuple

import imgui
from attr import define, field
from ShaderFlow import SHADERFLOW
from ShaderFlow.Message import Message
from ShaderFlow.Optional.Monocular import Monocular
from ShaderFlow.Scene import ShaderScene
from ShaderFlow.Texture import ShaderTexture
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken import image_hash
from Broken.Externals.Upscaler import BrokenUpscaler
from Broken.Externals.Upscaler.ncnn import BrokenRealEsrgan
from Broken.Loaders import LoaderImage
from DepthFlow import DEPTHFLOW


@define
class DepthFlowScene(ShaderScene):
    """🌊 Image to → 2.5D Parallax Effect Video. High quality, user first."""
    __name__ = "DepthFlow"

    # Constants
    DEFAULT_IMAGE  = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"
    DEPTH_SHADER   = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.frag")
    LOADING_SHADER = (SHADERFLOW.RESOURCES.FRAGMENT/"Loading.frag")

    # DepthFlow objects
    monocular: Monocular = field(factory=Monocular)
    upscaler: BrokenUpscaler = field(factory=BrokenRealEsrgan)

    # ------------------------------------------|
    # Parallax MDE and Loading screen tricky implementation

    def input(self,
        image: Annotated[str,  Option("--image",   "-i", help="• (Basic  ) Image to Parallax (Path, URL, NumPy, PIL)")],
        depth: Annotated[str,  Option("--depth",   "-d", help="• (Basic  ) Depthmap of the Image, None to estimate")]=None,
        cache: Annotated[bool, Option(" /--nc",          help="• (Basic  ) Cache the Depthmap estimations on Disk")]=True,
        ratio: Annotated[Tuple[int, int], Option("--upscale", "-u", help="• (Upscale) Upscale the Input and Depthmap respectively with Realesrgan (1, 2, 3, 4)")]=(1, 1),
    ):
        image = LoaderImage(image)
        depth = LoaderImage(depth) or self.monocular.estimate(image, cache=cache)
        width, height = image.size
        cache = DEPTHFLOW.DIRECTORIES.CACHE/f"{image_hash(image)}"
        depth = self.upscaler.upscale(depth, scale=ratio[1])
        image = self.upscaler.upscale(image, scale=ratio[0])
        self.aspect_ratio = (width/height)
        self.image.from_image(image)
        self.depth.from_image(depth)
        self.time = 0

    # ------------------------------------------|

    parallax_height: float = field(default=0.2)
    """Peak value of the Depth Map, in the range [0, 1]. The camera is 1 distance away from depth=0
    at the z=1 plane, so this also controls the intensity of the effect"""

    parallax_focus: float = field(default=0.0)
    """Focal depth of the effect, in the range [0, 1]. A value of 0 makes the background (depth=0)
    stationary, while a value of 1 makes the foreground (depth=1) stationary on displacements"""

    parallax_invert: float = field(default=0.0)
    """Interpolate between (0=max, 1=min)=0 or (0=min, 1=max)=1 Depth Map's value interpretation"""

    parallax_zoom: float = field(default=1.0)
    """Camera zoom factor, in the range [0, inf]. 2 means a quarter of the image is visible"""

    parallax_isometric: float = field(default=0.0)
    """Isometric factor of the camera projection. Zero is fully perspective, 1 is orthographic"""

    parallax_dolly: float = field(default=0.0)
    """Same effect as isometric, but with "natural units" of AFAIK `isometric = atan(dolly)*(2/pi)`.
    Keeps the ray target constant and move back ray origins by this amount"""

    parallax_offset: Tuple[float, float] = field(factory=lambda: [0.0, 0.0])
    """The effect displacement offset, change this over time for the 3D parallax effect"""

    parallax_center: Tuple[float, float] = field(factory=lambda: [0.0, 0.0])
    """Focal point of the offsets, use this to center off-screen objects"""

    def commands(self):
        self.broken_typer.command(self.input)

    def setup(self):
        if self.image.is_empty():
            self.input(image=DepthFlowScene.DEFAULT_IMAGE)

    def build(self):
        ShaderScene.build(self)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)
        self.shader.fragment = self.DEPTH_SHADER

    def update(self):

        # In and out dolly zoom
        self.parallax_dolly = 0.5*(1 + math.cos(self.time))

        # Infinite 8 loop shift
        self.parallax_offset = [
            0.1 * math.sin(self.time),
            0.1 * math.sin(2*self.time)
        ]

        # # Oscillating rotation
        self.camera.rotate(
            direction=self.camera.base_z,
            angle=math.cos(self.time)*self.dt*0.4
        )

        # Zoom in on the start
        # self.parallax_zoom = 1.2 - 0.2*(2/math.pi)*math.atan(self.time)

    def handle(self, message: Message):
        ShaderScene.handle(self, message)

        if isinstance(message, Message.Window.FileDrop):
            files = iter(message.files)
            self.input(image=next(files), depth=next(files, None))

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield ShaderVariable("uniform", "float", "iParallaxHeight",    self.parallax_height)
        yield ShaderVariable("uniform", "float", "iParallaxFocus",     self.parallax_focus)
        yield ShaderVariable("uniform", "float", "iParallaxInvert",    self.parallax_invert)
        yield ShaderVariable("uniform", "float", "iParallaxZoom",      self.parallax_zoom)
        yield ShaderVariable("uniform", "float", "iParallaxIsometric", self.parallax_isometric)
        yield ShaderVariable("uniform", "float", "iParallaxDolly",     self.parallax_dolly)
        yield ShaderVariable("uniform", "vec2",  "iParallaxOffset",    self.parallax_offset)
        yield ShaderVariable("uniform", "vec2",  "iParallaxCenter",    self.parallax_center)

    # ------------------------------------------|

    def ui(self) -> None:
        if (state := imgui.slider_float("Height", self.parallax_height, 0, 1, "%.2f"))[0]:
            self.parallax_height = max(0, state[1])
        if (state := imgui.slider_float("Focus", self.parallax_focus, 0, 1, "%.2f"))[0]:
            self.parallax_focus = max(0, state[1])
        if (state := imgui.slider_float("Invert", self.parallax_invert, 0, 1, "%.2f"))[0]:
            self.parallax_invert = max(0, state[1])
        if (state := imgui.slider_float("Zoom", self.parallax_zoom, 0, 2, "%.2f"))[0]:
            self.parallax_zoom = max(0, state[1])
        if (state := imgui.slider_float("Isometric", self.parallax_isometric, 0, 1, "%.2f"))[0]:
            self.parallax_isometric = max(0, state[1])
        if (state := imgui.slider_float("Dolly", self.parallax_dolly, 0, 5, "%.2f"))[0]:
            self.parallax_dolly = max(0, state[1])
        if (state := imgui.slider_float("Offset X", self.parallax_offset[0], -2, 2, "%.2f"))[0]:
            self.parallax_offset[0] = state[1]
        if (state := imgui.slider_float("Offset Y", self.parallax_offset[1], -2, 2, "%.2f"))[0]:
            self.parallax_offset[1] = state[1]
        if (state := imgui.slider_float("Center X", self.parallax_center[0], -2, 2, "%.2f"))[0]:
            self.parallax_center[0] = state[1]
        if (state := imgui.slider_float("Center Y", self.parallax_center[1], -2, 2, "%.2f"))[0]:
            self.parallax_center[1] = state[1]

# -------------------------------------------------------------------------------------------------|

class YourFlow(DepthFlowScene):
    """Example of defining your own class based on DepthFlowScene"""

    def update(self):
        DepthFlowScene.update(self)

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from DepthFlowScene.pipeline(self)
        ...

    def handle(self, message: Message):
        DepthFlowScene.handle(self, message)
        ...