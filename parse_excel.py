import dataclasses
import math
import re
from itertools import product

import pandas as pd

from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.layout_base import LayoutDirection
from technical_instruction_generator.steps.bodies import Bar, CutFaceStep, Face, ModifyBarStep, ModifyMultiBodyStep, \
    MultiCutFaceStep
from technical_instruction_generator.steps.drilling import DrillHole

CUTS_MEAS_COL = 'Maße [L x B x H]'
DIMENSIONS_OFFSET_X = 832.5


def get_identifiers(identifier: str) -> list[str]:
    if ',' in identifier:
        return sum([get_identifiers(x) for x in identifier.split(',')], [])
    if '+' in identifier:
        return sum([get_identifiers(x) for x in identifier.split('+')], [])
    if '-' in identifier:
        identifier_strs = identifier.split('-')
        major = int(identifier_strs[0].split(".")[0])
        minors = range(int(identifier_strs[0].split(".")[1]), int(identifier_strs[1].split(".")[1]) + 1)
        return [f"{major}.{minor}" for minor in minors]
    return [identifier]


def parse_bodies(df: pd.DataFrame) -> list[Bar]:
    bodies = []

    pattern = r"\b(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\b"
    for _, row in df.iterrows():
        if not re.search(pattern, str(row[CUTS_MEAS_COL])):
            continue
        identifiers = get_identifiers(str(row['Teil']))
        length, width, height = row[CUTS_MEAS_COL].split(" x ")
        bodies.extend([
            Bar(identifier, float(height), float(width), float(length))
            for identifier in identifiers
        ])

    return bodies


def parse_drillings(df: pd.DataFrame, bodies: list[Bar]) -> list[ModifyBarStep]:
    steps = []

    for _, row in df.iterrows():
        if row['manual'] == 'x':
            continue

        identifiers = get_identifiers(str(row['Teil']))
        face_identifier = str(row['Seite'])
        hole_identifier = str(row['Bohrung'])
        x = float(str(row['y']))
        y = float(str(row['x']))

        drill_strs = row['Typ'].split(";")

        for identifier, drill_str in product(identifiers, drill_strs):
            # select body from list
            bodies_list_ = [body_ for body_ in bodies if body_.identifier == identifier]
            assert len(bodies_list_) == 1
            bar = bodies_list_[0]
            face = bar[face_identifier]

            # parse diameter, depth and whether hole is through
            diam, depth = drill_str.replace("U", "").split("x")
            diam = float(diam)
            through = not "U" in drill_str
            depth = 0 if through else float(depth)

            steps.append(
                ModifyBarStep(
                    bar,
                    face_identifier,
                    DrillHole(x, y, diam, depth, through, dimensions_offset_x=DIMENSIONS_OFFSET_X),
                    ref_x_opposite=x > face.width / 2,
                )
            )

    return steps


def get_base_bars(steps: list[ModifyBarStep]) -> list[Bar]:
    # get base shapes (width x height)
    shapes = {(step.bar.width, step.bar.height) for step in steps}

    # get max. length bar for each shape
    return [
        max(
            [step.bar for step in steps if step.bar.width == shape[0] and step.bar.height == shape[1]],
            key=lambda b: b.length
        )
        for shape in shapes
    ]


def merge_drill_steps(steps: list[ModifyBarStep]) -> list[ModifyBarStep | ModifyMultiBodyStep]:
    steps = sorted(
        steps,
        key=lambda s: (
            s.step.through and s.step.diameter > 13,
            s.step.y,
            s.bar.length - s.step.x if s.ref_x_opposite else s.step.x,
            s.step.through,
            s.step.diameter,
            s.step.depth,
            s.face_identifier,
        ))

    res = []
    while steps:
        step = steps.pop()
        steps_ = [step_ for step_ in steps if step_ == step]
        for step_ in steps_:
            steps.remove(step_)
        bodies = [step.body] + [step_.body for step_ in steps_]
        res.append(ModifyMultiBodyStep(bodies, step))

    res = sorted(
        res,
        key=lambda s: (
            s.step.step.through and s.step.step.diameter > 13,
            s.step.step.y,
            s.step.bar.length - s.step.step.x if s.step.ref_x_opposite else s.step.step.x,
            s.step.step.through,
            s.step.step.diameter,
            s.step.step.depth,
            s.step.face_identifier,
        ))

    return res


