"""This file makes the example documentation videos"""

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "depthflow",
# ]
# ///

import math
from pathlib import Path
from typing import Iterable

import depthflow
from attrs import define
from depthflow.scene import DepthScene
from imgui_bundle import imgui
from shaderflow.message import ShaderMessage
from shaderflow.variable import Uniform

# ---------------------------------------------------------------------------- #

SHADER_PATCH = """
if (iSteadyPlane && abs(depthflow.value - iDepthSteady) < 0.002) {
    fragColor = vec4(255.0, 79.0, 0, 255.0)/255.0;
    return;
}
if (iFocusPlane && abs(depthflow.value - iDepthFocus) < 0.002) {
    fragColor = vec4(79.0, 255.0, 0, 255.0)/255.0;
    return;
}"""

@define
class ExampleScene(DepthScene):
    steady_plane: bool = False
    focus_plane: bool = False

    def build(self):
        DepthScene.build(self)
        self.shader.fragment = depthflow.resources.joinpath("depthflow.glsl").read_text().replace(
            "if (depthflow.oob) {", (SHADER_PATCH + "if (depthflow.oob) {")
        )

    def pipeline(self) -> Iterable[Uniform]:
        yield from DepthScene.pipeline(self)
        yield Uniform("bool", "iSteadyPlane", self.steady_plane)
        yield Uniform("bool", "iFocusPlane", self.focus_plane)

    def _render_ui(self):
        imgui.push_style_var(imgui.StyleVar_.window_border_size, 0.0)
        imgui.push_style_var(imgui.StyleVar_.window_rounding, 8)
        imgui.push_style_var(imgui.StyleVar_.grab_rounding, 8)
        imgui.push_style_var(imgui.StyleVar_.frame_rounding, 8)
        imgui.push_style_var(imgui.StyleVar_.child_rounding, 8)
        imgui.push_style_color(imgui.Col_.frame_bg, (0.1, 0.1, 0.1, 0.5))
        imgui.new_frame()
        imgui.set_next_window_pos((0, 0))
        imgui.set_next_window_bg_alpha(0.6)
        imgui.begin("Parameters", False, imgui.WindowFlags_.always_auto_resize)
        imgui.slider_float("Quality",   self.quality,         0, 100, "%.2f")
        imgui.slider_float("Height",    self.state.height,    0, 1, "%.2f")
        imgui.slider_float("Steady",    self.state.steady,    0, 1, "%.2f")
        imgui.slider_float("Sticky",    self.state.sticky,    0, 1, "%.0f")
        imgui.slider_float("Focus",     self.state.focus,     0, 1, "%.2f")
        imgui.slider_float("Zoom",      self.state.zoom,      0, 2, "%.2f")
        imgui.slider_float("Isometric", self.state.isometric, 0, 1, "%.2f")
        imgui.slider_float("Dolly",     self.state.dolly,     0, 5, "%.2f")
        imgui.slider_float("Offset X",  self.state.offset[0], -2, 2, "%.2f")
        imgui.slider_float("Offset Y",  self.state.offset[1], -2, 2, "%.2f")
        imgui.slider_float("Origin X",  self.state.origin[0], -2, 2, "%.2f")
        imgui.slider_float("Origin Y",  self.state.origin[1], -2, 2, "%.2f")
        imgui.slider_float("Center X",  self.state.center[0], -2, 2, "%.2f")
        imgui.slider_float("Center Y",  self.state.center[1], -2, 2, "%.2f")
        imgui.end()
        imgui.pop_style_color()
        imgui.pop_style_var(4)
        imgui.render()
        self._final.texture.fbo.use()
        self.imgui.render(imgui.get_draw_data())

    # Resets to true state zero
    def update(self):
        self.state.height    = 0.3
        self.state.steady    = 0.0
        self.state.focus     = 0.0
        self.state.zoom      = 1.0
        self.state.isometric = 0.0
        self.state.dolly     = 0.0
        self.state.offset    = (0.0, 0.0)
        self.state.center    = (0.0, 0.0)
        self.state.origin    = (0.0, 0.0)
        self.imguio.display_framebuffer_scale = (scale := 1.75, scale)
        self.imguio.display_size = (self._width/scale, self._height/scale)
        self._render_ui() # Fixme: No image on frame zero without

