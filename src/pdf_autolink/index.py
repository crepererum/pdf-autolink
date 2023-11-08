from __future__ import annotations

from bisect import bisect
from dataclasses import dataclass

import fitz
import structlog

__logger__ = structlog.get_logger()


@dataclass
class TextPosition:
    page: int
    page_pos: fitz.Rect
    txt_offset: int


@dataclass
class TextIndex:
    text: str
    positions: list[TextPosition]

    def extract(doc: fitz.Document) -> TextIndex:
        text = ""
        positions = []
        for i, page in enumerate(doc):
            __logger__.info("index page", page=i + 1, pages=len(doc))
            for word in page.get_text("words"):
                (x0, y0, x1, y1, word, block_no, line_no, word_no) = word
                positions.append(TextPosition(i, fitz.Rect(x0, y0, x1, y1), len(text)))
                text += word
                text += " "

        return TextIndex(text, positions)

    def find_indices(self, start: int, end: int) -> tuple[int, int]:
        idx_start = bisect(self.positions, start, key=lambda p: p.txt_offset) - 1
        idx_end = bisect(
            self.positions, end - 1, lo=idx_start, key=lambda p: p.txt_offset
        )
        assert idx_end > idx_start

        return (idx_start, idx_end)
