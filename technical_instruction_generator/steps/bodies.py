import math

import drawsvg as draw
from drawsvg import Drawing, Group

from .base import Step
from ..layout_base import ViewBox


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

    @property
    def view_box(self) -> ViewBox:
        return ViewBox(0, 0, math.ceil(self.width), math.ceil(self.height))

    def draw(self, drawing: Drawing) -> None:
        drawing.append(draw.Rectangle(0, 0, self.width, self.height, stroke='black', fill='none'))


class ModifyFaceStep(Step):
    def __init__(self, face: Face, step: Step) -> None:
        super().__init__()
        self.face = face
        self.step = step

    @property
    def identifier(self) -> str | None:
        return self.step.identifier

    @property
    def view_box(self) -> ViewBox:
        return ViewBox.combine([self.step.view_box, self.face.view_box])

    @property
    def view_box_closeup(self) -> ViewBox:
        x0 = self.step.view_box_closeup.x
        y0 = min(self.step.view_box_closeup.y, self.face.view_box.y)
        x1 = x0 + self.step.view_box_closeup.width
        y1 = max(self.step.view_box_closeup.y, self.face.view_box.y + self.face.view_box.height)
        return ViewBox(x0, y0, x1 - x0, y1 - y0)

    @property
    def instruction(self) -> str:
        return f"{self.step.instruction[:-1]} auf {self.face}."

    def draw(self, drawing: Drawing | Group, active: bool = True, dimensions: bool = True) -> None:
        self.face.draw(drawing)
        self.step.draw(drawing, active, dimensions)
