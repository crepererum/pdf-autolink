from __future__ import annotations

import re

import fitz
import structlog
from pydantic import BaseModel

from .interface import Pass
from ..config import JSON_DICT
from ..index import TextIndex
from ..link import create_links

__logger__ = structlog.get_logger()


class Config(BaseModel):
    pass


class ChaptersPass(Pass):
    def name(self) -> str:
        return "chapters"

    def run(self, doc: fitz.Document, index: TextIndex, config: JSON_DICT) -> None:
        config_typed = Config.parse_obj(config)
        self.run_typed(doc, index, config_typed)

    def run_typed(self, doc: fitz.Document, index: TextIndex, config: Config) -> None:
        # page for every top-level chapter
        chapter_targets = [
            (dst["page"], dst["to"])
            for lvl, _title, _page, dst in doc.get_toc(simple=False)
            if lvl == 1
        ]

        for match in re.finditer(r"chapter\s+([0-9]+)", index.text, re.I):
            # find target page
            chapter_number = int(match.group(1))

            if chapter_number <= 0 or chapter_number > len(chapter_targets):
                __logger__.warn(
                    "unknown chapter",
                    chapter=chapter_number,
                    n_chapters=len(chapter_targets),
                )
                continue
            (page_number, pos) = chapter_targets[chapter_number - 1]

            # build marker rects
            create_links(doc, index, match.start(), match.end(), page_number, pos)
