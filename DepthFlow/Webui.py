import os
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor as ThreadPool
from pathlib import Path
from typing import Annotated

import gradio
from attr import Factory
from attrs import define
from dotmap import DotMap
from gradio.themes.utils import colors, fonts, sizes
from typer import Option

from Broken import BrokenPath, BrokenResolution, DictUtils
from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator
from Broken.Externals.Upscaler import BrokenUpscaler, Realesr, Upscayl, Waifu2x
from DepthFlow import DEPTHFLOW
from DepthFlow.Animation import Actions, FilterBase, PresetBase

WEBUI_OUTPUT: Path = BrokenPath.recreate(DEPTHFLOW.DIRECTORIES.SYSTEM_TEMP/"WebUI")
"""The temporary output for the WebUI, cleaned at the start and after any render"""

ESTIMATORS: dict[str, DepthEstimator] = {
    "DepthAnything Small": DepthAnythingV2(model=DepthAnythingV2.Model.Small),
    "DepthAnything Base":  DepthAnythingV2(model=DepthAnythingV2.Model.Base),
    "DepthAnything Large": DepthAnythingV2(model=DepthAnythingV2.Model.Large),
}

UPSCALERS: dict[str, BrokenUpscaler] = {
    "Upscayl Digital Art":   Upscayl(model=Upscayl.Model.DigitalArt),
    "Upscayl High Fidelity": Upscayl(model=Upscayl.Model.HighFidelity),
    "Real-ESRGAN":           Realesr(),
    "Waifu2x":               Waifu2x(),
}

# ------------------------------------------------------------------------------------------------ #

