from __future__ import annotations

import fitz

from .index import TextIndex


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
