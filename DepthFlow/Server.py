# ------------------------------------------------------------------------------------------------ #
#
# (c) Tremeschin, all rights reserved.
#
# The DepthFlow API is made available for self-hosting, strictly for personal use. You're welcome to
# use it for developing plugins, integrations, or tools that would connect to an official service in
# the future (no barriers to get started). However, sharing, redistributing, selling or offering the
# service to others is not allowed without the author's explicit consent and permission.
#
# ------------------------------------------------------------------------------------------------ #
import asyncio
import itertools
import json
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import PriorityQueue
from typing import (
    Annotated,
    Dict,
    Optional,
    Self,
    Union,
)

import requests
import uvicorn
from attrs import Factory, define
from diskcache import Cache as DiskCache
from dotmap import DotMap
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import Field, HttpUrl
from ShaderFlow.Scene import RenderConfig
from typer import Option

from Broken import (
    BrokenModel,
    BrokenPlatform,
    BrokenThread,
    BrokenTyper,
    DictUtils,
    Runtime,
    log,
)
from Broken.Externals.Depthmap import DepthAnythingV2, DepthEstimator
from Broken.Externals.FFmpeg import BrokenFFmpeg
from Broken.Externals.Upscaler import BrokenUpscaler, NoUpscaler
from Broken.Types import MiB
from DepthFlow import DEPTHFLOW
from DepthFlow.Animation import Actions, DepthAnimation
from DepthFlow.Scene import DepthScene

# ------------------------------------------------------------------------------------------------ #

class Hosts:
    LOOPBACK: str = "127.0.0.1"
    WILDCARD: str = "0.0.0.0"

# Wildcard not necessarily is localhost on Windows, make it explicit
DEFAULT_HOST: str = (Hosts.WILDCARD if BrokenPlatform.OnUnix else Hosts.LOOPBACK)
DEFAULT_PORT: int = 8000

# ------------------------------------------------------------------------------------------------ #

class DepthInput(BrokenModel):
    image: Union[str, Path, HttpUrl] = DepthScene.DEFAULT_IMAGE
    depth: Optional[Union[str, Path, HttpUrl]] = None

class DepthPayload(BrokenModel):
    input:     DepthInput     = Field(default_factory=DepthInput)
    estimator: DepthEstimator = Field(default_factory=DepthAnythingV2)
    animation: DepthAnimation = Field(default_factory=DepthAnimation)
    upscaler:  BrokenUpscaler = Field(default_factory=NoUpscaler)
    render:    RenderConfig   = Field(default_factory=RenderConfig)
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