@define
class DepthGradio:
    interface: gradio.Blocks = None
    fields: DotMap = Factory(DotMap)

    def simple(self, method: Callable, **options: dict) -> dict:
        """An ugly hack to avoid manually listing inputs and outputs"""
        show_progress = bool(options.get("outputs"))
        outputs = options.pop("outputs", set(DictUtils.rvalues(self.fields)))
        inputs  = options.pop("inputs",  set(DictUtils.rvalues(self.fields)))
        return dict(
            fn=method,
            inputs=inputs,
            outputs=outputs,
            show_progress=show_progress,
            **options,
        )

    def _estimator(self, user: dict) -> DepthEstimator:
        return ESTIMATORS[user[self.fields.estimator]]

    def _upscaler(self, user: dict) -> BrokenUpscaler:
        return UPSCALERS[user[self.fields.upscaler]]

    def estimate(self, user: dict):
        if ((image := user[self.fields.image]) is None):
            return None
        yield {
            self.fields.depth:  self._estimator(user).estimate(image),
            self.fields.width:  image.size[0],
            self.fields.height: image.size[1]
        }

    def upscale(self, user: dict):
        if ((image := user[self.fields.image]) is None):
            return gradio.Warning("The input image is empty")
        yield {self.fields.image: self._upscaler(user).upscale(image)}

    def _fit_resolution(self, user: dict, target: tuple[int, int]) -> tuple[int, int]:
        if (user[self.fields.image] is None):
            raise GeneratorExit()
        width, height = user[self.fields.image].size
        return BrokenResolution().fit(
            old=(1920, 1080), new=target,
            ar=(width/height), multiple=1,
        )

    def fit_width(self, user: dict):
        yield {self.fields.height: self._fit_resolution(user, (user[self.fields.width], None))[1]}

    def fit_height(self, user: dict):
        yield {self.fields.width: self._fit_resolution(user, (None, user[self.fields.height]))[0]}

    def render(self, user: dict):
        if (user[self.fields.image] is None):
            return gradio.Warning("The input image is empty")
        if (user[self.fields.depth] is None):
            return gradio.Warning("The input depthmap is empty")

        def worker():
            from DepthFlow.Scene import DepthScene
            scene = DepthScene(backend="headless")
            scene.set_estimator(self._estimator(user))
            scene.input(image=user[self.fields.image], depth=user[self.fields.depth])
            scene.aspect_ratio = None

            # Build and add any enabled preset class
            for preset in Actions.members():
                preset_name = preset.__name__
                preset_dict = self.fields.animation[preset_name]
                if (not preset_dict.enable):
                    continue
                if (not user[preset_dict.enable]):
                    continue
                scene.config.animation.add(preset(**{
                    key: user[item] for (key, item) in preset_dict.options.items()
                }))

            return scene.main(
                width=user[self.fields.width],
                height=user[self.fields.height],
                ssaa=user[self.fields.ssaa],
                fps=user[self.fields.fps],
                time=user[self.fields.time],
                loop=user[self.fields.loop],
                output=(WEBUI_OUTPUT/f"{uuid.uuid4()}.mp4"),
                noturbo=(not user[self.fields.turbopipe]),
            )[0]

        with ThreadPool() as pool:
            task = pool.submit(worker)
            yield {self.fields.video: task.result()}
            os.remove(task.result())

    def launch(self,
        port: Annotated[int, Option("--port", "-p",
            help="Port to run the WebUI on")]=None,
        server: Annotated[str, Option("--server",
            help="Server to run the WebUI on")]="0.0.0.0",
        share: Annotated[bool, Option("--share", "-s",
            help="Share the WebUI on the network")]=False,
        threads: Annotated[int,  Option("--threads", "-t",
            help="Number of maximum concurrent renders")]=4,
        browser: Annotated[bool, Option("--open", " /--no-open",
            help="Open the WebUI in the browser")]=True,
        block: Annotated[bool, Option("--block", "-b", " /--no-block",
            help="Holds the main thread until the WebUI is closed")]=True,
    ) -> gradio.Blocks:
        with gradio.Blocks(
            theme=gradio.themes.Ocean(
                font=(fonts.GoogleFont("Roboto Slab"),),
                font_mono=(fonts.GoogleFont("Fira Code"),),
                primary_hue=colors.emerald,
                spacing_size=sizes.spacing_sm,
                radius_size=sizes.radius_sm,
                text_size=sizes.text_sm,
            ),
            analytics_enabled=False,
            title="DepthFlow WebUI",
            fill_height=True,
            fill_width=True
        ) as self.interface:

            gradio.Markdown("# 🌊 DepthFlow")

            with gradio.Tab("Application"):
                with gradio.Row(equal_height=True):
                    with gradio.Column(variant="panel"):
                        self.fields.image = gradio.Image(scale=1,
                            sources=["upload", "clipboard"],
                            type="pil", label="Input image",
                            interactive=True,
                        )
                        with gradio.Row(equal_height=True):
                            self.fields.upscaler = gradio.Dropdown(
                                choices=list(UPSCALERS.keys()),
                                value=list(UPSCALERS.keys())[0],
                                label="Upscaler", scale=10
                            )
                            self.fields.upscale = gradio.Button(value="🚀 Upscale", scale=1)

                    with gradio.Column(variant="panel"):
                        self.fields.depth = gradio.Image(scale=1,
                            sources=["upload", "clipboard"],
                            type="pil", label="Depthmap"
                        )
                        with gradio.Row(equal_height=True):
                            self.fields.estimator = gradio.Dropdown(
                                choices=list(ESTIMATORS.keys()),
                                value=list(ESTIMATORS.keys())[0],
                                label="Depth Estimator", scale=10
                            )
                            self.fields.estimate = gradio.Button(value="🔎 Estimate", scale=1)

                    with gradio.Column(variant="panel"):
                        self.fields.video = gradio.Video(scale=1,
                            label="Output video",
                            interactive=False,
                            autoplay=True,
                        )
                        self.fields.render = gradio.Button(
                            value="🔥 Render 🔥",
                            variant="primary",
                        )

                with gradio.Row(equal_height=True, variant="panel"):
                    with gradio.Accordion("Animation (WIP)", open=False):
                        def animation_type(type):
                            for preset in Actions.members():
                                if not issubclass(preset, type):
                                    continue
                                preset_name = preset.__name__
                                preset_dict = self.fields.animation[preset_name]

                                with gradio.Tab(preset_name):
                                    preset_dict.enable = gradio.Checkbox(
                                        value=False, label="Enable", info=preset.__doc__)

                                    for attr, field in preset.model_fields.items():
                                        if (attr.lower() == "enable"):
                                            continue
                                        if (field.annotation is bool):
                                            preset_dict.options[attr] = gradio.Checkbox(
                                                value=field.default,
                                                label=attr.capitalize(),
                                                info=field.description,
                                            )
                                        elif (field.annotation is float):
                                            preset_dict.options[attr] = gradio.Slider(
                                                minimum=field.metadata[0].min,
                                                maximum=field.metadata[0].max,
                                                step=0.01, label=attr.capitalize(),
                                                value=field.default,
                                                info=field.description,
                                            )
                                        elif (isinstance(field.annotation, tuple)):
                                            print(attr, field, field.annotation)

                        with gradio.Tab("Presets"):
                            animation_type(PresetBase)
                        with gradio.Tab("Filters"):
                            animation_type(FilterBase)

                with gradio.Row(equal_height=True):
                    with gradio.Column(variant="panel"):
                        self.fields.width = gradio.Number(label="Width",
                            minimum=1, precision=0, scale=10, value=1920)
                        self.fields.fit_height = gradio.Button(
                            value="➡️ Fit height", scale=1)

                    with gradio.Column(variant="panel"):
                        self.fields.height = gradio.Number(label="Height",
                            minimum=1, precision=0, scale=10, value=1080)
                        self.fields.fit_width = gradio.Button(
                            value="⬅️ Fit width", scale=1)

                    with gradio.Column(variant="panel"):
                        self.fields.ssaa = gradio.Slider(label="Super sampling anti-aliasing",
                            info="Smoother edges and better quality",
                            value=1.5, minimum=1, maximum=2, step=0.1)

                    with gradio.Column(variant="panel"):
                        self.fields.quality = gradio.Slider(label="Shader quality",
                            info="Improves intersections calculations",
                            value=50, minimum=0, maximum=100, step=10)

                    self.fields.fit_height.click(**self.simple(self.fit_width))
                    self.fields.fit_width.click(**self.simple(self.fit_height))

                with gradio.Row(equal_height=True, variant="panel"):
                    self.fields.time = gradio.Slider(label="Duration (seconds)",
                        info="How long the animation or its loop lasts",
                        minimum=0, maximum=30, step=0.5, value=5)
                    self.fields.fps = gradio.Slider(label="Framerate (fps)",
                        info="Defines the animation smoothness",
                        minimum=1, maximum=120, step=1, value=60)
                    self.fields.loop = gradio.Slider(label="Loop count",
                        info="Repeat the final video this many times",
                        minimum=1, maximum=10, step=1, value=1)

            with gradio.Tab("Advanced"):
                self.fields.turbopipe = gradio.Checkbox(label="Enable TurboPipe", value=True,
                    info="Improves rendering speeds, disable if you encounter issues or crashes")

            # Update depth map and resolution on image change
            outputs = {self.fields.image, self.fields.depth, self.fields.width, self.fields.height}
            self.fields.image    .change(**self.simple(self.estimate, outputs=outputs))
            self.fields.upscale  .click (**self.simple(self.upscale,  outputs=outputs))
            self.fields.estimator.change(**self.simple(self.estimate, outputs=outputs))
            self.fields.estimate .click (**self.simple(self.estimate, outputs=outputs))

            # Main render button
            self.fields.render.click(**self.simple(
                self.render, outputs={self.fields.video}
            ))

            gradio.Markdown(''.join((
                "Made with ❤️ by [**Tremeschin**](https://github.com/Tremeschin) | ",
                f"**Alpha** WebUI v{DEPTHFLOW.VERSION} | ",
                "[**Website**](https://brokensrc.dev/) | "
                "[**Discord**](https://discord.com/invite/KjqvcYwRHm/) | ",
                "[**Telegram**](https://t.me/BrokenSource/) | ",
                "[**GitHub**](https://github.com/BrokenSource/DepthFlow)"
            )))

        return self.interface.launch(
            allowed_paths=[DEPTHFLOW.DIRECTORIES.DATA],
            favicon_path=DEPTHFLOW.RESOURCES.ICON_PNG,
            inbrowser=browser, show_api=False,
            prevent_thread_lock=(not block),
            max_threads=threads,
            server_name=server,
            server_port=port,
            share=share,
        )

# ------------------------------------------------------------------------------------------------ #

if (__name__ == "__main__"):
    demo = DepthGradio()
    demo.launch()

# ------------------------------------------------------------------------------------------------ #