# ---------------------------------------------------------------------------- #

@define
class Quality(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.quality = 100.0*(math.sin(self.cycle/2)**2)**3
        self.state.offset = (8.0, 0.0)
        self.state.center = (-0.4, 0.0)
        self.state.zoom = 0.75

@define
class Height(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.height = math.sin(self.cycle/2)**2

@define
class Offset(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.offset = (
            math.cos(self.cycle),
            math.sin(self.cycle),
        )

@define
class Tiles(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.sticky = False
        self.state.height = 0.8
        self.state.offset = (
            0.15 * math.cos(self.cycle),
            0.15 * math.sin(self.cycle),
        )

@define
class Steady(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.steady_plane = True
        self.state.steady = 0.32
        self.state.offset = (1.5 * math.sin(self.cycle), 0.0)

@define
class Isometric(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.height = 0.80
        self.state.isometric = (1 - math.cos(self.cycle))/2
        self.state.offset = (
            0.3*math.cos(3*self.cycle),
            0.3*math.sin(3*self.cycle),
        )

@define
class Flat(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.height = 0.8
        self.state.isometric = 1.00
        self.state.offset = (
            0.3*math.cos(self.cycle),
            0.3*math.sin(self.cycle),
        )

@define
class Dolly(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.height = 1.0
        self.state.focus = 0.32
        self.state.dolly = (1 - math.cos(self.cycle))

@define
class Focus(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.focus_plane = True
        self.state.height = 1.0
        self.state.focus = 0.32
        self.state.isometric = 0.999*(1 - math.cos(self.cycle))/2

@define
class Zoom(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.zoom = 1 - 0.5*(1 - math.cos(self.cycle))/2

@define
class Center(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.center = (math.sin(self.cycle), 0.0)

@define
class Origin(ExampleScene):
    def update(self):
        ExampleScene.update(self)
        self.state.origin = (0.0, 1.0)
        self.state.height = (1 - math.cos(self.cycle))/2

# ---------------------------------------------------------------------------- #

output: Path = Path(__file__).parent.joinpath("docs")
"""Example videos output directory"""

def make(
    cls: type[DepthScene],
    time: float,
):
    scene = cls(backend="headless")
    scene.input(image=None)
    scene.ffmpeg.h264(
        preset="veryslow",
        profile="high",
        tune="film",
        crf=24,
        x264params=(
            "ref=8",
            "bframes=8",
            "b-adapt=2",
            "rc-lookahead=60",
            "me=umh",
            "subme=8",
            "merange=24",
            "analyse=all",
            "trellis=2",
            "deblock=-3,-3",
            "psy-rd=1.0",
            "aq-mode=2",
            "aq-strength=1.0",
        ),
    ) # type: ignore
    scene.relay(ShaderMessage.Shader.Compile)
    scene.main(
        output=output.joinpath(cls.__name__.lower() + ".mp4"),
        time=time,
        width=1920,
        height=1080,
        quality=100,
        subsample=4,
        ssaa=4,
    )
    imgui.destroy_context()

def main():
    make(cls=Quality, time=5)
    make(cls=Height, time=5)
    make(cls=Offset, time=5)
    make(cls=Tiles, time=5)
    make(cls=Steady, time=5)
    make(cls=Isometric, time=10)
    make(cls=Flat, time=5)
    make(cls=Dolly, time=5)
    make(cls=Focus, time=5)
    make(cls=Zoom, time=5)
    make(cls=Center, time=5)
    make(cls=Origin, time=5)

if __name__ == "__main__":
    main()
