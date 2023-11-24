from __future__ import annotations

from typing import Protocol

import fitz

from ..config import JSON_DICT
from ..index import TextIndex


class Pass(Protocol):
    @classmethod
    def name(cls) -> str:
        ...

    def __init__(self, config: JSON_DICT) -> None:
        ...

    def run(self, doc: fitz.Document, index: TextIndex) -> None:
        ...

    @property
    def order(self) -> int:
        ...

    @property
    def enabled(self) -> bool:
        ...
