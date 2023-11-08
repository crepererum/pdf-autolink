from __future__ import annotations

import fitz

from .chapters import mark_chapters
from .pages import mark_pages
from .page_tables import mark_page_tables

from ..index import TextIndex


def run_all(doc: fitz.Document, index: TextIndex) -> None:
    mark_pages(doc, index)
    mark_chapters(doc, index)
    mark_page_tables(doc, index)
