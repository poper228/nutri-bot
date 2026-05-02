from dataclasses import dataclass
from pathlib import Path

import pdfplumber


@dataclass(frozen=True, slots=True)
class PdfPage:
    page_number: int
    text: str


def extract_pdf_pages(file_path: Path) -> list[PdfPage]:
    pages: list[PdfPage] = []
    with pdfplumber.open(file_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PdfPage(page_number=index, text=text))
    return pages
