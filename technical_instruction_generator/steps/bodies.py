import math

import drawsvg as draw

from .base import Step
from ..dimensions import FACE_ANNOTATION_OFFSET, FONT_SIZE_BASE
from ..layout import LinearLayout
from ..layout_base import LayoutDirection, SizedGroup, ViewBox
from ..style import FONT_FAMILY_TECH


class Face:
    def __init__(self, identifier: str, width: float, height: float) -> None:
        self.identifier = identifier
        self.width = width
        self.height = height

    def __str__(self) -> str:
        return f"Fläche {self.identifier}"

    @property
    def size(self) -> tuple[int, int]:
        return math.ceil(self.width), math.ceil(self.height)

    @property
    def view_box(self) -> ViewBox:
        return ViewBox(0, 0, math.ceil(self.width), math.ceil(self.height))

    def draw(self, group: SizedGroup, x=0, y=0) -> None:
        group.append(draw.Rectangle(x, y, self.width, self.height, stroke='black', fill='none'))


class ModifyFaceStep(Step):
    def __init__(self, face: Face, step: Step) -> None:
        super().__init__()
        self.face = face
        self.step = step

    @property
    def identifier(self) -> str | None:
        return self.step.identifier

    @property
    def view_box(self) -> ViewBox:
        return ViewBox.combine([self.step.view_box, self.face.view_box])

    @property
    def view_box_closeup(self) -> ViewBox:
        x0 = self.step.view_box_closeup.x
        y0 = min(self.step.view_box_closeup.y, self.face.view_box.y)
        x1 = x0 + self.step.view_box_closeup.width
        y1 = max(self.step.view_box_closeup.y, self.face.view_box.y + self.face.view_box.height)
        return ViewBox(x0, y0, x1 - x0, y1 - y0)

    @property
    def instruction(self) -> str:
        return f"{self.step.instruction[:-1]} auf {self.face}."

    def draw(self, group: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True) -> None:
        self.face.draw(group, x, y)
        self.step.draw(group, x, y, active, dimensions)


class Bar:
    def __init__(self, identifier: str, width: float, height: float, length: float) -> None:
        self.identifier = identifier
        self.length = length
        self.width = width
        self.height = height
        self.faces = {
            'C': Face('C', length, height),
            'D': Face('D', length, width),
            'A': Face('A', length, height),
            'B': Face('B', length, width),
        }

    def __str__(self) -> str:
        return f"Latte {self.identifier}"

    def __getitem__(self, identifier: str) -> Face:
        return self.faces[identifier]

    def get_opposite_face(self, identifier: str) -> Face:
        if identifier == 'A':
            return self.faces['C']
        elif identifier == 'B':
            return self.faces['D']
        elif identifier == 'C':
            return self.faces['A']
        elif identifier == 'D':
            return self.faces['B']
        raise KeyError(identifier)


class ModifyBarStep(Step):
    def __init__(self, bar: Bar, face_identifier: str, step: Step, through: bool = False) -> None:
        super().__init__()
        self.bar = bar
        self.face_identifier = face_identifier
        self.face = self.bar[face_identifier]
        self.step = step
        self.through = through

        self.padding = 10
        self.layout_width = math.ceil(self.bar.length)
        self.layout_height = math.ceil(2 * self.bar.height + 2 * self.bar.width + 3 * self.padding)
        self.y0_offset = 0
        for key, face in self.bar.faces.items():
            if face.identifier == self.face_identifier:
                break
            self.y0_offset -= face.height + self.padding

    @property
    def identifier(self) -> str | None:
        return self.step.identifier

    @property
    def instruction(self) -> str:
        return f"{self.step.instruction[:-1]} auf {self.face} in {self.bar}."

    @property
    def view_box(self) -> ViewBox:
        return ViewBox(-FACE_ANNOTATION_OFFSET, 0, self.layout_width + FACE_ANNOTATION_OFFSET, self.layout_height)

    @property
    def view_box_closeup(self) -> ViewBox:
        x0 = self.step.view_box_closeup.x
        y0 = min(self.step.view_box_closeup.y, self.face.view_box.y)
        x1 = x0 + self.step.view_box_closeup.width
        y1 = max(self.step.view_box_closeup.y, self.face.view_box.y + self.face.view_box.height)
        return ViewBox(x0, y0 + self.y0_offset, x1 - x0, y1 - y0)

    def draw(self, group: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True, close_up=False) -> None:
        for key, face in self.bar.faces.items():
            face.draw(group, x, y)

            # annotate face
            if not close_up or face.identifier == self.face_identifier:
                group.register_text(draw.Text(
                    face.identifier,
                    FONT_SIZE_BASE,
                    x - FACE_ANNOTATION_OFFSET,
                    y + face.height / 2,
                    text_anchor='end',
                    dominant_baseline='middle',
                    font_family=FONT_FAMILY_TECH,
                ))

            if key == self.face_identifier:
                self.step.draw(group, x, y, active, dimensions)
            y += face.height + self.padding
