import math
import multiprocessing
import time
from multiprocessing import Process
from pathlib import Path
from threading import Thread

from DepthFlow import DepthScene

from Broken.Externals.Depthmap import DepthAnythingV2


class MultiDepth(DepthScene):
    def update(self):
        self.state.offset_x = math.sin(2*self.cycle)


IMAGES = "/home/tremeschin/Documents/Wallpapers"
THREADS = list()
MAX_THREADS = 4
MANAGER = multiprocessing.Manager()
OUTPUTS = MANAGER.list()

class Main:
    def __init__(self) -> None:
        estimator = DepthAnythingV2()

        def worker(self, image: Path):
            process = Process(target=self.render, args=(image,))
            process.start()
            process.join()

        for image in Path(IMAGES).iterdir():

            # Cache depth map
            estimator.estimate(image)

            # Wait for free thread
            while len(THREADS) >= MAX_THREADS:
                for index, thread in enumerate(THREADS):
                    if thread.is_alive():
                        continue
                    THREADS.pop(index)
                    break
                time.sleep(0.05)

            thread = Thread(target=worker, args=(self, image))
            THREADS.append(thread)
            thread.start()

        for thread in THREADS:
            thread.join()

        for output in OUTPUTS:
            print(f"• {output}")

    def render(self, image: Path):
        scene = MultiDepth()
        scene.input(image=image)
        video = scene.main(output=image.with_suffix(".mp4").name, time=5)[0]
        scene.window.destroy()
        OUTPUTS.append(video)

if __name__ == "__main__":
    Main()
