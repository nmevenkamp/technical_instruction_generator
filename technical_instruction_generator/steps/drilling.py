import math

import drawsvg as draw
from drawsvg import Drawing

from .base import Step
from ..dimensions import ANNOTATION_OFFSET, FONT_SIZE
from ..utils import draw_position, get_color, Text


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
