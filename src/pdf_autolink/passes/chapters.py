from __future__ import annotations

import re

import fitz

from ..index import TextIndex
from ..link import create_links


def mark_chapters(doc: fitz.Document, index: TextIndex) -> None:
    # page for every top-level chapter
    chapter_targets = [
        (dst["page"], dst["to"])
        for lvl, _title, _page, dst in doc.get_toc(simple=False)
        if lvl == 1
    ]

    for match in re.finditer(r"chapter\s+([0-9]+)", index.text, re.I):
        # find target page
        chapter_number = int(match.group(1))
        (page_number, pos) = chapter_targets[chapter_number - 1]

        # build marker rects
        create_links(doc, index, match.start(), match.end(), page_number, pos)
