from dataclasses import dataclass
from enum import Enum

import drawsvg as draw


@dataclass
class ViewBox:
    x: int
    y: int
    width: int
    height: int

    @staticmethod
    def combine(view_boxes: list['ViewBox']) -> 'ViewBox':
        x0 = min(vb.x for vb in view_boxes)
        y0 = min(vb.y for vb in view_boxes)
        x1 = max(vb.x + vb.width for vb in view_boxes)
        y1 = max(vb.y + vb.height for vb in view_boxes)
        return ViewBox(x0, y0, x1 - x0, y1 - y0)


class SizedGroup(draw.Group):
    def __init__(self, *args, width: int | None = None, height: int | None = None, flip_y: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = width
        self.height = height
        self._text: list[draw.Text] = []

        if flip_y:
            self.args['transform'] = f'scale(1,-1) translate(0,-{height})'

    @property
    def text(self) -> list[draw.Text]:
        return self._text

    def register_text(self, text: draw.Text | list[draw.Text]) -> None:
        if isinstance(text, draw.Text):
            self._text.append(text)
        else:
            self._text.extend(text)


class LayoutDirection(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class Alignment(Enum):
    START = 0
    END = 1
    CENTER = 2


class SizeBehaviour:
    def get_size_and_scale(self, size: tuple[int, int], available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        raise NotImplementedError()


class FixedSizeBehaviour(SizeBehaviour):
    def get_size_and_scale(self, size: tuple[int, int], available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        return (size[0], size[1]), (1.0, 1.0)


class ScaleBehaviour(SizeBehaviour):
    def get_size_and_scale(self, size: tuple[int, int], available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        if size[0] is None and size[1] is None:
            raise ValueError("Can't scale group that has neither `width` nor `height`")

        if size[0] is None:
            scale = available_size[1] / size[1]
        elif size[1] is None:
            scale = available_size[0] / size[0]
        else:
            scale = min(available_size[0] / size[0], available_size[1] / size[1])

        return (int(size[0] * scale), int(size[1] * scale)), (scale, scale)


class ExpandBehaviour(SizeBehaviour):
    def __init__(self, direction: LayoutDirection | None = None, keep_aspect_ratio: bool = True) -> None:
        self.direction = direction
        self.keep_aspect_ratio = keep_aspect_ratio

    def get_size_and_scale(self, size: tuple[int, int], available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        size = list(size)  # need copy to be able to modify
        if not self.keep_aspect_ratio or size[0] is None or size[1] is None:
            if self.direction is None or self.direction == LayoutDirection.HORIZONTAL:
                size[0] = available_size[0]
            if self.direction is None or self.direction == LayoutDirection.VERTICAL:
                size[1] = available_size[1]
            return (size[0], size[1]), (1.0, 1.0)

        factor = min(available_size[0] / size[0], available_size[1] / size[1])
        return (int(size[0] * factor), int(size[1] * factor)), (1, 1)