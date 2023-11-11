from __future__ import annotations

from typing import Protocol

import fitz

from ..config import JSON_DICT
from ..index import TextIndex


class Pass(Protocol):
    def name(self) -> str:
        ...

    def run(self, doc: fitz.Document, index: TextIndex, config: JSON_DICT) -> None:
        ...
