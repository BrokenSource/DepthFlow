from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated

import typer
from pydantic import BaseModel, Field
from typer import Option

from DepthFlow.State import StateTarget

# -------------------------------------------------------------------------------------------------|
# Base classes

class _DepthAnimation(BaseModel, ABC):

    @abstractmethod
    def update(self, scene: DepthScene) -> None:
        pass

    def set(self, scene: DepthScene, value: float) -> None:
        setattr(scene.state, self.target.value, value)

class DepthAnimation(_DepthAnimation):
    target: Annotated[StateTarget, Option("-t", "-T", "--target",
        help="[bold][red](🔴 Basic   )[/red][/bold] Target animation state component")] = None

class DepthPreset(_DepthAnimation):
    ...

# -------------------------------------------------------------------------------------------------|
# Components

class Constant(DepthAnimation):
    value: Annotated[float, typer.Option("-v")] = Field(default=0.0)

    def update(self, scene: DepthScene) -> None:
        ...

class Linear(DepthAnimation):
    t: Annotated[float, typer.Option("-t", min=0, max=1)] = Field(default=0.0)

    def update(self, scene: DepthScene) -> None:
        ...

# -------------------------------------------------------------------------------------------------|
# Full presets

# -------------------------------------------------------------------------------------------------|

if TYPE_CHECKING:
    from DepthFlow.Scene import DepthScene
