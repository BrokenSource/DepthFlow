"""
(c) CC BY-SA 4.0, Tremeschin

Advanced example of parallel rendering, with multiple parameters per rendered
file, limiting the number of concurrent processes, thread and vram leaks safe

Warning: This WILL use A LOT OF RAM depending on concurrency and image size
Warning: This WILL use A LOT OF CPU for the video encoding, if enough GPU

• For more information, visit https://brokensrc.dev/depthflow (WIP)
"""

import itertools
import math
import os
import time
from abc import abstractmethod
from pathlib import Path
from threading import Thread
from typing import List, Self, Type

from attr import Factory, define
from click import clear
from DepthFlow import DepthScene
from DepthFlow.Motion import Animation, Components, Preset, Presets, Target
from DepthFlow.State import DepthState
from dotmap import DotMap

from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator
from Broken.Externals.Upscaler import BrokenUpscaler, NoUpscaler, Realesr


def combinations(**options):
    """Returns a dictionary of key='this' of itertools.product"""
    for combination in itertools.product(*options.values()):
        yield DotMap(zip(options.keys(), combination))


# Note: You can also use your own subclassing like Custom.py!
class YourScene(DepthScene):
    def update(self):
        self.state.offset_x = 0.3 * math.sin(self.cycle)
        self.state.isometric = 1

# -------------------------------------------------------------------------------------------------|

@define
class DepthManager:

    estimator: DepthEstimator = Factory(DepthAnythingV2)
    """A **shared** estimator for all threads"""

    upscaler: BrokenUpscaler = Factory(NoUpscaler)
    """The upscaler to use for all threads"""

    threads: List[Thread] = Factory(list)
    """List of running threads"""

    concurrency: int = int(os.getenv("WORKERS", 4))
    """Maximum concurrent render workers (high memory usage)"""

    outputs: List[Path] = Factory(list)
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

    def parallax(self, scene: Type[DepthScene], image: Path) -> None:

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
        data.scene.add_animation(DepthState(
            vignette_enable=True,
            dof_enable=True,
        ))
        data.scene.add_animation(Components.Set(target=Target.Isometric, value=0.4))
        data.scene.add_animation(Components.Set(target=Target.Height, value=0.10))
        data.scene.add_animation(Presets.Circle(
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

    def _worker(self, scene: Type[DepthScene], image: Path):
        # Note: Share an estimator between threads to avoid memory leaks
        scene = scene(backend="headless")
        scene.estimator = self.estimator
        scene.set_upscaler(self.upscaler)
        scene.input(image=image)

        # Note: We reutilize the Scene to avoid re-creation!
        # Render multiple lengths, or framerates, anything
        for data in combinations(**self.variants(image)):
            data.update(scene=scene, image=image)

            # Find or set common parameters
            output = self.filename(data)
            scene.clear_animations()
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

# -------------------------------------------------------------------------------------------------|

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
            data.scene.add_animation(Presets.Orbital())
        if (data.variation == 1):
            data.scene.add_animation(Components.Set(target=Target.Isometric, value=0.4))
            data.scene.add_animation(Presets.Circle(intensity=0.3))

# -------------------------------------------------------------------------------------------------|

if (__name__ == "__main__"):
    images = Path(os.getenv("IMAGES", "/home/tremeschin/Public/Images"))

    # Multiple unique videos per file
    # Note: Use Realesr() for some upscaler!
    with DepthManager(upscaler=NoUpscaler()) as manager:
    # with YourManager(upscaler=Realesr()) as manager:
        for image in images.glob("*"):
            manager.parallax(DepthScene, image)

        for output in manager.outputs:
            print(f"• {output}")
