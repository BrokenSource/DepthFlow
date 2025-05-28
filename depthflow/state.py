from typing import Annotated, Iterable, Tuple

from pydantic import Field
from shaderflow.variable import ShaderVariable, Uniform
from typer import Option

from broken import BrokenModel, BrokenTyper

# ------------------------------------------------------------------------------------------------ #

class VignetteState(BrokenModel):
    enable: Annotated[bool, BrokenTyper.exclude()] = Field(False)
    """Enable this vignette (darken corners) effect"""

    intensity: Annotated[float, Option("--intensity", "-i", min=0, max=1)] = Field(0.2)
    """The intensity of the effect (darken amount on edges)"""

    decay: Annotated[float, Option("--decay", "-d", min=0, max=100)] = Field(20)
    """The shape of the effect (how fast it darkens)"""

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield Uniform("bool",  "iVigEnable",    self.enable)
        yield Uniform("float", "iVigIntensity", self.intensity)
        yield Uniform("float", "iVigDecay",     self.decay)

# ------------------------------------------------------------------------------------------------ #

class LensState(BrokenModel):
    enable: Annotated[bool, BrokenTyper.exclude()] = Field(False)
    """Enable this lens distortion effect"""

    intensity: Annotated[float, Option("--intensity", "-i", min=0, max=1)] = Field(0.1)
    """The intensity of the effect (blur amount on edges)"""

    decay: Annotated[float, Option("--decay", "-d", min=0, max=1)] = Field(0.4)
    """A decay of one starts the effect in the middle of the screen"""

    quality: Annotated[int, Option("--quality", "-q", min=0, max=50)] = Field(30)
    """The quality of the effect (samples per pixel)"""

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield Uniform("bool",  "iLensEnable",    self.enable)
        yield Uniform("float", "iLensIntensity", self.intensity)
        yield Uniform("float", "iLensDecay",     self.decay)
        yield Uniform("int",   "iLensQuality",   self.quality)

# ------------------------------------------------------------------------------------------------ #

class BlurState(BrokenModel):
    enable: Annotated[bool, BrokenTyper.exclude()] = Field(False)
    """Enable this depth of field (blur) effect"""

    intensity: Annotated[float, Option("--intensity", "-i", min=0, max=2)] = Field(1.0)
    """The intensity of the effect (blur radius)"""

    start: Annotated[float, Option("--start", "-a", min=0, max=1)] = Field(0.6)
    """The effect starts at this depth value"""

    end: Annotated[float, Option("--end", "-b", min=0, max=1)] = Field(1.0)
    """The effect ends at this depth value"""

    exponent: Annotated[float, Option("--exponent", "-x", min=0, max=8)] = Field(2.0)
    """Shaping exponent of the start and end interpolation"""

    quality: Annotated[int, Option("--quality", "-q", min=1, max=16)] = Field(4)
    """The quality of the effect (radial sampling steps)"""

    directions: Annotated[int, Option("--directions", "-d", min=1, max=32)] = Field(16)
    """The quality of the effect (radial sampling directions)"""

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield Uniform("bool",  "iBlurEnable",     self.enable)
        yield Uniform("float", "iBlurIntensity",  self.intensity/100)
        yield Uniform("float", "iBlurStart",      self.start)
        yield Uniform("float", "iBlurEnd",        self.end)
        yield Uniform("float", "iBlurExponent",   self.exponent)
        yield Uniform("int",   "iBlurQuality",    self.quality)
        yield Uniform("int",   "iBlurDirections", self.directions)

# ------------------------------------------------------------------------------------------------ #

class InpaintState(BrokenModel):
    enable: Annotated[bool, BrokenTyper.exclude()] = Field(False)
    """Enable the inpainting effect (masks stretchy regions for advanced usage)"""

    black: Annotated[bool, Option("--black", "-b")] = Field(False)
    """Replace non-steep regions with black color instead of the base image"""

    limit: Annotated[float, Option("--limit", "-l", min=0, max=20)] = Field(1.0)
    """The threshold for the steepness of the regions (heuristic)"""

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield Uniform("bool",  "iInpaint",      self.enable)
        yield Uniform("bool",  "iInpaintBlack", self.black)
        yield Uniform("float", "iInpaintLimit", self.limit)

# ------------------------------------------------------------------------------------------------ #

class ColorState(BrokenModel):
    enable: Annotated[bool, BrokenTyper.exclude()] = Field(False)
    """Enable color manipulation effects"""

    saturation: Annotated[float, Option("--saturation", "-s", min=0, max=200)] = Field(100.0)
    """Saturation of the image (0 is grayscale, 100 is original, makes colors more vibrant)"""

    contrast: Annotated[float, Option("--contrast", "-c", min=0, max=200)] = Field(100.0)
    """Contrast of the image (0 is full gray, 100 is original, increases difference between light and dark)"""

    brightness: Annotated[float, Option("--brightness", "-b", min=0, max=200)] = Field(100.0)
    """Brightness of the image (0 is black, 100 is original, increases overall lightness)"""

    gamma: Annotated[float, Option("--gamma", "-g", min=0, max=400)] = Field(100.0)
    """Gamma of the image (0 is black, 100 is original, increases brightness 'shaping' curve)"""

    grayscale: Annotated[float, Option("--grayscale", "-x", min=0, max=100)] = Field(0.0)
    """Grayscale effect of the image (0 is full color, 100 is grayscale)"""

    sepia: Annotated[float, Option("--sepia", "-n", min=0, max=100)] = Field(0.0)
    """Sepia effect of the image (0 is grayscale, 100 is full sepia, a brownish nostalgic tint)"""

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield Uniform("float", "iColorsSaturation", self.saturation/100)
        yield Uniform("float", "iColorsContrast",   self.contrast/100)
        yield Uniform("float", "iColorsBrightness", self.brightness/100)
        yield Uniform("float", "iColorsGamma",      self.gamma/100)
        yield Uniform("float", "iColorsGrayscale",  self.grayscale/100)
        yield Uniform("float", "iColorsSepia",      self.sepia/100)