def parse_cuts(df: pd.DataFrame) -> dict[str, list[Face]]:
    faces = {}
    for _, row in df.iterrows():
        measure_str = str(row['Maße [L x B x H]'])
        parts = measure_str.split(" x ")
        if len(parts) == 3:
            l, b, h = parts
        else:
            l, b = parts
            b = b.replace("D", "")
        identifiers = get_identifiers(str(row['Teil']))
        count = int(str(row['Anzahl']))
        if measure_str not in faces:
            faces[measure_str] = []
        faces[measure_str].extend([
            Face(identifier, int(l), int(b))
            for identifier in identifiers
            for _ in range(count)
        ])

    return faces


def parse_faces_base(df: pd.DataFrame) -> list[Face]:
    measure_strs = {str(row['Maße [Basis]']) for _, row in df.iterrows()}
    faces = []
    for measure_str in measure_strs:
        l, b = measure_str.split(" x ")
        faces.append(Face(measure_str, int(l), int(b)))
    return faces


def get_cuts(faces_dict: dict[str, list[Face]], faces_base: list[Face], mat_sep: str = '-') -> tuple[pd.DataFrame, list[CutFaceStep]]:
    faces = [face for _, faces in faces_dict.items() for face in faces]
    cuts = []

    data = []

    # width: 28
    width = 28
    faces_ = [face for face in faces if face.height == width]
    base = [face for face in faces_base if face.height == width][0]
    res = get_cuts_1d(faces_, base, mat_sep=mat_sep)
    cuts.extend(res.steps)
    data.append([base.identifier, f"{base.width}x{base.height}", res.base_count])

    # width: 300
    widths = [208, 210]
    faces_ = [face for face in faces if face.height in widths]
    base = [face for face in faces_base if face.height == 300][0]
    res = get_cuts_1d(faces_, base, mat_sep=mat_sep)
    cuts.extend(res.steps)
    data.append([base.identifier, f"{base.width}x{base.height}", res.base_count])

    # widths: 48, 70
    for width in [48, 70]:
        faces_ = [face for face in faces if face.height == width]
        base = [face for face in faces_base if face.height == width][0]
        res = get_cuts_1d(faces_, base, mat_sep=mat_sep)
        cuts.extend(res.steps)
        data.append([base.identifier, f"{base.width}x{base.height}", res.base_count])

    # widths: 200, 194, 160, 100
    widths = [200, 194, 160]
    faces_ = [face for face in faces if face.height in widths]
    base = [face for face in faces_base if face.height == 200][0]
    res_200 = get_cuts_1d(faces_, base, mat_sep=mat_sep)
    cuts.extend(res_200.steps)

    # width: 100 [uses rest from width 200]
    faces_ = [face for face in faces if face.height == 100]
    materials = []
    while res_200.rest:
        material = res_200.rest.pop(0)
        if material.width < min(face.width for face in faces_):
            continue
        cuts.append(CutFaceStep(material, material.height / 2, direction=LayoutDirection.HORIZONTAL, identifier=material.identifier))
        base_identifier, material_identifier = material.identifier.split(mat_sep)
        material_idx, cut_idx = material_identifier.split(".")
        for _ in range(2):
            cut_idx = int(cut_idx) + 1
            materials.append(Face(base_identifier + f"{mat_sep}{material_idx}.{cut_idx}", material.width, material.height / 2))
    res_100_base = Face(base.identifier + "|2", base.width, 100)
    res_100 = get_cuts_1d(faces_, res_100_base, materials=materials, start_idx=res_200.base_count + 1, mat_sep=mat_sep)
    res_100_base_count = math.ceil(res_100.base_count / 2)
    cuts.extend([
        CutFaceStep(base, base.height / 2, direction=LayoutDirection.HORIZONTAL, identifier=base.identifier + "|2")
        for idx in range(res_100_base_count)
    ])
    cuts.extend(res_100.steps)
    data.append([base.identifier, f"{base.width}x{base.height}", res_200.base_count + res_100_base_count])

    # height: 194
    faces = [
        Face('7.1', 875, 200),
        Face('7.2', 976, 200),
    ]
    for face in faces:
        cuts.append(CutFaceStep(face, 194, direction=LayoutDirection.HORIZONTAL, identifier=face.identifier))

    # height: 160
    faces = [
                Face(identifier, 916, 200)
                for identifier in ['11.1', '11.4']
            ] + [
                Face(identifier, 252, 200)
                for identifier in ['11.2', '11.3']
            ]
    for face in faces:
        cuts.append(CutFaceStep(face, 160, direction=LayoutDirection.HORIZONTAL, identifier=face.identifier))

    # generate material table
    df = pd.DataFrame(data, columns=["ID", "Maße [L x B]", "#"])
    df = df.sort_values("#", ascending=False)

    return df, cuts


