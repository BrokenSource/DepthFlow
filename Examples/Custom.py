"""
Basic example of defining your own class based on DepthScene
"""
import math

from DepthFlow import DepthScene
from ShaderFlow.Message import ShaderMessage

# Note: DepthScene.method(self) is preferred over super().method(self) for clarity

class YourScene(DepthScene):

    def update(self):
        self.state.offset_x = math.sin(2*self.cycle)
        ...

    def pipeline(self):
        yield from DepthScene.pipeline(self)
        ...

    def handle(self, message: ShaderMessage):
        DepthScene.handle(self, message)
        ...

def manual():
    scene = YourScene()
    scene.cli()

def managed():
    from Broken.Externals.Upscaler import Realesr
    # Note: For headless rendering / server, use backend='headless'
    scene = YourScene(backend="glfw")
    scene.set_upscaler(Realesr())
    scene.input(image="image.png")
    scene.main(output="./video.mp4", fps=30, time=5)

if __name__ == "__main__":
    # managed()
    manual()
