"""
(c) CC BY-SA 4.0, Tremeschin

Simple example of programmatically batch rendering multiple inputs
"""
from pathlib import Path

from depthflow.scene import DepthScene, DepthState


def main():
    # Change to your own paths!
    INPUTS  = Path("/home/tremeschin/Pictures/Wallpapers")
    OUTPUTS = (INPUTS/"DepthFlow")

    scene = DepthScene(backend="headless")
    scene.ffmpeg.h264(preset="veryfast")

    for ext in ("jpg", "jpeg", "png"):
        for file in Path(INPUTS).glob(f"*.{ext}"):
            scene.input(image=file)

            # Animation variation one
            scene.config.animation.clear()
            scene.state = DepthState()
            scene.circle(intensity=0.8)
            scene.main(
                output=(OUTPUTS/f"{file.stem}-circle.mp4"),
                time=7, ssaa=1.5, turbo=False,
            )

            # Animation variation two
            scene.config.animation.clear()
            scene.state = DepthState()
            scene.zoom(intensity=0.3, isometric=0, loop=True)
            scene.main(
                output=(OUTPUTS/f"{file.stem}-zoom.mp4"),
                time=10, ssaa=1.5, turbo=False,
            )

if __name__ == "__main__":
    main()
