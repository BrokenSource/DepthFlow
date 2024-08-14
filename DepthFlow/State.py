from typing import Annotated, Iterable, Tuple

from pydantic import BaseModel, Field, PrivateAttr
from ShaderFlow.Variable import ShaderVariable
from typer import Option

from Broken import BrokenTyper


class DepthState(BrokenTyper.BaseModel):
    """Set parallax parameter values on the state [green](See 'config --help' for options)[/green]"""

    height: Annotated[float, Option("--height", "-h", min=0, max=1,
        help="[bold][red](🔴 Basic   )[/red][/bold] Depthmap's peak value, the effect [bold][cyan]intensity[/cyan][/bold] [medium_purple3](The camera is 1 distance away from depth=0 at the z=1 plane)[/medium_purple3]")] = \
        Field(default=0.35)

    static: Annotated[float, Option("--static", "-s", min=0, max=1,
        help="[bold][red](🔴 Basic   )[/red][/bold] Focal depth plane of [bold][cyan]offsets[/cyan][/bold] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[/medium_purple3]")] = \
        Field(default=0.0)

    focus: Annotated[float, Option("--focus", "-f", min=0, max=1,
        help="[bold][red](🔴 Basic   )[/red][/bold] Focal depth plane of [bold][cyan]perspective[/cyan][/bold] [medium_purple3](A value of 0 makes the background stationary; and 1 for the foreground)[/medium_purple3]")] = \
        Field(default=0.0)

    zoom: Annotated[float, Option("--zoom", "-z", min=0,
        help="[bold][red](🔴 Basic   )[/red][/bold] Camera [bold][cyan]zoom factor[/cyan][/bold] [medium_purple3](2 means a quarter of the image is visible)[/medium_purple3]")] = \
        Field(default=1.0)

    isometric: Annotated[float, Option("--isometric", "-iso", min=0, max=1,
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Isometric factor of [bold][cyan]camera projections[/cyan][/bold] [medium_purple3](Zero is fully perspective, 1 is orthographic)[/medium_purple3]")] = \
        Field(default=0.0)

    dolly: Annotated[float, Option("--dolly", "-d", min=0, max=1,
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Same effect as --isometric, dolly zoom [medium_purple3](Move back ray projection origins by this amount)[/medium_purple3]")] = \
        Field(default=0.0)

    invert: Annotated[float, Option("--invert", "-inv", min=0, max=1,
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Interpolate depth values between (0=far, 1=near) and vice-versa, as in [bold][cyan]mix(height, 1-height, invert)[/bold][/cyan]")] = \
        Field(default=0.0)

    mirror: Annotated[bool, Option("--mirror", "-m", " /-n",
        help="[bold][yellow](🟡 Medium  )[/yellow][/bold] Apply [bold][cyan]GL_MIRRORED_REPEAT[/cyan][/bold] to the image [medium_purple3](The image is mirrored out of bounds on the respective edge)[/medium_purple3]")] = \
        Field(default=True)

    # # Center

    center_x: Annotated[float, Option("--center-x", "-cex", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Horizontal 'true' offset of the camera [medium_purple3](The camera *is* above this point)[/medium_purple3]")] = \
        Field(default=0)

    center_y: Annotated[float, Option("--center-y", "-cey", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Vertical   'true' offset of the camera [medium_purple3](The camera *is* above this point)[/medium_purple3]")] = \
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

    origin_x: Annotated[float, Option("--origin-x", "-orx",
        help="[green](🟢 Advanced)[/green] Horizontal focal point of the offsets [medium_purple3](*As if* the camera was above this point)[/medium_purple3]")] = \
        Field(default=0)

    origin_y: Annotated[float, Option("--origin-y", "-ory", min=0, max=1,
        help="[green](🟢 Advanced)[/green] Vertical   focal point of the offsets [medium_purple3](*As if* the camera was above this point)[/medium_purple3]")] = \
        Field(default=0)

    @property
    def origin(self) -> Tuple[float, float]:
        """Focal point of the offsets, *as if* the camera was above this point"""
        return (self.origin_x, self.origin_y)

    @origin.setter
    def origin(self, value: Tuple[float, float]):
        self.origin_x, self.origin_y = value

    # # Parallax

    offset_x: Annotated[float, Option("--offset-x", "-ofx",
        help="[green](🟢 Advanced)[/green] Horizontal parallax displacement [medium_purple3](Change this over time for the 3D effect)[/medium_purple3]")] = \
        Field(default=0)

    offset_y: Annotated[float, Option("--offset-y", "-ofy",
        help="[green](🟢 Advanced)[/green] Vertical   parallax displacement [medium_purple3](Change this over time for the 3D effect)[/medium_purple3]")] = \
        Field(default=0)

    @property
    def offset(self) -> Tuple[float, float]:
        """Parallax displacement, change this over time for the 3D effect"""
        return (self.offset_x, self.offset_y)

    @offset.setter
    def offset(self, value: Tuple[float, float]):
        self.offset_x, self.offset_y = value

    # # Special

    def reset(self) -> None:
        for object in (self, self.vignette, self.dof):
            for name, field in object.model_fields.items():
                setattr(object, name, field.default)

    # ---------------------------------------------------------------------------------------------|

    class Vignette(BaseModel):
        """Set vignette parameters [green](See 'vignette --help' for options)[/green]"""
        enable: Annotated[bool, Option("--enable", "-e",
            help="[bold][blue](🔵 Special )[/blue][/bold] Enable the Vignette effect")] = \
            Field(default=False)

        intensity: Annotated[float, Option("--intensity", "-i", min=0, max=100,
            help="[green](🟢 Advanced)[/green] Intensity of the Vignette effect")] = \
            Field(default=30)

        decay: Annotated[float, Option("--decay", "-d", min=0, max=1,
            help="[green](🟢 Advanced)[/green] Decay of the Vignette effect")] = \
            Field(default=0.1)

        def pipeline(self) -> Iterable[ShaderVariable]:
            yield ShaderVariable("uniform", "bool",  "iVignetteEnable",    self.enable)
            yield ShaderVariable("uniform", "float", "iVignetteIntensity", self.intensity)
            yield ShaderVariable("uniform", "float", "iVignetteDecay",     self.decay)

    _vignette: Vignette = PrivateAttr(default_factory=Vignette)

    @property
    def vignette(self) -> Vignette:
        """Vignette Post-Processing configuration"""
        return self._vignette

    # ---------------------------------------------------------------------------------------------|

    class DOF(BaseModel):
        """Set depth of field parameters [green](See 'dof --help' for options)[/green]"""
        enable: Annotated[bool, Option("--enable", "-e",
            help="[bold][blue](🔵 Special )[/blue][/bold] Enable the Depth of field effect")] = \
            Field(default=False)

        start: Annotated[float, Option("--start", "-a",
            help="[green](🟢 Advanced)[/green] Effect starts at this depth distance")] = \
            Field(default=0.6)

        end: Annotated[float, Option("--end", "-b",
            help="[green](🟢 Advanced)[/green] Effect ends at this depth distance")] = \
            Field(default=1.0)

        exponent: Annotated[float, Option("--exponent", "-t", min=0, max=10,
            help="[green](🟢 Advanced)[/green] Effect depth exponent")] = \
            Field(default=2.0)

        intensity: Annotated[float, Option("--intensity", "-i", min=0, max=2,
            help="[green](🟢 Advanced)[/green] Effect blur intensity")] = \
            Field(default=1.0)

        quality: Annotated[int, Option("--quality", "-q", min=1, max=16,
            help="[green](🟢 Advanced)[/green] Effect blur quality (radial steps)")] = \
            Field(default=4)

        directions: Annotated[int, Option("--directions", "-d",
            help="[green](🟢 Advanced)[/green] Effect blur quality (directions)")] = \
            Field(default=16)

        def pipeline(self) -> Iterable[ShaderVariable]:
            yield ShaderVariable("uniform", "bool",  "iDofEnable",     bool(self.enable))
            yield ShaderVariable("uniform", "float", "iDofStart",      self.start)
            yield ShaderVariable("uniform", "float", "iDofEnd",        self.end)
            yield ShaderVariable("uniform", "float", "iDofExponent",   self.exponent)
            yield ShaderVariable("uniform", "float", "iDofIntensity",  self.intensity/100)
            yield ShaderVariable("uniform", "int",   "iDofQuality",    self.quality)
            yield ShaderVariable("uniform", "int",   "iDofDirections", self.directions)

    _dof: DOF = PrivateAttr(default_factory=DOF)

    @property
    def dof(self) -> DOF:
        """Depth of Field Post-Processing configuration"""
        return self._dof

    # ---------------------------------------------------------------------------------------------|

    def commands(self, typer: BrokenTyper) -> None:
        with typer.panel("✨ Post processing"):
            typer.command(self.vignette, name="vignette")
            typer.command(self.dof, name="dof")

    def pipeline(self) -> Iterable[ShaderVariable]:
        yield ShaderVariable("uniform", "float", "iDepthHeight",    self.height)
        yield ShaderVariable("uniform", "float", "iDepthStatic",    self.static)
        yield ShaderVariable("uniform", "float", "iDepthFocus",     self.focus)
        yield ShaderVariable("uniform", "float", "iDepthInvert",    self.invert)
        yield ShaderVariable("uniform", "float", "iDepthZoom",      self.zoom)
        yield ShaderVariable("uniform", "float", "iDepthIsometric", self.isometric)
        yield ShaderVariable("uniform", "float", "iDepthDolly",     self.dolly)
        yield ShaderVariable("uniform", "vec2",  "iDepthCenter",    self.center)
        yield ShaderVariable("uniform", "vec2",  "iDepthOrigin",    self.origin)
        yield ShaderVariable("uniform", "vec2",  "iDepthOffset",    self.offset)
        yield ShaderVariable("uniform", "bool",  "iDepthMirror",    bool(self.mirror))
        yield from self.vignette.pipeline()
        yield from self.dof.pipeline()
