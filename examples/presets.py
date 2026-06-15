import math

from attrs import define
from depthflow.scene import DepthScene


@define
class Vertical(DepthScene):
    """Simple vertical parallax"""
    def update(self):
        self.state.offset = (0.0, 0.80 * math.sin(self.cycle))
        self.state.isometric = 0.60
        self.state.steady = 0.30


@define
class Horizontal(DepthScene):
    """Simple horizontal parallax"""
    def update(self):
        self.state.offset = (0.80 * math.sin(self.cycle), 0.0)
        self.state.isometric = 0.60
        self.state.steady = 0.30


@define
class Circle(DepthScene):
    """Parallax in a circular motion"""
    def update(self):
        intensity = 0.50
        self.state.isometric = 0.60
        self.state.steady = 0.30
        self.state.offset = (
            intensity * math.sin(self.cycle + math.pi/2.0),
            intensity * math.sin(self.cycle),
        )


@define
class Dolly(DepthScene):
    """Dolly zoom effect"""
    def update(self):
        self.state.height = 0.30
        self.state.steady = 0.35
        self.state.focus = 0.35
        self.state.zoom = 0.95
        self.state.isometric = 0.5 * (1.0 - math.cos(self.cycle))


@define
class Orbital(DepthScene):
    """Orbital parallax around focus"""
    def update(self):
        self.state.steady = 0.30
        self.state.focus = 0.30
        self.state.zoom = 0.98
        self.state.isometric = 0.50 * math.cos(self.cycle) + 0.75
        self.state.offset = (0.50 * math.sin(self.cycle), 0.0)


@define
class Zoom(DepthScene):
    """Zoom in and out"""
    def update(self):
        self.state.height = 0.8 * (math.sin(self.cycle/2.0)**2.0)


@define
class ZoomIn(DepthScene):
    """Linear Zoom in effect"""
    def update(self):
        self.state.height = self.tau


@define
class ZoomInSmooth(DepthScene):
    """Smoothed Zoom in effect"""
    def update(self):
        self.state.height = math.atan(2.0 * self.tau) * (2.0/math.pi)


@define
class ZoomOut(DepthScene):
    """Linear Zoom out effect"""
    def update(self):
        self.state.height = 1.0 - self.tau


@define
class ZoomOutSmooth(DepthScene):
    """Smoothed Zoom out effect"""
    def update(self):
        self.state.height = 1.0 - math.atan(2.0 * self.tau) * (2.0/math.pi)


if __name__ == "__main__":
    scene = ZoomOut()
    scene.main()
