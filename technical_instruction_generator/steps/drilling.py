import math

import drawsvg as draw
from drawsvg import Drawing, Group

from .base import Step
from ..dimensions import ANNOTATION_OFFSET, FONT_SIZE_BASE
from ..layout_base import SizedGroup, ViewBox
from ..style import DIMENSIONS_FONT_COLOR, FONT_FAMILY_TECH
from ..utils import draw_position, get_position_text, get_color, Text


class DrillHole(Step):
    def __init__(self, x: float, y: float, diameter: float, depth: float = 0, through: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)

        if not through and depth == 0:
            raise ValueError("Depth greater than 0 must be specified for non-through holes")

        self.x = x
        self.y = y
        self.diameter = diameter
        self.depth = depth
        self.through = through

    def clone(self, x=None, y=None) -> 'DrillHole':
        return DrillHole(x or self.x, y or self.y, self.diameter, self.depth, self.through)

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
            if not self.through:
                res += "U"
        return res

    @property
    def instruction(self) -> str:
        res = f"Bohre Loch bei ({self.x}, {self.y}) mit Durchmesser {self.diameter}"
        if self.depth > 0:
            res += f" und Tiefe {self.depth}"
        res += "."
        return res

    def draw(
        self,
        group: SizedGroup,
        x=0,
        y=0,
        active: bool = True,
        dimensions: bool = True,
        close_up: bool = False,
        faded: bool = False,
        dim_ref_pt: tuple[float, float] | None = None,
    ) -> None:
        if dim_ref_pt is None:
            dim_ref_pt = (0, 0)

        color = get_color(active)
        stroke_opacity = 0.4 if faded else 1
        fill = 'none' if self.through else 'gray'
        fill_opacity = 0.2 if faded else 0.5
        group.append(draw.Circle(x + self.x, y + self.y, self.radius, stroke=color, stroke_opacity=stroke_opacity, fill=fill, fill_opacity=fill_opacity))

        if dimensions:
            draw_position(group, x + dim_ref_pt[0], x + self.x, y + dim_ref_pt[1], y + self.y)

            group.register_text(draw.Text(
                self.annotation,
                FONT_SIZE_BASE,
                x + self.x + self.radius + ANNOTATION_OFFSET,
                y + self.y,
                fill=DIMENSIONS_FONT_COLOR,
                text_anchor='start',
                dominant_baseline='middle',
                font_family=FONT_FAMILY_TECH,
            ))
            group.register_text(get_position_text(x + dim_ref_pt[0], x + self.x, y + dim_ref_pt[1], y + self.y))



