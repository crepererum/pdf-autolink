from __future__ import annotations

import fitz
import structlog

from .chapters import ChaptersPass
from .interface import Pass
from .pages import PagesPass
from .page_tables import PageTablesPass

from ..config import JSON_DICT
from ..index import TextIndex

__logger__ = structlog.get_logger()


def run_all(
    doc: fitz.Document, index: TextIndex, pass_cfg: dict[str, JSON_DICT] | None
) -> None:
    passes = _setup_passes()

    if pass_cfg is None:
        pass_cfg = {name: {} for name in passes.keys()}

    for name, cfg in pass_cfg.items():
        __logger__.info("run pass", pass_name=name)
        passes[name].run(doc, index, cfg or {})


def _setup_passes() -> dict[str, Pass]:
    passes: dict[str, Pass] = {}

    _add_pass(passes, ChaptersPass())
    _add_pass(passes, PagesPass())
    _add_pass(passes, PageTablesPass())

    return passes


def _add_pass(passes: dict[str, Pass], p: Pass) -> None:
    passes[p.name()] = p
