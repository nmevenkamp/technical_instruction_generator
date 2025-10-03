import math

import drawsvg as draw
from drawsvg import Drawing, Group

from .base import Step
from ..dimensions import ANNOTATION_OFFSET, FONT_SIZE_BASE
from ..layout_base import ViewBox
from ..utils import draw_position, get_color, Text


class DrillHole(Step):
    def __init__(self, x: float, y: float, diameter: float, depth: float = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.diameter = diameter
        self.depth = depth

    @property
    def center(self) -> tuple[float, float]:
        return self.x, self.y

    @property
    def size(self) -> tuple[float, float]:
        return self.diameter, self.diameter

    @property
    def view_box(self) -> ViewBox:
        return ViewBox(
            math.floor(self.x - self.radius),
            math.floor(self.y - self.radius),
            math.ceil(2 * self.radius),
            math.ceil(2 * self.radius),
        )

    @property
    def view_box_closeup(self) -> ViewBox:
        return self.view_box

    @property
    def radius(self) -> float:
        return self.diameter / 2

    @property
    def annotation(self) -> str:
        res = f"D{self.diameter}"
        if self.depth > 0:
            res += f"x{self.depth}"
        return res

    @property
    def instruction(self) -> str:
        res = f"Bohre ein Loch bei ({self.x}, {self.y}) mit Durchmesser {self.diameter}"
        if self.depth > 0:
            res += f"und Tiefe {self.depth}"
        res += "."
        return res

    def draw(self, drawing: Drawing | Group, active: bool = True, dimensions: bool = True) -> None:
        color = get_color(active)
        drawing.append(draw.Circle(self.x, self.y, self.radius, stroke=color, fill='none'))

        if dimensions:
            drawing.append(Text(
                self.annotation,
                FONT_SIZE_BASE,
                self.x + self.radius + ANNOTATION_OFFSET,
                self.y,
                text_anchor='start',
                dominant_baseline='middle',
                transform_children='scale(1,-1)',
            ))

            draw_position(drawing, self.x, self.y)
