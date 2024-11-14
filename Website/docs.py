import math
import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable

from attr import Factory, define
from DepthFlow import DepthScene
from ShaderFlow.Imgui import imgui
from ShaderFlow.Variable import ShaderVariable, Uniform

from Broken import BROKEN, OnceTracker, install, log
from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator

install("manim", "minio")

if TYPE_CHECKING:
    import manim
    import minio

os.environ["IMGUI_FONT_SCALE"] = "1.21"

def _dir(path: str) -> str:
    return f"[bold blue]{path}[/]"

# ------------------------------------------------------------------------------------------------ #
# Todo: Move Minio and Manim common classes to a DocsFabric module

@define
class BrokenMinio:

    # Authentication
    access_key: str = os.getenv("MINIO_ACCESS_KEY")
    secret_key: str = os.getenv("MINIO_SECRET_KEY")
    endpoint:   str = os.getenv("MINIO_ENDPOINT")
    bucket:     str = os.getenv("MINIO_BUCKET")

    authenticated: bool = False
    client: minio.Minio = None

    def __attrs_post_init__(self):
        try:
            self.client = minio.Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=True
            )
            self.authenticated = True
            log.success(f"Connected to Minio instance at ({self.endpoint})")
            self.make_bucket(self.bucket)
        except Exception:
            log.warning(f"Failed to connect to Minio instance at ({self.endpoint})")

    def guarded(method: Callable) -> Callable:
        def wrapper(self, *args, **kwargs):
            if self.authenticated:
                return method(self, *args, **kwargs)
            log.warning("Minio instance is not authenticated")
        return wrapper

    @guarded
    def make_bucket(self, bucket: str):
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    @guarded
    def upload(self, local: Path, remote: Path) -> None:
        log.info(f"Uploading Minio file {_dir(local)} → {_dir(f'/{remote}@{self.bucket}')}")
        self.client.fput_object(self.bucket, str(remote), str(local))

    @guarded
    def download(self, remote: Path, local: Path) -> Path:
        log.info(f"Downloading Minio file {_dir(f'/{remote}@{self.bucket}')} → {_dir(local)}")
        self.client.fget_object(
            bucket_name=self.bucket,
            object_name=str(remote),
            file_path=str(local),
        )
        return local

    @guarded
    def remove(self, remote: Path) -> None:
        log.info(f"Removing Minio file {_dir(f'/{remote}@{self.bucket}')}")
        self.client.remove_object(self.bucket, str(remote))

    @guarded
    def rmdir(self, remote: Path) -> None:
        log.info(f"Removing Minio directory {_dir(f'/{remote}@{self.bucket}')}")

        for object in self.client.list_objects(self.bucket, prefix=f"{remote}/", recursive=True):
            log.info(f"• Deleted {_dir(f'/{object.object_name}@{self.bucket}')}")
            self.client.remove_object(self.bucket, object.object_name)

# ------------------------------------------------------------------------------------------------ #

SHADER_PATCH = """
if (iSteadyPlane && abs(depthflow.value - iDepthSteady) < 0.002) {
    fragColor = vec4(255.0, 79.0, 0, 255.0)/255.0;
    return;
}
if (iFocusPlane && abs(depthflow.value - iDepthFocus) < 0.002) {
    fragColor = vec4(255.0, 79.0, 0, 255.0)/255.0;
    return;
}"""

@define
class DocScene(DepthScene):
    other: OnceTracker = Factory(OnceTracker)

    steady_plane: bool = False
    focus_plane: bool = False

    def build(self):
        DepthScene.build(self)
        self.shader.fragment = self.DEPTH_SHADER.read_text().replace(
            "if (depthflow.oob) {", (SHADER_PATCH + "if (depthflow.oob) {")
        )

    def pipeline(self) -> Iterable[ShaderVariable]:
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
        imgui.slider_float("Height",    self.state.height,    0, 1, "%.2f")
        imgui.slider_float("Steady",    self.state.steady,    0, 1, "%.2f")
        imgui.slider_float("Focus",     self.state.focus,     0, 1, "%.2f")
        imgui.slider_float("Invert",    self.state.invert,    0, 1, "%.2f")
        imgui.slider_float("Zoom",      self.state.zoom,      0, 2, "%.2f")
        imgui.slider_float("Isometric", self.state.isometric, 0, 1, "%.2f")
        imgui.slider_float("Dolly",     self.state.dolly,     0, 5, "%.2f")
        imgui.slider_float("Offset X",  self.state.offset_x, -2, 2, "%.2f")
        imgui.slider_float("Offset Y",  self.state.offset_y, -2, 2, "%.2f")
        imgui.slider_float("Origin X",  self.state.origin_x, -2, 2, "%.2f")
        imgui.slider_float("Origin Y",  self.state.origin_y, -2, 2, "%.2f")
        imgui.slider_float("Center X",  self.state.center_x, -2, 2, "%.2f")
        imgui.slider_float("Center Y",  self.state.center_y, -2, 2, "%.2f")
        imgui.end()
        imgui.pop_style_color()
        imgui.pop_style_var(4)
        imgui.render()

        self._final.texture.fbo.use()
        self.imgui.render(imgui.get_draw_data())

        # Fixme: Dirty solution to frame zero issues
        if not self.other():
            self.next(dt=0)

# ------------------------------------------------------------------------------------------------ #

