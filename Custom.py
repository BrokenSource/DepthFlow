import math
import sys

from DepthFlow import DepthScene
from ShaderFlow.Message import ShaderMessage


class YourScene(DepthScene):
    """Example of defining your own class based on DepthFlowScene"""

    def update(self):
        self.state.offset_x = math.sin(2*self.cycle)

    def pipeline(self):
        yield from DepthScene.pipeline(self)
        ...

    def handle(self, message: ShaderMessage):
        DepthScene.handle(self, message)
        ...


if __name__ == "__main__":
    scene = YourScene()
    scene.cli(sys.argv[1:])

