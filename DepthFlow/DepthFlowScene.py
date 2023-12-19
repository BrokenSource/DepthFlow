from . import *


@attrs.define
class DepthFlowScene(SombreroScene):
    """Basics of Simplex noise"""
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
        return x*x*(3 - 2*x)

    def pipeline(self) -> Iterable[ShaderVariable]:

        # Smootly change isometric
        iso = self.smoothstep(0.5*(math.sin(self.context.time) + 1))

        # Infinite 8 loop shift
        pos = 0.1 * numpy.array([math.sin(self.context.time), math.sin(2*self.context.time)])

        # Zoom out on the start
        zoom = 0.6 + 0.25*(2/math.pi)*math.atan(2*self.context.time)

        # Output variables
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxHeight",    value=0.16)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxIsometric", value=iso)
        yield ShaderVariable(qualifier="uniform", type="vec2",  name=f"iParallaxPosition",  value=pos)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxZoom",      value=zoom)
