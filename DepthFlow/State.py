from typing import Annotated, Iterable, Tuple

import typer
from pydantic import BaseModel, Field, PrivateAttr
from ShaderFlow.Variable import ShaderVariable, Uniform


class DepthState(BaseModel):
    """Set effect parameters, animations might override them!"""

    height: Annotated[float, typer.Option("--height", "-h", min=0, max=2,
        help="[bold red](🔴 Basic   )[reset] Depthmap's peak value, the effect [bold cyan]intensity[reset] [medium_purple3](The camera is 1 distance away from depth=0 at the z=1 plane)[reset]")] = \
        Field(default=0.25)

    steady: Annotated[float, typer.Option("--steady", "-s", min=0, max=1,
        help="[bold red](🔴 Basic   )[reset] Focal depth plane of [bold cyan]offsets[reset] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[reset]")] = \
        Field(default=0.0)

    focus: Annotated[float, typer.Option("--focus", "-f", min=0, max=1,
        help="[bold red](🔴 Basic   )[reset] Focal depth plane of [bold cyan]perspective[reset] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[reset]")] = \
        Field(default=0.0)

    zoom: Annotated[float, typer.Option("--zoom", "-z", min=0, max=2,
        help="[bold red](🔴 Basic   )[reset] Camera [bold cyan]zoom factor[reset] [medium_purple3](2 means a quarter of the image is visible)[reset]")] = \
        Field(default=1.0)

    isometric: Annotated[float, typer.Option("--isometric", "-i", min=0, max=1,
        help="[bold yellow](🟡 Medium  )[reset] Isometric factor of [bold cyan]camera projections[reset] [medium_purple3](0 is full perspective, 1 is orthographic)[reset]")] = \
        Field(default=0.0)

    dolly: Annotated[float, typer.Option("--dolly", "-d", min=0, max=20,
        help="[bold yellow](🟡 Medium  )[reset] Same effect as --isometric, dolly zoom [medium_purple3](Move back ray projection origins by this amount)[reset]")] = \
        Field(default=0.0)

    invert: Annotated[float, typer.Option("--invert", "-v", min=0, max=1,
        help="[bold yellow](🟡 Medium  )[reset] Interpolate depth values between (0=far, 1=near) and vice-versa, as in [bold cyan]mix(height, 1-height, invert)[reset]")] = \
        Field(default=0.0)

    mirror: Annotated[bool, typer.Option("--mirror", "-m", " /-n",
        help="[bold yellow](🟡 Medium  )[reset] Apply [bold cyan]GL_MIRRORED_REPEAT[reset] to the image [medium_purple3](The image is mirrored out of bounds on the respective edge)[reset]")] = \
        Field(default=True)

    # # Offset

    offset_x: Annotated[float, typer.Option("--offset-x", "--ofx", min=-4, max=4,
        help="[bold green](🟢 Advanced)[reset] Horizontal parallax displacement [medium_purple3](Change this over time for the 3D effect)[reset]")] = \
        Field(default=0)

    offset_y: Annotated[float, typer.Option("--offset-y", "--ofy", min=-1, max=1,
        help="[bold green](🟢 Advanced)[reset] Vertical   parallax displacement [medium_purple3](Change this over time for the 3D effect)[reset]")] = \
        Field(default=0)

    @property
    def offset(self) -> Tuple[float, float]:
        """Parallax displacement, change this over time for the 3D effect"""
        return (self.offset_x, self.offset_y)

    @offset.setter
    def offset(self, value: Tuple[float, float]):
        self.offset_x, self.offset_y = value

    # # Center

    center_x: Annotated[float, typer.Option("--center-x", "--cex", min=-4, max=4,
        help="[bold green](🟢 Advanced)[reset] Horizontal 'true' offset of the camera [medium_purple3](The camera *is* above this point)[reset]")] = \
        Field(default=0)

    center_y: Annotated[float, typer.Option("--center-y", "--cey", min=-1, max=1,
        help="[bold green](🟢 Advanced)[reset] Vertical   'true' offset of the camera [medium_purple3](The camera *is* above this point)[reset]")] = \
        Field(default=0)

    @property
    def center(self) -> Tuple[float, float]:
        """'True' offset of the camera, the camera *is* above this point"""
        return (self.center_x, self.center_y)

    @center.setter
    def center(self, value: Tuple[float, float]):
        self.center_x, self.center_y = value

    # # Origin

    origin_x: float = Field(default=0)
    """Hozirontal focal point of the offsets, *as if* the camera was above this point"""

    origin_x: Annotated[float, typer.Option("--origin-x", "--orx", min=-4, max=4,
        help="[bold green](🟢 Advanced)[reset] Horizontal focal point of the offsets [medium_purple3](*As if* the camera was above this point)[reset]")] = \
        Field(default=0)

    origin_y: Annotated[float, typer.Option("--origin-y", "--ory", min=-1, max=1,
        help="[bold green](🟢 Advanced)[reset] Vertical   focal point of the offsets [medium_purple3](*As if* the camera was above this point)[reset]")] = \
        Field(default=0)

    @property
    def origin(self) -> Tuple[float, float]:
        """Focal point of the offsets, *as if* the camera was above this point"""
        return (self.origin_x, self.origin_y)

    @origin.setter
    def origin(self, value: Tuple[float, float]):
        self.origin_x, self.origin_y = value

    # # Special

    def reset(self) -> None:
        for name, field in self.model_fields.items():
            setattr(self, name, field.default)

    # ---------------------------------------------------------------------------------------------|

    vignette_enable: Annotated[bool, typer.Option("--vig-enable", "--ve",
        help="[bold blue](🔵 Vignette)[reset] Enable a Vignette effect [green](Darken the corners of the image)[reset]")] = \
        Field(default=False)

    vignette_intensity: Annotated[float, typer.Option("--vig-intensity", "--vi", min=0, max=100,
        help="[bold blue](🔵 Vignette)[reset] • Intensity of the Vignette effect")] = \
        Field(default=30)

    vignette_decay: Annotated[float, typer.Option("--vig-decay", "--vd", min=0, max=1,
        help="[bold blue](🔵 Vignette)[reset] • Decay of the Vignette effect")] = \
        Field(default=0.1)

    # ---------------------------------------------------------------------------------------------|

    dof_enable: Annotated[bool, typer.Option("--dof-enable", "--de",
        help="[bold blue](🔵 DoField )[reset] Enable a Depth of field effect [green](Blur the image based on depth)[reset]")] = \
        Field(default=False)

    dof_start: Annotated[float, typer.Option("--dof-start", "--da",
        help="[bold blue](🔵 DoField )[reset] • Blur starts at this depth value")] = \
        Field(default=0.6)

    dof_end: Annotated[float, typer.Option("--dof-end", "--db",
        help="[bold blue](🔵 DoField )[reset] • Blur ends at this depth value")] = \
        Field(default=1.0)

    dof_exponent: Annotated[float, typer.Option("--dof-exponent", "--dx", min=-10, max=10,
        help="[bold blue](🔵 DoField )[reset] • Shaping exponent")] = \
        Field(default=2.0)

    dof_intensity: Annotated[float, typer.Option("--dof-intensity", "--di", min=0, max=2,
        help="[bold blue](🔵 DoField )[reset] • Blur intensity (radius)")] = \
        Field(default=1.0)

    dof_quality: Annotated[int, typer.Option("--dof-quality", "--dq", min=1, max=16,
        help="[bold blue](🔵 DoField )[reset] • Blur quality (radial steps)")] = \
        Field(default=4)

    dof_directions: Annotated[int, typer.Option("--dof-directions", "--dd", min=1, max=32,
        help="[bold blue](🔵 DoField )[reset] • Blur quality (directions)")] = \
        Field(default=16)

    # ---------------------------------------------------------------------------------------------|

    saturation: Annotated[float, typer.Option("--saturation", "--sat", min=0, max=400,
        help="[bold blue](🔵 Saturate)[reset] Saturation of the image [medium_purple3](0 is grayscale, 100 is full color)[reset]")] = \
        Field(default=100)

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
        yield Uniform("bool",  "iVigEnable",      self.vignette_enable)
        yield Uniform("float", "iVigIntensity",   self.vignette_intensity)
        yield Uniform("float", "iVigDecay",       self.vignette_decay)
        yield Uniform("bool",  "iDofEnable",      self.dof_enable)
        yield Uniform("float", "iDofStart",       self.dof_start)
        yield Uniform("float", "iDofEnd",         self.dof_end)
        yield Uniform("float", "iDofExponent",    self.dof_exponent)
        yield Uniform("float", "iDofIntensity",   self.dof_intensity/100)
        yield Uniform("int",   "iDofQuality",     self.dof_quality)
        yield Uniform("int",   "iDofDirections",  self.dof_directions)
        yield Uniform("float", "iSaturation",     self.saturation/100)
