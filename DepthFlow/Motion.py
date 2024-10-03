from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Dict, Generator, Tuple, Type, TypeAlias

import typer
from pydantic import BaseModel, Field

from Broken import BrokenEnum
from DepthFlow.State import DepthState


class Target(BrokenEnum):
    Nothing            = "nothing"
    Height             = "height"
    Steady             = "steady"
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
    Dof_Enable         = "dof-enable"
    Dof_Start          = "dof-start"
    Dof_End            = "dof-end"
    Dof_Exponent       = "dof-exponent"
    Dof_Intensity      = "dof-intensity"
    Dof_Quality        = "dof-quality"
    Dof_Directions     = "dof-directions"
    Vignette_Enable    = "vignette-enable"
    Vignette_Intensity = "vignette-intensity"
    Vignette_Decay     = "vignette-decay"

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
hint: str = "[bold blue](🔵 Option)[reset]"

# -------------------------------------------------------------------------------------------------|

TargetType: TypeAlias = Annotated[Target, typer.Option("--target", "-t",
    help=f"{hint} Target animation state variable to modulate")]

IntensityType: TypeAlias = Annotated[float, typer.Option("--intensity", "-i", min=0, max=4,
    help=f"{hint} Global intensity of the animation (scales all amplitudes)")]

ReverseType: TypeAlias = Annotated[bool, typer.Option("--reverse", "-r", " /--forward", " /-fw",
    help=f"{hint} Time 'direction' to play the animation, makes the end the start")]

BiasType: TypeAlias = Annotated[float, typer.Option("--bias", "-b", min=-4, max=4,
    help=f"{hint} Constant offset added to the animation component")]

SmoothType: TypeAlias = Annotated[bool, typer.Option("--smooth", "-s", " /--linear", " /-ns",
    help=f"{hint} Use the smooth variant of the animation (often a Sine wave)")]

LoopType: TypeAlias = Annotated[bool, typer.Option("--loop", "-l", " /--no-loop", " /-nl",
    help=f"{hint} Loop the animation indefinitely (often 4x apparent frequency)")]

SteadyType: TypeAlias = Annotated[float, typer.Option("--steady", "-S", min=0, max=1,
    help=f"{hint} Depth value of no displacements on camera movements")]

IsometricType: TypeAlias = Annotated[float, typer.Option("--isometric", "-I", min=0, max=1,
    help=f"{hint} The 'flatness' of the projection, 0 is perspective, 1 is isometric")]

PhaseType: TypeAlias = Annotated[float, typer.Option("--phase", "-p", min=0, max=1,
    help=f"{hint} Phase shift of the main animation's wave")]

PhaseXYZType: TypeAlias = Annotated[Tuple[float, float, float], typer.Option("--phase", "-p", min=0, max=1,
    help=f"{hint} Phase shift of the horizontal, vertical and depth waves")]

AmplitudeXYZType: TypeAlias = Annotated[Tuple[float, float, float], typer.Option("--amplitude", "-a", min=0, max=2,
    help=f"{hint} Amplitude of the horizontal, vertical and depth waves")]

DepthType = Annotated[float, typer.Option("--depth", "-d", min=0, max=1,
    help=f"{hint} Focal depth of this animation (orbit point, dolly zoom, etc.)")]

CumulativeType = Annotated[bool, typer.Option("--cumulative", "-c", " /--force", " /-f",
    help=f"{hint} Cumulative animation, adds to the previous frame's target value")]

# -------------------------------------------------------------------------------------------------|
# Base classes

class Animation(BaseModel, ABC):
    target:     TargetType     = Field(default=Target.Nothing)
    reverse:    ReverseType    = Field(default=False)
    bias:       BiasType       = Field(default=0.0)
    cumulative: CumulativeType = Field(default=False)

    def get_time(self, scene: DepthScene) -> Tuple[float, float]:

        # Loop them for realtime window accurate preview
        tau, cycle = (scene.tau % 1), (scene.cycle % (math.tau))

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
            operator = ("+=" if self.cumulative else "=")
            modulate = self.target.value.replace("-", "_")
            exec(f"scene.state.{modulate} {operator} {value} + {self.bias}")

