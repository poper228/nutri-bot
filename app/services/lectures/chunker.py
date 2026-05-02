import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.services.lectures.pdf_parser import PdfPage

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP = 200
PAGE_SEPARATOR = "\n\n"
SENTENCE_BREAKS = (". ", ".\n", "!\n", "?\n", "! ", "? ", "\n\n")
BREAK_LOOKBACK = 250


@dataclass(frozen=True, slots=True)
class TextChunk:
    chunk_index: int
    page_number: int
    text: str


def _clean_text(text: str) -> str:
    text = re.sub(r"(?<=\S)-\n(?=\S)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _build_full_text(
    pages: Sequence[PdfPage],
) -> tuple[str, list[tuple[int, int]]]:
    """Returns (full_text, [(start_offset, page_number), ...] sorted by offset)."""
    parts: list[str] = []
    page_offsets: list[tuple[int, int]] = []
    cursor = 0
    for page in pages:
        cleaned = _clean_text(page.text)
        if not cleaned:
            continue
        page_offsets.append((cursor, page.page_number))
        parts.append(cleaned)
        cursor += len(cleaned) + len(PAGE_SEPARATOR)
    return PAGE_SEPARATOR.join(parts), page_offsets


def _resolve_page(offset: int, page_offsets: Sequence[tuple[int, int]]) -> int:
    page_number = page_offsets[0][1]
    for start, num in page_offsets:
        if start <= offset:
            page_number = num
        else:
            break
    return page_number


def _find_break(text: str, window_start: int, window_end: int) -> int | None:
    best = -1
    for marker in SENTENCE_BREAKS:
        idx = text.rfind(marker, window_start, window_end)
        if idx != -1:
            best = max(best, idx + len(marker))
    return best if best != -1 else None


def chunk_pages(
    pages: Sequence[PdfPage],
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[TextChunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be >= 0 and < max_chars")

    full_text, page_offsets = _build_full_text(pages)
    if not full_text:
        return []

    chunks: list[TextChunk] = []
    pos = 0
    chunk_index = 0
    n = len(full_text)

    while pos < n:
        end = min(pos + max_chars, n)
        if end < n:
            window_start = max(pos, end - BREAK_LOOKBACK)
            break_at = _find_break(full_text, window_start, end)
            if break_at is not None and break_at > pos:
                end = break_at

        text = full_text[pos:end].strip()
        if text:
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    page_number=_resolve_page(pos, page_offsets),
                    text=text,
                )
            )
            chunk_index += 1

        if end >= n:
            break
        pos = max(end - overlap, pos + 1)

    return chunks
