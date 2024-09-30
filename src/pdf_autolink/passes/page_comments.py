from __future__ import annotations

import fitz
import structlog
from pydantic import BaseModel

from .interface import Pass
from ..config import JSON_DICT
from ..constants import ANNOT_AUTHOR
from ..index import TextIndex

__logger__ = structlog.get_logger()


class Annotation(BaseModel):
    #: Page label.
    page: str

    #: Annotation text.
    text: str


class Config(BaseModel):
    #: Pass order.
    #:
    #: Lower order passes run first.
    order: int = 10

    #: Enable pass.
    enabled: bool = True

    #: Annotations
    annotations: list[Annotation] = []


class PageCommentsPass(Pass):
    @classmethod
    def name(cls) -> str:
        return "page_comments"

    def __init__(self, config: JSON_DICT) -> None:
        self.config = Config.parse_obj(config)

    def run(self, doc: fitz.Document, index: TextIndex) -> None:
        created = 0

        for annotation in self.config.annotations:
            created += self._create_annotation(annotation, doc)

        __logger__.info("created page comments", num_comments=created)

    def _create_annotation(self, annotation: Annotation, doc: fitz.Document) -> int:
        created = 0

        page_numbers = doc.get_page_numbers(annotation.page)
        if len(page_numbers) == 0:
            __logger__.warn("did not find page to annotade", label=annotation.page)
        elif len(page_numbers) > 1:
            __logger__.warn(
                "found more than one page to annotade",
                label=annotation.page,
                pages=[p + 1 for p in page_numbers],
            )

        for page_number in page_numbers:
            page = doc[page_number]

            annot = page.add_text_annot((0, 0), annotation.text)
            annot.set_info(title=ANNOT_AUTHOR)
            annot.update()

            created += 1

        return created

    @property
    def order(self) -> int:
        return self.config.order

    @property
    def enabled(self) -> bool:
        return self.config.enabled
