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
        self._page_idx = -1
        self._y_group = 0
        self._drawing: Drawing | None = None

    def draw(self, path: str | Path | os.PathLike):
        if not isinstance(path, Path):
            path = Path(path)

        path.parent.mkdir(exist_ok=True)

        # compile SVGs
        self._init_document(path)
        for i in range(len(self.steps)):
            step_id = self.steps[i].identifier or f"{i + 1}"

            w_steps, h_steps = combined_size([step.size for step in self.steps])
            w_box = A4_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
            h_box = h_steps + 2 * INSTRUCTION_BOX_PADDING + HEADER_SIZE
            x_box = -INSTRUCTION_BOX_PADDING
            y_box = -INSTRUCTION_BOX_PADDING

            group = Group(transform='scale(1,-1)')

            # add box
            group.append(draw.Rectangle(x_box, y_box, w_box, h_box, fill='white', stroke=INSTRUCTION_BOX_STROKE_COLOR, stroke_width=2, rx='5', ry='5'))

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
            text.append(draw.TSpan(self.steps[i].instruction, dx=5, font_weight='normal'))
            group.append(text)

            # add steps
            # TODO: only add steps performed on the same face of the same part
            for step in self.steps[:-i]:
                step.draw(group, active=False)
            self.steps[i].draw(group, active=True)

            if self._y_group + h_box > A4_HEIGHT - MARGIN_BOTTOM:
                self._finalize_page()

            self._drawing.append(draw.Use(group, MARGIN_LEFT, self._y_group + h_box))
            self._y_group += h_box + INSTRUCTION_BOX_MARGIN

        self._finalize_page()
        self._pdf_canvas.save()

    def _finalize_page(self) -> None:
        renderPDF.draw(self._get_pdf_drawing(), self._pdf_canvas, 0, 0)
        self._pdf_canvas.showPage()
        self._add_page()

    def _init_document(self, path: Path) -> None:
        self._page_idx = -1
        self._add_page()
        self._init_pdf(path)

    def _init_pdf(self, path: Path) -> None:
        d = renderScaledDrawing(self._get_pdf_drawing())
        self._pdf_canvas = Canvas(str(path))
        self._pdf_canvas.setTitle("")
        self._pdf_canvas.setPageSize((d.width, d.height))

    def _add_page(self) -> None:
        self._page_idx += 1
        w_canvas = A4_WIDTH
        h_canvas = A4_HEIGHT
        self._drawing = draw.Drawing(w_canvas, h_canvas, origin=(0, 0))
        self._drawing.append(draw.Rectangle(0, 0, w_canvas, h_canvas, fill='white'))
        self._drawing.append(draw.Text(f"{self._page_idx + 1}", FONT_SIZE_BASE, A4_WIDTH - 100, A4_HEIGHT - 100, text_anchor='end', font_weight='bold', font_family=FONT_FAMILY_TEXT))
        self._y_group = MARGIN_TOP

        if self._page_idx == 0 and self.title:
            self._drawing.append(draw.Text(self.title, FONT_SIZE_TITLE, A4_WIDTH / 2, MARGIN_TOP, text_anchor='middle', font_family=FONT_FAMILY_TEXT))
            self._y_group += MARGIN_TITLE

    def _get_pdf_drawing(self) -> SvglibDrawing:
        parser = etree.XMLParser(remove_comments=True, recover=True, resolve_entities=False)
        return SvgRenderer("").render(etree.fromstring(self._drawing.as_svg().encode("utf-8"), parser=parser))
