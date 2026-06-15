from attrs import define
from depthflow.scene import DepthScene


@define
class Vignette(DepthScene):
    """Vignette example, darkens the borders of the image"""
    def update(self):
        self.state.vignette.intensity = 0.2


@define
class Lens(DepthScene):
    """Lens distortion example (Chromatic Aberration)"""
    def update(self):
        self.state.lens.intensity = 0.3


@define
class Blur(DepthScene):
    """Depth of field example example"""
    def update(self):
        self.state.blur.intensity = 1.0


@define
class Inpaint(DepthScene):
    """Paint green the stretchy regions"""
    def update(self):
        self.state.inpaint.limit = 1.0


# Walk around with mouse, wasd
if __name__ == "__main__":
    scene = Blur()
    scene.main()