@define(slots=False)
class DepthServer:
    cli: BrokenTyper = Factory(lambda: BrokenTyper(chain=True))
    app: FastAPI     = Factory(lambda: FastAPI(
        title="DepthFlow Rendering API",
        version=Runtime.Version,
    ))

    def __attrs_post_init__(self):
        self.cli.command(self.launch)
        self.cli.command(self.runpod)
        self.cli.command(self.test)
        self.app.post("/render")(self.render)

    @property
    def openapi(self) -> dict:
        return self.app.openapi()

    @property
    def openapi_json(self) -> str:
        return json.dumps(self.openapi, ensure_ascii=False)

    # -------------------------------------------|
    # Properties

    host: str = DEFAULT_HOST
    """Hostname currently being used by the server"""

    port: int = DEFAULT_PORT
    """Port currently being used by the server"""

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    workers: int = None
    """Maximum number of concurrent rendering workers"""

    queue: int = None
    """Maximum number of back-pressure requests until 503 error"""

    # -------------------------------------------|
    # Routes

    def launch(self,
        host: Annotated[str, Option("--host", "-h",
            help="Target Hostname to run the server on")]=DEFAULT_HOST,
        port: Annotated[int, Option("--port", "-p",
            help="Target Port to run the server on")]=DEFAULT_PORT,
        workers: Annotated[int, Option("--workers", "-w",
            help="Maximum number of simultaneous renders")]=3,
        queue: Annotated[int, Option("--queue", "-q",
            help="Maximum number of requests until 503 (back-pressure)")]=20,
        block: Annotated[bool, Option("--block", "-b", " /--free", " /-f",
            help="Block the current thread until the server stops")]=True,
    ) -> None:
        log.info("Launching DepthFlow Server")

        # Update the server's attributes
        for key, value in DictUtils.selfless(locals()).items():
            setattr(self, key, value)

        # Create the pool and the workers
        for _ in range(workers):
            BrokenThread.new(self.worker)

        # Proxy async converter
        async def serve():
            await uvicorn.Server(uvicorn.Config(
                limit_concurrency=self.queue,
                host=self.host, port=self.port,
                app=self.app, loop="uvloop",
            )).serve()

        # Start the server
        BrokenThread.new(asyncio.run, serve())

        # Optionally hold main thread
        for _ in itertools.count(1):
            if (not block):
                break
            time.sleep(1)

    def runpod(self) -> None:
        import runpod
        self.launch(block=False)

        runpod.serverless.start(dict(
            handler=self.render,
        ))

    # -------------------------------------------|
    # Routes

    render_jobs: PriorityQueue = Factory(PriorityQueue)
    render_data: DiskCache = Factory(lambda: DiskCache(
        size_limit=int(float(os.getenv("DEPTHSERVER_CACHE_SIZE_MB", 500))*MiB),
        directory=(DEPTHFLOW.DIRECTORIES.CACHE/"ServerRender"),
    ))

    def worker(self) -> None:
        scene = DepthScene(backend="headless")

        for total in itertools.count(1):
            config = self.render_jobs.get(block=True)
            print("Rendering payload:", config.json())

            try:
                # The classes are already cooked by fastapi!
                scene.estimator = config.estimator
                scene.animation = config.animation
                scene.upscaler  = config.upscaler
                scene.ffmpeg    = config.ffmpeg
                scene.ffmpeg.empty_audio()
                scene.input(
                    image=config.input.image,
                    depth=config.input.depth
                )

                # Render the video, read contents, delete temp file
                with tempfile.NamedTemporaryFile(
                    suffix=("."+config.render.format),
                    delete=False,
                ) as temp:
                    video = scene.main(
                        **config.render.dict(),
                        output=Path(temp.name),
                    )[0].read_bytes()

            except Exception as error:
                log.error(f"Error rendering video: {error}")
                video: Exception = error

            finally:
                os.unlink(temp.name)

            # Return the video to the main thread
            self.render_jobs.task_done()
            self.render_data.set(
                expire=config.expire,
                key=config.hash,
                value=video,
            )

    async def render(self, config: DepthPayload) -> Response:

        # Ensure 'config' is a DepthPayload instance
        if (not isinstance(config, DepthPayload)):
            config = DepthPayload(**config)

        # Metrics and calculate presistent hash
        start: float = time.perf_counter()
        config.hash = hash(config)

        for index in itertools.count(1):

            # Video is already cached or finished
            if (video := self.render_data.get(config.hash)):
                if isinstance(video, Exception):
                    self.render_data.pop(config.hash)
                    return Response(
                        status_code=500,
                        media_type="text/plain",
                        content=str(video),
                    )

                return Response(
                    media_type=f"video/{config.render.format}",
                    content=video,
                    headers=dict(
                        took=f"{time.perf_counter() - start:.2f}",
                        cached=str(index == 1).lower(),
                    ),
                )

            # Queue the job if not already in progress
            elif (config.hash not in self.render_data):
                self.render_data.set(config.hash, None, expire=30)
                self.render_jobs.put(config)

            # Timeout logic to prevent hanging
            elif (start + 30 < time.perf_counter()):
                return Response(
                    status_code=503,
                    media_type="text/plain",
                    content="Request timed out",
                )

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
                ),
                # ffmpeg=BrokenFFmpeg().h264_nvenc(),
                render=RenderConfig(
                    ssaa=1.0,
                    width=1920,
                    fps=60,
                    loop=1,
                    time=5,
                ),
                animation=DepthAnimation(
                    steps=[
                        Actions.Orbital(),
                        Actions.Lens(),
                    ]
                )
            )

            # Debug print the payload
            from rich.pretty import pprint
            pprint("JSON: " + config.json())

            # Actually send the job request
            response = requests.post(
                url=f"{self.url}/render",
                json=config.dict()
            )

            # Save the video to disk
            Path(path := f"/tmp/video-{client}.mp4") \
                .write_bytes(response.content)

            headers = DotMap(response.headers)
            log.success(f"Saved video to {path}, cached: {headers.cached}")

        # Stress test parallel requests
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            for worker in range(jobs):
                pool.submit(request, worker)

# ------------------------------------------------------------------------------------------------ #
