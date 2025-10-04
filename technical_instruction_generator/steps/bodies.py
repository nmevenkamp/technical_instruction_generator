import math
import re
from abc import ABC

import drawsvg as draw

from .base import Step
from .drilling import DrillHole
from ..dimensions import FACE_ANNOTATION_OFFSET, FONT_SIZE_BASE
from ..layout_base import SizedGroup, ViewBox
from ..style import FONT_FAMILY_TECH, DASH
from ..utils import draw_position


class Body:
    def __init__(self, identifier: str):
        self.identifier = identifier


class ModifyBodyStep(Step, ABC):
    def __init__(self, identifier: str, body: Body, step: Step):
        super().__init__(identifier)
        self.body = body
        self.step = step
        self._active_bodies = None

    def set_active_body(self, body: Body) -> None:
        self._active_bodies = [body]

    def set_active_bodies(self, active_bodies: list[Body]) -> None:
        self._active_bodies = active_bodies


class ModifyMultiBodyStep(Step):
    def __init__(self, bodies: list[Body], step: ModifyBodyStep):
        super().__init__(identifier=step.identifier)
        self.bodies = bodies
        self.step = step
        self._active_bodies = None

    def set_active_body(self, body: Body) -> None:
        self._active_bodies = [body]

    def set_active_bodies(self, active_bodies: list[Body]) -> None:
        self._active_bodies = active_bodies

    def get_common_bodies(self, other: 'ModifyMultiBodyStep') -> list[Body]:
        return [body for body in other.bodies if body in self.bodies]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModifyMultiBodyStep):
            return False
        return len(self.bodies) == len(other.bodies) and all(body == body_ for body, body_ in zip(other.bodies, self.bodies)) and self.step == other.step

    @property
    def identifier(self) -> str | None:
        return self.step.identifier

    @property
    def instruction(self) -> str:
        res = self.step.instruction
        if len(self.bodies) > 1:
            res += f" Wiederhole für {self.bodies_str}."
        return res

    @property
    def bodies_str(self) -> str:
        """Print a string that lists all the bodies in this step comma separated.

        Bodies are sorted alphanumerically.
        Consecutive strs of the form `x.y` are joined together (e.g. 1.4,1.5,1.6 -> 1.4-1.6)
        """
        bodies_strs = sorted([body.identifier for body in self.bodies])
        pattern = re.compile(r'[8-9|1[0-3][.][0-9|1[0-5]')
        nrs_list = [
            [int(nr) for nr in body_str.split('.')] if re.search(pattern, body_str) else None
            for body_str in bodies_strs
        ]

        bodies_str = ""
        prev_nrs = None
        for body_str, body_nrs in zip(bodies_strs, nrs_list):
            if body_nrs is None:
                bodies_str += "," + body_str
                prev_nrs = None
                continue
            if prev_nrs is None:
                bodies_str += "," + body_str
                prev_nrs = body_nrs
                continue
            if body_nrs[0] == prev_nrs[0] and body_nrs[1] == (prev_nrs[1] + 1):
                prev_nrs = body_nrs
                continue
            bodies_str += "-" + ".".join([str(nr) for nr in prev_nrs])
            prev_nrs = body_nrs
            bodies_str += "," + body_str
        if prev_nrs is not None:
            bodies_str += "-" + ".".join([str(nr) for nr in prev_nrs])

        return bodies_str[1:]

    @property
    def view_box(self) -> ViewBox:
        return self.step.view_box

    @property
    def view_box_closeup(self) -> ViewBox:
        return self.step.view_box_closeup

    def draw(
            self,
            group: SizedGroup,
            x=0,
            y=0,
            active: bool = True,
            dimensions: bool = True,
            close_up: bool = False,
            faded: bool = False,
            dim_ref_pt: tuple[float, float] | None = None
    ) -> None:
        # if self._active_bodies is not None:
        #     faded |= set(self._active_bodies).issubset(self.bodies)
        self.step.draw(group, x, y, active, dimensions, close_up, faded, dim_ref_pt)


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
    def __init__(self, body: Face, step: Step, ref_x_opposite: bool = False, ref_y_opposite: bool = False) -> None:
        super().__init__(step.identifier, body, step)
        self.ref_x_opposite = ref_x_opposite
        self.ref_y_opposite = ref_y_opposite

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

    def draw(
        self,
        group: SizedGroup,
        x=0,
        y=0,
        active: bool = True,
        dimensions: bool = True,
        close_up: bool = False,
        faded: bool = False,
        dim_ref_pt: tuple[float, float] | None = None
    ) -> None:
        if self._active_bodies is not None:
            faded |= set(self._active_bodies).issubset({self.body})
        self.face.draw(group, x, y)

        dim_ref_pt = (
            self.face.width if self.ref_x_opposite else 0.0,
            self.face.height if self.ref_y_opposite else 0.0,
        )
        self.step.draw(group, x, y, active, dimensions, close_up, faded, dim_ref_pt)


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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bar):
            return False
        return other.width == self.width and other.height == self.height and other.length == self.length

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
    def __init__(
        self,
        bar: Bar,
        face_identifier: str,
        step: Step,
        ref_x_opposite: bool = False,
        ref_y_opposite: bool = False,
    ) -> None:
        super().__init__(step.identifier, bar, step)
        self.face_identifier = face_identifier
        self.face = self.bar[face_identifier]
        self.ref_x_opposite = ref_x_opposite
        self.ref_y_opposite = ref_y_opposite

        self.padding = 10
        self.layout_width = math.ceil(self.bar.length)
        self.layout_height = math.ceil(2 * self.bar.height + 2 * self.bar.width + 3 * self.padding)
        self.ys = {}
        y = 0
        for key, face in self.bar.faces.items():
            self.ys[key]  = y
            y += face.height + self.padding

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModifyBarStep):
            return False
        return self.bar == other.bar and self.face_identifier == other.face_identifier and self.step == other.step

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
        offset = -FACE_ANNOTATION_OFFSET - 50
        return ViewBox(offset, 0, self.layout_width - offset, self.layout_height)

    @property
    def view_box_closeup(self) -> ViewBox:
        x0 = self.step.view_box_closeup.x
        y0 = min(self.step.view_box_closeup.y, self.face.view_box.y)
        x1 = x0 + self.step.view_box_closeup.width
        y1 = max(self.step.view_box_closeup.y, self.face.view_box.y + self.face.view_box.height)
        return ViewBox(x0, y0 - self.ys[self.face_identifier], x1 - x0, y1 - y0)

    def draw(
        self,
        group: SizedGroup,
        x=0,
        y=0,
        active: bool = True,
        dimensions: bool = True,
        close_up: bool = False,
        faded: bool = False,
        dim_ref_pt: tuple[float, float] | None = None,
    ) -> None:
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
                    fill='red' if face.identifier == self.face_identifier else 'black',
                    text_anchor='end',
                    dominant_baseline='middle',
                    font_family=FONT_FAMILY_TECH,
                ))

            if key == self.face_identifier:
                dim_ref_pt = (
                    self.face.width if self.ref_x_opposite else 0.0,
                    self.face.height if self.ref_y_opposite else 0.0,
                )
                self.step.draw(group, x, y_face, active, dimensions, faded=faded, dim_ref_pt=dim_ref_pt)
                self._transfer_step_to_other_faces(group, x, y, active, dimensions, faded=faded)

    def _transfer_step_to_other_faces(self, group: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True, faded: bool = False) -> None:
        fill_opacity = 0.4 if faded else 1
        stroke_opacity = 0.4 if faded else 1
        if isinstance(self.step, DrillHole):
            if self.step.through:
                # transfer step to opposite face
                face = self.bar.get_opposite_face(self.face_identifier)
                self.step.clone(y=face.height - self.step.y).draw(group, x, y + self.ys[face.identifier], False, False, faded=faded)

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
                        fill_opacity=0.25 * fill_opacity,
                    ))
                    y0 = y_face if face_sign >= 0 else y_face + face.height
                    y1 = y0 + face_sign * height
                    group.append(draw.Line(
                        x + self.step.x - self.step.radius,
                        y1,
                        x + self.step.x + self.step.radius,
                        y1,
                        stroke='gray',
                        stroke_opacity=stroke_opacity,
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
