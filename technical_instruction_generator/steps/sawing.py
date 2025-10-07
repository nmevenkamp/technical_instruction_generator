import drawsvg as draw
import numpy as np

from .base import Step
from ..layout_base import SizedGroup, ViewBox
from ..utils import draw_position_x, get_color, disp, get_position_text_x


class Cut(Step):
    """TODO: currently, only x-cuts are implemented"""

    def __init__(self, x: float, y: float, direction: tuple[float, float], length: float, identifier: str | None = None) -> None:
        super().__init__(identifier)
        self.x = x
        self.y = y
        self.direction = direction
        self.length = length
        self.x0 = np.array([x, y])
        self.v = np.array(direction)
        self.x1 = self.x0 + self.v * length
        self.x_left = np.min([self.x0[0], self.x1[0]])
        self.x_right = np.max([self.x0[0], self.x1[0]])
        self.y_left = np.min([self.x0[1], self.x1[1]])
        self.y_right = np.max([self.x0[1], self.x1[1]])
        self.width = self.x_left - self.x_right
        self.height = self.y_right - self.y_left

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.x == self.x and other.y == self.y and other.direction == self.direction and other.length == self.length

    def clone(self, x=None, y=None, direction=None, length=None) -> 'Cut':
        return Cut(x or self.x, y or self.y, direction or self.direction, length or self.length)

    @property
    def position(self) -> tuple[float, float]:
        return self.x, self.y

    @property
    def size(self) -> tuple[float, float]:
        return self.width, self.height

    @property
    def view_box(self) -> ViewBox:
        return ViewBox(
            self.x_left,
            self.y_left,
            self.width,
            self.height,
        )

    @property
    def view_box_closeup(self) -> ViewBox:
        return self.view_box

    @property
    def annotation(self) -> str:
        return ""

    def get_instruction(self, dim_ref_pt: tuple[float, float] | None = None) -> str:
        if dim_ref_pt is None:
            dim_ref_pt = (0, 0)

        x = self.x - dim_ref_pt[0]

        return f"Schnitt bei {disp(x)}."

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
        group.append(draw.Line(x + self.x, y + self.y, x + self.x, y + self.y + self.length, stroke=color, stroke_opacity=stroke_opacity))

        delta = 5
        delta_sign = 1 if dim_ref_pt[0] < self.x else -1
        y2 = y + self.y + 0.5 * self.length
        group.append(draw.Line(x + self.x, y2, x + self.x + delta_sign * delta, y2 + delta, stroke=color, stroke_opacity=stroke_opacity))

        if dimensions:
            draw_position_x(group, x + dim_ref_pt[0], x + self.x, y + self.y + y2)
            group.register_text(get_position_text_x(x + dim_ref_pt[0], x + self.x, y + self.y + y2))



