from . import *


@attrs.define
class DepthFlowScene(SombreroScene):
    """Basics of Simplex noise"""
    __name__ = "DepthFlow"

    # DepthFlow objects
    mde = attrs.field(factory=DepthFlowMDE)

    # # Image parallax

    def parallax(self, image: Option[PilImage, Path, "url"]):
        """Parallax effect"""
        self.image.from_image(image)
        self.depth.from_image(self.mde(image))
        self.context.time = 0

    def resize_to_image(self):
        self.context.resize(*self.image.size)

    def settings(self, image: str):
        self.parallax(image)

    def handle(self, message: SombreroMessage):

        # Drag and drop images or urls to parallax
        if isinstance(message, SombreroMessage.Window.FileDrop):
            self.parallax(message.files[0])

    # # SombreroScene

    def setup(self):

        # Create textures
        self.image = self.engine.new_texture("image")
        self.depth = self.engine.new_texture("depth")
        self.engine.new_texture("self").from_module(self.engine)

        # Don't repeat textures
        self.image.repeat(False)
        self.depth.repeat(False)

        # Create a Camera Shake Noise module
        self.shake_noise = self.engine.add(SombreroNoise(
            name="Position",
            frequency=0.25,
            roughness=0.3,
            octaves=6,
            dimensions=2,
        ))

        # Create a Camera Zoom Noise module
        self.zoom_noise = self.engine.add(SombreroNoise(
            name="Zoom",
            frequency=0.2,
            roughness=0.5,
            octaves=3,
            dimensions=1
        ))

        # Create a Camera Rotation Noise module
        self.rotate_noise = self.engine.add(SombreroNoise(
            name="Rotation",
            frequency=0.2,
            roughness=0.5,
            octaves=3,
            dimensions=1
        ))

        # Load the Default DepthFlow shader
        self.engine.shader.fragment = (DEPTHFLOW.RESOURCES.SHADERS/"DepthFlow.frag").read_text()

    def update(self):

        # Load default image if none was provided
        if self.image.is_empty:
            self.parallax("https://w.wallhaven.cc/full/pk/wallhaven-pkz5r9.png")

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iFocus",          value=1)
        yield ShaderVariable(qualifier="uniform", type="float", name=f"iParallaxFactor", value=0.52)
