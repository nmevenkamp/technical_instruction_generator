import drawsvg as draw

from .dimensions import A4_HEIGHT, A4_WIDTH, FONT_SIZE_BASE, FONT_SIZE_TITLE, \
    INSTRUCTION_BOX_PADDING, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TITLE, MARGIN_TOP
from .layout_base import FixedSizeBehaviour, SizedGroup, SizeBehaviour, LayoutDirection, Alignment
from .steps.views import View
from .style import FONT_FAMILY_TEXT


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
        self._start = 0

    def add_view(self, view: View, size_behaviour: SizeBehaviour = None) -> bool:
        return self.add_group(view.get_group(), size_behaviour=size_behaviour, clip_path=view.get_clip_path())

    def add_group(self, group: SizedGroup, size_behaviour: SizeBehaviour | None = None, clip_path: draw.ClipPath | None = None) -> bool:
        if self.direction == LayoutDirection.HORIZONTAL:
            available_size = self.width - self._start, self.height
        else:
            available_size = self.width, self.height - self._start

        if size_behaviour is None:
            size_behaviour = FixedSizeBehaviour()
        size, scale = size_behaviour.get_size_and_scale((group.width, group.height), available_size)

        if size[0] > available_size[0] or size[1] > available_size[1]:
            return False

        group.width = size[0]
        group.height = size[1]

        if self.direction == LayoutDirection.HORIZONTAL:
            x = self._start
            if self.alignment == Alignment.START:
                y = 0
            elif self.alignment == Alignment.END:
                y = self.height - group.height
            else:
                y = (self.height - group.height) / 2
        else:
            y = self._start
            if self.alignment == Alignment.START:
                x = 0
            elif self.alignment == Alignment.END:
                x = self.width - group.width
            else:
                x = (self.width - group.width) / 2

        x /= scale[0]
        y /= scale[1]
        transform = f"scale({scale[0]}, {scale[1]})"
        self.append(draw.Use(group, x, y, transform=transform, clip_path=clip_path))

        self._start += group.width if self.direction == LayoutDirection.HORIZONTAL else group.height
        self._start += self.padding

        return True
