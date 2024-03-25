import math
from threading import Thread
from typing import Annotated
from typing import Iterable

import imgui
from attr import define
from attr import field
from PIL import Image
from ShaderFlow import SHADERFLOW
from ShaderFlow.Message import Message
from ShaderFlow.Optional.Monocular import Monocular
from ShaderFlow.Scene import ShaderScene
from ShaderFlow.Texture import ShaderTexture
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken.Base import BrokenThread
from Broken.Loaders.LoaderPIL import LoadableImage
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
    mde: Monocular = field(factory=Monocular)

    # Parallax parameters
    parallax_fixed     = field(default=True)
    parallax_height    = field(default=0.2)
    parallax_focus     = field(default=1.0)
    parallax_zoom      = field(default=1.0)
    parallax_isometric = field(default=0.0)
    parallax_dolly     = field(default=0.0)
    parallax_x         = field(default=0.0)
    parallax_y         = field(default=0.0)

    # ------------------------------------------|
    # Parallax MDE and Loading screen tricky implementation

    _loading:    Thread = None
    _load_image: Image  = None
    _load_depth: Image  = None

    def _parallax(self,
        image: LoadableImage,
        depth: LoadableImage=None,
        cache: bool=True
    ):
        self._load_image = LoaderImage(image)
        self._load_depth = LoaderImage(depth) or self.mde(image, cache=cache)

    def parallax(self,
        image: Annotated[str,  Option("--image", "-i", help="Image to parallax (path, url)")],
        depth: Annotated[str,  Option("--depth", "-d", help="Depth map of the Image, None to estimate")]=None,
        cache: Annotated[bool, Option("--cache", "-c", help="Cache the Depth Map estimations")]=True,
        block: Annotated[bool, Option("--block", "-b", help="Wait for the Image and Depth Map to be loaded")]=False
    ):
        """
        Load a new parallax image and depth map. If depth is None, it will be estimated.
        • If block is True, the function will wait until the images are loaded (implied on rendering)
        """
        if self._loading and not block:
            return

        # Start loading process
        self.shader.fragment = self.LOADING_SHADER
        self._loading = BrokenThread.new(self._parallax,
            image=image, depth=depth, cache=cache
        )

        # Wait until loading finish
        if block: self._loading.join()
        self.time = 0

    # ------------------------------------------|

    def _ui_(self) -> None:
        if (state := imgui.checkbox("Fixed", self.parallax_fixed))[0]:
            self.parallax_fixed = state[1]
        if (state := imgui.input_float("Height", self.parallax_height, 0.01, 0.01, "%.2f"))[0]:
            self.parallax_height = max(0, state[1])

    def _default_image(self):

        # Set default image if none provided
        if self.image.is_empty():
            self.parallax(image=DepthFlowScene.DEFAULT_IMAGE)

        # Block when rendering (first Scene update)
        if self.rendering and self.image.is_empty():
            self._loading.join()

        # Load new parallax images and parallax shader
        if self._load_image and self._load_depth:
            self._load_image = self.image.from_image(self._load_image) and None
            self._load_depth = self.depth.from_image(self._load_depth) and None
            self.shader.fragment = self.DEPTH_SHADER
            self._loading = None
            self.time = 0

    # ------------------------------------------|

    def commands(self):
        self.broken_typer.command(self.parallax)

    def build(self):
        ShaderScene.build(self)
        self.image = ShaderTexture(scene=self, name="image").repeat(False)
        self.depth = ShaderTexture(scene=self, name="depth").repeat(False)

    def update(self):
        self._default_image()

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
            self.parallax(image=next(files), depth=next(files, None))

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