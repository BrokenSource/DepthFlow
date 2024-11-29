"""
(c) CC BY-SA 4.0, Tremeschin

Basic example of defining your own class based on DepthScene, running
it via CLI or a code managing it for automation

• For more information, visit https://brokensrc.dev/depthflow
"""
import math
import sys

from DepthFlow.Scene import DepthScene
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
    scene.cli(sys.argv[1:])

def managed():
    from Broken.Externals.Upscaler import Upscayl
    # Note: For headless rendering / server, use backend='headless'
    scene = YourScene(backend="glfw")
    scene.set_upscaler(Upscayl())
    scene.input(image="image.png")
    scene.main(output="./video.mp4", fps=30, time=5)
    scene.window.destroy()

if __name__ == "__main__":
    # managed()
    manual()
