from __future__ import annotations

import fitz
import structlog
import typer

from .config import load_config
from .error import UserError
from .index import TextIndex
from .logging import init_logging
from .passes import run_all


__logger__ = structlog.get_logger()


def run(file_in: str, file_out: str, config_file: str = "") -> None:
    try:
        _run_inner(file_in, file_out, config_file)
    except UserError as e:
        __logger__.error(str(e))
        raise typer.Exit(code=1)


def _run_inner(file_in: str, file_out: str, config_file: str) -> None:
    init_logging()

    if file_in == file_out:
        raise UserError("cannot override file")

    config = load_config(config_file)
    doc = fitz.open(file_in)

    idx = TextIndex.extract(doc)
    __logger__.info("text extraction done", text_len=len(idx.text))

    run_all(doc, idx, config.passes)

    doc.save(file_out)


def main() -> None:
    typer.run(run)


if __name__ == "__main__":
    main()
