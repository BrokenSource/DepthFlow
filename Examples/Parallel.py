"""
Advanced example of parallel rendering using DepthFlow, with multiple parameters
per rendered file, limiting the number of concurrent processes, properly cleaning
resources and caching the depth map for optimizations, thread safety
"""
import itertools
import math
import time
from pathlib import Path
from threading import Thread
from typing import List

from attr import Factory, define
from DepthFlow import DepthScene
from dotmap import DotMap

from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator


def combinations(**options):
    for combination in itertools.product(*options.values()):
        yield DotMap(zip(options.keys(), combination))


class YourScene(DepthScene):
    def update(self):
        self.state.offset_x = math.sin(2 * self.cycle)
        self.state.isometric = 1

@define
class Logic:

    # Threads management
    threads: List[Thread] = Factory(list)
    outputs: List[Path] = Factory(list)
    max_workers: int = 4

    # DepthFlow objects
    estimator: DepthEstimator = Factory(DepthAnythingV2)

    def run(self, data: DotMap):

        # Optimization: Cache depth map, so the worker doesn't have to load it;
        # Note: The estimator must match the one used in the worker
        self.estimator.estimate(data.image)

        # Limit the maximum concurrent workers
        while len(self.threads) >= self.max_workers:
            self.threads = list(filter(lambda x: x.is_alive(), self.threads))
            time.sleep(0.05)

        # Create and add a new running worker
        thread = Thread(target=self._worker, args=(data,))
        self.threads.append(thread)
        thread.start()

    def join(self):
        for thread in self.threads:
            thread.join()

    def _worker(self, data: DotMap):
        scene = YourScene(backend="headless")
        scene.input(image=data.image)

        # Find the output path (same path, render folder)
        output = data.image.parent / "Render" / ("_".join((
            data.image.stem,
            f"fps-{data.fps}",
            f"length-{data.length}",
        )) + ".mp4")

        # Make sure the output folder exists
        output.parent.mkdir(parents=True, exist_ok=True)

        # Render the video
        video = scene.main(
            output=output,
            time=data.length,
            fps=data.fps,
            ssaa=1.5,
        )[0]

        # Cleanup, notify exported file
        scene.window.destroy()
        self.outputs.append(video)

if __name__ == "__main__":
    images = Path("/home/tremeschin/Documents/Wallpapers")
    logic = Logic()

    # Multiple unique videos per file
    for data in combinations(
        image=images.glob("*"),
        length=(5, 10),
        fps=(30, 60),
    ):
        logic.run(data)

    logic.join()

    for output in logic.outputs:
        print(f"• {output}")
