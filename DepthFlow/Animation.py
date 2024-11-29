from __future__ import annotations

import copy
import math
import os
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generator,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeAlias,
    Union,
)

from pydantic import BaseModel, Field
from typer import Option

from Broken import BrokenBaseModel, BrokenTyper, MultiEnum
from Broken.Loaders import LoaderString
from DepthFlow.State import (
    BlurState,
    ColorState,
    DepthState,
    InpaintState,
    LensState,
    VignetteState,
)

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene

# ------------------------------------------------------------------------------------------------ #

class ClassEnum:

    @classmethod
    def members(cls) -> Generator[Type, None, None]:
        for name in dir(cls):
            if name.startswith("_"):
                continue
            if (name == "members"):
                continue
            yield getattr(cls, name)

# ------------------------------------------------------------------------------------------------ #

class Target(MultiEnum):
    Nothing           = ("nothing")
    Height            = ("height")
    Steady            = ("steady")
    Focus             = ("focus")
    Zoom              = ("zoom")
    Isometric         = ("isometric")
    Dolly             = ("dolly")
    Invert            = ("invert")
    Mirror            = ("mirror")
    CenterX           = ("center_x",           "center-x")
    CenterY           = ("center_y",           "center-y")
    OriginX           = ("origin_x",           "origin-x")
    OriginY           = ("origin_y",           "origin-y")
    OffsetX           = ("offset_x",           "offset-x")
    OffsetY           = ("offset_y",           "offset-y")
    BlurEnable        = ("blur_enable",        "blur-enable")
    BlurStart         = ("blur_start",         "blur-start")
    BlurEnd           = ("blur_end",           "blur-end")
    BlurExponent      = ("blur_exponent",      "blur-exponent")
    BlurIntensity     = ("blur_intensity",     "blur-intensity")
    BlurQuality       = ("blur_quality",       "blur-quality")
    BlurDirections    = ("blur_directions",    "blur-directions")
    VignetteEnable    = ("vignette_enable",    "vignette-enable")
    VignetteIntensity = ("vignette_intensity", "vignette-intensity")
    VignetteDecay     = ("vignette_decay",     "vignette-decay")

# ------------------------------------------------------------------------------------------------ #

hint: str = "[bold blue](🔵 Option)[/]"

TargetType: TypeAlias = Annotated[Target, Option("--target", "-t",
    help=f"{hint} Target animation state variable to modulate")]

IntensityType: TypeAlias = Annotated[float, Option("--intensity", "-i", min=0, max=4,
    help=f"{hint} Global intensity of the animation (scales all amplitudes)")]

ReverseType: TypeAlias = Annotated[bool, Option("--reverse", "-r", " /--forward", " /-fw",
    help=f"{hint} Time 'direction' to play the animation, makes the end the start")]

SmoothType: TypeAlias = Annotated[bool, Option("--smooth", "-s", " /--linear", " /-ns",
    help=f"{hint} Use the smooth variant of the animation (often a Sine wave)")]

LoopType: TypeAlias = Annotated[bool, Option("--loop", "-l", " /--no-loop", " /-nl",
    help=f"{hint} Loop the animation indefinitely (often 4x apparent frequency)")]

SteadyType: TypeAlias = Annotated[float, Option("--steady", "-S", min=-1, max=2,
    help=f"{hint} Depth value of no displacements on camera movements")]

IsometricType: TypeAlias = Annotated[float, Option("--isometric", "-I", min=0, max=1,
    help=f"{hint} The 'flatness' of the projection, 0 is perspective, 1 is isometric")]

PhaseType: TypeAlias = Annotated[float, Option("--phase", "-p", min=0, max=1,
    help=f"{hint} Phase shift of the main animation's wave")]

PhaseXYZType: TypeAlias = Annotated[Tuple[float, float, float], Option("--phase", "-p", min=0, max=1,
    help=f"{hint} Phase shift of the horizontal, vertical and depth waves")]

AmplitudeXYZType: TypeAlias = Annotated[Tuple[float, float, float], Option("--amplitude", "-a", min=-2, max=2,
    help=f"{hint} Amplitude of the horizontal, vertical and depth waves")]

DepthType = Annotated[float, Option("--depth", "-d", min=-1, max=2,
    help=f"{hint} Focal depth of this animation (orbit point, dolly zoom, etc.)")]

CumulativeType = Annotated[bool, Option("--cumulative", "-c", " /--force", " /-f",
    help=f"{hint} Cumulative animation, adds to the previous frame's target value")]

# ------------------------------------------------------------------------------------------------ #

