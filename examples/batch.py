"""
(c) CC BY-SA 4.0, Tremeschin

Simple example of programmatically batch rendering multiple inputs
"""
import math
from pathlib import Path
from typing import Literal

from attrs import define
from depthflow.scene import DepthScene, DepthState


@define
class MyAnimation(DepthScene):
    animation: Literal["circle", "zoom"] = "circle"

    def update(self) -> None:
        if self.animation == "circle":
            self.state.isometric = 0.60
            self.state.steady = 0.30
            self.state.offset = (
                0.5 * math.sin(self.cycle + math.pi/2.0),
                0.5 * math.sin(self.cycle),
            )

        elif self.animation == "zoom":
            self.state.height = 0.8 * (math.sin(self.cycle/2.0)**2.0)


def main():
    # Change to your own paths!
    INPUTS  = Path("/home/tremeschin/Pictures/Wallpapers")
    OUTPUTS = Path(INPUTS/"DepthFlow")

    scene = MyAnimation(backend="headless")
    scene.ffmpeg.h264(preset="veryfast")

    for ext in ("jpg", "jpeg", "png"):
        for file in Path(INPUTS).glob(f"*.{ext}"):
            scene.input(image=file)

            # Animation variation one
            scene.state = DepthState()
            scene.animation = "circle"
            scene.main(
                output=(OUTPUTS/f"{file.stem}-circle.mp4"),
                time=5, ssaa=1.5,
            )

            # Animation variation two
            scene.state = DepthState()
            scene.animation = "zoom"
            scene.main(
                output=(OUTPUTS/f"{file.stem}-zoom.mp4"),
                time=8, ssaa=1.5,
            )

if __name__ == "__main__":
    main()
