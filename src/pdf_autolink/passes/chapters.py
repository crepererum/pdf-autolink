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
    #: Pass order.
    #:
    #: Lower order passes run first.
    order: int = 10

    #: Enable pass.
    enabled: bool = True

    #: Regular expression for a chapter link.
    #:
    #: Must contain the named capture group `chapter_number` that refers to the chapter number.
    #:
    #: The regex is applied case-insensitive.
    chapter_regex: str = r"chapter\s+(?P<chapter_number>[0-9]+)"


class ChaptersPass(Pass):
    @classmethod
    def name(cls) -> str:
        return "chapters"

    def __init__(self, config: JSON_DICT) -> None:
        self.config = Config.parse_obj(config)

    def run(self, doc: fitz.Document, index: TextIndex) -> None:
        # page for every top-level chapter
        chapter_targets = [
            (dst["page"], dst["to"])
            for lvl, _title, _page, dst in doc.get_toc(simple=False)
            if lvl == 1
        ]

        marked = 0
        for match in re.finditer(self.config.chapter_regex, index.text, re.I):
            # find target page
            chapter_number = int(match.group("chapter_number"))

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

            marked += 1

        __logger__.info("marked chapters", num_links=marked)

    @property
    def order(self) -> int:
        return self.config.order

    @property
    def enabled(self) -> bool:
        return self.config.enabled
