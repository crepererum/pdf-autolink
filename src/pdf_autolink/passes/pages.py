from __future__ import annotations

import re

import fitz

from ..index import TextIndex
from ..link import create_links


def mark_pages(doc: fitz.Document, index: TextIndex) -> None:
    for match in re.finditer(r"page\s+([0-9]+)", index.text, re.I):
        # find target page
        page_label = match.group(1)
        page_numbers = doc.get_page_numbers(page_label)
        assert len(page_numbers) == 1, f"{page_label}, {page_numbers}"
        page_number = page_numbers[0]

        # build marker rects
        create_links(doc, index, match.start(), match.end(), page_number)
