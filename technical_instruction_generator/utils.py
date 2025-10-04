import math
from typing import Any

import drawsvg as draw

from .dimensions import ANNOTATION_OFFSET, DIMENSIONS_OFFSET, FONT_SIZE_BASE
from .layout_base import SizedGroup
from .style import DASH, FONT_FAMILY_TECH


def get_color(active: bool) -> str:
    return "red" if active else "black"


class Text(draw.Text):
    def __init__(self, text: Any, font_size: Any, x: float, y: float, font_family=FONT_FAMILY_TECH, **kwargs):
        super().__init__(text, font_size, x, -y, transform='scale(1, -1)', font_family=font_family, **kwargs)


def draw_position(group: SizedGroup, x0: float, x1: float, y0: float, y1: float) -> None:
    group.draw(draw.Line(x0, y1, x1, y1, stroke='red', stroke_width=0.5, stroke_dasharray=DASH))  # x
    group.draw(draw.Line(x1, y0, x1, y1, stroke='red', stroke_width=0.5, stroke_dasharray=DASH))  # y


def get_position_text(x0: float, x1: float, y0: float, y1: float) -> list[draw.Text]:
    return [
        draw.Text(
            str(x1 - x0),
            FONT_SIZE_BASE,
            x1 + math.copysign(DIMENSIONS_OFFSET, x0 - x1),
            y1 + ANNOTATION_OFFSET,
            fill='red',
            text_anchor='middle',
            dominant_baseline='auto',
            font_family=FONT_FAMILY_TECH,
        ),
        draw.Text(
            str(y1 - y0),
            FONT_SIZE_BASE,
            x1 + ANNOTATION_OFFSET,
            y1 + math.copysign(DIMENSIONS_OFFSET, y0 - y1),
            fill='red',
            text_anchor='start',
            dominant_baseline='middle',
            font_family=FONT_FAMILY_TECH,
        ),
    ]