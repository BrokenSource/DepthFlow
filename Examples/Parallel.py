"""
Advanced example of parallel rendering using DepthFlow
"""
import math
import time
from multiprocessing import Manager, Process
from pathlib import Path
from typing import List

from attr import Factory, define
from DepthFlow import DepthScene

from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator

# Sharing objects between processes
MANAGER = Manager()

class YourScene(DepthScene):
    def update(self):
        self.state.offset_x = math.sin(2 * self.cycle)
        self.state.isometric = 1

@define
class Logic:

    # Process management
    outputs: List[Path] = MANAGER.list()
    workers: List[Process] = list()
    max_workers: int = 4

    # DepthFlow objects
    estimator: DepthEstimator = Factory(DepthAnythingV2)

    def run(self, image: Path):

        # Optimization: Cache depth map, so the worker doesn't have to load it;
        # Note: The estimator must match the one used in the worker
        self.estimator.estimate(image)

        # Limit the maximum concurrent processes
        while len(self.workers) >= self.max_workers:
            self.workers = list(filter(lambda x: x.is_alive(), self.workers))
            time.sleep(0.05)

        # Create and add a new running process
        process = Process(target=self._worker, args=(image,))
        self.workers.append(process)
        process.start()

    def join(self):
        for process in self.workers:
            process.join()

    def _worker(self, image: Path):
        scene = YourScene()
        scene.input(image=image)
        video = scene.main(
            output=image.with_suffix(".mp4").name,
            time=5, fps=30
        )[0]
        scene.window.destroy()
        self.outputs.append(video)

if __name__ == "__main__":
    IMAGES = Path("/home/tremeschin/Documents/Wallpapers")
    logic = Logic()

    for image in IMAGES.glob("*"):
        logic.run(image)

    logic.join()

    for output in logic.outputs:
        print(f"• {output}")
