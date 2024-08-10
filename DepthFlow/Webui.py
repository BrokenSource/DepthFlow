import os

import gradio
from attrs import define

from Broken import BrokenEnum
from Broken.Externals.Depthmap import (
    DepthAnythingV1,
    DepthAnythingV2,
    Marigold,
    ZoeDepth,
)
from Broken.Externals.Upscaler import NoUpscaler, Realesr, Waifu2x
from DepthFlow import DEPTHFLOW, DepthScene


class Quality(BrokenEnum):
    Low    = 0
    Medium = 25
    High   = 50
    Ultra  = 100

@define(slots=False)
class DepthFlowWebui:
    interface: gradio.Blocks = None

    estimators = {
        "DepthAnything V2": DepthAnythingV2,
        "DepthAnything V1": DepthAnythingV1,
        "ZoeDepth": ZoeDepth,
        "Marigold": Marigold
    }

    upscalers = {
        "No Upscaler": NoUpscaler,
        "Real-ESRGAN": Realesr,
        "Waifu2x": Waifu2x
    }

    resolutions = {
        "720p (16:9)": (1280, 720),
        "1080p (16:9)": (1920, 1080),
        "1440p (16:9)": (2560, 1440),
        "2160p (16:9)": (3840, 2160),
        "720p (9:16)": (720, 1280),
        "1080p (9:16)": (1080, 1920),
        "1440p (9:16)": (1440, 2560),
        "2160p (9:16)": (2160, 3840),
        "720p (4:3)": (960, 720),
        "1080p (4:3)": (1440, 1080),
        "1440p (4:3)": (1920, 1440),
        "2160p (4:3)": (2880, 2160),
    }

    def estimate_depth(self, estimator, image):
        return self.estimators[estimator]().estimate(image)

    def set_resolution(self, resolution_name):
        width, height = self.resolutions[resolution_name]
        return width, height

    def render(self, image, depth, width, height, fps, quality, ssaa, time, repeat, estimator, upscaler):
        scene = DepthScene(backend="headless")
        scene.input(image=image, depth=depth)
        scene.set_estimator(self.estimators[estimator]())
        scene.set_upscaler(self.upscalers[upscaler]())
        video = scene.main(
            width=int(width),
            height=int(height),
            fps=int(fps),
            quality=Quality.get(quality).value,
            ssaa=float(ssaa),
            time=float(time),
            repeat=int(repeat),
            render=True
        )[0]
        # scene.window.destroy()
        return gradio.Video(video)

    def launch(self):
        with gradio.Blocks(
            css="footer{display:none !important}",
            theme=gradio.themes.Soft(),
            analytics_enabled=False
        ) as self.interface:
            gradio.Markdown("# DepthFlow")

            with gradio.Tab("Application"):
                with gradio.Row():
                    self.image = gradio.Image(sources=["upload", "clipboard"], type="pil", label="Input image")
                    self.depth = gradio.Image(interactive=False, label="Depthmap")

                with gradio.Row():
                    self.upscaler = gradio.Dropdown(
                        choices=list(self.upscalers.keys()),
                        value=list(self.upscalers.keys())[0],
                        label="Upscaler",
                    )
                    self.estimator = gradio.Dropdown(
                        choices=list(self.estimators.keys()),
                        value=list(self.estimators.keys())[0],
                        label="Depth Estimator",
                    )
                    self.estimator.change(
                        self.estimate_depth,
                        inputs=[self.estimator, self.image],
                        outputs=[self.depth]
                    )

                self.image.change(
                    self.estimate_depth,
                    inputs=[self.estimator, self.image],
                    outputs=[self.depth]
                )

                with gradio.Row():
                    self.width = gradio.Number(label="Width", value=1920, minimum=1, maximum=4096)
                    self.height = gradio.Number(label="Height", value=1080, minimum=1, maximum=4096)
                    self.resolution_preset = gradio.Dropdown(
                        choices=list(self.resolutions.keys()),
                        label="Resolution", value="1080p (16:9)"
                    )
                    self.resolution_preset.change(
                        self.set_resolution,
                        inputs=[self.resolution_preset],
                        outputs=[self.width, self.height]
                    )
                    self.quality = gradio.Dropdown(label="Quality",
                        choices=Quality.values(), value=Quality.High)

                    self.ssaa = gradio.Slider(label="SSAA", minimum=0.1, maximum=2, step=0.1, value=1.0)
                    self.fps = gradio.Slider(label="FPS", minimum=1, maximum=120, step=1, value=60)

                with gradio.Row():
                    self.time = gradio.Slider(
                        minimum=0, maximum=30, step=0.5,
                        label="Duration (seconds)", value=10
                    )
                    self.repeat = gradio.Slider(
                        minimum=1, maximum=10, step=1,
                        label="Number of Loops", value=1
                    )

                render_button = gradio.Button("Render", size="lg")
                self.video = gradio.PlayableVideo(label="Output Video")

                render_button.click(
                    self.render,
                    inputs=[self.image, self.depth, self.width, self.height, self.fps, self.quality, self.ssaa, self.time, self.repeat, self.estimator, self.upscaler],
                    outputs=[self.video]
                )

            gradio.Markdown(''.join((
                "Made with ❤️ by [**Tremeschin**](https://github.com/Tremeschin) | ",
                f"**Version** {DEPTHFLOW.VERSION} | ",
                "[**Website**](https://brokensrc.dev/) | "
                "[**Discord**](https://discord.com/invite/KjqvcYwRHm/) | ",
                "[**Telegram**](https://t.me/brokensource/) | ",
                "[**GitHub**](https://github.com/BrokenSource/)"
            )))

        self.interface.launch(
            share=bool(eval(os.getenv("SHARE_WEBUI", "0"))),
            allowed_paths=[DEPTHFLOW.DIRECTORIES.DATA]
        )
