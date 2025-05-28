from __future__ import annotations

import copy
import math
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    Optional,
    TypeAlias,
    Union,
)

from pydantic import BaseModel, Field
from typer import Option

from broken import BrokenAttribute, BrokenModel, BrokenTyper, Environment, MultiEnum
from broken.core.extra.loaders import LoadString
from depthflow.state import (
    BlurState,
    ColorState,
    DepthState,
    InpaintState,
    LensState,
    VignetteState,
)

if TYPE_CHECKING:
    from depthflow.scene import DepthScene

# ------------------------------------------------------------------------------------------------ #

class ClassEnum:

    @classmethod
    def members(cls) -> Iterable[type]:
        for name in cls.__dict__:
            if name.startswith("_"):
                continue
            if (name == "members"):
                continue
            yield getattr(cls, name)

# ------------------------------------------------------------------------------------------------ #

class Target(MultiEnum):
    Nothing           = "nothing"
    Height            = "height"
    Steady            = "steady"
    Focus             = "focus"
    Zoom              = "zoom"
    Isometric         = "isometric"
    Dolly             = "dolly"
    Invert            = "invert"
    Mirror            = "mirror"
    CenterX           = "center-x"
    CenterY           = "center-y"
    OriginX           = "origin-x"
    OriginY           = "origin-y"
    OffsetX           = "offset-x"
    OffsetY           = "offset-y"
    VignetteEnable    = "vignette.enable"
    VignetteIntensity = "vignette.intensity"
    VignetteDecay     = "vignette.decay"
    LensEnable        = "lens.enable"
    LensIntensity     = "lens.intensity"
    LensDecay         = "lens.decay"
    LensQuality       = "lens.quality"
    BlurEnable        = "blur.enable"
    BlurStart         = "blur.start"
    BlurEnd           = "blur.end"
    BlurExponent      = "blur.exponent"
    BlurIntensity     = "blur.intensity"
    BlurQuality       = "blur.quality"
    BlurDirections    = "blur.directions"
    InpaintEnable     = "inpaint.enable"
    InpaintBlack      = "inpaint.black"
    InpaintLimit      = "inpaint.limit"
    ColorEnable       = "colors.enable"
    ColorSaturation   = "colors.saturation"
    ColorContrast     = "colors.contrast"
    ColorBrightness   = "colors.brightness"
    ColorGamma        = "colors.gamma"
    ColorGrayscale    = "colors.grayscale"
    ColorSepia        = "colors.sepia"

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

ZoomType: TypeAlias = Annotated[float, Option("--zoom", "-z", min=0, max=2,
    help=f"{hint} Crops parts of the image, 0.5 a quarter is visible, 1 is full frame")]

PhaseType: TypeAlias = Annotated[float, Option("--phase", "-p", min=0, max=1,
    help=f"{hint} Phase shift of the main animation's wave")]

PhaseXYZType: TypeAlias = Annotated[tuple[float, float, float], Option("--phase", "-p", min=0, max=1,
    help=f"{hint} Phase shift of the horizontal, vertical and depth waves")]

AmplitudeXYZType: TypeAlias = Annotated[tuple[float, float, float], Option("--amplitude", "-a", min=-2, max=2,
    help=f"{hint} Amplitude of the horizontal, vertical and depth waves")]

DepthType = Annotated[float, Option("--depth", "-d", min=-1, max=2,
    help=f"{hint} Focal depth of this animation (orbit point, dolly zoom, etc.)")]

CumulativeType = Annotated[bool, Option("--cumulative", "-c", " /--force", " /-f",
    help=f"{hint} Cumulative animation, adds to the previous frame's target value")]

# ------------------------------------------------------------------------------------------------ #

