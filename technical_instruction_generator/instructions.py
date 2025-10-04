import os
from pathlib import Path
from tkinter.constants import HORIZONTAL

import drawsvg as draw
from drawsvg import Drawing, Group
from lxml import etree
from svglib.svglib import SvgRenderer
from svglib.svglib import Drawing as SvglibDrawing
from reportlab.graphics import renderPDF
from reportlab.graphics.renderbase import renderScaledDrawing
from reportlab.pdfgen.canvas import Canvas

from .layout_base import Alignment, ExpandBehaviour, LayoutDirection, ScaleBehaviour, SizedGroup
from .layout import  LinearLayout, Page
from .steps.bodies import ModifyBodyStep, ModifyMultiBodyStep
from .steps.views import CloseUpView, FullView
from .style import FONT_FAMILY_TEXT, INSTRUCTION_BOX_STROKE_COLOR
from .dimensions import (
    CLOSE_UP_PADDING, FONT_SIZE_BASE,
    HEADER_TEXT_OFFSET_X,
    HEADER_SIZE,
    INSTRUCTION_BOX_PADDING,
)
from .steps.base import Step


class Instructions:
    def __init__(self, steps: list[Step], title: str | None = None) -> None:
        self.steps = steps
        self.title = title

        self._etree_parser = etree.XMLParser(remove_comments=True, recover=True, resolve_entities=False)

    def save_svgs(self, path: str | Path | os.PathLike) -> None:
        if not isinstance(path, Path):
            path = Path(path)

        path.parent.mkdir(exist_ok=True)

        for idx, page in enumerate(self._generate_svgs()):
            page.drawing.save_svg(path.parent / f"{path.stem}_{idx + 1:03d}.svg")

    def save_pdf(self, path: str | Path | os.PathLike) -> None:
        self._save_pdf(path, self._generate_svgs())

    def _generate_svgs(self) -> list[Page]:
        pages: list[Page] = []

        # compile SVGs
        page_idx = 0
        page = Page(page_idx, self.title)
        for step_idx in range(len(self.steps)):
            if not self._add_step(page, step_idx):
                pages.append(page)
                page_idx += 1
                page = Page(page_idx)
                if not self._add_step(page, step_idx):
                    raise ValueError(f"Unable to add step {step_idx} `{self.steps[step_idx].instruction}` to new page!")

        pages.append(page)

        return pages

    def _add_step(self, page: Page, step_idx: int) -> bool:
        step = self.steps[step_idx]
        steps = self.steps[:(step_idx + 1)]
        step_id = step.identifier or f"{step_idx + 1}"

        box = SizedGroup(width=None, height=400)
        size_behaviour = ExpandBehaviour(direction=LayoutDirection.HORIZONTAL, keep_aspect_ratio=False)
        if not page.layout.add_group(box, size_behaviour):
            return False

        box.append(draw.Rectangle(0, 0, box.width, box.height, fill='white', stroke=INSTRUCTION_BOX_STROKE_COLOR,
                                    stroke_width=2, rx='5', ry='5'))

        # add instructions
        box.append(draw.Line(0, HEADER_SIZE, box.width, HEADER_SIZE, stroke=INSTRUCTION_BOX_STROKE_COLOR))
        text = draw.Text(
            f"Schritt {step_id}:",
            FONT_SIZE_BASE,
            HEADER_TEXT_OFFSET_X,
            HEADER_SIZE / 2,
            dominant_baseline="middle",
            font_weight='bold',
            font_family=FONT_FAMILY_TEXT,
        )
        text.append(draw.TSpan(step.instruction, dx=5, font_weight='normal'))
        box.append(text)

        # add layout containing steps
        x = INSTRUCTION_BOX_PADDING
        y = HEADER_SIZE + INSTRUCTION_BOX_PADDING
        width = box.width - 2 * INSTRUCTION_BOX_PADDING
        height = box.height - HEADER_SIZE - 2 * INSTRUCTION_BOX_PADDING
        step_layout = LinearLayout(
            width=width,
            height=height,
            alignment=Alignment.CENTER,
            direction=LayoutDirection.HORIZONTAL,
            padding=32,
        )
        box.append(draw.Use(step_layout, x, y))

        # add step views
        if isinstance(step, ModifyBodyStep):
            steps = [
                step_ for step_ in steps
                if (isinstance(step_, ModifyBodyStep) and step_.body == step.body)
                or (isinstance(step_, ModifyMultiBodyStep) and step in step_.bodies)
            ]
            for step_ in steps[:-1]:
                step.set_active_body(step_.body)
        elif isinstance(step, ModifyMultiBodyStep):
            steps = [
                step_ for step_ in steps
                if (isinstance(step_, ModifyBodyStep) and step_.body in step.bodies)
                or (isinstance(step_, ModifyMultiBodyStep) and step.get_common_bodies(step_))
            ]
            for step_ in steps[:-1]:
                step_.set_active_bodies(step.bodies)
        else:
            steps = [step]
        step_layout.add_view(CloseUpView(steps, padding=(CLOSE_UP_PADDING, 0)), size_behaviour=ScaleBehaviour())
        step_layout.add_view(FullView(steps), size_behaviour=ScaleBehaviour())

        return True

    def _save_pdf(self, path: Path, pages: list[Page]) -> None:
        if not pages:
            raise "Cannot convert empty drawings to PDF!"

        # initialize canvas
        d = renderScaledDrawing(self._to_pdf_drawing(pages[0].drawing))
        pdf_canvas = Canvas(str(path))
        pdf_canvas.setTitle("")
        pdf_canvas.setPageSize((d.width, d.height))

        for page in pages:
            renderPDF.draw(self._to_pdf_drawing(page.drawing), pdf_canvas, 0, 0)
            pdf_canvas.showPage()

        pdf_canvas.save()

    def _to_pdf_drawing(self, drawing: Drawing) -> SvglibDrawing:
        return SvgRenderer("").render(etree.fromstring(drawing.as_svg().encode("utf-8"), parser=self._etree_parser))
