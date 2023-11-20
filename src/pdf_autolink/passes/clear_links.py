from __future__ import annotations

import fitz
import structlog
from pydantic import BaseModel

from .interface import Pass
from ..config import JSON_DICT
from ..index import TextIndex

__logger__ = structlog.get_logger()


class Config(BaseModel):
    #: Pass order.
    #:
    #: Lower order passes run first.
    order: int = 0


class ClearLinksPass(Pass):
    @classmethod
    def name(cls) -> str:
        return "clear_links"

    def __init__(self, config: JSON_DICT) -> None:
        self.config = Config.parse_obj(config)

    def run(self, doc: fitz.Document, index: TextIndex) -> None:
        cleared = 0

        for page in doc:
            links = list(page.get_links())
            for link in links:
                page.delete_link(link)
                cleared += 1

        __logger__.info("cleared links", num_links=cleared)

    @property
    def order(self) -> int:
        return self.config.order
