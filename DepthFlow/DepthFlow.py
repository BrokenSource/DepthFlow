from . import *


@attrs.define
class DepthFlow(SombreroScene):
    """🌊 Image to → 2.5D Parallax Effect Video. High quality, user first."""
    __name__ = "DepthFlow"

    # DepthFlow objects
    mde = attrs.field(factory=DepthFlowMDE)

    # # Image parallax

    def parallax(self,
        image: Option[PilImage, Path, "url"],
        depth: Option[PilImage, Path, "url"]=None
    ):
        """Parallax effect"""
        self.image.from_image(image)
        self.depth.from_image(depth or self.mde(image))
        self.context.time = 0

    def resize_to_image(self):
        self.context.resize(*self.image.size)

    def settings(self,
        image: Annotated[str, typer.Option("--image", "-i", help="Image to parallax (path, url)")],
        depth: Annotated[str, typer.Option("--depth", "-d", help="Depth map of the image, None to estimate")]=None,
    ):
        self.parallax(image=image, depth=depth)

    def handle(self, message: SombreroMessage):
        if isinstance(message, SombreroMessage.Window.FileDrop):
            self.parallax(image=message.files[0], depth=message.files.get(1))

    # # SombreroScene

    def setup(self):

        # Create textures
        self.image = self.engine.new_texture("image")
        self.depth = self.engine.new_texture("depth")
        self.engine.new_texture("self").from_module(self.engine)

        # Don't repeat textures
        self.image.repeat(False)
        self.depth.repeat(False)

        # Load the Default DepthFlow shader
        self.engine.shader.fragment = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.frag").read_text()

    def update(self):
        if self.image.is_empty:
            self.parallax(image="https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png")

    def smoothstep(self, x: float) -> float:
        return numpy.clip(3*x**2 - 2*x**3, 0, 1)

    # Parallax configuration and presets
    fixed  = field(default=True)
    height = field(default=0.25)

    def ui(self) -> None:
        if (state := imgui.checkbox("Fixed", self.fixed))[0]:
            self.fixed = state[1]
        if (state := imgui.input_float("Height", self.height, 0.01, 0.01, "%.2f"))[0]:
            self.height = max(0, state[1])

    def pipeline(self) -> Iterable[ShaderVariable]:

        # Smootly change isometric
        iso = self.smoothstep(0.5*(math.sin(self.context.time) + 1))

        # Infinite 8 loop shift
        pos = 0.1 * numpy.array([math.sin(self.context.time), math.sin(2*self.context.time)])

        # Zoom out on the start
        zoom = 0.6 + 0.25*(2/math.pi)*math.atan(2*self.context.time)

        # Output variables
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxHeight",    value=self.height)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxIsometric", value=iso)
        yield ShaderVariable(qualifier="uniform", type="vec2",  name=f"iParallaxPosition",  value=pos)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxZoom",      value=zoom)
        yield ShaderVariable(qualifier="uniform", type="bool",  name=f"iParallaxFixed",     value=self.fixed)

