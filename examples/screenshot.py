"""
(c) CC BY-SA 4.0, Tremeschin

Simple example of grabbing frames from a scene
"""
from depthflow.scene import DepthScene
from PIL import Image


class CustomScene(DepthScene):
    def setup(self):
        DepthScene.setup(self)
        self.on_frame.bind(self.capture)

    def capture(self):
        data = self.screenshot()
        print(data.shape)

        # Grab a screenshot from a target frame
        if (self.frame >= 1) and (SCREENSHOT := True):
            image = Image.fromarray(data)
            image.save("screenshot.png")
            exit(0)

def main():
    scene = CustomScene()
    scene.main(
        height=1080,
        ssaa=4,
    )

if __name__ == "__main__":
    main()