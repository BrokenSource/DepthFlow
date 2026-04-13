import math
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from depthflow.state import DepthState


class _BaseModel(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)


class Target(str, Enum):
    ...

class Sine(_BaseModel):

    cycles: float = 1.0
    """How many cycles to complete in the animation"""

    amplitude: float = 1.0
    """Amplitude of the wave"""

    phase: float = Field(default=0.0, ge=-1.0, le=1.0)
    """Normalized phase shift"""

    def at(self, time: float) -> float:
        angle = math.tau * (self.cycles * time + self.phase)
        return self.amplitude * math.sin(angle)

# ---------------------------------------------------------------------------- #

class Action(BaseModel, ABC):

    @abstractmethod
    def apply(self, state: DepthState, time: float) -> None:
        ...

class Horizontal(Action):
    wave: Sine = Field(default_factory=Sine)

    def apply(self, state: DepthState, time: float) -> None:
        state.offset[0] = self.wave.at(time)

class Vertical(Action):
    wave: Sine = Field(default_factory=Sine)

    def apply(self, state: DepthState, time: float) -> None:
        state.offset[1] = self.wave.at(time)

class Circle(Action):
    """Applies a circular motion to offsets"""
    x: Sine = Field(default_factory=Sine)
    y: Sine = Field(default_factory=Sine)

    def model_post_init(self, context):
        self.y.phase += 0.25

    def apply(self, state: DepthState, time: float) -> None:
        state.offset = (
            self.x.at(time)*0.5,
            self.y.at(time)*0.5,
        )

# ---------------------------------------------------------------------------- #

class DepthAnimation(BaseModel):
    steps: list[Action] = Field(default_factory=list)

    def clear(self) -> None:
        self.steps.clear()

    def apply(self, state: DepthState, time: float) -> None:
        for step in self.steps:
            step.apply(state, time)