# -------------------------------------------------------------------------------------------------|
# Shaping functions

class Components(GetMembers):

    class Custom(Animation):
        code: Annotated[str, typer.Option("-c", "--code",
            help=f"{hint} Custom code to run for the animation [yellow](be sure to trust it)[reset]")] = \
            Field(default="")

        def compute(self, scene: DepthScene) -> None:
            exec(self.code)

    # ----------------------------------------------|
    # Constant functions

    class Set(Animation):
        """Add a Constant value to some component's animation"""
        value: Annotated[float, typer.Option("-v", "--value")] = Field(default=0.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.value

    # ----------------------------------------------|
    # Basic functions

    class Linear(Animation):
        """Add a Linear interpolation to some component's animation"""
        start: Annotated[float, typer.Option("--start", "-t0",
            help=f"{hint} Normalized start time")] = \
            Field(default=0.0)

        end: Annotated[float, typer.Option("--end", "-t1",
            help=f"{hint} Normalized end time")] = \
            Field(default=1.0)

        low: Annotated[float, typer.Option("--low", "-v0",
            help=f"{hint} Start value")] = \
            Field(default=0.0)

        hight: Annotated[float, typer.Option("--high", "-v1",
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
        """Add an Exponential curve to some component's animation"""
        base: Annotated[float, typer.Option("-b", "--base",
            help=f"{hint} Base of the exponential function")] = \
            Field(default=2.0)

        scale: Annotated[float, typer.Option("-s", "--scale",
            help=f"{hint} Scale factor for the exponent")] = \
            Field(default=1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return math.pow(self.base, self.scale * tau)

    class Arc(Animation):
        """Add a Quadratic Bezier curve to some component's animation"""
        points: Annotated[Tuple[float, float, float], typer.Option("--points", "-p",
            help=f"{hint} Control points of the quadratic Bezier curve")] = \
            Field(default=(0.0, 0.0, 0.0))

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            start, middle, end = self.points
            return (1 - tau)**2 * start + 2 * (1 - tau) * tau * middle + tau**2 * end

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
        """Add a Sine wave to some component's animation [green](See 'sine --help' for options)[reset]"""
        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.sin((cycle * self.cycles) + (self.phase * math.tau))

    class Cosine(_WaveBase):
        """Add a Cosine wave to some component's animation [green](See 'cosine --help' for options)[reset]"""
        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.cos((cycle * self.cycles) + (self.phase * math.tau))

    class Triangle(_WaveBase):
        """Add a Triangle wave to some component's animation [green](See 'triangle --help' for options)[reset]"""
        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            tau = (tau * self.cycles + self.phase + 0.25) % 1
            return self.amplitude * (1 - 4 * abs(tau - 0.5))

# -------------------------------------------------------------------------------------------------|
# Full presets

class Preset(BaseModel, ABC):
    intensity:  IntensityType  = Field(default=1.0)
    reverse:    ReverseType    = Field(default=False)
    cumulative: CumulativeType = Field(default=False)

    def common(self) -> Dict[str, float]:
        """Common passthrough options to the Animations"""
        return dict(
            reverse    = self.reverse,
            cumulative = self.cumulative,
        )

    @abstractmethod
    def animation(self) -> Generator[Animation, None, None]:
        pass

# --------------------------------------------------|

class Presets(GetMembers):
    Config: DepthState = DepthState

    class Vertical(Preset):
        """Add a Vertical motion to the camera"""
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=True)
        phase:   PhaseType   = Field(default=0.0)
        steady:  SteadyType  = Field(default=0.3)
        isometric: IsometricType = Field(default=0.6)

        def animation(self):
            yield Components.Set(target=Target.Isometric, value=self.isometric)
            yield Components.Set(target=Target.Steady, value=self.steady)
            if self.loop:
                yield (Components.Sine if self.smooth else Components.Triangle)(
                    target    = Target.OffsetY,
                    amplitude = 0.5*self.intensity,
                    phase     = self.phase,
                    cycles    = 1.00,
                    **self.common()
                )
            else:
                yield (Components.Sine if self.smooth else Components.Triangle)(
                    target    = Target.OffsetY,
                    amplitude = self.intensity,
                    phase     = -0.25,
                    cycles    = 0.50,
                    **self.common()
                )

    class Horizontal(Preset):
        """Add a Horizontal motion to the camera"""
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=True)
        phase:   PhaseType   = Field(default=0.0)
        steady:  SteadyType  = Field(default=0.3)
        isometric: IsometricType = Field(default=0.6)

        def animation(self):
            yield Components.Set(target=Target.Isometric, value=self.isometric)
            yield Components.Set(target=Target.Steady, value=self.steady)
            if self.loop:
                yield (Components.Sine if self.smooth else Components.Triangle)(
                    target    = Target.OffsetX,
                    amplitude = 0.5*self.intensity,
                    phase     = self.phase,
                    cycles    = 1.00,
                    **self.common()
                )
            else:
                yield (Components.Sine if self.smooth else Components.Triangle)(
                    target    = Target.OffsetX,
                    amplitude = self.intensity,
                    phase     = -0.25,
                    cycles    = 0.50,
                    **self.common()
                )

    class Zoom(Preset):
        """Add a Zoom motion to the camera"""
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=False)
        phase:   PhaseType   = Field(default=0.0)

        def animation(self):
            if self.loop:
                yield (Components.Sine if self.smooth else Components.Triangle)(
                    target    = Target.Height,
                    amplitude = 0.50 * (self.intensity/2),
                    bias      = 0.50 * (self.intensity/2),
                    phase     = self.phase,
                    cycles    = 1.00,
                    **self.common()
                )
            else:
                yield (Components.Sine if self.smooth else Components.Triangle)(
                    target    = Target.Height,
                    amplitude = 0.75 * self.intensity,
                    phase     = 0.00,
                    cycles    = 0.25,
                    **self.common()
                )

    class Circle(Preset):
        """Add a Circular motion to the camera"""
        smooth:    SmoothType       = Field(default=True)
        phase:     PhaseXYZType     = Field(default=(0.0, 0.0, 0.0))
        amplitude: AmplitudeXYZType = Field(default=(1.0, 1.0, 0.0))
        steady:    SteadyType       = Field(default=0.3)
        isometric: IsometricType    = Field(default=0.6)

        def animation(self):
            yield Components.Set(target=Target.Isometric, value=self.isometric)
            yield Components.Set(target=Target.Steady, value=self.steady)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetX,
                amplitude = (0.2*self.intensity*self.amplitude[0]),
                phase     = self.phase[0] + 0.25,
                **self.common()
            )
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.OffsetY,
                amplitude = (0.2*self.intensity*self.amplitude[1]),
                phase     = self.phase[1],
                **self.common()
            )
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.Isometric,
                amplitude = (self.intensity*self.amplitude[2]*0.2),
                phase     = self.phase[2],
                **self.common()
            )

    class Dolly(Preset):
        """Add a Dolly zoom to the camera"""
        smooth:  SmoothType  = Field(default=True)
        loop:    LoopType    = Field(default=True)
        depth:   DepthType   = Field(default=0.5)

        def animation(self):
            yield Components.Set(target=Target.Focus, value=self.depth)
            yield Components.Set(target=Target.Steady, value=self.depth)
            yield (Components.Sine if self.smooth else Components.Triangle)(
                target    = Target.Isometric,
                amplitude = self.intensity,
                phase     = 0.5,
                cycles    = (1 if self.loop else 0.25),
                bias      = 1,
                **self.common()
            )

    class Orbital(Preset):
        """Orbit the camera around a fixed point"""
        depth: DepthType = Field(default=0.5)

        def animation(self):
            yield Components.Set(target=Target.Steady, value=self.depth)
            yield Components.Set(target=Target.Focus, value=self.depth)
            yield Components.Cosine(
                target    = Target.Isometric,
                amplitude = self.intensity/2,
                bias      = self.intensity/2,
                **self.common()
            )
            yield Components.Sine(
                target    = Target.OffsetX,
                amplitude = self.intensity/2,
                **self.common()
            )

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
