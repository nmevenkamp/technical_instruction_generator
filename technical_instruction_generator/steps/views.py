from abc import abstractmethod

import drawsvg as draw

from .base import Step
from ..layout_base import SizedGroup, ViewBox


class View:
    def __init__(self, steps: list[Step]):
        self.steps = steps

    @abstractmethod
    def get_group(self) -> SizedGroup:
        raise NotImplementedError

    def get_draw_offset(self) -> tuple[int, int]:
        return 0, 0

    def get_clip_path(self) -> draw.ClipPath | None:
        return None


class FullView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_box = ViewBox.combine([step.view_box for step in self.steps])

    @property
    def view_box(self):
        return self._view_box

    def get_group(self) -> SizedGroup:
        group = SizedGroup(width=self.view_box.width, height=self.view_box.height, flip_y=True)
        for step in self.steps[:-2]:
            step.draw(group, active=False, dimensions=False)
        self.steps[-1].draw(group, active=True, dimensions=False)
        return group

    def get_draw_offset(self) -> tuple[int, int]:
        return -self.view_box.x, -self.view_box.y


class CloseUpView(View):
    def __init__(self, *args, padding: int | tuple[int, int] = 0, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(padding, int):
            padding = (padding, padding)
        self.padding = padding

        # initialize ViewBox
        view_box = self.steps[-1].view_box_closeup
        self._view_box = ViewBox(
            view_box.x - self.padding[0],
            view_box.y - self.padding[1],
            view_box.width + 2 * self.padding[0],
            view_box.height + 2 * self.padding[1],
        )

    @property
    def view_box(self) -> ViewBox:
        return self._view_box

    def get_group(self) -> SizedGroup:
        group = SizedGroup(width=self.view_box.width, height=self.view_box.height, flip_y=True)
        for step in self.steps[:-2]:
            step.draw(group, active=False, dimensions=False)
        self.steps[-1].draw(group, active=True, dimensions=True)
        return group

    def get_draw_offset(self) -> tuple[int, int]:
        return -self.view_box.x, -self.view_box.y

    def get_clip_path(self) -> draw.ClipPath:
        rect = draw.Rectangle(self.view_box.x, self.view_box.y, self.view_box.width, self.view_box.height)
        clip_path = draw.ClipPath()
        clip_path.append(rect)
        return clip_path
