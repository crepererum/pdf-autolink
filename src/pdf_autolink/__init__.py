from __future__ import annotations

import fitz
import typer

from .index import TextIndex
from .passes import run_all


def run(file_in: str, file_out: str) -> None:
    doc = fitz.open(file_in)
    idx = TextIndex.extract(doc)
    print(f"text_len={len(idx.text)}")
    run_all(doc, idx)
    doc.save(file_out)


def main() -> None:
    typer.run(run)


if __name__ == "__main__":
    main()