# ------------------------------------------------------------------------------------------------ #

class DepthState(BrokenModel):
    """Set effect parameters, animations might override them!"""

    height: Annotated[float, Option("--height", "-h", min=0, max=2)] = Field(0.20)
    """Depthmap's peak value, the parallax intensity"""

    steady: Annotated[float, Option("--steady", "-s", min=0, max=1)] = Field(0.0)
    """Focal depth plane of offsets (A value of 0 makes the background stationary; and 1 for the foreground)"""

    focus: Annotated[float, Option("--focus", "-f", min=0, max=1)] = Field(0.0)
    """Focal depth plane of perspective (A value of 0 makes the background stationary; and 1 for the foreground)"""

    zoom: Annotated[float, Option("--zoom", "-z", min=0, max=2)] = Field(1.0)
    """Camera zoom factor (0.5 means a quarter of the image is visible)"""

    isometric: Annotated[float, Option("--isometric", "-i", min=0, max=1)] = Field(0.0)
    """Isometric factor of camera projections (0 is full perspective, 1 is orthographic)"""

    dolly: Annotated[float, Option("--dolly", "-d", min=0, max=20)] = Field(0.0)
    """Natural isometric changes (Moves back ray projections origins by this amount)"""

    invert: Annotated[float, Option("--invert", "-v", min=0, max=1)] = Field(0.0)
    """Interpolate depth values between (0=far, 1=near) and vice-versa, as in mix(height, 1-height, invert)"""

    mirror: Annotated[bool, Option("--mirror", "-m", " /-n")] = Field(True)
    """Apply GL_MIRRORED_REPEAT to the image (The image is mirrored out of bounds on the respective edge)"""

    # # Offset

    offset_x: Annotated[float, Option("--offset-x", "--ofx", min=-4, max=4)] = Field(0.0)
    """Horizontal parallax displacement, change this over time for the 3D effect"""

    offset_y: Annotated[float, Option("--offset-y", "--ofy", min=-1, max=1)] = Field(0.0)
    """Vertical parallax displacement, change this over time for the 3D effect"""

    @property
    def offset(self) -> tuple[float, float]:
        """Parallax displacement vector, change this over time for the 3D effect"""
        return (self.offset_x, self.offset_y)

    @offset.setter
    def offset(self, value: tuple[float, float]):
        self.offset_x, self.offset_y = value

    # # Center

    center_x: Annotated[float, Option("--center-x", "--cex", min=-4, max=4)] = Field(0.0)
    """Horizontal 'true' offset of the camera, the camera *is* above this point"""

    center_y: Annotated[float, Option("--center-y", "--cey", min=-1, max=1)] = Field(0.0)
    """Vertical 'true' offset of the camera, the camera *is* above this point"""

    @property
    def center(self) -> tuple[float, float]:
        """'True' offset vector of the camera, the camera *is* above this point"""
        return (self.center_x, self.center_y)

    @center.setter
    def center(self, value: tuple[float, float]):
        self.center_x, self.center_y = value

    # # Origin

    origin_x: Annotated[float, Option("--origin-x", "--orx", min=-4, max=4)] = Field(0.0)
    """Horizontal focal point of the offsets, *as if* the camera was above this point"""

    origin_y: Annotated[float, Option("--origin-y", "--ory", min=-1, max=1)] = Field(0.0)
    """Vertical focal point of the offsets, *as if* the camera was above this point"""

    @property
    def origin(self) -> tuple[float, float]:
        """Focal point vector of the offsets, *as if* the camera was above this point"""
        return (self.origin_x, self.origin_y)

    @origin.setter
    def origin(self, value: tuple[float, float]):
        self.origin_x, self.origin_y = value

    # ---------------------------------------------------------------------------------------------|

    vignette: Annotated[VignetteState, BrokenTyper.exclude()] = \
        Field(default_factory=VignetteState)

    lens: Annotated[LensState, BrokenTyper.exclude()] = \
        Field(default_factory=LensState)

    inpaint: Annotated[InpaintState, BrokenTyper.exclude()] = \
        Field(default_factory=InpaintState)

    colors: Annotated[ColorState, BrokenTyper.exclude()] = \
        Field(default_factory=ColorState)

    blur: Annotated[BlurState, BrokenTyper.exclude()] = \
        Field(default_factory=BlurState)

    # ---------------------------------------------------------------------------------------------|

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield Uniform("float", "iDepthHeight",    self.height)
        yield Uniform("float", "iDepthSteady",    self.steady)
        yield Uniform("float", "iDepthFocus",     self.focus)
        yield Uniform("float", "iDepthInvert",    self.invert)
        yield Uniform("float", "iDepthZoom",      self.zoom)
        yield Uniform("float", "iDepthIsometric", self.isometric)
        yield Uniform("float", "iDepthDolly",     self.dolly)
        yield Uniform("vec2",  "iDepthOffset",    self.offset)
        yield Uniform("vec2",  "iDepthCenter",    self.center)
        yield Uniform("vec2",  "iDepthOrigin",    self.origin)
        yield Uniform("bool",  "iDepthMirror",    self.mirror)
        yield from self.vignette.pipeline()
        yield from self.lens.pipeline()
        yield from self.inpaint.pipeline()
        yield from self.colors.pipeline()
        yield from self.blur.pipeline()
