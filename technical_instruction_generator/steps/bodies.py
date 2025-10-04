import math
from abc import ABC

import drawsvg as draw

from .base import Step
from .drilling import DrillHole
from ..dimensions import FACE_ANNOTATION_OFFSET, FONT_SIZE_BASE
from ..layout_base import SizedGroup, ViewBox
from ..style import FONT_FAMILY_TECH, DASH


class Body:
    def __init__(self, identifier: str):
        self.identifier = identifier


class ModifyBodyStep(Step, ABC):
    def __init__(self, body: Body):
        super().__init__()
        self.body = body


class Face(Body):
    def __init__(self, identifier: str, width: float, height: float) -> None:
        super().__init__(identifier)
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


class ModifyFaceStep(ModifyBodyStep):
    def __init__(self, body: Face, step: Step) -> None:
        super().__init__(body)
        self.step = step

    @property
    def identifier(self) -> str | None:
        return self.step.identifier

    @property
    def face(self) -> Face:
        assert isinstance(self.body, Face)
        return self.body

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

    def draw(self, group: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True, close_up: bool = False) -> None:
        self.face.draw(group, x, y)
        self.step.draw(group, x, y, active, dimensions)


class Bar(Body):
    def __init__(self, identifier: str, width: float, height: float, length: float) -> None:
        super().__init__(identifier)
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

    def get_adjacent_faces(self, identifier: str) -> list[Face]:
        if identifier == 'A':
            return [self.faces['B'], self.faces['D']]
        elif identifier == 'B':
            return [self.faces['C'], self.faces['A']]
        elif identifier == 'C':
            return [self.faces['D'], self.faces['B']]
        elif identifier == 'D':
            return [self.faces['A'], self.faces['C']]
        raise KeyError(identifier)


class ModifyBarStep(ModifyBodyStep):
    def __init__(self, bar: Bar, face_identifier: str, step: Step, through: bool = False) -> None:
        super().__init__(bar)
        self.face_identifier = face_identifier
        self.face = self.bar[face_identifier]
        self.step = step
        self.through = through

        self.padding = 10
        self.layout_width = math.ceil(self.bar.length)
        self.layout_height = math.ceil(2 * self.bar.height + 2 * self.bar.width + 3 * self.padding)
        self.ys = {}
        y = 0
        for key, face in self.bar.faces.items():
            self.ys[key]  = y
            y += face.height + self.padding

    @property
    def identifier(self) -> str | None:
        return self.step.identifier

    @property
    def bar(self) -> Bar:
        assert isinstance(self.body, Bar)
        return self.body

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
        return ViewBox(x0, y0 - self.ys[self.face_identifier], x1 - x0, y1 - y0)

    def draw(self, group: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True, close_up=False) -> None:
        for key, face in self.bar.faces.items():
            y_face = y + self.ys[key]
            face.draw(group, x, y_face)

            # annotate face
            if not close_up or face.identifier == self.face_identifier:
                group.register_text(draw.Text(
                    face.identifier,
                    FONT_SIZE_BASE,
                    x - FACE_ANNOTATION_OFFSET,
                    y_face + face.height / 2,
                    text_anchor='end',
                    dominant_baseline='middle',
                    font_family=FONT_FAMILY_TECH,
                ))

            if key == self.face_identifier:
                self.step.draw(group, x, y_face, active, dimensions)
                self._transfer_step_to_other_faces(group, x, y, active, dimensions)

    def _transfer_step_to_other_faces(self, group: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True) -> None:
        if isinstance(self.step, DrillHole):
            if self.step.through:
                # transfer step to opposite face
                face = self.bar.get_opposite_face(self.face_identifier)
                self.step.clone(y=face.height - self.step.y).draw(group, x, y + self.ys[face.identifier], False, False)

            # transfer step to adjacent faces
            for face, face_sign in zip(self.bar.get_adjacent_faces(self.face_identifier), [1, -1]):
                height = face.height if self.step.through else self.step.depth
                y_face = y + self.ys[face.identifier]
                if not self.step.through:
                    y0 = y_face if face_sign >= 0 else y_face + face.height - height
                    y1 = y0 + height
                    group.append(draw.Rectangle(
                        x + self.step.x - self.step.radius,
                        y0,
                        self.step.diameter,
                        y1 - y0,
                        stroke='none',
                        fill='gray',
                        fill_opacity=0.25,
                    ))
                    y0 = y_face if face_sign >= 0 else y_face + face.height
                    y1 = y0 + face_sign * height
                    group.append(draw.Line(
                        x + self.step.x - self.step.radius,
                        y1,
                        x + self.step.x + self.step.radius,
                        y1,
                        stroke='gray',
                        stroke_dasharray=DASH,
                    ))
                y0 = y_face if face_sign >= 0 else y_face + face.height
                y1 = y0 + face_sign * height
                for sign in [-1, 1]:
                    group.append(draw.Line(
                        x + self.step.x + sign * self.step.radius,
                        y0,
                        x + self.step.x + sign * self.step.radius,
                        y1,
                        stroke='gray',
                        stroke_dasharray=DASH,
                        fill='none',
                    ))
