import contextlib
import sys
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor as ThreadPool
from pathlib import Path
from typing import Annotated, Iterable

import gradio
from attr import Factory, define
from dotmap import DotMap
from gradio.themes.utils import fonts, sizes
from PIL.Image import Image as ImageType
from typer import Option

from broken import (
    BrokenPath,
    BrokenTorch,
    BrokenWorker,
    DictUtils,
    Runtime,
    denum,
)
from broken.core.extra.resolution import BrokenResolution
from broken.externals.depthmap import DepthAnythingV2, DepthEstimator
from broken.externals.upscaler import BrokenUpscaler, Realesr, Upscayl, Waifu2x
from depthflow import DEPTHFLOW
from depthflow.animation import Animation, FilterBase, PresetBase

# ------------------------------------------------------------------------------------------------ #

class BrokenGradio:

    @staticmethod
    def theme() -> gradio.Theme:
        return gradio.themes.Base(
            font=fonts.GoogleFont("Rubik"),
            spacing_size=sizes.Size(
                name="spacing_sm",
                xxs="0px",
                xs="0px",
                sm="1px",
                md="2px",
                lg="0px",
                xl="4px",
                xxl="2px",
            ),
            radius_size=sizes.radius_lg,
            text_size=sizes.text_md,
        ).set(
            block_title_text_weight="bold",
            border_color_primary_dark="#00000000",
            link_text_color_dark="#00000000",
        )

    @staticmethod
    def _css() -> Iterable[str]:

        # Fullscreen like app without body padding
        yield ".app {padding: 0 !important;}"

        # Remove up and down arrows from number inputs
        yield """
            input[type=number]::-webkit-inner-spin-button,
            input[type=number]::-webkit-outer-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }

            input[type=number] {
                -moz-appearance: textfield;
            }
        """

        # Remove nested tabs padding
        yield """
            .tabitem.svelte-wv8on1 .tabitem.svelte-wv8on1 {
                padding: 0 !important;
            }
        """

        # Add margin-top to the first tab element (non-child), only first one
        yield """
            *:not(.tabs) > .tabs:first-of-type {
                margin-top: 3px !important;
            }
        """

        # No margin top on the whole footer component
        yield """
            footer {
                margin-bottom: 4px !important;
                margin-top: 0 !important;
            }
        """

        # Remove image sources selection to align with video
        yield ".source-selection {display: none;}"

        # Apply rounding to sliders
        yield """
            input, .reset-button {
                border-radius: 6px !important;
            }
        """

    @staticmethod
    def css() -> str:
        return '\n'.join(BrokenGradio._css())

    @staticmethod
    def progress_button(element: Callable, then: Callable):
        """Disables a button while a task is running"""
        def toggle(state: bool) -> dict:
            return dict(
                fn=lambda: gradio.update(interactive=state),
                inputs=None, outputs=element
            )
        element.click(**toggle(False)) \
            .then(**then) \
            .then(**toggle(True))

# ------------------------------------------------------------------------------------------------ #

WEBUI_OUTPUT: Path = (DEPTHFLOW.DIRECTORIES.SYSTEM_TEMP/"webui")
"""The temporary output for the WebUI, cleaned at the start and after any render"""

ESTIMATORS: dict[str, DepthEstimator] = {
    "DepthAnything2 Small": DepthAnythingV2(model=DepthAnythingV2.Model.Small),
    "DepthAnything2 Base":  DepthAnythingV2(model=DepthAnythingV2.Model.Base),
    "DepthAnything2 Large": DepthAnythingV2(model=DepthAnythingV2.Model.Large),
}

UPSCALERS: dict[str, BrokenUpscaler] = {
    "Upscayl Digital Art":   Upscayl(model=Upscayl.Model.DigitalArt),
    "Upscayl High Fidelity": Upscayl(model=Upscayl.Model.HighFidelity),
    "Real-ESRGAN":           Realesr(),
    "Waifu2x":               Waifu2x(),
}

# ------------------------------------------------------------------------------------------------ #