class AnimationBase(BaseModel, ABC):
    """The simplest animation meta-type, applies anything to the scene"""

    def get_time(self, scene: DepthScene) -> Tuple[float, float]:
        (tau, cycle) = (scene.tau, scene.cycle)

        # Fixme: Is setting phase and reversing non intuitive?
        if getattr(self, "reverse", False):
            cycle = (2*math.pi - cycle)
            tau = (1 - tau)

        return (tau, cycle)

    @abstractmethod
    def apply(self, scene: DepthScene) -> None:
        ...

class ComponentBase(AnimationBase):
    """An animation type that targets a specific state variable"""
    target:     TargetType     = Field(Target.Nothing)
    cumulative: CumulativeType = Field(False)

    @property
    def current(self) -> Optional[Any]:
        return getattr(self, self.target.value, None)

    def apply(self, scene: DepthScene) -> None:
        if (self.target != Target.Nothing):
            setattr(scene.state, self.target.value, sum((
                (self.compute(scene, *self.get_time(scene))),
                (self.cumulative * (self.current or 0)),
            )))

    @abstractmethod
    def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
        ...

class ReversibleComponentBase(ComponentBase):
    reverse: ReverseType = Field(False)

class PresetBase(AnimationBase):
    intensity: IntensityType = Field(1.0)
    reverse:   ReverseType   = Field(False)

class FilterBase(AnimationBase):
    """Meta-class for post processing effects"""
    ...

# ------------------------------------------------------------------------------------------------ #

