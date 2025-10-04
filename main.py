from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.steps.drilling import  DrillHole
from technical_instruction_generator.steps.bodies import Face, ModifyFaceStep, Bar, ModifyBarStep


def main() -> None:
    face = Face("A", 1000, 100)

    bar = Bar("1.1", 42, 48, 1000)

    manual = Instructions(
        title="Tims Abenteuerbett",
        steps=[
            # ModifyFaceStep(face, DrillHole(100, 10, 4)),
            # ModifyFaceStep(face, DrillHole(10, 90, 4)),
            # ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyBarStep(bar, 'D', DrillHole(20, 21, 20, 12, False)),
        ]
    )
    manual.save_svgs('output/instructions.svg')
    manual.save_pdf('output/instructions.pdf')


if __name__ == "__main__":
    main()