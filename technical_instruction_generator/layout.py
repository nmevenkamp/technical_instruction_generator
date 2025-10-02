from enum import Enum

import drawsvg as draw

from technical_instruction_generator.dimensions import A4_HEIGHT, A4_WIDTH, FONT_SIZE_BASE, FONT_SIZE_TITLE, \
    INSTRUCTION_BOX_PADDING, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TITLE, MARGIN_TOP
from technical_instruction_generator.style import FONT_FAMILY_TEXT


class SizedGroup(draw.Group):
    def __init__(self, *args, width: int | None = None, height: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = width
        self.height = height


class LayoutDirection(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class Alignment(Enum):
    START = 0
    END = 1
    CENTER = 2


class SizeBehaviour:
    def get_size_and_scale(self, group: SizedGroup, available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        raise NotImplementedError()


class FixedSizeBehaviour(SizeBehaviour):
    def get_size_and_scale(self, group: SizedGroup, available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        return (group.width, group.height), (1.0, 1.0)


class ScaleBehaviour(SizeBehaviour):
    def get_size_and_scale(self, group: SizedGroup, available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        if group.width is None and group.height is None:
            raise ValueError("Can't scale group that has neither `width` nor `height`")

        if group.width is None:
            scale = available_size[1] / group.height
        elif group.height is None:
            scale = available_size[0] / group.width
        else:
            scale = min(available_size[0] / group.width, available_size[1] / group.height)

        return (int(group.width * scale), int(group.height * scale)), (scale, scale)


class ExpandBehaviour(SizeBehaviour):
    def __init__(self, direction: LayoutDirection | None = None, keep_aspect_ratio: bool = True) -> None:
        self.direction = direction
        self.keep_aspect_ratio = keep_aspect_ratio

    def get_size_and_scale(self, group: SizedGroup, available_size: tuple[int, int]) -> tuple[tuple[int, int], tuple[float, float]]:
        if not self.keep_aspect_ratio or group.width is None or group.height is None:
            if self.direction is None or self.direction == LayoutDirection.HORIZONTAL:
                group.width = available_size[0]
            if self.direction is None or self.direction == LayoutDirection.VERTICAL:
                group.height = available_size[1]
            return

        factor = min(available_size[0] / group.width, available_size[1] / group.height)
        return (int(group.width * factor), int(group.height * factor)), (1, 1)


class Page:
    def __init__(self, page_idx: int | None = None, title: str | None = None):
        self.drawing = draw.Drawing(A4_WIDTH, A4_HEIGHT, origin=(0, 0))
        self.drawing.append(draw.Rectangle(0, 0, A4_WIDTH, A4_HEIGHT, fill='white'))

        if page_idx is not None:
            self.drawing.append(
                draw.Text(f"{page_idx + 1}", FONT_SIZE_BASE, A4_WIDTH - 100, A4_HEIGHT - 100, text_anchor='end',
                          font_weight='bold', font_family=FONT_FAMILY_TEXT))

        y = MARGIN_TOP
        if title is not None:
            self.drawing.append(draw.Text(title, FONT_SIZE_TITLE, A4_WIDTH / 2, MARGIN_TOP, text_anchor='middle',
                                  font_family=FONT_FAMILY_TEXT))
            y += MARGIN_TITLE

        self.layout = LinearLayout(id="layout", width=A4_WIDTH - MARGIN_LEFT - MARGIN_RIGHT,
                              height=A4_HEIGHT - y - MARGIN_BOTTOM, direction=LayoutDirection.VERTICAL,
                              padding=INSTRUCTION_BOX_PADDING)
        self.drawing.append(draw.Use(self.layout, MARGIN_LEFT, y))


class LinearLayout(SizedGroup):
    def __init__(self, *args, direction: LayoutDirection, alignment: Alignment = None, padding: int = 0, **kwargs):
        if alignment is None:
            alignment = Alignment.CENTER

        super().__init__(*args, **kwargs)
        self.direction = direction
        self.alignment = alignment
        self.padding = padding
        self._named_groups: dict[str, SizedGroup] = {}
        self._groups: list[SizedGroup] = []

    def __item__(self, identifier: str) -> SizedGroup | None:
        return self._named_groups.get(identifier, None)

    def add_group(self, group: SizedGroup, identifier: str | None = None, size_behaviour: SizeBehaviour | None = None) -> bool:
        start = sum(self._get_length(group) for group in self._groups) + self.padding * len(self._groups)
        if self.direction == LayoutDirection.HORIZONTAL:
            available_size = self.width - start, self.height
        else:
            available_size = self.width, self.height - start

        if size_behaviour is None:
            size_behaviour = FixedSizeBehaviour()
        size, scale = size_behaviour.get_size_and_scale(group, available_size)

        if size[0] > available_size[0] or size[1] > available_size[1]:
            return False

        group.width = size[0]
        group.height = size[1]

        size_wrapper = SizedGroup(width=size[0], height=size[1], transform=f"scale({scale[0]}, {scale[1]})")
        size_wrapper.append(draw.Use(group, 0, 0))

        if self.direction == LayoutDirection.HORIZONTAL:
            x = start
            if self.alignment == Alignment.START:
                y = 0
            elif self.alignment == Alignment.END:
                y = self.height - group.height
            else:
                y = (self.height - group.height) / 2
        else:
            y = start
            if self.alignment == Alignment.START:
                x = 0
            elif self.alignment == Alignment.END:
                x = self.width - group.width
            else:
                x = (self.width - group.width) / 2

        self.append(draw.Use(size_wrapper, x, y))
        self._groups.append(group)
        if identifier is not None:
            self._named_groups[identifier] = group

        return True

    def _get_length(self, group: SizedGroup) -> int:
        return group.width if self.direction == LayoutDirection.HORIZONTAL else group.height
