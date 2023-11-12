from __future__ import annotations

from collections import defaultdict
import re
from typing import Mapping, TypeAlias

import fitz
import structlog
from pydantic import BaseModel

from .interface import Pass
from ..config import JSON_DICT
from ..index import TextIndex
from ..link import create_links

__logger__ = structlog.get_logger()

#: Maps "source page" -> "per source page info".
#:
#: Every source page is represented by a map of "target page" to "list of text index ranges".
#:
#: Hence the final type is:
#: source_page -> (target_page -> [range])
PAGE_MAPPING: TypeAlias = Mapping[int, Mapping[int, list[tuple[int, int]]]]


class Config(BaseModel):
    #: Minimum number of non-unique outgoing links to consider a page as a member of a page table.
    min_links_per_page: int = 10

    #: How many page tables should be marked?
    #:
    #: Page tables are sorted by number of unique outgoing links in descending order.
    top_most_runs: int = 2

    #: Regular expression for a page link.
    #:
    #: Must contain the named capture group `page_number` that refers to the page number.
    #:
    #: The regex is applied case-insensitive.
    page_regex: str = r"([a-z()]+\s+)*[a-z()]{2,}\s+(?P<page_number>[0-9]+)"


class PageTablesPass(Pass):
    def name(self) -> str:
        return "page_tables"

    def run(self, doc: fitz.Document, index: TextIndex, config: JSON_DICT) -> None:
        config_typed = Config.parse_obj(config)
        self.run_typed(doc, index, config_typed)

    def run_typed(self, doc: fitz.Document, index: TextIndex, config: Config) -> None:
        pages = self._find_pages(doc, index, config)

        # filter out pages w/ not enough of links
        pages = {
            page: links
            for page, links in pages.items()
            if len(links) >= config.min_links_per_page
        }

        runs = self._detect_runs(pages)

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

        __logger__.info("detected page tables", num_page_tables=len(runs))

        # emit top-most runs
        marked = 0
        for run in runs[: config.top_most_runs]:
            __logger__.info("mark page table", pages=[p + 1 for p in run])

            for page in run:
                page_entries = pages[page]
                for page_number in sorted(page_entries.keys()):
                    targets = page_entries[page_number]
                    for start, end in targets:
                        create_links(doc, index, start, end, page_number)
                        marked += 1

        __logger__.info("marked links in page tables", num_links=marked)

    def _find_pages(
        self, doc: fitz.Document, index: TextIndex, config: Config
    ) -> PAGE_MAPPING:
        """
        Find page references.
        """

        pages: defaultdict[int, defaultdict[int, list[tuple[int, int]]]] = defaultdict(
            lambda: defaultdict(lambda: [])
        )

        # find potential links
        for match in re.finditer(config.page_regex, index.text, re.I):
            # find target page
            page_label = match.group("page_number")
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

    def _detect_runs(self, pages: PAGE_MAPPING) -> list[list[int]]:
        """
        Organize link source pages into runs.
        """

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

        return runs
