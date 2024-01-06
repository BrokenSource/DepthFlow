from . import *


@attrs.define
class DepthFlow(SombreroScene):
    """🌊 Image to → 2.5D Parallax Effect Video. High quality, user first."""
    __name__ = "DepthFlow"

    DEFAULT_IMAGE = "https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png"

    # DepthFlow objects
    mde = attrs.field(factory=DepthFlowMDE)

    # ------------------------------------------|

    # Objects for a loading screen
    __loading__:     Thread   = None
    __load_image__:  PilImage = None
    __load_depth__:  PilImage = None

    def __parallax__(self,
        image: Option[PilImage, Path, "url"],
        depth: Option[PilImage, Path, "url"]=None,
        cache: bool=True
    ):
        self.__load_image__  = BrokenUtils.load_image(image)
        self.__load_depth__  = BrokenUtils.load_image(depth or self.mde(image, cache=cache))

    def parallax(self,
        image: Annotated[str,  typer.Option("--image", "-i", help="Image to parallax (path, url)")],
        depth: Annotated[str,  typer.Option("--depth", "-d", help="Depth map of the Image, None to estimate")]=None,
        cache: Annotated[bool, typer.Option("--cache", "-c", help="Cache the Depth Map estimations")]=True,
        block: Annotated[bool, typer.Option("--block", "-b", help="Wait for the Image and Depth Map to be loaded")]=False
    ):
        """
        Load a new parallax image and depth map. If depth is None, it will be estimated.
        • If block is True, the function will wait until the images are loaded (implied on rendering)
        """
        if self.__loading__:
            return

        # Start loading process
        self.engine.fragment = SHADERFLOW.RESOURCES.FRAGMENT/"Loading.frag"
        self.__loading__ = BrokenUtils.better_thread(self.__parallax__,
            image=image, depth=depth, cache=cache
        )

        # Rendering needs block mode
        if block or self.__rendering__:
            self.__loading__.join()

    def resize_to_image(self):
        self.resize(*self.image.size)

    # ------------------------------------------|

    def commands(self):
        self.broken_typer.command(self.parallax)

    def setup(self):
        self.image = self.engine.new_texture("image").repeat(False)
        self.depth = self.engine.new_texture("depth").repeat(False)

    def handle(self, message: SombreroMessage):
        if isinstance(message, SombreroMessage.Window.FileDrop):
            self.parallax(image=message.files[0], depth=message.files.get(1))

    def update(self):

        # Set default image if none provided
        if self.image.is_empty:
            self.parallax(image=DepthFlow.DEFAULT_IMAGE)

        # Load new parallax images
        if self.__load_image__ and self.__load_depth__:
            self.engine.fragment = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.frag").read_text()
            self.image.from_pil(self.__load_image__); self.__load_image__ = None
            self.depth.from_pil(self.__load_depth__); self.__load_depth__ = None
            self.__loading__ = None
            self.time = 0

    # ------------------------------------------|

    # Parallax configuration and presets
    parallax_fixed  = field(default=True)
    parallax_height = field(default=0.25)

    def ui(self) -> None:
        if (state := imgui.checkbox("Fixed", self.parallax_fixed))[0]:
            self.parallax_fixed = state[1]
        if (state := imgui.input_float("Height", self.parallax_height, 0.01, 0.01, "%.2f"))[0]:
            self.parallax_height = max(0, state[1])

    def pipeline(self) -> Iterable[ShaderVariable]:

        # Smootly change isometric
        iso = self.smoothstep(0.5*(math.sin(self.time) + 1))

        # Infinite 8 loop shift
        pos = 0.1 * numpy.array([math.sin(self.time), math.sin(2*self.time)])

        # Zoom out on the start
        zoom = 0.6 + 0.25*(2/math.pi)*math.atan(2*self.time)

        # Output variables
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxHeight",    value=self.parallax_height)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxIsometric", value=iso)
        yield ShaderVariable(qualifier="uniform", type="vec2",  name=f"iParallaxPosition",  value=pos)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxZoom",      value=zoom)
        yield ShaderVariable(qualifier="uniform", type="bool",  name=f"iParallaxFixed",     value=self.parallax_fixed)

