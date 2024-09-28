from typing import Annotated, Iterable, Tuple

import typer
from pydantic import BaseModel, Field, PrivateAttr
from ShaderFlow.Variable import ShaderVariable


class DepthState(BaseModel):
    """Set effect parameters, animations might override them!"""

    height: Annotated[float, typer.Option("--height", "-h", min=0,
        help="[bold red](🔴 Basic   )[/red bold] Depthmap's peak value, the effect [bold cyan]intensity[/cyan bold] [medium_purple3](The camera is 1 distance away from depth=0 at the z=1 plane)[/medium_purple3]")] = \
        Field(default=0.25)

    static: Annotated[float, typer.Option("--static", "-s",
        help="[bold red](🔴 Basic   )[/red bold] Focal depth plane of [bold cyan]offsets[/cyan bold] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[/medium_purple3]")] = \
        Field(default=0.0)

    focus: Annotated[float, typer.Option("--focus", "-f",
        help="[bold red](🔴 Basic   )[/red bold] Focal depth plane of [bold cyan]perspective[/cyan bold] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[/medium_purple3]")] = \
        Field(default=0.0)

    zoom: Annotated[float, typer.Option("--zoom", "-z", min=0,
        help="[bold red](🔴 Basic   )[/red bold] Camera [bold cyan]zoom factor[/cyan bold] [medium_purple3](2 means a quarter of the image is visible)[/medium_purple3]")] = \
        Field(default=1.0)

    isometric: Annotated[float, typer.Option("--isometric", "-i",
        help="[bold yellow](🟡 Medium  )[/yellow bold] Isometric factor of [bold cyan]camera projections[/cyan bold] [medium_purple3](0 is full perspective, 1 is orthographic)[/medium_purple3]")] = \
        Field(default=0.0)

    dolly: Annotated[float, typer.Option("--dolly", "-d", min=0,
        help="[bold yellow](🟡 Medium  )[/yellow bold] Same effect as --isometric, dolly zoom [medium_purple3](Move back ray projection origins by this amount)[/medium_purple3]")] = \
        Field(default=0.0)

    invert: Annotated[float, typer.Option("--invert", "-v", min=0, max=1,
        help="[bold yellow](🟡 Medium  )[/yellow bold] Interpolate depth values between (0=far, 1=near) and vice-versa, as in [bold cyan]mix(height, 1-height, invert)[/bold cyan]")] = \
        Field(default=0.0)

    mirror: Annotated[bool, typer.Option("--mirror", "-m", " /-n",
        help="[bold yellow](🟡 Medium  )[/yellow bold] Apply [bold cyan]GL_MIRRORED_REPEAT[/cyan bold] to the image [medium_purple3](The image is mirrored out of bounds on the respective edge)[/medium_purple3]")] = \
        Field(default=True)

    # # Offset

    offset_x: Annotated[float, typer.Option("--offset-x", "--ofx",
        help="[bold green](🟢 Advanced)[/bold green] Horizontal parallax displacement [medium_purple3](Change this over time for the 3D effect)[/medium_purple3]")] = \
        Field(default=0)

    offset_y: Annotated[float, typer.Option("--offset-y", "--ofy",
        help="[bold green](🟢 Advanced)[/bold green] Vertical   parallax displacement [medium_purple3](Change this over time for the 3D effect)[/medium_purple3]")] = \
        Field(default=0)

    @property
    def offset(self) -> Tuple[float, float]:
        """Parallax displacement, change this over time for the 3D effect"""
        return (self.offset_x, self.offset_y)

    @offset.setter
    def offset(self, value: Tuple[float, float]):
        self.offset_x, self.offset_y = value

    # # Center

    center_x: Annotated[float, typer.Option("--center-x", "--cex",
        help="[bold green](🟢 Advanced)[/bold green] Horizontal 'true' offset of the camera [medium_purple3](The camera *is* above this point)[/medium_purple3]")] = \
        Field(default=0)

    center_y: Annotated[float, typer.Option("--center-y", "--cey",
        help="[bold green](🟢 Advanced)[/bold green] Vertical   'true' offset of the camera [medium_purple3](The camera *is* above this point)[/medium_purple3]")] = \
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

    origin_x: Annotated[float, typer.Option("--origin-x", "--orx",
        help="[bold green](🟢 Advanced)[/bold green] Horizontal focal point of the offsets [medium_purple3](*As if* the camera was above this point)[/medium_purple3]")] = \
        Field(default=0)

    origin_y: Annotated[float, typer.Option("--origin-y", "--ory",
        help="[bold green](🟢 Advanced)[/bold green] Vertical   focal point of the offsets [medium_purple3](*As if* the camera was above this point)[/medium_purple3]")] = \
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
        help="[bold blue](🔵 Vignette)[/blue bold] Enable a Vignette effect [green](Darken the corners of the image)[/green]")] = \
        Field(default=False)

    vignette_intensity: Annotated[float, typer.Option("--vig-intensity", "--vi", min=0, max=100,
        help="[bold blue](🔵 Vignette)[/blue bold] • Intensity of the Vignette effect")] = \
        Field(default=30)

    vignette_decay: Annotated[float, typer.Option("--vig-decay", "--vd", min=0, max=1,
        help="[bold blue](🔵 Vignette)[/blue bold] • Decay of the Vignette effect")] = \
        Field(default=0.1)

    # ---------------------------------------------------------------------------------------------|

    dof_enable: Annotated[bool, typer.Option("--dof-enable", "--de",
        help="[bold blue](🔵 DoField )[/blue bold] Enable a Depth of field effect [green](Blur the image based on depth)[/green]")] = \
        Field(default=False)

    dof_start: Annotated[float, typer.Option("--dof-start", "--da",
        help="[bold blue](🔵 DoField )[/blue bold] • Blur starts at this depth value")] = \
        Field(default=0.6)

    dof_end: Annotated[float, typer.Option("--dof-end", "--db",
        help="[bold blue](🔵 DoField )[/blue bold] • Blur ends at this depth value")] = \
        Field(default=1.0)

    dof_exponent: Annotated[float, typer.Option("--dof-exponent", "--dx", min=-10, max=10,
        help="[bold blue](🔵 DoField )[/blue bold] • Shaping exponent")] = \
        Field(default=2.0)

    dof_intensity: Annotated[float, typer.Option("--dof-intensity", "--di", min=0, max=2,
        help="[bold blue](🔵 DoField )[/blue bold] • Blur intensity (radius)")] = \
        Field(default=1.0)

    dof_quality: Annotated[int, typer.Option("--dof-quality", "--dq", min=1, max=16,
        help="[bold blue](🔵 DoField )[/blue bold] • Blur quality (radial steps)")] = \
        Field(default=4)

    dof_directions: Annotated[int, typer.Option("--dof-directions", "--dd", min=1, max=32,
        help="[bold blue](🔵 DoField )[/blue bold] • Blur quality (directions)")] = \
        Field(default=16)

    # ---------------------------------------------------------------------------------------------|

    saturation: Annotated[float, typer.Option("--saturation", "--sat", min=0, max=400,
        help="[bold blue](🔵 Saturate)[/bold blue] Saturation of the image [medium_purple3](0 is grayscale, 100 is full color)[/medium_purple3]")] = \
        Field(default=100)

    # ---------------------------------------------------------------------------------------------|

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield ShaderVariable("uniform", "float", "iDepthHeight",    self.height)
        yield ShaderVariable("uniform", "float", "iDepthStatic",    self.static)
        yield ShaderVariable("uniform", "float", "iDepthFocus",     self.focus)
        yield ShaderVariable("uniform", "float", "iDepthInvert",    self.invert)
        yield ShaderVariable("uniform", "float", "iDepthZoom",      self.zoom)
        yield ShaderVariable("uniform", "float", "iDepthIsometric", self.isometric)
        yield ShaderVariable("uniform", "float", "iDepthDolly",     self.dolly)
        yield ShaderVariable("uniform", "vec2",  "iDepthOffset",    self.offset)
        yield ShaderVariable("uniform", "vec2",  "iDepthCenter",    self.center)
        yield ShaderVariable("uniform", "vec2",  "iDepthOrigin",    self.origin)
        yield ShaderVariable("uniform", "bool",  "iDepthMirror",    self.mirror)
        yield ShaderVariable("uniform", "bool",  "iVigEnable",      self.vignette_enable)
        yield ShaderVariable("uniform", "float", "iVigIntensity",   self.vignette_intensity)
        yield ShaderVariable("uniform", "float", "iVigDecay",       self.vignette_decay)
        yield ShaderVariable("uniform", "bool",  "iDofEnable",      self.dof_enable)
        yield ShaderVariable("uniform", "float", "iDofStart",       self.dof_start)
        yield ShaderVariable("uniform", "float", "iDofEnd",         self.dof_end)
        yield ShaderVariable("uniform", "float", "iDofExponent",    self.dof_exponent)
        yield ShaderVariable("uniform", "float", "iDofIntensity",   self.dof_intensity/100)
        yield ShaderVariable("uniform", "int",   "iDofQuality",     self.dof_quality)
        yield ShaderVariable("uniform", "int",   "iDofDirections",  self.dof_directions)
        yield ShaderVariable("uniform", "float", "iSaturation",     self.saturation/100)
