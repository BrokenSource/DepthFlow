"""
(c) CC BY-SA 4.0, Tremeschin

Advanced example of parallel rendering, with multiple parameters per rendered
file, limiting the number of concurrent processes, thread and vram leaks safe

Warning: This WILL use A LOT OF RAM depending on concurrency and image size
Warning: This WILL use A LOT OF CPU for the video encoding, if enough GPU

• For more information, visit https://brokensrc.dev/depthflow
"""
import math
import os
import time
from abc import abstractmethod
from pathlib import Path
from threading import Thread
from typing import Self

from attr import Factory, define
from depthflow.animation import Animation, Target
from depthflow.scene import DepthScene
from dotmap import DotMap

from broken import Environment, combinations
from broken.externals.depthmap import DepthAnythingV2, DepthEstimator
from broken.externals.upscaler import BrokenUpscaler, NoUpscaler, Upscayl


# Note: You can also use your own subclassing like Custom.py!
class YourScene(DepthScene):
    def update(self):
        self.state.offset_x = 0.3 * math.sin(self.cycle)
        self.state.isometric = 1

# ------------------------------------------------------------------------------------------------ #

@define
class DepthManager:

    estimator: DepthEstimator = Factory(DepthAnythingV2)
    """A **shared** estimator for all threads"""

    upscaler: BrokenUpscaler = Factory(NoUpscaler)
    """The upscaler to use for all threads"""

    threads: list[Thread] = Factory(list)
    """List of running threads"""

    concurrency: int = Environment.int("WORKERS", 4)
    """Maximum concurrent render workers (high memory usage)"""

    outputs: list[Path] = Factory(list)
    """List of all rendered videos on this session"""

    def __attrs_post_init__(self):
        self.estimator.load_torch()
        self.estimator.load_model()
        self.upscaler.load_model()

    # # Allow for using with statements

    def __enter__(self) -> Self:
        self.outputs = list()
        return self
    def __exit__(self, *ignore) -> None:
        self.join()

    # # User methods

    def parallax(self, scene: type[DepthScene], image: Path) -> None:
        self.estimator.estimate(image)

        # Limit the maximum concurrent threads, nice pattern 😉
        while len(self.threads) >= self.concurrency:
            self.threads = list(filter(lambda x: x.is_alive(), self.threads))
            time.sleep(0.05)

        # Create and add a new running worker, daemon so it dies with the main thread
        thread = Thread(target=self._worker, args=(scene, image), daemon=True)
        self.threads.append(thread)
        thread.start()

    @abstractmethod
    def filename(self, data: DotMap) -> Path:
        """Find the output path (Default: same path as image, 'Render' folder)"""
        return (data.image.parent / "Render") / ("_".join((
            data.image.stem,
            f"v{data.variation or 0}",
            f"{data.render.time}s",
            f"{data.render.height}p{data.render.fps or ''}",
        )) + ".mp4")

    @abstractmethod
    def animate(self, data: DotMap) -> None:
        """Add preset system's animations to each export"""
        data.scene.animation.add(Animation.State(
            vignette_enable=True,
            blur_enable=True,
        ))
        data.scene.animation.add(Animation.Set(target=Target.Isometric, value=0.4))
        data.scene.animation.add(Animation.Set(target=Target.Height, value=0.10))
        data.scene.animation.add(Animation.Circle(
            intensity=0.5,
        ))

    @abstractmethod
    def variants(self, image: Path) -> DotMap:
        return DotMap(
            render=combinations(
                height=(1080, 1440),
                time=(5, 10),
                fps=(60,),
            )
        )

    # # Internal methods

    def _worker(self, scene: type[DepthScene], image: Path):
        # Note: Share an estimator between threads to avoid memory leaks
        scene = scene(backend="headless")
        scene.config.estimator = self.estimator
        scene.set_upscaler(self.upscaler)
        scene.input(image=image)

        # Note: We reutilize the Scene to avoid re-creation!
        # Render multiple lengths, or framerates, anything
        for data in combinations(**self.variants(image)):
            data.update(scene=scene, image=image)

            # Find or set common parameters
            output = self.filename(data)
            scene.config.animation.clear()
            self.animate(data)

            # Make sure the output folder exists
            output.parent.mkdir(parents=True, exist_ok=True)

            # Render the video
            video = scene.main(output=output, **data.render)[0]
            self.outputs.append(video)

        # Imporant: Free up OpenGL resources
        scene.window.destroy()

    def join(self):
        for thread in self.threads:
            thread.join()

# ------------------------------------------------------------------------------------------------ #

# Nice: You can subclass the manager itself 🤯
class YourManager(DepthManager):
    def variants(self, image: Path) -> DotMap:
        return DotMap(
            variation=[0, 1],
            render=combinations(
                height=[1080],
                time=[5],
                loop=[2],
                fps=[60],
            )
        )

    def animate(self, data: DotMap):
        if (data.variation == 0):
            data.scene.animation.add(Animation.Orbital())
        if (data.variation == 1):
            data.scene.animation.add(Animation.Set(target=Target.Isometric, value=0.4))
            data.scene.animation.add(Animation.Circle(intensity=0.3))

# ------------------------------------------------------------------------------------------------ #

if (__name__ == "__main__"):
    images = Path(os.getenv("IMAGES", "/home/tremeschin/Public/Images"))

    # Multiple unique videos per file
    # Note: Use Upscayl() for some upscaler!
    with DepthManager(upscaler=NoUpscaler()) as manager:
    # with YourManager(upscaler=Upscayl()) as manager:
        for image in images.glob("*"):
            if (image.is_file()):
                manager.parallax(DepthScene, image)

        for output in manager.outputs:
            print(f"• {output}")
