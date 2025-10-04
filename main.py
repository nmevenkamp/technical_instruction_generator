from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.steps.drilling import  DrillHole
from technical_instruction_generator.steps.bodies import Face, ModifyFaceStep, Bar, ModifyBarStep


def main() -> None:
    bar1 = Bar("1.1", 42, 48, 1000)
    bar2 = Bar("2.1", 42, 70, 768)
    manual = Instructions(
        title="Tims Abenteuerbett",
        steps=[
            # ModifyFaceStep(face, DrillHole(100, 10, 4)),
            # ModifyFaceStep(face, DrillHole(10, 90, 4)),
            # ModifyFaceStep(face, DrillHole(10, 90, 4)),
            ModifyBarStep(bar1, 'D', DrillHole(200, 21, 20, 12, False)),
            ModifyBarStep(bar1, 'D', DrillHole(200, 21, 7, )),
            ModifyBarStep(bar1, 'D', DrillHole(100, 21, 20, 12, False)),
            ModifyBarStep(bar2, 'D', DrillHole(20, 21, 20, 12, False)),
            ModifyBarStep(bar2, 'D', DrillHole(20, 21, 4, )),
        ]
    )
    manual.save_svgs('output/instructions.svg')
    manual.save_pdf('output/instructions.pdf')


if __name__ == "__main__":
    main()