class AnimationBase(BaseModel, ABC):
    """The simplest animation meta-type, applies anything to the scene"""

    def get_time(self, scene: DepthScene) -> tuple[float, float]:
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

    def current(self, scene: DepthScene) -> Optional[Any]:
        return BrokenAttribute.get(
            root=scene.state,
            key=self.target.value
        )

    def apply(self, scene: DepthScene) -> None:
        if (self.target != Target.Nothing):
            BrokenAttribute.set(scene.state, self.target.value, sum((
                (self.compute(scene, *self.get_time(scene))),
                (self.cumulative * (self.current(scene) or 0)),
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

class Animation(ClassEnum):

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

        code: Annotated[str, Option("--code", "-c")] = Field("")
        """Custom code to run for the animation [yellow](be sure to trust it)[/]"""

        def apply(self, scene: DepthScene, tau: float, cycle: float) -> float:
            if Environment.flag("CUSTOM_CODE", 0):
                return exec(LoadString(self.code))
            raise RuntimeError("Custom code execution is disabled")

    class Reset(AnimationBase):
        type: Annotated[Literal["reset"], BrokenTyper.exclude()] = "reset"

        def apply(self, scene: DepthScene) -> None:
            scene.state = DepthState()

    # ----------------------------------------------|
    # Constant components

    class _ConstantBase(ComponentBase):
        value: Annotated[float, Option("--value", "-v")] = Field(0.0)

    class Set(_ConstantBase):
        """Set a constant value to some component's animation"""
        type: Annotated[Literal["set"], BrokenTyper.exclude()] = "set"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            self.cumulative = False
            return self.value

    class Add(_ConstantBase):
        """Add a constant value to some component's animation"""
        type: Annotated[Literal["add"], BrokenTyper.exclude()] = "add"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            self.cumulative = True
            return self.value

    # ----------------------------------------------|
    # Basic components

    class Linear(ReversibleComponentBase):
        """Add a Linear interpolation to some component's animation"""
        type: Annotated[Literal["linear"], BrokenTyper.exclude()] = "linear"

        start: Annotated[float, Option("--start", "-t0")] = Field(0.0)
        """Normalized start time"""

        end: Annotated[float, Option("--end", "-t1")] = Field(1.0)
        """Normalized end time"""

        low: Annotated[float, Option("--low", "-v0")] = Field(0.0)
        """Start value"""

        hight: Annotated[float, Option("--high", "-v1")] = Field(1.0)
        """End value"""

        exponent: Annotated[float, Option("-e", "--exponent")] = Field(1.0)
        """Exponent for shaping the interpolation"""

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            normal = (tau - self.start) / (self.end - self.start)
            shaped = math.pow(max(0, min(1, normal)), self.exponent)
            return self.low + (self.hight - self.low) * shaped

    # ----------------------------------------------|
    # Wave functions

    class _WaveBase(ReversibleComponentBase):
        amplitude: Annotated[float, Option("--amplitude", "-a")] = Field(1.0)
        """Amplitude of the wave"""

        bias: Annotated[float, Option("--bias", "-b")] = Field(0.0)
        """Bias of the wave"""

        cycles: Annotated[float, Option("--cycles", "-c")] = Field(1.0)
        """Number of cycles of the wave"""

        phase: Annotated[float, Option("--phase", "-p")] = Field(0.0)
        """Phase shift of the wave"""

    class Sine(_WaveBase):
        """Add a Sine wave to some component's animation [green](See 'sine --help' for options)[/]"""
        type: Annotated[Literal["sine"], BrokenTyper.exclude()] = "sine"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.sin((cycle * self.cycles) + (self.phase * math.tau)) + self.bias

    class Cosine(_WaveBase):
        """Add a Cosine wave to some component's animation [green](See 'cosine --help' for options)[/]"""
        type: Annotated[Literal["cosine"], BrokenTyper.exclude()] = "cosine"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            return self.amplitude * math.cos((cycle * self.cycles) + (self.phase * math.tau)) + self.bias

    class Triangle(_WaveBase):
        """Add a Triangle wave to some component's animation [green](See 'triangle --help' for options)[/]"""
        type: Annotated[Literal["triangle"], BrokenTyper.exclude()] = "triangle"

        def compute(self, scene: DepthScene, tau: float, cycle: float) -> float:
            tau = (tau * self.cycles + self.phase + 0.25) % 1
            return self.amplitude * (1 - 4 * abs(tau - 0.5)) + self.bias

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
        """Add a Vertical Motion animation preset"""
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
                (Animation.Sine if self.smooth else Animation.Triangle)(
                    target    = Target.OffsetY,
                    amplitude = 0.8*self.intensity,
                    phase     = self.phase,
                    cycles    = 1.00,
                ).apply(scene)
            else:
                (Animation.Sine if self.smooth else Animation.Triangle)(
                    target    = Target.OffsetY,
                    amplitude = self.intensity,
                    phase     = -0.25,
                    cycles    = 0.50,
                ).apply(scene)

    class Horizontal(PresetBase):
        """Add a Horizontal Motion animation preset"""
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
                (Animation.Sine if self.smooth else Animation.Triangle)(
                    target    = Target.OffsetX,
                    amplitude = 0.8*self.intensity,
                    phase     = self.phase,
                    cycles    = 1.00,
                ).apply(scene)
            else:
                (Animation.Sine if self.smooth else Animation.Triangle)(
                    target    = Target.OffsetX,
                    amplitude = self.intensity,
                    phase     = -0.25,
                    cycles    = 0.50,
                ).apply(scene)

    class Zoom(PresetBase):
        """Add a Zoom Motion animation preset"""
        type:      Annotated[Literal["zoom"], BrokenTyper.exclude()] = "zoom"
        smooth:    SmoothType    = Field(True)
        loop:      LoopType      = Field(False)
        phase:     PhaseType     = Field(0.0)
        isometric: IsometricType = Field(0.8)

        def apply(self, scene: DepthScene) -> None:
            scene.state.isometric = self.isometric

            if self.loop:
                (Animation.Sine if self.smooth else Animation.Triangle)(
                    target    = Target.Height,
                    amplitude = (self.intensity/2),
                    bias      = (self.intensity/2),
                    phase     = self.phase,
                    cycles    = 1.00,
                    reverse   = self.reverse,
                ).apply(scene)
            else:
                (Animation.Sine if self.smooth else Animation.Triangle)(
                    target    = Target.Height,
                    amplitude = (2*self.intensity),
                    phase     = 0.00,
                    cycles    = 0.25,
                    reverse   = self.reverse,
                ).apply(scene)

    class Circle(PresetBase):
        """Add a Circular Motion animation preset"""
        type:      Annotated[Literal["circle"], BrokenTyper.exclude()] = "circle"
        phase:     PhaseXYZType     = Field((0.0, 0.0, 0.0))
        amplitude: AmplitudeXYZType = Field((1.0, 1.0, 0.0))
        steady:    SteadyType       = Field(0.3)
        isometric: IsometricType    = Field(0.6)

        def apply(self, scene: DepthScene) -> None:
            scene.state.isometric = self.isometric
            scene.state.steady    = self.steady

            Animation.Sine(
                target    = Target.OffsetX,
                amplitude = (0.5*self.intensity*self.amplitude[0]),
                phase     = self.phase[0] + 0.25,
                reverse   = self.reverse,
            ).apply(scene)

            Animation.Sine(
                target    = Target.OffsetY,
                amplitude = (0.5*self.intensity*self.amplitude[1]),
                phase     = self.phase[1],
                reverse   = self.reverse,
            ).apply(scene)

    class Dolly(PresetBase):
        """Add a Dolly Zoom animation preset"""
        type:   Annotated[Literal["dolly"], BrokenTyper.exclude()] = "dolly"
        smooth: SmoothType  = Field(True)
        loop:   LoopType    = Field(True)
        focus:  DepthType   = Field(0.35)
        phase:  PhaseType   = Field(0.0)

        def apply(self, scene: DepthScene) -> None:
            scene.state.height = self.intensity/3
            scene.state.steady = self.focus
            scene.state.focus  = self.focus

            if self.loop:
                phase, cycles = ( 0.75 if self.reverse else 0.25), 1.0
            else:
                phase, cycles = (-0.75 if self.reverse else 0.25), 0.5

            (Animation.Sine if self.smooth else Animation.Triangle)(
                target    = Target.Isometric,
                amplitude = self.intensity/2,
                bias      = self.intensity/2,
                phase     = self.phase + phase,
                reverse   = (not self.reverse),
                cycles    = cycles,
            ).apply(scene)

    class Orbital(PresetBase):
        """Orbit the camera around a fixed point"""
        type:   Annotated[Literal["orbital"], BrokenTyper.exclude()] = "orbital"
        steady: DepthType = Field(0.3)
        zoom:   ZoomType  = Field(0.98)

        def apply(self, scene: DepthScene) -> None:
            scene.state.steady = self.steady
            scene.state.focus  = self.steady
            scene.state.zoom   = self.zoom

            Animation.Cosine(
                target    = Target.Isometric,
                amplitude = self.intensity/4,
                bias      = self.intensity/2 + 0.5,
                reverse   = self.reverse,
            ).apply(scene)

            Animation.Sine(
                target    = Target.OffsetX,
                amplitude = self.intensity/4,
                reverse   = self.reverse,
            ).apply(scene)

# ------------------------------------------------------------------------------------------------ #

AnimationType: TypeAlias = Union[
    # Special
    DepthState,
    Animation.Nothing,
    Animation.Custom,
    Animation.Reset,
    # Constants
    Animation.Set,
    Animation.Add,
    # Basic
    Animation.Linear,
    Animation.Sine,
    Animation.Cosine,
    Animation.Triangle,
    # Filters
    Animation.Vignette,
    Animation.Lens,
    Animation.Blur,
    Animation.Inpaint,
    Animation.Colors,
    # Presets
    Animation.Vertical,
    Animation.Horizontal,
    Animation.Zoom,
    Animation.Circle,
    Animation.Dolly,
    Animation.Orbital,
]

# ------------------------------------------------------------------------------------------------ #

class DepthAnimation(BrokenModel):
    steps: list[AnimationType] = Field(default_factory=list)

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
