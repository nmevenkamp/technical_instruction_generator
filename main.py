from technical_instruction_generator.instructions import Instructions
from technical_instruction_generator.steps.drilling import  DrillHole
from technical_instruction_generator.steps.bodies import Bar, ModifyBarStep, ModifyMultiBodyStep


def main() -> None:
    bar1 = Bar("1.1", 42, 48, 1000)
    bar2 = Bar("1.2", 42, 48, 768)
    bar3 = Bar("1.4", 42, 48, 1000)
    bar4 = Bar("1.5", 42, 48, 1000)
    bar5 = Bar("1.6", 42, 48, 1000)
    manual = Instructions(
        title="Tims Abenteuerbett",
        steps=[
            ModifyBarStep(bar1, 'D', DrillHole(200, 21, 20, 12, False)),
            # ModifyBarStep(bar1, 'D', DrillHole(200, 21, 7, )),
            ModifyBarStep(bar1, 'D', DrillHole(100, 21, 20, 12, False)),
            ModifyBarStep(bar2, 'D', DrillHole(20, 21, 20, 12, False)),
            ModifyMultiBodyStep([bar1, bar3], ModifyBarStep(bar1, 'B', DrillHole(400, 21, 16))),
            ModifyBarStep(bar3, 'D', DrillHole(20, 21, 4, )),
            ModifyMultiBodyStep([bar1, bar2, bar3, bar4, bar5], ModifyBarStep(bar1, 'D', DrillHole(100, 21, 8, ))),
        ]
    )
    manual.save_svgs('output/instructions.svg')
    manual.save_pdf('output/instructions.pdf')


if __name__ == "__main__":
    main()