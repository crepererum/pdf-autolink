from __future__ import annotations

from collections import defaultdict
import re

import fitz
import structlog

from ..index import TextIndex
from ..link import create_links

__logger__ = structlog.get_logger()


def mark_page_tables(doc: fitz.Document, index: TextIndex) -> None:
    pages: defaultdict[int, defaultdict[int, list[tuple[int, int]]]] = defaultdict(
        lambda: defaultdict(lambda: [])
    )

    # find potential links
    for match in re.finditer(r"([a-z()]+\s+)*[a-z()]{2,}\s+([0-9]+)", index.text, re.I):
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

    # organize link source pages into runs
    runs: list[list[int]] = []
    run = None
    for page in sorted(pages.keys()):
        # filter out pages w/ not enough of links
        if len(pages[page]) < 10:
            continue

        # add page to run
        if run is None:
            run = [page]
        elif run[-1] + 1 == page:
            run.append(page)
        else:
            runs.append(run)
            run = [page]

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

    # emit two top-most runs
    for run in runs[:2]:
        for page in run:
            __logger__.info("found page table", page=page + 1)

            page_entries = pages[page]
            for page_number in sorted(page_entries.keys()):
                targets = page_entries[page_number]
                for start, end in targets:
                    create_links(doc, index, start, end, page_number)
