from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Generator, Tuple, Type, TypeAlias

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

class Animation(BaseModel, ABC):
    target: Annotated[Target, typer.Option("-t", "--target",
        help="[bold red](🔴 Common )[/red bold] Target animation component to modulate")] = \
        Field(default=Target.Nothing)

    reverse: Annotated[bool, typer.Option("-r", "--reverse",
        help="[yellow](🟡 Advanced)[/yellow] Reverse the animation")] = \
        Field(default=False)

    bias: Annotated[float, typer.Option("-b", "--bias",
        help="[bold red](🔴 Common )[/red bold] Constant offset added to the animation")] = \
        Field(default=0.0)

    def get_time(self, scene: DepthScene) -> Tuple[float, float]:

        # Loop them for realtime window accurate preview
        tau, cycle = (scene.tau % 1, scene.cycle % (2*math.pi))

        # Fixme: Is setting phase and reversing non intuitive?
        if self.reverse:
            cycle = (2*math.pi - cycle)
            tau = (1 - tau)

        return (tau, cycle)

    @abstractmethod
    def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
        pass

    def apply(self, scene: DepthScene) -> float:
        tau, cycle = self.get_time(scene)
        self.set(scene, self.compute(scene, tau, cycle))

    def __call__(self, scene: DepthScene) -> float:
        return self.apply(scene)

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

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.value

    # ----------------------------------------------|
    # Basic functions

    class Linear(Animation):
        """Add a Linear interpolation to some component's animation [green](See 'linear --help' for options)[/green]"""
        start: Annotated[float, typer.Option("--start", "-t0",
            help="[green](🟢 Basic  )[/green] Normalized start time")] = \
            Field(default=0.0, ge=0, le=1)

        end: Annotated[float, typer.Option("--end", "-t1",
            help="[green](🟢 Basic  )[/green] Normalized end time")] = \
            Field(default=1.0, ge=0, le=1)

        low: Annotated[float, typer.Option("--low", "-v0",
            help="[green](🟢 Basic  )[/green] Start value")] = \
            Field(default=0.0)

        hight: Annotated[float, typer.Option("--hight", "-v1",
            help="[green](🟢 Basic  )[/green] End value")] = \
            Field(default=1.0)

        exponent: Annotated[float, typer.Option("-e", "--exponent",
            help="[yellow](🟡 Advanced)[/yellow] Exponent for shaping the interpolation")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            normal = (tau - self.start) / (self.end - self.start)
            shaped = math.pow(max(0, min(1, normal)), self.exponent)
            return self.low + (self.hight - self.low) * shaped

    class Exponential(Animation):
        """Add an Exponential curve to some component's animation [green](See 'exponential --help' for options)[/green]"""
        base: Annotated[float, typer.Option("-b", "--base",
            help="[green](🟢 Basic  )[/green] Base of the exponential function")] = \
            Field(default=2.0)

        scale: Annotated[float, typer.Option("-s", "--scale",
            help="[yellow](🟡 Advanced)[/yellow] Scale factor for the exponent")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return math.pow(self.base, self.scale * tau)

    class Bezier2(Animation):
        """Add a Quadratic Bezier curve to some component's animation [green](See 'bezier2 --help' for options)[/green]"""
        start: Annotated[float, typer.Option("--start", "-a",
            help="[green](🟢 Basic  )[/green] Start value")] = \
            Field(default=0.0)

        middle: Annotated[float, typer.Option("--middle", "-b",
            help="[green](🟢 Basic  )[/green] Middle value")] = \
            Field(default=0.5)

        end: Annotated[float, typer.Option("--end", "-c",
            help="[green](🟢 Basic  )[/green] End value")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return (1 - tau)**2 * self.start + 2 * (1 - tau) * tau * self.middle + tau**2 * self.end

    # ----------------------------------------------|
    # Wave functions

    class _WaveBase(Animation):
        amplitude: Annotated[float, typer.Option("-a", "--amplitude",
            help="[green](🟢 Basic  )[/green] Amplitude of the wave")] = \
            Field(default=1.0)

        cycles: Annotated[float, typer.Option("-c", "--cycles",
            help="[green](🟢 Basic  )[/green] Number of cycles of the wave")] = \
            Field(default=1.0)

        phase: Annotated[float, typer.Option("-p", "--phase",
            help="[yellow](🟡 Advanced)[/yellow] Phase shift of the wave")] = \
            Field(default=0.0)

    class Sine(_WaveBase):
        """Add a Sine wave to some component's animation [green](See 'sine --help' for options)[/green]"""
        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.sin((cycle * self.cycles) + (self.phase * math.tau))

    class Cosine(_WaveBase):
        """Add a Cosine wave to some component's animation [green](See 'cosine --help' for options)[/green]"""
        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.cos((cycle * self.cycles) + (self.phase * math.tau))

    class Triangle(_WaveBase):
        """Add a Triangle wave to some component's animation [green](See 'triangle --help' for options)[/green]"""
        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            t = (tau + 0.25) % (1 / self.cycles)
            return self.amplitude * (1 - 4 * abs((t * self.cycles) - 0.5))

# -------------------------------------------------------------------------------------------------|

Smooth: TypeAlias = Annotated[bool, typer.Option("-s", "--smooth",
    help="[bold green](🟢 Basic  )[/bold green] Use the smooth variant of the animation (often a Sine)")]

Loop: TypeAlias = Annotated[bool, typer.Option("-l", "--loop",
    help="[bold green](🟢 Basic  )[/bold green] Loop the animation indefinitely (4x apparent frequency)")]

Phase: TypeAlias = Annotated[float, typer.Option("-p", "--phase",
    help="[bold green](🟢 Basic  )[/bold green] Phase shift of the animation")]

Reverse: TypeAlias = Annotated[bool, typer.Option("-r", "--reverse",
    help="[bold green](🟢 Basic  )[/bold green] Play this animation in reverse")]

AmplitudeX: TypeAlias = Annotated[float, typer.Option("-ax", "--amplitude-x",
    help="[bold green](🟢 Basic  )[/bold green] Amplitude of the horizontal wave")]

AmplitudeY: TypeAlias = Annotated[float, typer.Option("-ay", "--amplitude-y",
    help="[bold green](🟢 Basic  )[/bold green] Amplitude of the vertical wave")]

AmplitudeZ: TypeAlias = Annotated[float, typer.Option("-az", "--amplitude-z",
    help="[bold green](🟢 Basic  )[/bold green] Amplitude of the depth wave")]

# -------------------------------------------------------------------------------------------------|

class _Reverse(BaseModel):
    reverse: Reverse = Field(default=False)

class _Smooth(BaseModel):
    smooth: Smooth = Field(default=False)

class _Phase(BaseModel):
    phase: Phase = Field(default=0.0)

class _Loop(BaseModel):
    loop: Loop = Field(default=False)

class _AmplitudeXYZ(BaseModel):
    amplitude_x: AmplitudeX = Field(default=1.0)
    amplitude_y: AmplitudeY = Field(default=1.0)
    amplitude_z: AmplitudeZ = Field(default=1.0)

# -------------------------------------------------------------------------------------------------|
# Full presets

class Preset(BaseModel, ABC):
    intensity: Annotated[float, typer.Option("-i", "--intensity",
        help="[green](🟢 Basic  )[/green] Intensity of the preset")] = \
        Field(default=1.0)

    reverse: Annotated[bool, typer.Option("-r", "--reverse",
        help="[yellow](🟡 Advanced)[/yellow] Reverse the animation")] = \
        Field(default=False)

    @abstractmethod
    def animation(self) -> Generator[Animation, None, None]:
        pass

# --------------------------------------------------|

class Presets(GetMembers):
    class Nothing(Preset):
        """Do nothing, bypasses the default injected animation"""
        def animation(self):
            yield lambda scene: None

    # # Offsets

    class Vertical(Preset, _Reverse, _Smooth, _Loop):
        """Add a Vertical motion to the camera [green](See 'vertical --help' for options)[/green]"""
        def animation(self):
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target=Target.OffsetY,
                amplitude=self.intensity,
                cycles=(1 if self.loop else 0.25),
                reverse=self.reverse,
            )

    class Horizontal(Preset, _Reverse, _Smooth, _Loop):
        """Add a Horizontal motion to the camera [green](See 'horizontal --help' for options)[/green]"""
        def animation(self):
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target=Target.OffsetX,
                amplitude=self.intensity,
                cycles=(1 if self.loop else 0.25),
                reverse=self.reverse,
            )

    class Circular(Preset, _Reverse, _Loop, _Phase, _AmplitudeXYZ):
        """Add a Circular motion to the camera [green](See 'circle --help' for options)[/green]"""
        def animation(self):
            yield Components.Cosine(
                amplitude=(self.intensity*self.amplitude_x),
                target=Target.OffsetX,
                phase=self.phase,
                reverse=self.reverse,
            )
            yield Components.Sine(
                amplitude=(self.intensity*self.amplitude_y),
                target=Target.OffsetY,
                phase=self.phase,
                reverse=self.reverse,
            )
            yield Components.Sine(
                amplitude=(self.intensity*self.amplitude_z*0.2),
                target=Target.Isometric,
                phase=self.phase,
                reverse=self.reverse,
            )

    # # Zooms

    class Dolly(Preset, _Reverse, _Smooth, _Loop):
        """Add a Dolly zoom to the camera [green](See 'dolly --help' for options)[/green]"""
        def animation(self):
            yield Components.Set(target=Target.Focus, compute=0.5)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target=Target.Isometric,
                reverse=self.reverse,
                amplitude=self.intensity,
                cycles=(1 if self.loop else 0.25),
                bias=0.5,
            )

    # # Organics

    class Orbital(Preset):
        """Orbit the camera around a fixed point at a certain depth [green](See 'orbital --help' for options)[/green]"""
        depth: Annotated[float, typer.Option("-d", "--depth",
            help="[green](🟢 Basic  )[/green] Depth value the camera orbits")] = \
            Field(default=0.5)

        def animation(self):
            yield Components.Cosine(
                target=Target.Isometric,
                amplitude=self.intensity/2,
                bias=self.intensity/2,
                reverse=self.reverse,
            )
            yield Components.Sine(
                target=Target.OffsetX,
                amplitude=self.intensity/2,
                reverse=self.reverse,
            )
            yield Components.Set(target=Target.Static, compute=self.depth)
            yield Components.Set(target=Target.Focus, compute=self.depth)

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
