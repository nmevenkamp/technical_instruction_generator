import os
from pathlib import Path

import drawsvg as draw
from drawsvg import Drawing, Group
from lxml import etree
from svglib.svglib import SvgRenderer
from svglib.svglib import Drawing as SvglibDrawing
from reportlab.graphics import renderPDF
from reportlab.graphics.renderbase import renderScaledDrawing
from reportlab.pdfgen.canvas import Canvas

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

        for idx, drawing in enumerate(self._generate_svgs()):
            drawing.save_svg(path.parent / f"{path.stem}_{idx + 1:03d}.svg")

    def save_pdf(self, path: str | Path | os.PathLike) -> None:
        self._save_pdf(path, self._generate_svgs())

    def _generate_svgs(self) -> list[Drawing]:
        pages = []

        # compile SVGs
        page_idx = 0
        page, y0 = self._generate_page(page_idx, self.title)
        for step_idx in range(len(self.steps)):
            step_group, h_box = self._generate_step(step_idx)

            if y0 + h_box > A4_HEIGHT - MARGIN_BOTTOM:
                pages.append(page)
                page_idx += 1
                page, y0 = self._generate_page(page_idx)

            page.append(draw.Use(step_group, MARGIN_LEFT, y0 + h_box))
            y0 += h_box + INSTRUCTION_BOX_MARGIN

        pages.append(page)

        return pages

    def _generate_step(self, step_idx: int) -> tuple[Group, float]:
        step = self.steps[step_idx]
        step_id = step.identifier or f"{step_idx + 1}"

        w_steps, h_steps = combined_size([step.size for step in self.steps])
        w_box = A4_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        h_box = h_steps + 2 * INSTRUCTION_BOX_PADDING + HEADER_SIZE
        x_box = -INSTRUCTION_BOX_PADDING
        y_box = -INSTRUCTION_BOX_PADDING

        group = Group(transform='scale(1,-1)')

        # add box
        group.append(draw.Rectangle(x_box, y_box, w_box, h_box, fill='white', stroke=INSTRUCTION_BOX_STROKE_COLOR,
                                    stroke_width=2, rx='5', ry='5'))

        # add instructions
        y = h_box - INSTRUCTION_BOX_PADDING - HEADER_SIZE
        group.append(draw.Line(x_box, y, x_box + w_box, y, stroke=INSTRUCTION_BOX_STROKE_COLOR))
        text = Text(
            f"Schritt {step_id}:",
            FONT_SIZE_BASE,
            -INSTRUCTION_BOX_PADDING + HEADER_TEXT_OFFSET_X,
            y + HEADER_SIZE / 2,
            dominant_baseline="middle",
            font_weight='bold',
            font_family=FONT_FAMILY_TEXT,
        )
        text.append(draw.TSpan(step.instruction, dx=5, font_weight='normal'))
        group.append(text)

        # add steps
        # TODO: only add steps performed on the same face of the same part
        for step_ in self.steps[:-step_idx]:
            step_.draw(group, active=False)
        step.draw(group, active=True)

        return group, h_box

    def _generate_page(self, page_idx: int = None, title: str = None) -> tuple[Drawing, float]:
        w_canvas = A4_WIDTH
        h_canvas = A4_HEIGHT

        drawing = draw.Drawing(w_canvas, h_canvas, origin=(0, 0))
        drawing.append(draw.Rectangle(0, 0, w_canvas, h_canvas, fill='white'))

        if page_idx is not None:
            drawing.append(
                draw.Text(f"{page_idx + 1}", FONT_SIZE_BASE, A4_WIDTH - 100, A4_HEIGHT - 100, text_anchor='end',
                          font_weight='bold', font_family=FONT_FAMILY_TEXT))

        y0 = MARGIN_TOP

        if title is not None:
            drawing.append(draw.Text(self.title, FONT_SIZE_TITLE, A4_WIDTH / 2, MARGIN_TOP, text_anchor='middle', font_family=FONT_FAMILY_TEXT))
            y0 += MARGIN_TITLE

        return drawing, y0

    def _save_pdf(self, path: Path, drawings: list[Drawing]) -> None:
        if not drawings:
            raise "Cannot convert empty drawings to PDF!"

        # initialize canvas
        d = renderScaledDrawing(self._to_pdf_drawing(drawings[0]))
        pdf_canvas = Canvas(str(path))
        pdf_canvas.setTitle("")
        pdf_canvas.setPageSize((d.width, d.height))

        for drawing in drawings:
            renderPDF.draw(self._to_pdf_drawing(drawing), pdf_canvas, 0, 0)
            pdf_canvas.showPage()

        pdf_canvas.save()

    def _to_pdf_drawing(self, drawing: Drawing) -> SvglibDrawing:
        return SvgRenderer("").render(etree.fromstring(drawing.as_svg().encode("utf-8"), parser=self._etree_parser))
