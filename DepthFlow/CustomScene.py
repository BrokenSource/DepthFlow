import sys

from ShaderFlow import Message

from DepthFlow import DepthFlowScene


class YourScene(DepthFlowScene):
    """Example of defining your own class based on DepthFlowScene"""

    def update(self):
        DepthFlowScene.update(self)

    def pipeline(self):
        yield from DepthFlowScene.pipeline(self)
        ...

    def handle(self, message: Message):
        DepthFlowScene.handle(self, message)
        ...


if __name__ == "__main__":
    scene = YourScene()
    scene.build()
    scene.cli(sys.argv[1:])

