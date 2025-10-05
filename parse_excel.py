import re
from itertools import product

import pandas as pd

from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.steps.bodies import Bar, ModifyBarStep, ModifyMultiBodyStep
from technical_instruction_generator.steps.drilling import DrillHole

CUTS_MEAS_COL = 'Maße [L x B x H]'


def get_identifiers(identifier: str) -> list[str]:
    if '-' in identifier:
        identifier_strs = identifier.split('-')
        major = int(identifier_strs[0].split(".")[0])
        minors = range(int(identifier_strs[0].split(".")[1]), int(identifier_strs[1].split(".")[1]) + 1)
        identifiers = [f"{major}.{minor}" for minor in minors]
    elif '+' in identifier:
        identifiers = identifier.split('+')
    else:
        identifiers = [identifier]
    return identifiers

def parse_bodies(df: pd.DataFrame) -> list[Bar]:
    bodies = []

    pattern = r"\b(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)\b"
    for _, row in df.iterrows():
        if not re.search(pattern, row[CUTS_MEAS_COL]):
            continue
        identifiers = get_identifiers(row['Teil'])
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

        identifiers = get_identifiers(row['Teil'])
        face_identifier = row['Seite']
        hole_identifier = row['Bohrung']
        x = float(row['y'])
        y = float(row['x'])

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
                    DrillHole(x, y, diam, depth, through),
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


def merge_steps(steps: list[ModifyBarStep]) -> list[ModifyBarStep | ModifyMultiBodyStep]:
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


def main():
    path = 'D:/Dokumente/Tim/Hochbett.xlsx'
    df_cut = pd.read_excel(path, sheet_name='Schnitte')
    df_drill = pd.read_excel(path, sheet_name='Bohrungen')

    bodies = parse_bodies(df_cut)
    steps = parse_drillings(df_drill, bodies)
    steps = merge_steps(steps)

    for step in steps:
        print(step.get_instruction())

    print(len(steps))

    instructions = Instructions(steps, 'Tims Hochbett (Standardbohrungen)')
    instructions.save_pdf('output/standardbohrungen.pdf')


if __name__ == "__main__":
    main()