from __future__ import annotations

from collections import defaultdict
import re
from typing import Mapping

import fitz
import structlog
from pydantic import BaseModel

from .interface import Pass
from ..config import JSON_DICT
from ..index import TextIndex
from ..link import create_links

__logger__ = structlog.get_logger()


class Config(BaseModel):
    min_links_per_page: int = 10
    top_most_runs: int = 2


class PageTablesPass(Pass):
    def name(self) -> str:
        return "page_tables"

    def run(self, doc: fitz.Document, index: TextIndex, config: JSON_DICT) -> None:
        config_typed = Config.parse_obj(config)
        self.run_typed(doc, index, config_typed)

    def run_typed(self, doc: fitz.Document, index: TextIndex, config: Config) -> None:
        pages = self._find_pages(doc, index)

        # filter out pages w/ not enough of links
        pages = {
            page: links
            for page, links in pages.items()
            if len(links) >= config.min_links_per_page
        }

        # organize link source pages into runs
        runs: list[list[int]] = []
        run = None
        for page in sorted(pages.keys()):
            # add page to run
            if run is None:
                run = [page]
            elif run[-1] + 1 == page:
                run.append(page)
            else:
                runs.append(run)
                run = [page]
        if run is not None:
            runs.append(run)

        # sort runs by number of outgoing unique links
        runs = sorted(
            runs,
            key=lambda run: len(
                {
                    target_page
                    for source_page in run
                    for target_page in pages[source_page].keys()
                }
            ),
            reverse=True,
        )

        # emit top-most runs
        for run in runs[: config.top_most_runs]:
            for page in run:
                __logger__.info("found page table", page=page + 1)

                page_entries = pages[page]
                for page_number in sorted(page_entries.keys()):
                    targets = page_entries[page_number]
                    for start, end in targets:
                        create_links(doc, index, start, end, page_number)

    def _find_pages(
        self, doc: fitz.Document, index: TextIndex
    ) -> Mapping[int, Mapping[int, list[tuple[int, int]]]]:
        pages: defaultdict[int, defaultdict[int, list[tuple[int, int]]]] = defaultdict(
            lambda: defaultdict(lambda: [])
        )

        # find potential links
        for match in re.finditer(
            r"([a-z()]+\s+)*[a-z()]{2,}\s+([0-9]+)", index.text, re.I
        ):
            # find target page
            page_label = match.group(2)
            page_numbers = doc.get_page_numbers(page_label)
            if len(page_numbers) != 1:
                continue
            page_number = page_numbers[0]

            start = match.start()
            end = match.end()
            idx_start, idx_end = index.find_indices(start, end)

            page = index.positions[idx_start].page
            if page != index.positions[idx_end].page:
                continue

            pages[page][page_number].append((start, end))

        return pages
