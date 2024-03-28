import math
from threading import Thread
from typing import Annotated, Iterable

import imgui
from attr import define, field
from PIL import Image
from ShaderFlow import SHADERFLOW
from ShaderFlow.Message import Message
from ShaderFlow.Optional.Monocular import Monocular
from ShaderFlow.Scene import ShaderScene
from ShaderFlow.Texture import ShaderTexture
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken.Base import BrokenThread
from Broken.Loaders.LoaderPIL import LoaderImage
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

    # ------------------------------------------|
    # Parallax MDE and Loading screen tricky implementation

    _loading:    Thread = None
    _load_image: Image  = None
    _load_depth: Image  = None

    def input(self,
        image:  Annotated[str,   Option("--image",  "-i", help="Image to parallax (Path, URL, NumPy, PIL)")],
        depth:  Annotated[str,   Option("--depth",  "-d", help="Depth map of the Image, None to estimate")]=None,
        cache:  Annotated[bool,  Option("--cache",  "-c", help="Cache the Depth Map estimations")]=True,
        width:  Annotated[int,   Option("--width",  "-w", help="Final video Width,  None for the Image's one. Adjusts to Aspect Ratio")]=None,
        height: Annotated[int,   Option("--height", "-h", help="Final video Height, None for the Image's one. Adjusts to Aspect Ratio")]=None,
        scale:  Annotated[float, Option("--scale",  "-s", help="Post-multiply the Image resolution by a factor")]=1.0,
        block:  Annotated[bool,  Option("--block",  "-b", help="Freeze until Depth Map is estimated, no loading screen")]=False
    ):
        # Already loading something
        if self._loading and not block:
            return

        def load():
            nonlocal image, depth, cache, width, height, scale
            self._load_image = LoaderImage(image)
            iwidth, iheight = self._load_image.size
            aspect_ratio = (iwidth/iheight)

            # Force resolution if both set or image's one, else ajust to aspect ratio
            if (bool(width) == bool(height)):
                resolution = ((width or iwidth), (height or iheight))
            else:
                resolution = (
                    ((height or 0)*aspect_ratio) or width,
                    ((width  or 0)/aspect_ratio) or height,
                )

            # The order of calling imports here for rendering
            self.eloop.once(callback=self.resize, args=[x*scale for x in resolution])
            self._load_depth = LoaderImage(depth) or self.monocular(image, cache=cache)
            self.time = 0

        # Start loading process
        self.shader.fragment = self.LOADING_SHADER
        self.shader.load_shaders()
        self._loading = BrokenThread.new(load)

        # Wait until loading finish
        if block: self._loading.join()

    # ------------------------------------------|

    def _ui_(self) -> None:
        if (state := imgui.checkbox("Fixed", self.parallax_fixed))[0]:
            self.parallax_fixed = state[1]
        if (state := imgui.input_float("Height", self.parallax_height, 0.01, 0.01, "%.2f"))[0]:
            self.parallax_height = max(0, state[1])

    def _load_new_or_default(self):

        # Set default image if none provided
        if self.image.is_empty():
            self.input(image=DepthFlowScene.DEFAULT_IMAGE)

        # Block when rendering (first Scene update)
        if self.rendering and self.image.is_empty():
            self._loading.join()

        # Load new parallax images and parallax shader
        if self._load_image and self._load_depth:
            self._load_image = self.image.from_image(self._load_image) and None
            self._load_depth = self.depth.from_image(self._load_depth) and None
            self.shader.fragment = self.DEPTH_SHADER
            self.shader.load_shaders()
            self._loading = None
            self.time = 0

    # ------------------------------------------|

    # Parallax parameters
    parallax_fixed     = field(default=True)
    parallax_height    = field(default=0.2)
    parallax_focus     = field(default=1.0)
    parallax_zoom      = field(default=1.0)
    parallax_isometric = field(default=0.0)
    parallax_dolly     = field(default=0.0)
    parallax_x         = field(default=0.0)
    parallax_y         = field(default=0.0)

    def commands(self):
        self.broken_typer.command(self.input)

    def setup(self):
        self._load_new_or_default()

    def build(self):
        ShaderScene.build(self)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)

    def update(self):
        self._load_new_or_default()

        # In and out dolly zoom
        self.parallax_dolly = 0.5*(1 + math.cos(self.time))

        # Infinite 8 loop shift
        self.parallax_x = 0.1 * math.sin(  self.time)
        self.parallax_y = 0.1 * math.sin(2*self.time)

        # Oscillating rotation
        self.camera.rotate(
            direction=self.camera.base_z,
            angle=math.cos(self.time)*self.dt*0.4
        )

        # Zoom out on the start
        # self.parallax_zoom = 0.6 + 0.4*(2/math.pi)*math.atan(3*self.time)

    def handle(self, message: Message):
        ShaderScene.handle(self, message)
        if isinstance(message, Message.Window.FileDrop):
            files = iter(message.files)
            self.input(image=next(files), depth=next(files, None))

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield from ShaderScene.pipeline(self)
        yield ShaderVariable("uniform", "bool",  "iParallaxFixed",     self.parallax_fixed)
        yield ShaderVariable("uniform", "float", "iParallaxHeight",    self.parallax_height)
        yield ShaderVariable("uniform", "float", "iParallaxFocus",     self.parallax_focus)
        yield ShaderVariable("uniform", "float", "iParallaxZoom",      self.parallax_zoom)
        yield ShaderVariable("uniform", "float", "iParallaxIsometric", self.parallax_isometric)
        yield ShaderVariable("uniform", "float", "iParallaxDolly",     self.parallax_dolly)
        yield ShaderVariable("uniform", "vec2",  "iParallaxPosition",  (self.parallax_x, self.parallax_y))

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