@dataclasses.dataclass
class CutsResult:
    base_count: int
    steps: list[CutFaceStep]
    rest: list[Face]


def get_cuts_1d(
    faces: list[Face],
    base: Face,
    materials: list[Face] | None = None,
    start_idx: int = 1,
    cut_width: int = 3,
    mat_sep: str = '-',
) -> CutsResult:
    base_count = 0
    cuts = []
    idx = start_idx
    if not materials:
        materials = [Face(base.identifier + f"{mat_sep}{idx}.1", base.width, base.height)]
        base_count += 1
    faces = sorted(faces, key=lambda f: f.width, reverse=True)
    while faces:
        face = faces.pop(0)
        materials = sorted(materials, key=lambda m: m.width)
        materials_ = [m for m in materials if m.width >= face.width]
        if not materials_:
            idx += 1
            material = Face(base.identifier + f"{mat_sep}{idx}.1", base.width, base.height)
            base_count += 1
            cuts.append(CutFaceStep(material, face.width, identifier=face.identifier))
            rest_width = base.width - face.width - cut_width
            materials.append(Face(base.identifier + f"{mat_sep}{idx}.2", rest_width, base.height))
            continue
        material = materials_.pop(0)
        materials.remove(material)
        cuts.append(CutFaceStep(material, face.width, identifier=face.identifier))
        base_identifier, material_identifier = material.identifier.split(mat_sep)
        material_idx, cut_idx = material_identifier.split(".")
        cut_idx = int(cut_idx) + 1
        rest_width = material.width - face.width - cut_width
        materials.append(Face(base_identifier + f"{mat_sep}{material_idx}.{cut_idx}", rest_width, base.height))

    return CutsResult(base_count, cuts, materials)


def merge_cuts(steps: list[CutFaceStep]) -> list[CutFaceStep | MultiCutFaceStep]:
    res = []
    steps = steps[:]  # copy list
    while steps:
        steps_ = [steps.pop(0)]
        while steps and steps[0] == steps_[-1]:
            steps_.append(steps.pop(0))
        if len(steps_) == 1:
            res.append(steps_[0])
        else:
            res.append(MultiCutFaceStep(steps_[0], [step.identifier for step in steps_]))
    return res


def main_drillings():
    path = 'D:/Dokumente/Tim/Hochbett.xlsx'
    df_cut = pd.read_excel(path, sheet_name='Schnitte')
    df_drill = pd.read_excel(path, sheet_name='Bohrungen')
    bodies = parse_bodies(df_cut)
    steps = parse_drillings(df_drill, bodies)
    steps = merge_drill_steps(steps)

    print("Schritte:")
    for step in steps:
        print(f"\t{step.get_instruction()} -> {step.identifier}")

    print(f"\nAnzahl Schritte: {len(steps)}")

    instructions = Instructions(steps, 'Tims Hochbett (Bohrungen)')
    instructions.save_pdf('output/2_bohrungen.pdf')


def main_cuts():
    path = 'D:/Dokumente/Tim/Hochbett.xlsx'
    df_cut = pd.read_excel(path, sheet_name='Schnitte')

    faces_dict = parse_cuts(df_cut)
    faces_base = parse_faces_base(df_cut)
    base_counts, steps = get_cuts(faces_dict, faces_base)
    steps = merge_cuts(steps)

    print("Schritte:")
    for step in steps:
        if isinstance(step, CutFaceStep):
            print(f"\t{step.get_instruction()} -> {step.identifier}")
        else:
            print(f"\t{step.get_instruction()}")
    print(f"\nAnzahl Schritte: {len(steps)}")

    print("\n\nMaterialien:")
    for face in faces_base:
        print(f"\t{face.width}x{face.height}: {face}")

    print("\n\nBenötigte Teile:")
    for measure_str, faces in faces_dict.items():
        faces_str = ",".join(str(face) for face in faces)
        print(f"\t{measure_str.replace(" ", "")}: {faces_str}")

    print("\n\nKaufliste:")
    print(base_counts)

    instructions = Instructions(steps, 'Tims Hochbett (Schnitte)')
    instructions.save_pdf('output/1_schnitte.pdf')


if __name__ == "__main__":
    # main_cuts()
    main_drillings()