# ------------------------------------------------------------------------------------------------ #
# (c) Tremeschin, all rights reserved.
#
# The DepthFlow API is made available for self-hosting, strictly for personal use. You're welcome to
# use it for developing plugins, integrations, or tools that would connect to an official service in
# the future (no barriers to get started). However, sharing, redistributing, selling or offering the
# service to others is not allowed without the author's explicit consent and permission.
# ------------------------------------------------------------------------------------------------ #

import asyncio
import contextlib
import itertools
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Optional, Self, Union

import requests
from attrs import Factory, define
from dotmap import DotMap
from fastapi.responses import Response
from PIL import Image
from pydantic import Field, HttpUrl
from ShaderFlow.Scene import RenderSettings
from typer import Option

from Broken import (
    BrokenModel,
    BrokenTyper,
    Environment,
    ParallelQueue,
    Runtime,
    log,
)
from Broken.Core.BrokenFastAPI import BrokenFastAPI, WorkersType
from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator
from Broken.Externals.FFmpeg import BrokenFFmpeg
from Broken.Externals.Upscaler import BrokenUpscaler, NoUpscaler
from DepthFlow import DEPTHFLOW, DEPTHFLOW_ABOUT
from DepthFlow.Animation import Actions, DepthAnimation
from DepthFlow.Scene import DepthScene

# ------------------------------------------------------------------------------------------------ #

PydanticImage = Union[str, Path, HttpUrl]

class DepthInput(BrokenModel):
    image: PydanticImage = DepthScene.DEFAULT_IMAGE
    depth: Optional[PydanticImage] = None

class DepthPayload(BrokenModel):
    input:     DepthInput     = Field(default_factory=DepthInput)
    estimator: DepthEstimator = Field(default_factory=DepthAnythingV2)
    animation: DepthAnimation = Field(default_factory=DepthAnimation)
    upscaler:  BrokenUpscaler = Field(default_factory=NoUpscaler)
    render:    RenderSettings = Field(default_factory=RenderSettings)
    ffmpeg:    BrokenFFmpeg   = Field(default_factory=BrokenFFmpeg)
    expire:    int            = Field(3600, exclude=True)
    hash:      int            = Field(0, exclude=True)
    priority:  int            = Field(0, exclude=True)

    # Priority queue sorting

    def __lt__(self, other: Self) -> bool:
        return (self.priority > other.priority)

    def __gt__(self, other: Self) -> bool:
        return (self.priority < other.priority)

# ------------------------------------------------------------------------------------------------ #

class DepthWorker(ParallelQueue):
    def worker(self):
        scene = DepthScene(backend="headless")

        for endurance in itertools.count(1):
            task: DepthPayload = self.next()
            print("Rendering payload:", task.json())

            try:
                # The classes are already cooked by fastapi!
                scene.estimator = task.estimator
                scene.animation = task.animation
                scene.upscaler  = task.upscaler
                scene.ffmpeg    = task.ffmpeg
                scene.ffmpeg.empty_audio()
                scene.input(
                    image=task.input.image,
                    depth=task.input.depth
                )

                # Render the video, read contents, delete temp file
                with tempfile.NamedTemporaryFile(
                    suffix=("."+task.render.format),
                    delete=False,
                ) as temp:
                    video: bytes = scene.main(
                        **task.render.dict(),
                        output=Path(temp.name),
                        progress=False
                    )[0].read_bytes()

                    self.done(task, video)

            except Exception as error:
                log.error(f"Error rendering video: {error}")
                self.done(task, error)

            finally:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(temp.name)

# ------------------------------------------------------------------------------------------------ #