class Actions(ClassEnum):

    # ----------------------------------------------|
    # Special components

    class State(PresetBase, DepthState):
        def apply(self, scene: DepthScene) -> None:
            scene.state = self

    class Nothing(AnimationBase):
        type: Annotated[Literal["nothing"], BrokenTyper.exclude()] = "nothing"

        def apply(self, scene: DepthScene) -> None:
            pass

    class Custom(AnimationBase):
        type: Annotated[Literal["custom"], BrokenTyper.exclude()] = "custom"

        code: Annotated[str, Option("-c", "--code",
            help=f"{hint} Custom code to run for the animation [yellow](be sure to trust it)[/]")] = \
            Field("")

        def apply(self, scene: DepthScene, tau: float, cycle: float) -> float:
            if (os.getenv("CUSTOM_CODE", "0") == "1"):
                return exec(LoaderString(self.code))
            else:
                raise RuntimeError("Custom code execution is disabled")

    class Reset(AnimationBase):
        type: Annotated[Literal["reset"], BrokenTyper.exclude()] = "reset"

        def apply(self, scene: DepthScene) -> None:
            scene.state = DepthState()

    # ----------------------------------------------|
    # Constant components

    class _ConstantBase(ComponentBase):
        value: Annotated[float, Option("-v", "--value")] = Field(0.0)

    class Set(_ConstantBase):
        type: Annotated[Literal["set"], BrokenTyper.exclude()] = "set"
        cumulative: CumulativeType = Field(False)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.value

    class Add(_ConstantBase):
        type: Annotated[Literal["add"], BrokenTyper.exclude()] = "add"
        cumulative: CumulativeType = Field(True)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.value

    # ----------------------------------------------|
    # Basic components

    class Linear(ReversibleComponentBase):
        """Add a Linear interpolation to some component's animation"""
        type: Annotated[Literal["linear"], BrokenTyper.exclude()] = "linear"

        start: Annotated[float, Option("--start", "-t0",
            help=f"{hint} Normalized start time")] = \
            Field(0.0)

        end: Annotated[float, Option("--end", "-t1",
            help=f"{hint} Normalized end time")] = \
            Field(1.0)

        low: Annotated[float, Option("--low", "-v0",
            help=f"{hint} Start value")] = \
            Field(0.0)

        hight: Annotated[float, Option("--high", "-v1",
            help=f"{hint} End value")] = \
            Field(1.0)

        exponent: Annotated[float, Option("-e", "--exponent",
            help=f"{hint} Exponent for shaping the interpolation")] = \
            Field(1.0)

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            normal = (tau - self.start) / (self.end - self.start)
            shaped = math.pow(max(0, min(1, normal)), self.exponent)
            return self.low + (self.hight - self.low) * shaped

    # ----------------------------------------------|
    # Wave functions

    class _WaveBase(ReversibleComponentBase):
        amplitude: Annotated[float, Option("-a", "--amplitude",
            help=f"{hint} Amplitude of the wave")] = \
            Field(1.0)

        cycles: Annotated[float, Option("-c", "--cycles",
            help=f"{hint} Number of cycles of the wave")] = \
            Field(1.0)

        phase: Annotated[float, Option("-p", "--phase",
            help=f"{hint} Phase shift of the wave")] = \
            Field(0.0)

    class Sine(_WaveBase):
        """Add a Sine wave to some component's animation [green](See 'sine --help' for options)[/]"""
        type: Annotated[Literal["sine"], BrokenTyper.exclude()] = "sine"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.sin((cycle * self.cycles) + (self.phase * math.tau))

    class Cosine(_WaveBase):
        """Add a Cosine wave to some component's animation [green](See 'cosine --help' for options)[/]"""
        type: Annotated[Literal["cosine"], BrokenTyper.exclude()] = "cosine"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.cos((cycle * self.cycles) + (self.phase * math.tau))

    class Triangle(_WaveBase):
        """Add a Triangle wave to some component's animation [green](See 'triangle --help' for options)[/]"""
        type: Annotated[Literal["triangle"], BrokenTyper.exclude()] = "triangle"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            tau = (tau * self.cycles + self.phase + 0.25) % 1
            return self.amplitude * (1 - 4 * abs(tau - 0.5))

    # ----------------------------------------------|
    # Post processing

    class Vignette(FilterBase, VignetteState):
        """Add a Vignette effect to the video"""
        type: Annotated[Literal["vignette"], BrokenTyper.exclude()] = "vignette"

        def apply(self, scene: DepthScene) -> None:
            scene.state.vignette = self.update(enable=True)

    class Lens(FilterBase, LensState):
        """Add a Lens distortion effect to the video"""
        type: Annotated[Literal["lens"], BrokenTyper.exclude()] = "lens"

        def apply(self, scene: DepthScene) -> None:
            scene.state.lens = self.update(enable=True)

    class Blur(FilterBase, BlurState):
        """Add a Blur effect (depth of field) to the video"""
        type: Annotated[Literal["blur"], BrokenTyper.exclude()] = "blur"

        def apply(self, scene: DepthScene) -> None:
            scene.state.blur = self.update(enable=True)

    class Inpaint(FilterBase, InpaintState):
        """Replace steep regions with green color"""
        type: Annotated[Literal["inpaint"], BrokenTyper.exclude()] = "inpaint"

        def apply(self, scene: DepthScene) -> None:
            scene.state.inpaint = self.update(enable=True)

    class Colors(FilterBase, ColorState):
        """Add coloring effects to the video"""
        type: Annotated[Literal["colors"], BrokenTyper.exclude()] = "colors"

        def apply(self, scene: DepthScene) -> None:
            scene.state.colors = self.update(enable=True)

    # ----------------------------------------------|
    # Presets

    class Vertical(PresetBase):
        """Add a Vertical motion to the camera"""
        type:      Annotated[Literal["vertical"], BrokenTyper.exclude()] = "vertical"
        smooth:    SmoothType    = Field(True)
        loop:      LoopType      = Field(True)
        phase:     PhaseType     = Field(0.0)
        steady:    SteadyType    = Field(0.3)
        isometric: IsometricType = Field(0.6)

        def apply(self, scene: DepthScene) -> None:
            scene.state.isometric = self.isometric
            scene.state.steady    = self.steady

            if self.loop:
                (Actions.Sine if self.smooth else Actions.Triangle)(
                    target    = Target.OffsetY,
                    amplitude = 0.5*self.intensity,
                    phase     = self.phase,
                    cycles    = 1.00,
                ).apply(scene)
            else:
                (Actions.Sine if self.smooth else Actions.Triangle)(
                    target    = Target.OffsetY,
                    amplitude = self.intensity,
                    phase     = -0.25,
                    cycles    = 0.50,
                ).apply(scene)

    class Horizontal(PresetBase):
        """Add a Horizontal motion to the camera"""
        type:      Annotated[Literal["horizontal"], BrokenTyper.exclude()] = "horizontal"
        smooth:    SmoothType    = Field(True)
        loop:      LoopType      = Field(True)
        phase:     PhaseType     = Field(0.0)
        steady:    SteadyType    = Field(0.3)
        isometric: IsometricType = Field(0.6)

        def apply(self, scene: DepthScene) -> None:
            scene.state.isometric = self.isometric
            scene.state.steady    = self.steady

            if self.loop:
                (Actions.Sine if self.smooth else Actions.Triangle)(
                    target    = Target.OffsetX,
                    amplitude = 0.5*self.intensity,
                    phase     = self.phase,
                    cycles    = 1.00,
                ).apply(scene)
            else:
                (Actions.Sine if self.smooth else Actions.Triangle)(
                    target    = Target.OffsetX,
                    amplitude = self.intensity,
                    phase     = -0.25,
                    cycles    = 0.50,
                ).apply(scene)

    class Zoom(PresetBase):
        """Add a Zoom motion to the camera"""
        type:    Annotated[Literal["zoom"], BrokenTyper.exclude()] = "zoom"
        smooth:  SmoothType  = Field(True)
        loop:    LoopType    = Field(True)
        phase:   PhaseType   = Field(0.0)

        def apply(self, scene: DepthScene) -> None:
            if self.loop:
                (Actions.Sine if self.smooth else Actions.Triangle)(
                    target    = Target.Height,
                    amplitude = 0.50 * (self.intensity/2),
                    bias      = 0.50 * (self.intensity/2),
                    phase     = self.phase,
                    cycles    = 1.00,
                    reverse   = self.reverse,
                ).apply(scene)
            else:
                (Actions.Sine if self.smooth else Actions.Triangle)(
                    target    = Target.Height,
                    amplitude = 0.75 * self.intensity,
                    phase     = 0.00,
                    cycles    = 0.25,
                    reverse   = self.reverse,
                ).apply(scene)

    class Circle(PresetBase):
        """Add a Circular motion to the camera"""
        type:      Annotated[Literal["circle"], BrokenTyper.exclude()] = "circle"
        smooth:    SmoothType       = Field(True)
        phase:     PhaseXYZType     = Field((0.0, 0.0, 0.0))
        amplitude: AmplitudeXYZType = Field((1.0, 1.0, 0.0))
        steady:    SteadyType       = Field(0.3)
        isometric: IsometricType    = Field(0.6)

        def apply(self, scene: DepthScene) -> None:
            scene.state.isometric = self.isometric
            scene.state.steady    = self.steady

            (Actions.Sine if self.smooth else Actions.Triangle)(
                target    = Target.OffsetX,
                amplitude = (0.5*self.intensity*self.amplitude[0]),
                phase     = self.phase[0] + 0.25,
                reverse   = self.reverse,
            ).apply(scene)

            (Actions.Sine if self.smooth else Actions.Triangle)(
                target    = Target.OffsetY,
                amplitude = (0.5*self.intensity*self.amplitude[1]),
                phase     = self.phase[1],
                reverse   = self.reverse,
            ).apply(scene)

            (Actions.Sine if self.smooth else Actions.Triangle)(
                target    = Target.Isometric,
                amplitude = (self.intensity*self.amplitude[2]*0.2),
                phase     = self.phase[2],
                reverse   = self.reverse,
            ).apply(scene)

    class Dolly(PresetBase):
        """Add a Dolly zoom to the camera"""
        type:    Annotated[Literal["dolly"], BrokenTyper.exclude()] = "dolly"
        smooth:  SmoothType  = Field(True)
        loop:    LoopType    = Field(True)
        depth:   DepthType   = Field(0.5)
        phase:   PhaseType   = Field(0.0)

        def apply(self, scene: DepthScene) -> None:
            scene.state.steady = self.depth
            scene.state.focus  = self.depth

            if self.loop:
                phase, cycles = ( 0.75 if self.reverse else 0.25), 1.0
            else:
                phase, cycles = (-0.75 if self.reverse else 0.25), 0.5

            (Actions.Sine if self.smooth else Actions.Triangle)(
                target    = Target.Isometric,
                amplitude = self.intensity,
                phase     = self.phase + phase,
                cycles    = cycles,
                bias      = 1,
                reverse   = self.reverse,
            ).apply(scene)

    class Orbital(PresetBase):
        """Orbit the camera around a fixed point"""
        type:  Annotated[Literal["orbital"], BrokenTyper.exclude()] = "orbital"
        depth: DepthType = Field(0.5)

        def apply(self, scene: DepthScene) -> None:
            scene.state.steady = self.depth
            scene.state.focus  = self.depth

            Actions.Cosine(
                target    = Target.Isometric,
                amplitude = self.intensity/2,
                bias      = self.intensity/2,
                reverse   = self.reverse,
            ).apply(scene)

            Actions.Sine(
                target    = Target.OffsetX,
                amplitude = self.intensity/2,
                reverse   = self.reverse,
            ).apply(scene)

# ------------------------------------------------------------------------------------------------ #

AnimationType: TypeAlias = Union[
    # Special
    DepthState,
    Actions.Nothing,
    Actions.Custom,
    Actions.Reset,
    # Constants
    Actions.Set,
    Actions.Add,
    # Basic
    Actions.Linear,
    Actions.Sine,
    Actions.Cosine,
    Actions.Triangle,
    # Filters
    Actions.Vignette,
    Actions.Lens,
    Actions.Blur,
    Actions.Inpaint,
    Actions.Colors,
    # Presets
    Actions.Vertical,
    Actions.Horizontal,
    Actions.Zoom,
    Actions.Circle,
    Actions.Dolly,
    Actions.Orbital,
]

# ------------------------------------------------------------------------------------------------ #

class DepthAnimation(BrokenBaseModel):
    steps: List[AnimationType] = Field(default_factory=list)

    def add(self, animation: AnimationBase) -> AnimationBase:
        self.steps.append(animation := copy.deepcopy(animation))
        return animation

    def clear(self) -> None:
        self.steps.clear()

    def apply(self, scene: DepthScene) -> None:
        for animation in self.steps:
            animation.apply(scene)

    def __bool__(self) -> bool:
        return bool(self.steps)
