from __future__ import annotations

from bisect import bisect
from collections import defaultdict
from dataclasses import dataclass
import re

import fitz
import typer


def run(file_in: str, file_out: str) -> None:
    doc = fitz.open(file_in)
    idx = extract_text(doc)
    print(f"text_len={len(idx.text)}")
    mark_pages(doc, idx)
    mark_chapters(doc, idx)
    mark_page_tables(doc, idx)
    doc.save(file_out)


def extract_text(doc: fitz.Document) -> TextIndex:
    text = ""
    positions = []
    for i, page in enumerate(doc):
        print(f"page: {i+1}/{len(doc)}")
        for word in page.get_text("words"):
            (x0, y0, x1, y1, word, block_no, line_no, word_no) = word
            positions.append(TextPosition(i, fitz.Rect(x0, y0, x1, y1), len(text)))
            text += word
            text += " "

    return TextIndex(text, positions)


@dataclass
class TextPosition:
    page: int
    page_pos: fitz.Rect
    txt_offset: int


@dataclass
class TextIndex:
    text: str
    positions: list[TextPosition]

    def find_indices(self, start: int, end: int) -> tuple[int, int]:
        idx_start = bisect(self.positions, start, key=lambda p: p.txt_offset) - 1
        idx_end = bisect(
            self.positions, end - 1, lo=idx_start, key=lambda p: p.txt_offset
        )
        assert idx_end > idx_start

        return (idx_start, idx_end)


def mark_pages(doc: fitz.Document, index: TextIndex) -> None:
    for match in re.finditer(r"page\s+([0-9]+)", index.text, re.I):
        # find target page
        page_label = match.group(1)
        page_numbers = doc.get_page_numbers(page_label)
        assert len(page_numbers) == 1, f"{page_label}, {page_numbers}"
        page_number = page_numbers[0]

        # build marker rects
        create_links(doc, index, match.start(), match.end(), page_number)


def mark_chapters(doc: fitz.Document, index: TextIndex) -> None:
    # page for every top-level chapter
    chapter_targets = [
        (dst["page"], dst["to"])
        for lvl, _title, _page, dst in doc.get_toc(simple=False)
        if lvl == 1
    ]

    for match in re.finditer(r"chapter\s+([0-9]+)", index.text, re.I):
        # find target page
        chapter_number = int(match.group(1))
        (page_number, pos) = chapter_targets[chapter_number - 1]

        # build marker rects
        create_links(doc, index, match.start(), match.end(), page_number, pos)


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
            print(f"found page table at page {page+1}")
            page_entries = pages[page]
            for page_number in sorted(page_entries.keys()):
                targets = page_entries[page_number]
                for start, end in targets:
                    create_links(doc, index, start, end, page_number)


def create_links(
    doc: fitz.Document,
    index: TextIndex,
    start: int,
    end: int,
    target_page: int,
    target_pos: fitz.Point | None = None,
) -> None:
    assert end > start

    idx_start, idx_end = index.find_indices(start, end)

    marker_page = None
    marker_rect = None
    for pos in index.positions[idx_start:idx_end]:
        if marker_page is None:
            # first element
            marker_page = pos.page
            marker_rect = pos.page_pos
        else:
            if (
                (marker_page != pos.page)
                or (pos.page_pos.x1 < marker_rect.x0)
                or (pos.page_pos.y1 < marker_rect.y0)
            ):
                # not the same rect
                create_link(doc, marker_page, marker_rect, target_page, target_pos)
                marker_page = pos.page
                marker_rect = pos.page_pos

        marker_rect = fitz.Rect(
            min(marker_rect.x0, pos.page_pos.x0),
            min(marker_rect.y0, pos.page_pos.y0),
            max(marker_rect.x1, pos.page_pos.x1),
            max(marker_rect.y1, pos.page_pos.y1),
        )

    assert marker_page is not None
    create_link(doc, marker_page, marker_rect, target_page, target_pos)


def create_link(
    doc: fitz.Document,
    source_page: int,
    source_rect: fitz.Rect,
    target_page: int,
    target_pos: fitz.Point | None,
) -> None:
    if target_pos is None:
        target_pos = fitz.Point(0.0, 0.0)

    doc[source_page].insert_link(
        {
            "kind": fitz.LINK_GOTO,
            "page": target_page,
            "from": source_rect,
            "to": target_pos,
        }
    )


def main() -> None:
    typer.run(run)


if __name__ == "__main__":
    main()
