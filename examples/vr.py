# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "depthflow",
# ]
# ///

from depthflow.scene import DepthScene
from shaderflow.camera import CameraProjection


class CustomScene(DepthScene):
    def setup(self):
        DepthScene.setup(self)
        self.camera.projection = CameraProjection.Stereoscopic

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
