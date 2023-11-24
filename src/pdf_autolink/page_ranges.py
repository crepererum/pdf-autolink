from typing import Iterator


class PageRanges:
    def __init__(self, s: str) -> None:
        self.ranges = []

        for part in s.split(","):
            part = part.strip()
            if not part:
                continue

            numbers = [int(n.strip()) for n in part.split("-")]

            if len(numbers) == 1:
                (n,) = numbers
                self.ranges.append((n, n))
            elif len(numbers) == 2:
                (n, m) = numbers
                self.ranges.append((n, m))
            else:
                raise ValueError(
                    f"Expected one or two numbers but got {len(numbers)} in '{part}'"
                )

    def __iter__(self) -> Iterator[int]:
        for n, m in self.ranges:
            for p in range(n, m + 1):
                yield p
