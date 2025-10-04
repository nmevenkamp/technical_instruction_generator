import math
from typing import Any

import drawsvg as draw

from .dimensions import ANNOTATION_OFFSET, DIMENSIONS_TEXT_OFFSET, FONT_SIZE_BASE
from .layout_base import SizedGroup
from .style import ACTIVE_STROKE_COLOR, DASH, DIMENSIONS_FONT_COLOR, DIMENSIONS_LINE_COLOR, FONT_FAMILY_TECH


def disp(nr: int | float) -> str:
    if int(nr) == nr:
        return f"{nr:.0f}"
    return str(nr)


def get_color(active: bool) -> str:
    return ACTIVE_STROKE_COLOR if active else "black"


class Text(draw.Text):
    def __init__(self, text: Any, font_size: Any, x: float, y: float, font_family=FONT_FAMILY_TECH, **kwargs):
        super().__init__(text, font_size, x, -y, transform='scale(1, -1)', font_family=font_family, **kwargs)


def draw_position(group: SizedGroup, x0: float, x1: float, y0: float, y1: float) -> None:
    group.draw(draw.Line(x0, y1, x1, y1, stroke=DIMENSIONS_LINE_COLOR, stroke_width=0.5, stroke_dasharray=DASH))  # x
    group.draw(draw.Line(x1, y0, x1, y1, stroke=DIMENSIONS_LINE_COLOR, stroke_width=0.5, stroke_dasharray=DASH))  # y


def get_position_text(x0: float, x1: float, y0: float, y1: float) -> list[draw.Text]:
    return [
        draw.Text(
            disp(math.fabs(x1 - x0)),
            FONT_SIZE_BASE,
            x1 + math.copysign(DIMENSIONS_TEXT_OFFSET, x0 - x1),
            y1 + ANNOTATION_OFFSET,
            fill=DIMENSIONS_FONT_COLOR,
            text_anchor='end' if x0 < x1 else 'start',
            dominant_baseline='auto',
            font_family=FONT_FAMILY_TECH,
        ),
        draw.Text(
            disp(math.fabs(y1 - y0)),
            FONT_SIZE_BASE,
            x1 + ANNOTATION_OFFSET,
            y1 + math.copysign(DIMENSIONS_TEXT_OFFSET, y0 - y1),
            fill=DIMENSIONS_FONT_COLOR,
            text_anchor='start',
            dominant_baseline='middle',
            font_family=FONT_FAMILY_TECH,
        ),
    ]


def get_text_background(text: Any) -> draw.Rectangle:
    width = len(text.escaped_text) * text.args['font-size']
    height = text.args['font-size']
    text_anchor = text.args.get('text-anchor', 'start')
    if text_anchor == 'start':
        x = 0
    elif text_anchor == 'middle':
        x = -width / 2
    else:
        x = -width
    dominant_baseline = text.args.get('dominant-baseline', 'auto')
    if dominant_baseline == 'auto':
        y = -height
    elif dominant_baseline == 'middle':
        y = -height / 2
    else:
        y = 0
    return draw.Rectangle(x + text.args['x'], y + text.args['y'], width, height, fill='white')