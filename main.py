from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.steps.drilling import  DrillHole
from technical_instruction_generator.steps.face_handling import Face, ModifyFaceStep


def main() -> None:
    face = Face("A", 1000, 100)

    manual = Instructions(
        title="Tims Abenteuerbett",
        steps=[
            ModifyFaceStep(face, DrillHole(10, 10, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyFaceStep(face, DrillHole(10, 90, 4)),
        ]
    )
    manual.draw('output/instructions.pdf')


if __name__ == "__main__":
    main()