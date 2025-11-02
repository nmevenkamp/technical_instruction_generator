import math

import drawsvg as draw
from drawsvg import Drawing, Group

from .base import Step
from ..dimensions import (
    ANNOTATION_DIMENSION_X_OFFSET_OFFSET,
    ANNOTATION_OFFSET,
    DRILL_ANNOTATION_OFFSET_Y,
    FONT_SIZE_BASE,
)
from ..layout_base import SizedGroup, ViewBox
from ..style import DIMENSIONS_FONT_COLOR, FONT_FAMILY_TECH
from ..utils import draw_position, get_position_text, get_color, disp, get_position_text_x


class DrillHole(Step):
    def __init__(
        self,
        x: float,
        y: float,
        diameter: float,
        depth: float = 0,
        through: bool = True,
        dimensions_offset_x: float = 0,
        identifier: str | None = None
    ) -> None:
        super().__init__(identifier)

        if not through and depth == 0:
            raise ValueError("Depth greater than 0 must be specified for non-through holes")

        self.x = x
        self.y = y
        self.diameter = diameter
        self.depth = depth
        self.through = through
        self.dimensions_offset_x = dimensions_offset_x

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.x == self.x and other.y == self.y and other.diameter == self.diameter and other.depth == self.depth and other.through == self.through

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
        res = f"D{disp(self.diameter)}"
        if self.depth > 0:
            res += f"x{disp(self.depth)}"
            if not self.through:
                res += "U"
        return res

    def get_instruction(self, dim_ref_pt: tuple[float, float] | None = None) -> str:
        if dim_ref_pt is None:
            dim_ref_pt = (0, 0)

        x = self.x - dim_ref_pt[0]
        y = self.y - dim_ref_pt[1]

        res = f"Bohre Loch bei "

        if self.dimensions_offset_x == 0:
            res += f"{disp(x)}, {disp(y)}"
        else:
            res += f"({disp(x + self.dimensions_offset_x)}, {disp(y)})"
        res += f" mit DM {disp(self.diameter)}"
        if self.depth > 0:
            res += f" und Tiefe {disp(self.depth)}"
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
                y + self.y - DRILL_ANNOTATION_OFFSET_Y,
                fill=DIMENSIONS_FONT_COLOR,
                text_anchor='start',
                dominant_baseline='hanging',
                font_family=FONT_FAMILY_TECH,
            ))
            y0 = y + dim_ref_pt[1]
            y1 = y + self.y
            group.register_text(get_position_text(x + dim_ref_pt[0], x + self.x, y0, y1))
            if self.dimensions_offset_x is not None:
                group.register_text(get_position_text_x(x + dim_ref_pt[0], x + self.x, (y0 + y1) / 2 + 18, x_offset=self.dimensions_offset_x))



