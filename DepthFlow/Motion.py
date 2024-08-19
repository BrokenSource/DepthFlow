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

# Todo: Make a Broken class for this
hint: str = "[bold blue](🔵 Option)[/bold blue]"

# -------------------------------------------------------------------------------------------------|

TargetType: TypeAlias = Annotated[Target, typer.Option("--target", "-t",
    help=f"{hint} Target animation state variable to modulate")]

IntensityType: TypeAlias = Annotated[float, typer.Option("--intensity", "-i",
    help=f"{hint} Global intensity of the animation (scales all amplitudes)")]

ReverseType: TypeAlias = Annotated[bool, typer.Option("--reverse", "-r", " /--forward", " /-fw",
    help=f"{hint} Time 'direction' to play the animation, makes the end the start")]

BiasType: TypeAlias = Annotated[float, typer.Option("--bias", "-b",
    help=f"{hint} Constant offset added to the animation component")]

SmoothType: TypeAlias = Annotated[bool, typer.Option("--smooth", "-s", " /--linear", " /-ns",
    help=f"{hint} Use the smooth variant of the animation (often a Sine wave)")]

LoopType: TypeAlias = Annotated[bool, typer.Option("--loop", "-l", " /--no-loop", " /-nl",
    help=f"{hint} Loop the animation indefinitely (often 4x apparent frequency)")]

StaticType: TypeAlias = Annotated[float, typer.Option("--static", "-S",
    help=f"{hint} Depth value of no displacements on camera movements")]

PhaseType: TypeAlias = Annotated[float, typer.Option("--phase", "-p",
    help=f"{hint} Phase shift of the main animation's wave")]

PhaseXYZType: TypeAlias = Annotated[Tuple[float, float, float], typer.Option("--phase", "-p",
    help=f"{hint} Phase shift of the horizontal, vertical and depth waves")]

AmplitudeXYZType: TypeAlias = Annotated[Tuple[float, float, float], typer.Option("--amplitude", "-a",
    help=f"{hint} Amplitude of the horizontal, vertical and depth waves")]

DepthType = Annotated[float, typer.Option("--depth", "-d",
    help=f"{hint} Focal depth of this animation (orbit point, dolly zoom, etc.)")]

# -------------------------------------------------------------------------------------------------|
# Base classes

class Animation(BaseModel, ABC):
    target: TargetType = Field(default=Target.Nothing)
    reverse: ReverseType = Field(default=False)
    bias: BiasType = Field(default=0.0)

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
        if (self.target != Target.Nothing):
            exec(f"scene.state.{self.target.value} += {self.bias} + {value}")

# -------------------------------------------------------------------------------------------------|
# Shaping functions