@define
class DepthServer(BrokenFastAPI):
    cli: BrokenTyper = Factory(lambda: BrokenTyper(chain=True))

    queue: ParallelQueue = None
    """The queue of workers processing tasks"""

    def __attrs_post_init__(self):
        self.api.title = "DepthFlow Project API"
        self.api.version = Runtime.Version
        self.cli.description = DEPTHFLOW_ABOUT

        # Commands
        with self.cli.panel("📦 Server endpoints"):
            self.cli.command(self.launch)
            self.cli.command(self.runpod)

        with self.cli.panel("🚀 Core"):
            self.cli.command(self.config)
            self.cli.command(self.test)

        # Endpoints
        self.api.post("/estimate")(self.estimate)
        self.api.post("/upscale")(self.upscale)
        self.api.post("/render")(self.render)

        # Processing
        self.queue = DepthWorker(
            cache_path=(DEPTHFLOW.DIRECTORIES.CACHE/"ServerRender"),
            cache_size=Environment.float("DEPTHSERVER_CACHE_SIZE_MB", 500),
            size=Environment.int("DEPTHSERVER_WORKERS", 3),
        ).start()

    def config(self,
        workers: WorkersType=3
    ) -> None:
        self.queue.size = workers

    # -------------------------------------------|
    # Routes

    async def estimate(self,
        image: PydanticImage,
        estimator: DepthEstimator=DepthAnythingV2(),
    ) -> Response:
        return Response(
            media_type="image/png",
            content=Image.open(estimator.estimate(image)).tobytes()
        )

    async def upscale(self,
        image: PydanticImage,
        upscaler: BrokenUpscaler=NoUpscaler(),
    ) -> Response:
        return Response(
            media_type="image/png",
            content=upscaler.upscale(image).tobytes()
        )

    async def render(self, task: DepthPayload) -> Response:
        start: float = time.perf_counter()
        task = DepthPayload.load(task)
        task.hash = hash(task)

        for index in itertools.count(1):

            # Video is already cached or finished
            if (video := self.queue.get(task)):
                if isinstance((error := video), Exception):
                    return Response(
                        status_code=500,
                        media_type="text/plain",
                        content=str(error),
                    )

                return Response(
                    media_type=f"video/{task.render.format}",
                    content=video,
                    headers=dict(
                        took=f"{time.perf_counter() - start:.2f}",
                        cached=str(index == 1).lower(),
                    ),
                )

            # Timeout logic to prevent hanging
            elif (start + 30 < time.perf_counter()):
                return Response(
                    status_code=503,
                    media_type="text/plain",
                    content="Request timed out",
                )

            self.queue.put(task)
            await asyncio.sleep(0.100)

    # -------------------------------------------|
    # Testing

    def test(self,
        jobs: Annotated[int, Option("--jobs", "-j",
            help="How many jobs to queue up")]=1,
    ) -> None:
        def request(client: int) -> None:
            config = DepthPayload(
                priority=client,
                input=DepthInput(
                    image="https://w.wallhaven.cc/full/ex/wallhaven-ex1yxk.jpg"
                    # image="/home/tremeschin/plant.jpg"
                ),
                ffmpeg=BrokenFFmpeg().h264_nvenc(),
                render=RenderSettings(
                    ssaa=1.0,
                    width=1280,
                    fps=60,
                    loop=1,
                    time=0.01 + client/1000000,
                ),
                animation=DepthAnimation(
                    steps=[
                        Actions.Orbital(),
                        # Actions.Lens(),
                    ]
                )
            )

            # Debug print the payload
            from rich.pretty import pprint
            pprint(f"POST: {config.json()}")

            # Actually send the job request
            response = requests.post(
                url=f"{self.api_url}/render",
                json=config.dict()
            )

            # Save the video to disk
            Path(path := f"/tmp/video-{client}.mp4") \
                .write_bytes(response.content)

            headers = DotMap(response.headers)
            log.success(f"Saved video to {path}, cached: {headers.cached}")

        # Stress test parallel requests
        with ThreadPoolExecutor(max_workers=10) as pool:
            for worker in range(jobs):
                pool.submit(request, worker)
                # time.sleep(0.1)

# ------------------------------------------------------------------------------------------------ #
