from typing import Any

import drawsvg as draw

from .dimensions import ANNOTATION_OFFSET, DASH, FONT_SIZE_BASE
from .layout_base import SizedGroup
from .style import FONT_FAMILY_TECH


def get_color(active: bool) -> str:
    return "red" if active else "black"


class Text(draw.Text):
    def __init__(self, text: Any, font_size: Any, x: float, y: float, font_family=FONT_FAMILY_TECH, **kwargs):
        super().__init__(text, font_size, x, -y, transform='scale(1, -1)', font_family=font_family, **kwargs)


def draw_position(group: SizedGroup, x: float, y: float) -> None:
    group.draw(draw.Line(0, y, x, y, stroke='black', stroke_width=0.5, stroke_dasharray=DASH))  # x
    group.draw(draw.Line(x, 0, x, y, stroke='black', stroke_width=0.5, stroke_dasharray=DASH))  # y


def get_position_text(x: float, y: float) -> list[draw.Text]:
    return [
        draw.Text(
            str(x),
            FONT_SIZE_BASE,
            x / 2,
            y + ANNOTATION_OFFSET,
            color='black',
            text_anchor='middle',
            dominant_baseline='auto',
            font_family=FONT_FAMILY_TECH,
        ),
        draw.Text(
            str(y),
            FONT_SIZE_BASE,
            x + ANNOTATION_OFFSET,
            y / 2,
            color='black',
            text_anchor='start',
            dominant_baseline='middle',
            font_family=FONT_FAMILY_TECH,
        ),
    ]