@define(slots=False)
class DepthGradio:
    interface: gradio.Blocks = None
    ui: DotMap = Factory(DotMap)

    # -------------------------------------------|

    def simple(self, method: Callable, **options: dict) -> dict:
        """An ugly hack to avoid manually listing inputs and outputs"""
        show_progress = bool(options.get("outputs"))
        outputs = options.pop("outputs", set(DictUtils.rvalues(self.ui)))
        inputs  = options.pop("inputs",  set(DictUtils.rvalues(self.ui)))
        return dict(
            fn=method,
            inputs=inputs,
            outputs=outputs,
            show_progress=show_progress,
            **options,
        )

    # -------------------------------------------|
    # Estimators

    def _estimator(self, user: dict) -> DepthEstimator:
        return ESTIMATORS[user[self.ui.estimator]]

    def _upscaler(self, user: dict) -> BrokenUpscaler:
        return UPSCALERS[user[self.ui.upscaler]]

    def estimate(self, user: dict):
        if ((image := user[self.ui.image]) is None):
            return None
        (width, height) = image.size
        yield {
            self.ui.image:  gradio.Image(label=f"Size: ({width}x{height})"),
            self.ui.depth:  self._estimator(user).estimate(image),
            self.ui.width:  width,
            self.ui.height: height,
        }

    # -------------------------------------------|
    # Upscalers

    def upscale(self, user: dict):
        if ((image := user[self.ui.image]) is None):
            return gradio.Warning("The input image is empty")
        yield {self.ui.image: (image := self._upscaler(user).upscale(image))}

    # -------------------------------------------|
    # Resolution

    def _fit_resolution(self, user: dict, target: tuple[int, int]) -> tuple[int, int]:
        if (user[self.ui.image] is None):
            raise GeneratorExit()
        width, height = user[self.ui.image].size
        return BrokenResolution().fit(
            old=(1920, 1080), new=target,
            ar=(width/height), multiple=1,
        )

    def fit_width(self, user: dict):
        yield {self.ui.height: self._fit_resolution(user, (user[self.ui.width], None))[1]}

    def fit_height(self, user: dict):
        yield {self.ui.width: self._fit_resolution(user, (None, user[self.ui.height]))[0]}

    # -------------------------------------------|
    # Rendering

    turbo: bool = False
    nvenc: bool = False

    def render(self, user: dict):
        # Warn: This method leaks about 50MB of RAM per 100 renders
        #       due a bug in (moderngl?) I'll look into the future

        if (user[self.ui.image] is None):
            return gradio.Warning("The input image is empty")
        if (user[self.ui.depth] is None):
            return gradio.Warning("The input depthmap is empty")

        def worker(output: Path) -> Path:
            from depthflow.scene import DepthScene
            scene = DepthScene(backend="headless")
            scene.input(
                image=user[self.ui.image],
                depth=user[self.ui.depth]
            )

            # Build and add any enabled preset class
            for preset in Animation.members():
                preset_name = preset.__name__
                preset_dict = self.ui.animation[preset_name]
                if (not preset_dict.enable):
                    continue
                if (not user[preset_dict.enable]):
                    continue
                scene.config.animation.add(preset(**{
                    key: user[item] for (key, item) in preset_dict.options.items()
                }))

            if self.nvenc:
                scene.ffmpeg.h264_nvenc()

            # Let the user override the ratio
            width  = user[self.ui.width]
            height = user[self.ui.height]

            return scene.main(
                width=width, height=height,
                ratio=(width/height),
                ssaa=user[self.ui.ssaa],
                fps=user[self.ui.fps],
                time=user[self.ui.time],
                loops=user[self.ui.loop],
                turbo=self.turbo,
                output=output,
            )[0]

        with ThreadPool() as pool:
            try:
                output = (WEBUI_OUTPUT/f"{uuid.uuid4()}.mp4")
                task = pool.submit(worker, output=output)
                yield {self.ui.video: task.result()}
            finally:
                def remove(path: Path, delay: float):
                    with contextlib.suppress(FileNotFoundError):
                        time.sleep(delay)
                        path.unlink()

                # Gradio doesn't accept bytes, give some time to read
                BrokenWorker.thread(remove, path=output, delay=10)

    # -------------------------------------------|
    # Layout

    def launch(self,
        port: Annotated[int, Option("--port", "-p",
            help="Port to run the WebUI on, None finds a free one")]=None,
        server: Annotated[str, Option("--server",
            help="Hostname or IP address to run the WebUI")]="0.0.0.0",
        share: Annotated[bool, Option("--share", "-s", " /--local",
            help="Get a public shareable link tunneled through Gradio")]=False,
        workers: Annotated[int,  Option("--workers", "-w",
            help="Number of maximum concurrent renders")]=4,
        browser: Annotated[bool, Option("--open", " /--no-open",
            help="Open the WebUI in a new tab on the default browser")]=True,
        block: Annotated[bool, Option("--block", "-b", " /--no-block",
            help="Blocks the main thread while the WebUI is running")]=True,
        pwa: Annotated[bool, Option("--pwa", " /--no-pwa",
            help="Enable Gradio's Progressive Web Application mode")]=False,
        ssr: Annotated[bool, Option("--ssr", " /--no-ssr",
            help="Enable Server Side Rendering mode (Needs Node)")]=False,
        turbo: Annotated[bool, Option("--turbo", " /--no-turbo",
            help="Enable TurboPipe for faster rendering")]=False,
        nvenc: Annotated[bool, Option("--nvenc", " /--no-nvenc",
            help="Enable NVENC hardware acceleration for encoding")]=False,
    ) -> gradio.Blocks:
        """🚀 Launch DepthFlow's Gradio WebUI with the given options"""
        BrokenPath.recreate(WEBUI_OUTPUT)

        self.turbo = turbo
        self.nvenc = nvenc

        # Todo: Gradio UI from Pydantic models
        def make_animation(type):
            for preset in reversed(list(Animation.members())):
                if not issubclass(preset, type):
                    continue
                preset_name = preset.__name__
                preset_dict = self.ui.animation[preset_name]

                with gradio.Tab(preset_name):
                    preset_dict.enable = gradio.Checkbox(
                        value=(preset is Animation.Orbital),
                        label="Enable"
                    )

                    for attr, field in preset.model_fields.items():
                        if (attr.lower() == "enable"):
                            continue
                        if (field.annotation is bool):
                            with gradio.Group():
                                preset_dict.options[attr] = gradio.Checkbox(
                                    value=field.default,
                                    label=attr.capitalize(),
                                    info=field.description,
                                )
                        elif (field.annotation is float):
                            with gradio.Group():
                                preset_dict.options[attr] = gradio.Slider(
                                    minimum=field.metadata[0].min,
                                    maximum=field.metadata[0].max,
                                    step=0.01, label=attr.capitalize(),
                                    value=field.default,
                                    info=field.description,
                                )
                        elif (isinstance(field.annotation, tuple)):
                            print(attr, field, field.annotation)

        with gradio.Blocks(
            theme=BrokenGradio.theme(),
            css=BrokenGradio.css(),
            analytics_enabled=False,
            title="DepthFlow",
            fill_height=True,
            fill_width=True,
        ) as self.interface:

            # Stretch up to the footer images and videos
            HEIGHT = "calc(100vh - 184px)" # 102px

            with gradio.Row():
                with gradio.Column(variant="panel"):
                    with gradio.Tab("Image"):
                        with gradio.Column(variant="panel"):
                            self.ui.image = gradio.Image(
                                sources=["upload", "clipboard"],
                                type="pil", label="Input image",
                                interactive=True, height=HEIGHT
                            )
                            with gradio.Row(equal_height=True):
                                self.ui.upscaler = gradio.Dropdown(
                                    choices=list(UPSCALERS.keys()),
                                    value=list(UPSCALERS.keys())[0],
                                    label="Upscaler", scale=10
                                )
                                self.ui.upscale = gradio.Button(
                                    value="🚀 Upscale", scale=1)

                    with gradio.Tab("Depth"):
                        with gradio.Column(variant="panel"):
                            self.ui.depth = gradio.Image(
                                sources=["upload", "clipboard"],
                                type="pil", label="Depthmap",
                                height=HEIGHT
                            )
                            with gradio.Row(equal_height=True):
                                self.ui.estimator = gradio.Dropdown(
                                    choices=list(ESTIMATORS.keys()),
                                    value=list(ESTIMATORS.keys())[0],
                                    label="Depth estimator", scale=10
                                )
                                self.ui.estimate = gradio.Button(
                                    value="🔎 Estimate", scale=1)

                    with gradio.Tab("Animation"):
                        make_animation(PresetBase)

                    with gradio.Tab("Filters"):
                        make_animation(FilterBase)

                    with gradio.Tab("Output"):

                        self.ui.time = gradio.Slider(label="Duration (seconds)",
                            info="How long each loop will last",
                            minimum=0, maximum=30, step=0.5, value=5)

                        with gradio.Row():
                            with gradio.Group():
                                with gradio.Group():
                                    self.ui.fps = gradio.Slider(label="Framerate",
                                        info="Smoothness of the final video",
                                        minimum=1, maximum=144, step=1, value=60)

                            with gradio.Group():
                                self.ui.loop = gradio.Slider(label="Loops",
                                    info="Loop the animation multiple times",
                                    minimum=1, maximum=10, step=1, value=1)

                        with gradio.Row(equal_height=True):
                            with gradio.Column(variant="panel"):
                                self.ui.quality = gradio.Slider(label="Shader quality",
                                    info="Improves intersections calculations",
                                    value=50, minimum=0, maximum=100, step=10)
                            with gradio.Column(variant="panel"):
                                self.ui.ssaa = gradio.Slider(label="Super sampling anti-aliasing",
                                    info="Reduce aliasing and improve quality **(expensive)**",
                                    value=1.5, minimum=1, maximum=4, step=0.1)

                        with gradio.Row(equal_height=True):
                            with gradio.Group():
                                self.ui.width = gradio.Number(label="Width",
                                    minimum=1, precision=0, scale=10, value=1920)
                                self.ui.fit_width = gradio.Button(
                                    size="sm", value="Fit aspect")

                            with gradio.Group():
                                self.ui.height = gradio.Number(label="Height",
                                    minimum=1, precision=0, scale=10, value=1080)
                                self.ui.fit_height = gradio.Button(
                                    size="sm", value="Fit aspect")

                            self.ui.fit_height.click(**self.simple(self.fit_width))
                            self.ui.fit_width.click(**self.simple(self.fit_height))

                with gradio.Column(variant="panel"):
                    with gradio.Tab("Rendering"):
                        with gradio.Column(variant="panel"):
                            self.ui.video = gradio.Video(
                                label="Output video",
                                interactive=False,
                                height=HEIGHT,
                                autoplay=True,
                                loop=True,
                            )

                            # Fixme: Stretch to match gradio.Dropdown
                            with gradio.Row(height=52, equal_height=True):
                                self.ui.render = gradio.Button(
                                    value="🔥 Render 🔥",
                                    variant="primary",
                                )

            # Update depth map and resolution on image change
            outputs = {self.ui.image, self.ui.depth, self.ui.width, self.ui.height}
            self.ui.image.change(**self.simple(self.estimate, outputs=outputs))

            # Estimate or upscale explicit buttons
            BrokenGradio.progress_button(element=self.ui.estimate,
                then=self.simple(self.estimate, outputs=outputs))
            BrokenGradio.progress_button(element=self.ui.upscale,
                then=self.simple(self.upscale, outputs=outputs))

            # Render video on render button click
            BrokenGradio.progress_button(self.ui.render, self.simple(
                self.render, outputs={self.ui.video},
                concurrency_limit=workers,
            ))

            # Footer-like credits :^)
            gradio.Markdown(f"""
                <center><div style='padding-top: 10px; opacity: 0.7'>
                    <b>DepthFlow</b> {Runtime.Method} v{DEPTHFLOW.VERSION} •
                    <b>Python</b> v{sys.version.split(' ')[0]} •
                    <b>PyTorch</b> v{denum(BrokenTorch.version())}
                    <p><small style='opacity: 0.6'>
                        Made with ❤️ by <a href='https://github.com/Tremeschin'>
                            <b>Tremeschin</b></a> •
                        <a href='https://brokensrc.dev/'><b>Website</b></a> •
                        <a href='https://discord.com/invite/KjqvcYwRHm/'><b>Discord</b></a> •
                        <a href='https://t.me/BrokenSource/'><b>Telegram</b></a> •
                        <a href='https://github.com/BrokenSource/DepthFlow/'><b>GitHub</b></a> •
                        <a href='https://github.com/sponsors/Tremeschin/'><b>Sponsoring</b></a>
                    </small></p>
                </div></center>
            """)

        return self.interface.launch(
            favicon_path=str(DEPTHFLOW.RESOURCES.ICON_PNG),
            inbrowser=browser, show_api=False,
            prevent_thread_lock=(not block),
            max_threads=workers,
            server_name=server,
            server_port=port,
            show_error=True,
            ssr_mode=ssr,
            share=share,
            pwa=pwa,
        )

# ------------------------------------------------------------------------------------------------ #

if (__name__ == "__main__"):
    demo = DepthGradio()
    demo.launch()
