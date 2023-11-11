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


class PagesPass(Pass):
    def name(self) -> str:
        return "pages"

    def run(self, doc: fitz.Document, index: TextIndex, config: JSON_DICT) -> None:
        config_typed = Config.parse_obj(config)
        self.run_typed(doc, index, config_typed)

    def run_typed(self, doc: fitz.Document, index: TextIndex, config: Config) -> None:
        for match in re.finditer(r"page\s+([0-9]+)", index.text, re.I):
            # find target page
            page_label = match.group(1)

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
