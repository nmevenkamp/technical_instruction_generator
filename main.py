from classes import (
    DrillHole,
    Face,
    Manual,
    ModifyFaceStep,
)

def main() -> None:
    face = Face("A", 1000, 100)

    manual = Manual(steps=[
        ModifyFaceStep(face, DrillHole(10, 10, 4)),
        ModifyFaceStep(face, DrillHole(10, 90, 4)),
    ])
    manual.draw('output/manual.svg')


if __name__ == "__main__":
    main()