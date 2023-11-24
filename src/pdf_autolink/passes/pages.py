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

    #: Regular expression for a page link.
    #:
    #: Must contain the named capture group `page_number` that refers to the page number.
    #:
    #: The regex is applied case-insensitive.
    page_regex: str = r"page\s+(?P<page_number>[0-9]+)"


class PagesPass(Pass):
    @classmethod
    def name(cls) -> str:
        return "pages"

    def __init__(self, config: JSON_DICT) -> None:
        self.config = Config.parse_obj(config)

    def run(self, doc: fitz.Document, index: TextIndex) -> None:
        marked = 0

        for match in re.finditer(self.config.page_regex, index.text, re.I):
            # find target page
            page_label = match.group("page_number")

            page_numbers = doc.get_page_numbers(page_label)
            if len(page_numbers) == 0:
                __logger__.warn("found no target page", label=page_label)
                continue
            elif len(page_numbers) > 1:
                __logger__.warn(
                    "found multiple target pages",
                    label=page_label,
                    targets=page_numbers,
                )
                continue

            page_number = page_numbers[0]

            # build marker rects
            create_links(doc, index, match.start(), match.end(), page_number)
            marked += 1

        __logger__.info("marked page links", num_links=marked)

    @property
    def order(self) -> int:
        return self.config.order

    @property
    def enabled(self) -> bool:
        return self.config.enabled
