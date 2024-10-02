import os
import uuid
from concurrent.futures import ThreadPoolExecutor as ThreadPool
from pathlib import Path
from typing import Annotated, Callable, Dict, Tuple

import gradio
import typer
from attr import Factory
from attrs import define
from dotmap import DotMap
from gradio.themes.utils import colors, fonts, sizes

import Broken
from Broken import BrokenPath, BrokenResolution, iter_dict
from Broken.Externals.Depthmap import (
    DepthAnythingV1,
    DepthAnythingV2,
    Marigold,
    ZoeDepth,
)
from Broken.Externals.Upscaler import NoUpscaler, Realesr, Waifu2x
from DepthFlow import DEPTHFLOW
from DepthFlow.Motion import Presets

WEBUI_OUTPUT: Path = BrokenPath.recreate(DEPTHFLOW.DIRECTORIES.SYSTEM_TEMP/"DepthFlow"/"WebUI")
"""The temporary output for the WebUI, cleaned at the start and after any render"""

# ------------------------------------------------------------------------------------------------ #

@define(slots=False)
class DepthGradio:
    interface: gradio.Blocks = None
    fields: DotMap = Factory(DotMap)

    estimators = {
        "DepthAnything V2": DepthAnythingV2,
        "DepthAnything V1": DepthAnythingV1,
        "ZoeDepth": ZoeDepth,
        "Marigold": Marigold,
    }

    upscalers = {
        "No upscaler": NoUpscaler,
        "Real-ESRGAN": Realesr,
        "Waifu2x": Waifu2x,
    }

    def simple(self, method: Callable, **options: Dict) -> Dict:
        show_progress = bool(options.get("outputs"))
        outputs = options.pop("outputs", set(iter_dict(self.fields)))
        inputs = options.pop("inputs", set(iter_dict(self.fields)))
        return dict(
            fn=method, inputs=inputs, outputs=outputs,
            show_progress=show_progress,
            **options,
        )

    def estimate(self, user: Dict):
        if (user[self.fields.image] is None):
            return gradio.Warning("The input image is empty")
        estimator = self.estimators[user[self.fields.estimator]]()
        image = user[self.fields.image]
        yield {self.fields.width:  image.size[0]}
        yield {self.fields.height: image.size[1]}
        yield {self.fields.depth:  estimator.estimate(image)}

    def _fit_resolution(self, live: Dict, target: Tuple[int, int]) -> Tuple[int, int]:
        if (live[self.fields.image] is None):
            raise GeneratorExit()
        width, height = live[self.fields.image].size
        return BrokenResolution().fit(
            old=(1920, 1080), new=target,
            ar=(width/height), multiple=1,
        )

    def fit_width(self, user: Dict):
        yield {self.fields.height: self._fit_resolution(user, (user[self.fields.width], None))[1]}

    def fit_height(self, user: Dict):
        yield {self.fields.width: self._fit_resolution(user, (None, user[self.fields.height]))[0]}

    def render(self, user: Dict):
        if (user[self.fields.image] is None):
            return gradio.Warning("The input image is empty")
        if (user[self.fields.depth] is None):
            return gradio.Warning("The input depthmap is empty")

        def _thread():
            from DepthFlow import DepthScene
            scene = DepthScene(backend="headless")
            scene.set_estimator(self.estimators[user[self.fields.estimator]]())
            scene.set_upscaler(self.upscalers[user[self.fields.upscaler]]())
            scene.input(image=user[self.fields.image], depth=user[self.fields.depth])

            # Build and add any enabled preset class
            for preset in Presets.members():
                preset_name = preset.__name__
                preset_dict = self.fields.animation[preset_name]
                if (not user[preset_dict.enabled]):
                    continue
                scene.add_animation(preset(**{
                    key: user[item] for (key, item) in preset_dict.options.items()
                }))

            return scene.main(
                width=user[self.fields.width],
                height=user[self.fields.height],
                fps=user[self.fields.fps],
                time=user[self.fields.time],
                loop=user[self.fields.repeat],
                output=(WEBUI_OUTPUT/f"{uuid.uuid4()}.mp4"),
                noturbo=(os.getenv("NOTURBO","0")=="1"),
                ssaa=1.5,
            )[0]

        with ThreadPool() as pool:
            task = pool.submit(_thread)
            yield {self.fields.video: task.result()}
            os.remove(task.result())

    def launch(self,
        share: Annotated[bool, typer.Option("--share", "-s",
            help="Share the WebUI on the network")]=False,
        threads: Annotated[int,  typer.Option("--threads", "-t",
            help="Number of maximum concurrent renders")]=4,
        browser: Annotated[bool, typer.Option("--open", " /--quiet", "-q",
            help="Open the WebUI in the browser")]=True,
    ) -> gradio.Blocks:
        with gradio.Blocks(
            theme=gradio.themes.Default(
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
                with gradio.Row():
                    with gradio.Column(variant="panel"):
                        self.fields.image = gradio.Image(scale=1,
                            sources=["upload", "clipboard"],
                            type="pil", label="Input image",
                        )
                        self.fields.upscaler = gradio.Dropdown(
                            choices=list(self.upscalers.keys()),
                            value=list(self.upscalers.keys())[0],
                            label="Upscaler",
                        )

                    with gradio.Column(variant="panel"):
                        self.fields.depth = gradio.Image(scale=1,
                            sources=["upload", "clipboard"],
                            type="pil", label="Depthmap",
                        )
                        self.fields.estimator = gradio.Dropdown(
                            choices=list(self.estimators.keys()),
                            value=list(self.estimators.keys())[0],
                            label="Depth Estimator",
                        )

                    with gradio.Column(variant="panel"):
                        self.fields.video = gradio.Video(scale=1,
                            label="Output video",
                            interactive=False,
                            autoplay=True,
                        )
                        self.fields.render = gradio.Button(
                            value="🔥 Render 🔥",
                            variant="primary",
                            size="lg",
                        )

                with gradio.Accordion("Animation", open=False):
                    for preset in Presets.members():
                        preset_name = preset.__name__
                        preset_dict = self.fields.animation[preset_name]

                        with gradio.Tab(preset_name):
                            preset_dict.enabled = gradio.Checkbox(
                                value=False, label="Enabled", info=preset.__doc__)

                            for attr, field in preset.model_fields.items():
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
                                elif (isinstance(field.annotation, Tuple)):
                                    print(attr, field, field.annotation)

                with gradio.Row():
                    self.fields.width = gradio.Number(label="Width", value=1920, minimum=1, step=2)
                    self.fields.height = gradio.Number(label="Height", value=1080, minimum=1, step=2)

                    self.fields.width.change(**self.simple(self.fit_width), trigger_mode="once")
                    self.fields.height.change(**self.simple(self.fit_height), trigger_mode="once")

                    self.fields.fps = gradio.Slider(
                        minimum=1, maximum=120, step=1,
                        label="Framerate", value=60,
                    )

                with gradio.Row():
                    self.fields.time = gradio.Slider(
                        minimum=0, maximum=30, step=0.5,
                        label="Duration (seconds)", value=5
                    )
                    self.fields.repeat = gradio.Slider(
                        minimum=1, maximum=10, step=1,
                        label="Number of loops", value=1
                    )

            # Update depth map and resolution on image change
            self.fields.estimator.change(**self.simple(self.estimate,
                outputs={self.fields.depth, self.fields.width, self.fields.height}
            ))
            self.fields.image.change(**self.simple(self.estimate,
                outputs={self.fields.depth, self.fields.width, self.fields.height}
            ))

            # Main render button
            self.fields.render.click(**self.simple(
                self.render, outputs={self.fields.video}
            ))

            gradio.Markdown(''.join((
                "Made with ❤️ by [**Tremeschin**](https://github.com/Tremeschin) | ",
                f"**Alpha** WebUI v{DEPTHFLOW.VERSION} | ",
                "[**Website**](https://brokensrc.dev/depthflow) | "
                "[**Discord**](https://discord.com/invite/KjqvcYwRHm/) | ",
                "[**Telegram**](https://t.me/brokensource/) | ",
                "[**GitHub**](https://github.com/BrokenSource/DepthFlow)"
            )))

        return self.interface.launch(
            allowed_paths=[DEPTHFLOW.DIRECTORIES.DATA],
            favicon_path=DEPTHFLOW.RESOURCES.ICON_PNG,
            inbrowser=browser, show_api=False,
            quiet=Broken.RELEASE,
            max_threads=threads,
            share=share,
        )

# ------------------------------------------------------------------------------------------------ #
