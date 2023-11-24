import pytest

from pdf_autolink.page_ranges import PageRanges


@pytest.mark.parametrize(
    "s,expected",
    [
        ("", []),
        ("1", [1]),
        ("1, 3,4", [1, 3, 4]),
        ("2-5", [2, 3, 4, 5]),
        ("2-2", [2]),
        ("2-1", []),
        ("3-5,1", [3, 4, 5, 1]),
    ],
)
def test_page_ranges(s: str, expected: list[int]) -> None:
    ranges = PageRanges(s)
    assert list(ranges) == expected
