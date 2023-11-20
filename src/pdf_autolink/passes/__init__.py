from __future__ import annotations

import fitz
import structlog

from .chapters import ChaptersPass
from .clear_links import ClearLinksPass
from .interface import Pass
from .pages import PagesPass
from .page_tables import PageTablesPass

from ..config import JSON_DICT
from ..index import TextIndex

__logger__ = structlog.get_logger()


def run_all(
    doc: fitz.Document, index: TextIndex, pass_cfg: dict[str, JSON_DICT] | None
) -> None:
    pass_types = _setup_pass_types()

    if pass_cfg is None:
        pass_cfg = {name: {} for name in pass_types.keys()}

    passes = []
    for name, cfg in pass_cfg.items():
        __logger__.info("configure pass", pass_name=name)
        passes.append(pass_types[name](cfg))

    passes = sorted(passes, key=lambda p: (p.order, p.name()))

    for p in passes:
        __logger__.info("run pass", pass_name=p.name())
        p.run(doc, index)


def _setup_pass_types() -> dict[str, type[Pass]]:
    passes: dict[str, type[Pass]] = {}

    _add_pass_type(passes, ChaptersPass)
    _add_pass_type(passes, ClearLinksPass)
    _add_pass_type(passes, PagesPass)
    _add_pass_type(passes, PageTablesPass)

    return passes


def _add_pass_type(passes: dict[str, type[Pass]], p: type[Pass]) -> None:
    passes[p.name()] = p
