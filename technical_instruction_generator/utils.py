from typing import Any

import drawsvg as draw
from drawsvg import Drawing

from .dimensions import ANNOTATION_OFFSET, DASH, FONT_SIZE


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