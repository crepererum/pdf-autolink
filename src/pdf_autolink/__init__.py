from __future__ import annotations

import fitz
import structlog
import typer

from .index import TextIndex
from .logging import init_logging
from .passes import run_all


__logger__ = structlog.get_logger()


def run(file_in: str, file_out: str) -> None:
    init_logging()

    doc = fitz.open(file_in)

    idx = TextIndex.extract(doc)
    __logger__.info("text extraction done", text_len=len(idx.text))

    run_all(doc, idx)

    doc.save(file_out)


def main() -> None:
    typer.run(run)


if __name__ == "__main__":
    main()