@define
class DocsParameters:
    estimator: DepthEstimator = Factory(DepthAnythingV2)
    minio: BrokenMinio = Factory(BrokenMinio)

    def render(self, scene: DepthScene, name: str, *, time: float=10):
        # Find local and remote paths for the asset video
        base = BROKEN.DIRECTORIES.SYSTEM_TEMP/"mkdocs"
        file = Path(name).with_suffix(".mp4")
        output = (base/file)

        # Initialize and configure the scene
        scene.estimator = self.estimator
        scene.ffmpeg.h264(
            preset="veryslow",
            profile="high",
            tune="film",
            crf=28,
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
        )

        # Render variations, upload
        for _ in range(1):
            video = scene.main(
                output=output,
                width=1920,
                height=1080,
                quality=100,
                time=time,
                ssaa=2,
            )[0]
            self.minio.upload(
                remote=Path("depthflow")/output.relative_to(base),
                local=video,
            )

        # Cleanup
        scene.window.destroy()

    def make_height(self):
        class Example(DocScene):
            def update(self):
                self.state.height = (1 - math.cos(self.cycle))/2

        self.render(
            scene=Example(),
            name="learn/parameters/height-varying.mp4",
        )

    def make_offset(self):
        class Example(DocScene):
            def update(self):
                self.state.offset_x = 1.5*math.sin(self.cycle)

        self.render(
            scene=Example(),
            name="learn/parameters/offset-x-varying.mp4",
            time=5,
        )

        class Example(DocScene):
            def update(self):
                self.state.offset_x = math.cos(self.cycle)
                self.state.offset_y = math.sin(self.cycle)

        self.render(
            scene=Example(),
            name="learn/parameters/offset-xy-varying.mp4",
            time=5,
        )

    def make_steady(self):
        class Example(DocScene):
            def update(self):
                self.state.offset_x = 1.5*math.sin(self.cycle)
                self.state.steady = 0.32

        self.render(
            scene=Example(steady_plane=True),
            name="learn/parameters/steady-varying.mp4",
            time=5,
        )

    def make_isometric(self):
        class Example(DocScene):
            def update(self):
                self.state.height = 0.80
                self.state.isometric = (1 - math.cos(self.cycle))/2
                self.state.offset_x = 0.3*math.cos(3*self.cycle)
                self.state.offset_y = 0.3*math.sin(3*self.cycle)

        self.render(
            scene=Example(),
            name="learn/parameters/isometric-varying.mp4",
        )

        class Example(DocScene):
            def update(self):
                self.state.height = 0.80
                self.state.isometric = 1.00
                self.state.offset_x = 0.3*math.cos(self.cycle)
                self.state.offset_y = 0.3*math.sin(self.cycle)

        self.render(
            scene=Example(),
            name="learn/parameters/isometric-flat.mp4",
            time=5,
        )

    def make_dolly(self):
        class Example(DocScene):
            def update(self):
                self.state.height = 1
                self.state.dolly = 1.5*(1 - math.cos(self.cycle))

        self.render(
            scene=Example(),
            name="learn/parameters/dolly-varying.mp4",
            time=5,
        )

        class Example(DocScene):
            def update(self):
                self.state.height = 1
                self.state.focus = 0.32
                self.state.dolly = 1.5*(1 - math.cos(self.cycle))

        self.render(
            scene=Example(focus_plane=True),
            name="learn/parameters/dolly-focus-varying.mp4",
            time=5,
        )

    def make_focus(self):
        class Example(DocScene):
            def update(self):
                self.state.height = 1.00
                self.state.focus = 0.32
                self.state.isometric = 0.999*(1 - math.cos(self.cycle))/2

        self.render(
            scene=Example(focus_plane=True),
            name="learn/parameters/focus-varying.mp4",
            time=5,
        )

    def make_zoom(self):
        class Example(DocScene):
            def update(self):
                self.state.zoom = 1 - 0.5*(1 - math.cos(self.cycle))/2

        self.render(
            scene=Example(),
            name="learn/parameters/zoom-varying.mp4",
        )

    def make_invert(self):
        class Example(DocScene):
            def update(self):
                self.state.height = 0.40
                self.state.invert = (1 - math.cos(self.cycle))/2
                self.state.offset_x = 1.5*math.sin(self.cycle)

        self.render(
            scene=Example(),
            name="learn/parameters/invert-varying.mp4",
        )

    def make_center(self):
        class Example(DocScene):
            def update(self):
                self.state.center_x = math.sin(self.cycle)

        self.render(
            scene=Example(),
            name="learn/parameters/center-varying.mp4",
        )

    def make_origin(self):
        class Example(DocScene):
            def update(self):
                self.state.origin_x = 1
                self.state.height = (1 - math.cos(self.cycle))/2

        self.render(
            scene=Example(),
            name="learn/parameters/origin-varying.mp4",
            time=5
        )

# ------------------------------------------------------------------------------------------------ #

@define
class DocsMath(manim.Scene):
    ...

# ------------------------------------------------------------------------------------------------ #

def main():
    fabric = DocsParameters()
    fabric.make_height()
    fabric.make_offset()
    fabric.make_steady()
    fabric.make_isometric()
    fabric.make_dolly()
    fabric.make_focus()
    fabric.make_zoom()
    fabric.make_invert()
    fabric.make_center()
    fabric.make_origin()
