from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Generator, List, Type

import typer
from pydantic import BaseModel, Field

from Broken import BrokenEnum


class Target(BrokenEnum):
    Nothing            = "nothing"
    Height             = "height"
    Static             = "static"
    Focus              = "focus"
    Zoom               = "zoom"
    Isometric          = "isometric"
    Dolly              = "dolly"
    Invert             = "invert"
    Mirror             = "mirror"
    CenterX            = "center_x"
    CenterY            = "center_y"
    OriginX            = "origin_x"
    OriginY            = "origin_y"
    OffsetX            = "offset_x"
    OffsetY            = "offset_y"
    Dof_Enable         = "dof.enable"
    Dof_Start          = "dof.start"
    Dof_End            = "dof.end"
    Dof_Exponent       = "dof.exponent"
    Dof_Intensity      = "dof.intensity"
    Dof_Quality        = "dof.quality"
    Dof_Directions     = "dof.directions"
    Vignette_Enable    = "vignette.enable"
    Vignette_Intensity = "vignette.intensity"
    Vignette_Decay     = "vignette.decay"

class GetMembers:

    @classmethod
    def members(cls) -> Generator[Type, None, None]:
        for name in dir(cls):
            if name.startswith("_"):
                continue
            if (name == "members"):
                continue
            yield getattr(cls, name)

# -------------------------------------------------------------------------------------------------|
# Base classes

class _Animation(BaseModel, ABC):

    @abstractmethod
    def compute(self, scene: DepthScene) -> None:
        pass

    def update(self, scene: DepthScene) -> None:
        self.set(scene, self.compute(scene))

class Animation(_Animation):
    target: Annotated[Target, typer.Option("-t", "--target",
        help="[bold red](🔴 Common )[/red bold] Target animation component to modulate")] = \
        Field(default=Target.Nothing)

    bias: Annotated[float, typer.Option("-b", "--bias",
        help="[bold red](🔴 Common )[/red bold] Constant offset added to the animation")] = \
        Field(default=0.0)

    def set(self, scene: DepthScene, value: float) -> None:
        exec(f"scene.state.{self.target.value} += {self.bias} + {value}")

# -------------------------------------------------------------------------------------------------|
# Shaping functions

