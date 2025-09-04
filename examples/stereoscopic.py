"""
(c) CC BY-SA 4.0, Tremeschin

Simple example of rendering a side-by-side video
"""
from depthflow.scene import DepthScene


class CustomScene(DepthScene):
    def setup(self):
        DepthScene.setup(self)
        self.camera.projection = "stereoscopic"
        self.camera.separation.value = 0.3

def main():
    # Note: Ensure the aspect ratio is double of the input
    scene = CustomScene()
    scene.main(
        # output="./video.mp4",
        ratio=(32/9),
        height=1080,
    )

if __name__ == "__main__":
    main()
