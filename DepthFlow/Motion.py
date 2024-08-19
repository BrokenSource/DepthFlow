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
        help="[bold red](🔴 Common )[/red bold] Reverse the animation")] = \
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

    class Add(Animation):
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

    class Arc(Animation):
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
            t = (tau + self.phase) % (1 / self.cycles)
            return self.amplitude * (1 - 4 * abs((t * self.cycles) - 0.5))

# -------------------------------------------------------------------------------------------------|

Reverse: TypeAlias = Annotated[bool, typer.Option("--reverse", "-r", " /--forward", " /-fw",
    help="[bold green](🟢 Basic  )[/bold green] Play this animation in reverse")]

Smooth: TypeAlias = Annotated[bool, typer.Option("--smooth", "-s", " /--linear", " /-ns",
    help="[bold green](🟢 Basic  )[/bold green] Use the smooth variant of the animation (often a Sine wave)")]

Loop: TypeAlias = Annotated[bool, typer.Option("--loop", "-l", " /--no-loop", " /-nl",
    help="[bold green](🟢 Basic  )[/bold green] Loop the animation indefinitely (often 4x apparent frequency)")]

Static: TypeAlias = Annotated[float, typer.Option("--static", "-S",
    help="[bold green](🟢 Basic  )[/bold green] Depth value of no displacements on camera movements")]

Phase: TypeAlias = Annotated[float, typer.Option("--phase", "-p",
    help="[bold green](🟢 Basic  )[/bold green] Phase shift of the main animation's wave")]

PhaseXYZ: TypeAlias = Annotated[Tuple[float, float, float], typer.Option("--phase", "-p",
    help="[bold green](🟢 Basic  )[/bold green] Phase shift of the horizontal, vertical and depth waves")]

AmplitudeXYZ: TypeAlias = Annotated[Tuple[float, float, float], typer.Option(
    help="[bold green](🟢 Basic  )[/bold green] Amplitude of the horizontal, vertical and depth waves")]

# -------------------------------------------------------------------------------------------------|
# Full presets

class Preset(BaseModel, ABC):
    intensity: Annotated[float, typer.Option("-i", "--intensity",
        help="[bold red](🔴 Common )[/red bold] Intensity of the preset")] = \
        Field(default=1.0)

    reverse: Annotated[bool, typer.Option("-r", "--reverse",
        help="[bold red](🔴 Common )[/red bold] Reverse the animation")] = \
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

    class Vertical(Preset):
        """Add a Vertical motion to the camera [green](See 'vertical --help' for options)[/green]"""
        reverse: Reverse = Field(default=False)
        smooth:  Smooth  = Field(default=True)
        loop:    Loop    = Field(default=True)
        phase:   Phase   = Field(default=0.0)
        static:  Static  = Field(default=0.5)

        def animation(self):
            yield Components.Add(target=Target.Static, value=self.static)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetY,
                amplitude = self.intensity,
                cycles    = (1 if self.loop else 0.25),
                reverse   = self.reverse,
                phase     = self.phase,
            )

    class Horizontal(Preset):
        """Add a Horizontal motion to the camera [green](See 'horizontal --help' for options)[/green]"""
        reverse: Reverse = Field(default=False)
        smooth:  Smooth  = Field(default=True)
        loop:    Loop    = Field(default=True)
        phase:   Phase   = Field(default=0.0)
        static:  Static  = Field(default=0.5)

        def animation(self):
            yield Components.Add(target=Target.Static, value=self.static)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetX,
                amplitude = self.intensity,
                cycles    = (1 if self.loop else 0.25),
                reverse   = self.reverse,
                phase     = self.phase,
            )

    class Circular(Preset):
        """Add a Circular motion to the camera [green](See 'circle --help' for options)[/green]"""
        reverse:   Reverse      = Field(default=False)
        smooth:    Smooth       = Field(default=True)
        phase:     PhaseXYZ     = Field(default=(0.0, 0.0, 0.0))
        amplitude: AmplitudeXYZ = Field(default=(1.0, 1.0, 0.0))

        def animation(self):
            yield (Components.Sine if self.smooth else Components.Triangle)(
                amplitude = (self.intensity*self.amplitude[0]),
                target    = Target.OffsetX,
                phase     = self.phase[0],
                reverse   = self.reverse,
            )
            yield (Components.Sine if self.smooth else Components.Triangle)(
                amplitude = (self.intensity*self.amplitude[1]),
                target    = Target.OffsetY,
                phase     = self.phase[1] + 0.25,
                reverse   = self.reverse,
            )
            yield (Components.Sine if self.smooth else Components.Triangle)(
                amplitude = (self.intensity*self.amplitude[2]*0.2),
                target    = Target.Isometric,
                phase     = self.phase[2],
                reverse   = self.reverse,
            )

    # # Zooms

    class Dolly(Preset):
        """Add a Dolly zoom to the camera [green](See 'dolly --help' for options)[/green]"""
        reverse: Reverse = Field(default=False)
        smooth:  Smooth  = Field(default=True)
        loop:    Loop    = Field(default=True)

        def animation(self):
            yield Components.Add(target=Target.Focus, compute=0.5)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.Isometric,
                reverse   = self.reverse,
                amplitude = self.intensity,
                cycles    = (1 if self.loop else 0.25),
                bias      = 0.5,
            )

    # # Organics

    class Orbital(Preset):
        """Orbit the camera around a fixed point at a certain depth [green](See 'orbital --help' for options)[/green]"""
        depth: Annotated[float, typer.Option("-d", "--depth",
            help="[bold green](🟢 Basic  )[/bold green] Depth value the camera orbits")] = \
            Field(default=0.5)

        def animation(self):
            yield Components.Cosine(
                target    = Target.Isometric,
                amplitude = self.intensity/2,
                bias      = self.intensity/2,
                reverse   = self.reverse,
            )
            yield Components.Sine(
                target    = Target.OffsetX,
                amplitude = self.intensity/2,
                reverse   = self.reverse,
            )
            yield Components.Add(target=Target.Static, compute=self.depth)
            yield Components.Add(target=Target.Focus, compute=self.depth)

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
