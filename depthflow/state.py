from typing import Annotated, Iterable

from pydantic import BaseModel, ConfigDict, Field
from shaderflow.variable import Uniform


class _BaseModel(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

# ---------------------------------------------------------------------------- #

class VignetteState(_BaseModel):

    intensity: float = Field(default=0.00, ge=0.0, le=1.0)
    """Darken amount in edges of the image"""

    decay: float = Field(default=20.00, ge=0.0, le=100.0)
    """Shape of the effect, how fast it darkens"""

    def pipeline(self) -> Iterable[Uniform]:
        yield Uniform("float", "iVigIntensity", self.intensity)
        yield Uniform("float", "iVigDecay",     self.decay)

# ---------------------------------------------------------------------------- #

class LensState(_BaseModel):

    intensity: float = Field(default=0.00, ge=0.0, le=2.0)
    """Blur amount on edges"""

    decay: float = Field(default=0.4, ge=0.0, le=1.0)
    """Shape of the effect, 1 starts at the center"""

    quality: int = Field(default=30, ge=0, le=60)
    """Number of samples per pixel"""

    def pipeline(self) -> Iterable[Uniform]:
        yield Uniform("float", "iLensIntensity", self.intensity)
        yield Uniform("float", "iLensDecay",     self.decay)
        yield Uniform("int",   "iLensQuality",   self.quality)

# ---------------------------------------------------------------------------- #

class InpaintState(_BaseModel):

    limit: float = Field(default=0.0, ge=0.0)
    """The threshold for the steepness of the regions (heuristic)"""

    def pipeline(self) -> Iterable[Uniform]:
        yield Uniform("float", "iInpaint", self.limit)

# ---------------------------------------------------------------------------- #

class BlurState(_BaseModel):

    intensity: float = Field(default=0.00, ge=0.0, le=2.0)
    """The intensity of the effect (blur radius)"""

    start: float = Field(default=0.60, ge=0.0, le=1.0)
    """The effect starts at this depth value"""

    end: float = Field(default=1.00, ge=0.0, le=1.0)
    """The effect ends at this depth value"""

    exponent: float = Field(default=2.00, ge=0.0, le=8.0)
    """Shaping exponent of the start and end interpolation"""

    quality: int = Field(default=4, ge=1, le=16)
    """The quality of the effect (radial sampling steps)"""

    directions: int = Field(default=16, ge=1, le=32)
    """The quality of the effect (radial sampling directions)"""

    def pipeline(self) -> Iterable[Uniform]:
        yield Uniform("float", "iBlurIntensity",  self.intensity/100)
        yield Uniform("float", "iBlurStart",      self.start)
        yield Uniform("float", "iBlurEnd",        self.end)
        yield Uniform("float", "iBlurExponent",   self.exponent)
        yield Uniform("int",   "iBlurQuality",    self.quality)
        yield Uniform("int",   "iBlurDirections", self.directions)

# ---------------------------------------------------------------------------- #

class ColorState(_BaseModel):

    saturation: float = Field(default=100.0, ge=0.0, le=200.0)
    """Makes color more vibrant from grayscale to oversaturated"""

    contrast: float= Field(default=100.0, ge=0.0, le=200.0)
    """Increases difference between light and dark"""

    brightness: float = Field(default=100.0, ge=0.0, le=200.0)
    """Increases overall lightness"""

    sepia: float = Field(default=0.0, ge=0.0, le=100.0)
    """Applies a brownish nostalgic tint"""

    def pipeline(self) -> Iterable[Uniform]:
        yield Uniform("float", "iColorsSaturation", self.saturation/100)
        yield Uniform("float", "iColorsContrast",   self.contrast/100)
        yield Uniform("float", "iColorsBrightness", self.brightness/100)
        yield Uniform("float", "iColorsSepia",      self.sepia/100)

# ---------------------------------------------------------------------------- #

class DepthState(_BaseModel):

    height: float = Field(default=0.20, ge=-2.0, le=2.0)
    """Peak surface height, the parallax intensity"""

    steady: float = Field(default=0.15, ge=-2.0, le=2.0)
    """Focal depth for offsets, the pivot point of the effect"""

    focus: float = Field(default=0.00, ge=-2.0, le=1.0)
    """Focal depth where perspective changes makes no effect"""

    zoom: float = Field(default=1.00, ge=0.0, le=2.0)
    """Camera zoom factor, 0.5 makes a quarter image visible"""

    isometric: float = Field(default=0.00, ge=0.0, le=1.0)
    """Isometric factor of projections, how much rays are parallel"""

    dolly: float = Field(default=0.00, ge=0.0, le=100.0)
    """Natural isometric changes, moves ray origins by this amount"""

    offset: tuple[float, float] = Field(default=(0.00, 0.00), ge=(-2.0, -2.0), le=(2.0, 2.0))
    """Camera position displacement that actually makes parallax"""

    center: tuple[float, float] = Field(default=(0.00, 0.00), ge=(-2.0, -2.0), le=(2.0, 2.0))
    """Camera is above this point, shifts the scene around"""

    origin: tuple[float, float] = Field(default=(0.00, 0.00), ge=(-2.0, -2.0), le=(2.0, 2.0))
    """Camera point where rays hits perpendicular to the surface"""

    def pipeline(self) -> Iterable[Uniform]:
        yield Uniform("float", "iDepthHeight",    self.height)
        yield Uniform("float", "iDepthSteady",    self.steady)
        yield Uniform("float", "iDepthFocus",     self.focus)
        yield Uniform("float", "iDepthZoom",      self.zoom)
        yield Uniform("float", "iDepthIsometric", self.isometric)
        yield Uniform("float", "iDepthDolly",     self.dolly)
        yield Uniform("vec2",  "iDepthOffset",    self.offset)
        yield Uniform("vec2",  "iDepthCenter",    self.center)
        yield Uniform("vec2",  "iDepthOrigin",    self.origin)
        yield from self.vignette.pipeline()
        yield from self.lens.pipeline()
        yield from self.inpaint.pipeline()
        yield from self.color.pipeline()
        yield from self.blur.pipeline()

    vignette: VignetteState = Field(default_factory=VignetteState)
    lens:     LensState     = Field(default_factory=LensState)
    inpaint:  InpaintState  = Field(default_factory=InpaintState)
    color:    ColorState    = Field(default_factory=ColorState)
    blur:     BlurState     = Field(default_factory=BlurState)
