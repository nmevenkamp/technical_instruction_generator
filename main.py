from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.steps.drilling import  DrillHole
from technical_instruction_generator.steps.bodies import Bar, ModifyBarStep, ModifyMultiBodyStep


def main() -> None:
    bar1 = Bar("1.1", 42, 48, 1000)
    bar2 = Bar("2.1", 42, 70, 768)
    bar3 = Bar("3.1", 42, 48, 1000)
    manual = Instructions(
        title="Tims Abenteuerbett",
        steps=[
            ModifyBarStep(bar1, 'D', DrillHole(200, 21, 20, 12, False)),
            ModifyBarStep(bar1, 'D', DrillHole(200, 21, 7, )),
            ModifyBarStep(bar1, 'D', DrillHole(100, 21, 20, 12, False)),
            ModifyBarStep(bar2, 'D', DrillHole(20, 21, 20, 12, False)),
            ModifyMultiBodyStep([bar1, bar3], ModifyBarStep(bar1, 'B', DrillHole(400, 21, 16))),
            ModifyBarStep(bar3, 'D', DrillHole(20, 21, 4, )),
        ]
    )
    manual.save_svgs('output/instructions.svg')
    manual.save_pdf('output/instructions.pdf')


if __name__ == "__main__":
    main()