class Components(GetMembers):

    class Custom(Animation):
        code: Annotated[str, typer.Option("-c", "--code",
            help=f"{hint} Custom code to run for the animation [yellow](be sure to trust it)[/yellow]")] = \
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
            help=f"{hint} Normalized start time")] = \
            Field(default=0.0, ge=0, le=1)

        end: Annotated[float, typer.Option("--end", "-t1",
            help=f"{hint} Normalized end time")] = \
            Field(default=1.0, ge=0, le=1)

        low: Annotated[float, typer.Option("--low", "-v0",
            help=f"{hint} Start value")] = \
            Field(default=0.0)

        hight: Annotated[float, typer.Option("--hight", "-v1",
            help=f"{hint} End value")] = \
            Field(default=1.0)

        exponent: Annotated[float, typer.Option("-e", "--exponent",
            help=f"{hint} Exponent for shaping the interpolation")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            normal = (tau - self.start) / (self.end - self.start)
            shaped = math.pow(max(0, min(1, normal)), self.exponent)
            return self.low + (self.hight - self.low) * shaped

    class Exponential(Animation):
        """Add an Exponential curve to some component's animation [green](See 'exponential --help' for options)[/green]"""
        base: Annotated[float, typer.Option("-b", "--base",
            help=f"{hint} Base of the exponential function")] = \
            Field(default=2.0)

        scale: Annotated[float, typer.Option("-s", "--scale",
            help=f"{hint} Scale factor for the exponent")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return math.pow(self.base, self.scale * tau)

    class Arc(Animation):
        """Add a Quadratic Bezier curve to some component's animation [green](See 'bezier2 --help' for options)[/green]"""
        start: Annotated[float, typer.Option("--start", "-a",
            help=f"{hint} Start value")] = \
            Field(default=0.0)

        middle: Annotated[float, typer.Option("--middle", "-b",
            help=f"{hint} Middle value")] = \
            Field(default=0.5)

        end: Annotated[float, typer.Option("--end", "-c",
            help=f"{hint} End value")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return (1 - tau)**2 * self.start + 2 * (1 - tau) * tau * self.middle + tau**2 * self.end

    # ----------------------------------------------|
    # Wave functions

    class _WaveBase(Animation):
        amplitude: Annotated[float, typer.Option("-a", "--amplitude",
            help=f"{hint} Amplitude of the wave")] = \
            Field(default=1.0)

        cycles: Annotated[float, typer.Option("-c", "--cycles",
            help=f"{hint} Number of cycles of the wave")] = \
            Field(default=1.0)

        phase: Annotated[float, typer.Option("-p", "--phase",
            help=f"{hint} Phase shift of the wave")] = \
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
            tau = (tau * self.cycles + self.phase + 0.25) % 1
            return self.amplitude * (1 - 4 * abs(tau - 0.5))

# -------------------------------------------------------------------------------------------------|
# Full presets

class Preset(BaseModel, ABC):
    intensity: IntensityType = Field(default=1.0)
    reverse: ReverseType = Field(default=False)

    @abstractmethod
    def animation(self) -> Generator[Animation, None, None]:
        pass

# --------------------------------------------------|

class Presets(GetMembers):
    class Nothing(Preset):
        """Do nothing, bypasses the default injected animation"""
        def animation(self):
            yield lambda scene: None

    class Vertical(Preset):
        """Add a Vertical motion to the camera [green](See 'vertical --help' for options)[/green]"""
        reverse: ReverseType = Field(default=False)
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=True)
        phase:   PhaseType   = Field(default=0.0)
        static:  StaticType  = Field(default=0.3)

        def animation(self):
            yield Components.Add(target=Target.Static, value=self.static)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetY,
                reverse   = self.reverse,
                amplitude = self.intensity,
                cycles    = (1 if self.loop else 0.50),
                phase     = self.phase - (0 if self.loop else 0.25),
            )

    class Horizontal(Preset):
        """Add a Horizontal motion to the camera [green](See 'horizontal --help' for options)[/green]"""
        reverse: ReverseType = Field(default=False)
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=True)
        phase:   PhaseType   = Field(default=0.0)
        static:  StaticType  = Field(default=0.3)

        def animation(self):
            yield Components.Add(target=Target.Static, value=self.static)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetX,
                reverse   = self.reverse,
                amplitude = self.intensity,
                cycles    = (1 if self.loop else 0.50),
                phase     = self.phase - (0 if self.loop else 0.25),
            )

    class Circular(Preset):
        """Add a Circular motion to the camera [green](See 'circle --help' for options)[/green]"""
        reverse:   ReverseType      = Field(default=False)
        smooth:    SmoothType       = Field(default=True)
        phase:     PhaseXYZType     = Field(default=(0.0, 0.0, 0.0))
        amplitude: AmplitudeXYZType = Field(default=(1.0, 1.0, 0.0))
        static:    StaticType       = Field(default=0.3)

        def animation(self):
            yield Components.Add(target=Target.Static, value=self.static)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetX,
                reverse   = self.reverse,
                amplitude = (self.intensity*self.amplitude[0]),
                phase     = self.phase[0] + 0.25,
            )
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetY,
                reverse   = self.reverse,
                amplitude = (self.intensity*self.amplitude[1]),
                phase     = self.phase[1],
            )
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.Isometric,
                reverse   = self.reverse,
                amplitude = (self.intensity*self.amplitude[2]*0.2),
                phase     = self.phase[2],
            )

    class Dolly(Preset):
        """Add a Dolly zoom to the camera [green](See 'dolly --help' for options)[/green]"""
        reverse: ReverseType = Field(default=False)
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=True)
        depth:   DepthType   = Field(default=0.5)

        def animation(self):
            yield Components.Add(target=Target.Focus, value=self.depth)
            yield Components.Add(target=Target.Static, value=self.depth)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.Isometric,
                reverse   = self.reverse,
                amplitude = self.intensity,
                phase     = (-0.25 if self.loop else 0),
                cycles    = (1 if self.loop else 0.25),
                bias      = 1,
            )

    class Orbital(Preset):
        """Orbit the camera around a fixed point at a certain depth [green](See 'orbital --help' for options)[/green]"""
        depth: DepthType = Field(default=0.5)

        def animation(self):
            yield Components.Cosine(
                target    = Target.Isometric,
                reverse   = self.reverse,
                amplitude = self.intensity/2,
                bias      = self.intensity/2,
            )
            yield Components.Sine(
                target    = Target.OffsetX,
                reverse   = self.reverse,
                amplitude = self.intensity/2,
            )
            yield Components.Add(target=Target.Static, compute=self.depth)
            yield Components.Add(target=Target.Focus, compute=self.depth)

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