class Components(GetMembers):

    class Custom(Animation):
        code: Annotated[str, typer.Option("-c", "--code",
            help="[bold red](🔴 Common )[/red bold] Custom code to run for the animation [yellow](be sure to trust it)[/yellow]")] = \
            Field(default="")

        def compute(self, scene: DepthScene) -> None:
            exec(self.code)

    # ----------------------------------------------|
    # Constant functions

    class Set(Animation):
        """Add a Constant value to some component's animation [green](See 'constant --help' for options)[/green]"""
        value: Annotated[float, typer.Option("-v", "--value")] = Field(default=0.0)

        def compute(self, scene: DepthScene) -> None:
            return self.value

    # ----------------------------------------------|
    # Basic functions

    class Linear(Animation):
        """Add a Linear interpolation to some component's animation [green](See 'linear --help' for options)[/green]"""
        t0: Annotated[float, typer.Option("-t0",
            help="[green](🟢 Basic  )[/green] Normalized start time")] = \
            Field(default=0.0, ge=0, le=1)

        t1: Annotated[float, typer.Option("-t1",
            help="[green](🟢 Basic  )[/green] Normalized end time")] = \
            Field(default=1.0, ge=0, le=1)

        v0: Annotated[float, typer.Option("-v0",
            help="[green](🟢 Basic  )[/green] Start value")] = \
            Field(default=0.0)

        v1: Annotated[float, typer.Option("-v1",
            help="[green](🟢 Basic  )[/green] End value")] = \
            Field(default=1.0)

        exponent: Annotated[float, typer.Option("-e", "--exponent",
            help="[yellow](🟡 Advanced)[/yellow] Exponent for shaping the interpolation")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene) -> float:
            tau_normal = (scene.tau - self.t0) / (self.t1 - self.t0)
            tau_shaped = math.pow(max(0, min(1, tau_normal)), self.exponent)
            return self.v0 + (self.v1 - self.v0) * tau_shaped

    class Exponential(Animation):
        """Add an Exponential curve to some component's animation [green](See 'exponential --help' for options)[/green]"""
        base: Annotated[float, typer.Option("-b", "--base",
            help="[green](🟢 Basic  )[/green] Base of the exponential function")] = \
            Field(default=2.0)

        scale: Annotated[float, typer.Option("-s", "--scale",
            help="[yellow](🟡 Advanced)[/yellow] Scale factor for the exponent")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene) -> float:
            return math.pow(self.base, self.scale * scene.tau)

    # ----------------------------------------------|
    # Wave functions

    class _WaveBase(Animation):
        amplitude: Annotated[float, typer.Option("-a", "--amplitude",
            help="[green](🟢 Basic  )[/green] Amplitude of the wave")] = \
            Field(default=1.0)

        cycles: Annotated[float, typer.Option("-f", "--frequency",
            help="[green](🟢 Basic  )[/green] Frequency of the wave")] = \
            Field(default=1.0)

        phase: Annotated[float, typer.Option("-p", "--phase",
            help="[yellow](🟡 Advanced)[/yellow] Phase shift of the wave")] = \
            Field(default=0.0)

    class Sine(_WaveBase):
        """Add a Sine wave to some component's animation [green](See 'sine --help' for options)[/green]"""
        def compute(self, scene: DepthScene) -> float:
            return self.amplitude * math.sin(scene.cycle * self.cycles + self.phase)

    class Cosine(_WaveBase):
        """Add a Cosine wave to some component's animation [green](See 'cosine --help' for options)[/green]"""
        def compute(self, scene: DepthScene) -> float:
            return self.amplitude * math.cos(scene.cycle * self.cycles + self.phase)

    class Sawtooth(_WaveBase):
        """Add a Sawtooth wave to some component's animation [green](See 'sawtooth --help' for options)[/green]"""
        def compute(self, scene: DepthScene) -> float:
            t = (scene.tau + 0.25) % (1 / self.cycles)
            return self.amplitude * (2 * (t * self.cycles) - 1)

    class Triangle(_WaveBase):
        """Add a Triangle wave to some component's animation [green](See 'triangle --help' for options)[/green]"""
        def compute(self, scene: DepthScene) -> float:
            t = (scene.tau + 0.25) % (1 / self.cycles)
            return self.amplitude * (1 - 4 * abs((t * self.cycles) - 0.5))

# -------------------------------------------------------------------------------------------------|
# Full presets

class Preset(BaseModel, ABC):
    intensity: Annotated[float, typer.Option("-i", "--intensity",
        help="[green](🟢 Basic  )[/green] Intensity of the preset")] = \
        Field(default=1.0)

    @abstractmethod
    def animation(self) -> Generator[Animation, None, None]:
        pass

class Presets(GetMembers):

    # # Offsets

    class Vertical(Preset):
        """"""
        def animation(self):
            yield Components.Triangle(target=Target.OffsetY, amplitude=self.intensity)

    class Vertical_Smooth(Preset):
        def animation(self):
            yield Components.Sine(target=Target.OffsetY, amplitude=self.intensity)

    class Horizontal(Preset):
        def animation(self):
            yield Components.Triangle(target=Target.OffsetX, amplitude=self.intensity)

    class Horizontal_Smooth(Preset):
        def animation(self):
            yield Components.Sine(target=Target.OffsetX, amplitude=self.intensity)

    # # Zooms

    class Dolly_In(Preset):
        def animation(self):
            yield Components.Linear(target=Target.Dolly, v0=2*self.intensity, v1=0)

    class Dolly_Out(Preset):
        def animation(self):
            yield Components.Linear(target=Target.Dolly, v0=0, v1=2*self.intensity)

    # # Organics

    class Orbital(Preset):
        depth: Annotated[float, typer.Option("-d", "--depth",
            help="[green](🟢 Basic  )[/green] Depth value the camera orbits")] = \
            Field(default=0.5)

        def animation(self):
            yield Components.Cosine(
                target=Target.Isometric,
                amplitude=self.intensity/2,
                bias=self.intensity/2,
            )
            yield Components.Sine(
                target=Target.OffsetX,
                amplitude=self.intensity/2
            )
            yield Components.Set(target=Target.Static, value=self.depth)
            yield Components.Set(target=Target.Focus, value=self.depth)

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
