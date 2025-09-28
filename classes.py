import math
import os
from abc import ABC, abstractmethod
from builtins import _NotImplementedType
from pathlib import Path
from typing import Any

import drawsvg as draw
from drawsvg import Drawing


ANNOTATION_OFFSET = 2
FONT_SIZE = 8
DASH = '3,2'


def combined_size(sizes: list[tuple[int, int]]):
    return max(s[0] for s in sizes), max(s[1] for s in sizes)


def get_color(active: bool) -> str:
    return "red" if active else "black"


class Text(draw.Text):
    def __init__(self, text: Any, font_size: Any, x: float, y: float, **kwargs):
        super().__init__(text, font_size, x, -y, transform='scale(1, -1)', **kwargs)


def draw_position(drawing: Drawing, x: float, y: float) -> None:
    # x position
    drawing.draw(draw.Line(0, y, x, y, stroke='black', stroke_width=0.5, stroke_dasharray=DASH))
    drawing.draw(Text(
        str(x),
        FONT_SIZE,
        x / 2,
        y + ANNOTATION_OFFSET,
        color='black',
        text_anchor='middle',
        dominant_baseline='auto',
    ))

    # y position
    drawing.draw(draw.Line(x, 0, x, y, stroke='black', stroke_width=0.5, stroke_dasharray=DASH))
    drawing.draw(Text(
        str(y),
        FONT_SIZE, x + ANNOTATION_OFFSET,
        y / 2,
        color='black',
        text_anchor='start',
        dominant_baseline='middle',
    ))


class Step(ABC):
    @property
    @abstractmethod
    def size(self) -> tuple[int, int] | _NotImplementedType:
        return NotImplemented

    @property
    @abstractmethod
    def instruction(self) -> str:
        return NotImplemented

    @abstractmethod
    def draw(self, drawing: Drawing, active: bool = True) -> None:
        raise NotImplementedError


class Manual:
    def __init__(self, steps: list[Step]) -> None:
        self.steps = steps

    def draw(self, path: str | Path | os.PathLike):
        if not isinstance(path, Path):
            path = Path(path)

        path.parent.mkdir(exist_ok=True)

        width, height = combined_size([step.size for step in self.steps])

        for i in range(len(self.steps)):
            drawing = draw.Drawing(width, height, origin=(0, 0), transform='scale(1,-1)')
            drawing.append(draw.Rectangle(0, 0, width, height, fill="white"))

            for step in self.steps[:-i]:
                step.draw(drawing, active=False)
            self.steps[i].draw(drawing, active=True)

            drawing.save_svg(path.parent / f"{path.stem}_{i + 1:03d}.svg")


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


class DrillHole(Step):
    def __init__(self, x: float, y: float, diameter: float, depth: float = 0) -> None:
        self.x = x
        self.y = y
        self.diameter = diameter
        self.depth = depth

    @property
    def size(self) -> tuple[int, int]:
        return (
            math.ceil(self.x + self.radius),
            math.ceil(self.y + self.radius),
        )

    @property
    def radius(self) -> float:
        return self.diameter / 2

    @property
    def annotation(self) -> str:
        res = f"⌀{self.diameter}"
        if self.depth > 0:
            res += f"x{self.depth}"
        return res

    def instruction(self) -> str:
        res = f"Bohre ein Loch bei ({self.x}, {self.y}) mit Durchmesser {self.diameter}"
        if self.depth > 0:
            res += f"und Tiefe {self.depth}"
        res += "."
        return res

    def draw(self, drawing: Drawing, active: bool = True) -> None:
        color = get_color(active)
        drawing.append(draw.Circle(self.x, self.y, self.radius, stroke=color, fill='none'))
        if not active:
            return

        # hole dimensions
        drawing.append(Text(
            self.annotation,
            FONT_SIZE,
            self.x + self.radius + ANNOTATION_OFFSET,
            self.y,
            text_anchor='start',
            dominant_baseline='middle',
            transform_children='scale(1,-1)',
        ))

        draw_position(drawing, self.x, self.y)
