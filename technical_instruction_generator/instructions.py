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

from .layout import Alignment, ExpandBehaviour, LayoutDirection, LinearLayout, Page, ScaleBehaviour, SizedGroup
from .style import FONT_FAMILY_TEXT, INSTRUCTION_BOX_STROKE_COLOR
from .dimensions import (
    A4_HEIGHT, A4_WIDTH, FONT_SIZE_BASE, FONT_SIZE_TITLE, HEADER_TEXT_OFFSET_X, HEADER_SIZE, INSTRUCTION_BOX_MARGIN,
    INSTRUCTION_BOX_PADDING,
    MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TITLE, MARGIN_TOP, MARGIN_BOTTOM,
)
from .steps.base import Step
from .utils import combined_size, Text


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
            step_group = self._generate_step(step_idx)

            if not page.layout.add_group(step_group):
                pages.append(page)
                page_idx += 1
                page = Page(page_idx)
                if not page.layout.add_group(step_group):
                    raise ValueError(f"Unable to add step {step_idx} `{self.steps[step_idx].instruction}` to new page!")

        pages.append(page)

        return pages

    def _generate_step(self, step_idx: int) -> SizedGroup:
        step = self.steps[step_idx]
        step_id = step.identifier or f"{step_idx + 1}"

        group = SizedGroup(width=A4_WIDTH - MARGIN_LEFT - MARGIN_RIGHT, height=600)
        # , size_behaviour=ExpandBehaviour(direction=LayoutDirection.HORIZONTAL, keep_aspect_ratio=False)
        # TODO: actaully want to auto resize this before continuing

        group.append(draw.Rectangle(0, 0, group.width, group.height, fill='white', stroke=INSTRUCTION_BOX_STROKE_COLOR,
                                    stroke_width=2, rx='5', ry='5'))

        # add instructions
        group.append(draw.Line(0, HEADER_SIZE, group.width, HEADER_SIZE, stroke=INSTRUCTION_BOX_STROKE_COLOR))
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
        group.append(text)

        steps_layout = LinearLayout(width=group.width - 2 * INSTRUCTION_BOX_PADDING, height=group.height - HEADER_SIZE - 2 * INSTRUCTION_BOX_PADDING, alignment=Alignment.CENTER, direction=LayoutDirection.HORIZONTAL, padding=5)
        group.append(draw.Use(steps_layout, INSTRUCTION_BOX_PADDING, HEADER_SIZE + INSTRUCTION_BOX_PADDING))

        # add steps
        width, height = combined_size([step.size for step in self.steps])
        full_view = SizedGroup(width=width, height=height, transform=f'scale(1,-1) translate(0,-{height})')
        for step_ in self.steps[:-step_idx]:
            step_.draw(full_view, active=False)
        step.draw(full_view, active=True)

        steps_layout.add_group(full_view, size_behaviour=ScaleBehaviour())

        return group

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
