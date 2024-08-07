import math
import sys

from DepthFlow import DepthScene
from ShaderFlow.Message import ShaderMessage

# Note: DepthScene.method(self) is preferred over super().method(self) for clarity

class YourScene(DepthScene):
    """Example of defining your own class based on DepthScene"""

    def update(self):
        self.state.offset_x = math.sin(2*self.cycle)

    def pipeline(self):
        yield from DepthScene.pipeline(self)
        ...

    def handle(self, message: ShaderMessage):
        DepthScene.handle(self, message)
        ...

def manual():
    scene = YourScene()
    scene.cli(sys.argv[1:])

def managed():
    from Broken.Externals.Upscaler import Realesr
    scene = YourScene()
    scene.set_upscaler(Realesr())
    scene.input(image="image.png")
    scene.main(output="./video.mp4", fps=30, time=5)

if __name__ == "__main__":
    # managed()
    manual()
