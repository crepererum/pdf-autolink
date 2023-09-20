import re

from pypdf import PdfReader, PdfWriter


PATTERNS = (
    re.compile(r"page\s+[0-9]+"),
)


def main() -> None:
    reader = PdfReader("input.pdf")
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        print(f"page: {i+1}/{len(reader.pages)}")
        page.extract_text(visitor_text=visitor_text)
        writer.add_page(page)

    with open("output.pdf", "wb") as fp:
        writer.write(fp)


def visitor_text(text, cm, tm, fontDict, fontSize):
    (x, y) = (tm[4], tm[5])
    text = text.lower()
    for pattern in PATTERNS:
        if pattern.search(text):
            print(f"{x}.{y}: {text}")


if __name__ == "__main__":
    main()
