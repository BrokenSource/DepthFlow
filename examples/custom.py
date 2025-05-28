"""
(c) CC BY-SA 4.0, Tremeschin

Basic example of defining your own class based on DepthScene, running
it via CLI or a code managing it for automation

• For more information, visit https://brokensrc.dev/depthflow
"""
import math
import sys

from depthflow.scene import DepthScene
from shaderflow.Message import ShaderMessage

# Note: DepthScene.method(self) is preferred over super().method(self) for clarity

class CustomScene(DepthScene):
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
    scene = CustomScene()
    scene.cli(sys.argv[1:])

def managed():
    scene = CustomScene(backend="headless")
    scene.input(image="image.png")
    scene.main(output="./video.mp4", fps=30, time=5)
    scene.window.destroy()

if __name__ == "__main__":
    # managed()
    manual()
