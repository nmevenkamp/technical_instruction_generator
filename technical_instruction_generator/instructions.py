import os
from pathlib import Path

import drawsvg as draw

from .steps.base import Step
from .utils import combined_size


class Instructions:
    def __init__(self, steps: list[Step]) -> None:
        self.steps = steps

    def draw(self, path: str | Path | os.PathLike):
        if not isinstance(path, Path):
            path = Path(path)

        path.parent.mkdir(exist_ok=True)

        width, height = combined_size([step.size for step in self.steps])

        for i in range(len(self.steps)):
            drawing = draw.Drawing(width, height, origin=(0, 0), transform='scale(1,-1)')
            drawing.append(draw.Rectangle(0, 0, width, height, fill="white"))

            for step in self.steps[:-i]:
                step.draw(drawing, active=False)
            self.steps[i].draw(drawing, active=True)

            drawing.save_svg(path.parent / f"{path.stem}_{i + 1:03d}.svg")
