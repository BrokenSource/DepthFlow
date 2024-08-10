from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Literal

import typer
from pydantic import BaseModel, Field

from Broken import BrokenEnum, clamp
from DepthFlow.State import DepthState


class Target(BrokenEnum):
    Height    = "height"
    Static    = "static"
    Focus     = "focus"
    Zoom      = "zoom"
    Isometric = "isometric"
    Dolly     = "dolly"
    Invert    = "invert"
    Mirror    = "mirror"
    CenterX   = "center_x"
    CenterY   = "center_y"
    OriginX   = "origin_x"
    OriginY   = "origin_y"
    OffsetX   = "offset_x"
    OffsetY   = "offset_y"
    Dof_Enable     = "dof.enable"
    Dof_Start      = "dof.start"
    Dof_End        = "dof.end"
    Dof_Exponent   = "dof.exponent"
    Dof_Intensity  = "dof.intensity"
    Dof_Quality    = "dof.quality"
    Dof_Directions = "dof.directions"
    Vignette_Enable    = "vignette.enable"
    Vignette_Intensity = "vignette.intensity"
    Vignette_Decay     = "vignette.decay"

# -------------------------------------------------------------------------------------------------|
# Base classes

class _DepthAnimation(BaseModel, ABC):

    @abstractmethod
    def update(self, scene: DepthScene) -> None:
        pass

class DepthAnimation(_DepthAnimation):
    target: Annotated[Target, typer.Option("-t", "--target",
        help="[bold][red](🔴 Common )[/red][/bold] Target animation component to modulate")] = None

    def set(self, scene: DepthScene, value: float) -> None:
        exec(f"scene.state.{self.target.value} += {value}")

class DepthPreset(_DepthAnimation):
    ...

# -------------------------------------------------------------------------------------------------|
# Components

class Constant(DepthAnimation):
    """Add a Constant value to some component's animation         [green](See 'constant --help' for options)[/green]"""
    value: Annotated[float, typer.Option("-v", "--value")] = Field(default=0.0)

    def update(self, scene: DepthScene) -> None:
        self.set(scene, self.value)


class Linear(DepthAnimation):
    """Add a Linear interpolation to some component's animation   [green](See 'linear --help' for options)[/green]"""
    t0: Annotated[float, typer.Option("-t0",
        help="[green](🟢 Basic  )[/green] Normalized start time")] = \
        Field(default=0.0, min=0, max=1)
    t1: Annotated[float, typer.Option("-t1",
        help="[green](🟢 Basic  )[/green] Normalized end time")] = \
        Field(default=1.0, min=0, max=1)
    y0: Annotated[float, typer.Option("-y0",
        help="[green](🟢 Basic  )[/green] Value at t=t0")] = \
        Field(default=0.0)
    y1: Annotated[float, typer.Option("-y1",
        help="[green](🟢 Basic  )[/green] Value at t=t1")] = \
        Field(default=1.0)
    clamp: Annotated[bool, typer.Option("-c", "--clamp",
        help="[green](🟢 Basic  )[/green] Clamp parametric value to [0, 1]")] = \
        Field(default=True)
    exponent: Annotated[float, typer.Option("-e", "--exponent",
        help="[bold][blue](🔵 Special)[/blue][/bold] Interpolation exponent")] = \
        Field(default=1.0)

    def update(self, scene: DepthScene) -> None:
        parametric = (scene.tau - self.t0)/(self.t1 - self.t0)
        parametric = (clamp(parametric, 0, 1) if self.clamp else parametric)
        parametric = math.pow(parametric, self.exponent)
        self.set(scene, value=self.y0 + (self.y1 - self.y0)*parametric)


class Sine(DepthAnimation):
    """Add a Sine wave to some component's animation              [green](See 'sine --help' for options)[/green]"""
    amplitude: Annotated[float, typer.Option("-a", "--amplitude",
        help="[green](🟢 Basic  )[/green] Amplitude of the Sine wave")] = \
        Field(default=1.0)

    cycles: Annotated[float, typer.Option("-c", "--cycles",
        help="[green](🟢 Basic  )[/green] Number of cycles until the end of the Scene")] = \
        Field(default=1.0)

    phi: Annotated[float, typer.Option("-p", "--phi", min=-1, max=1,
        help="[green](🟢 Basic  )[/green] Phase offset of the wave (normalized)")] = \
        Field(default=0.0)

    bias: Annotated[float, typer.Option("-b", "--bias",
        help="[bold][blue](🔵 Special)[/blue][/bold] Constant value added to the function")] = \
        Field(default=0.0)

    cosine: Annotated[bool, typer.Option("-C", "--cosine",
        help="[bold][blue](🔵 Special)[/blue][/bold] Use a cosine instead of a sine (Adds PI/2)")] = \
        Field(default=False)

    def update(self, scene: DepthScene) -> None:
        trig = (math.cos if self.cosine else math.sin)
        self.set(scene, value=self.amplitude*trig(scene.cycle + 2*math.pi*self.phi) + self.bias)


# -------------------------------------------------------------------------------------------------|
# Full presets

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
