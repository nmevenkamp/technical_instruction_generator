import math

import drawsvg as draw
from drawsvg import Drawing

from .base import Step
from ..utils import combined_size


class Face:
    def __init__(self, identifier: str, width: float, height: float) -> None:
        self.identifier = identifier
        self.width = width
        self.height = height

    def __str__(self) -> str:
        return f"Fläche {self.identifier}"

    @property
    def size(self) -> tuple[int, int]:
        return math.ceil(self.width), math.ceil(self.height)

    def draw(self, drawing: Drawing) -> None:
        drawing.append(draw.Rectangle(0, 0, self.width, self.height, stroke='black', fill='none'))


class ModifyFaceStep(Step):
    def __init__(self, face: Face, step: Step) -> None:
        self.face = face
        self.step = step

    @property
    def size(self) -> tuple[int, int]:
        return combined_size([self.step.size, self.face.size])

    def instruction(self) -> str:
        return f"{self.step.instruction} auf {self.face}"

    def draw(self, drawing: Drawing, active: bool = True) -> None:
        self.face.draw(drawing)
        self.step.draw(drawing, active)
