import pytest

from app.services.lectures.chunker import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP,
    chunk_pages,
)
from app.services.lectures.pdf_parser import PdfPage


def test_empty_input_returns_empty_list() -> None:
    assert chunk_pages([]) == []


def test_all_blank_pages_returns_empty_list() -> None:
    pages = [PdfPage(1, ""), PdfPage(2, "   \n\n  "), PdfPage(3, "")]
    assert chunk_pages(pages) == []


def test_short_text_produces_single_chunk() -> None:
    pages = [PdfPage(1, "Гемоглобин у взрослых норма 130-160 г/л.")]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 1
    assert "Гемоглобин" in chunks[0].text


def test_hyphenation_is_repaired() -> None:
    pages = [PdfPage(1, "Это при-\nмер переноса слова.")]
    chunks = chunk_pages(pages)
    assert chunks[0].text == "Это пример переноса слова."


def test_blank_first_page_is_skipped_and_page_tracking_works() -> None:
    pages = [PdfPage(1, ""), PdfPage(2, "Реальный текст на второй странице.")]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].page_number == 2


def test_long_text_produces_multiple_chunks_with_overlap() -> None:
    sentence = "Витамин D критичен для усвоения кальция. "
    pages = [PdfPage(1, sentence * 100)]
    chunks = chunk_pages(pages, max_chars=500, overlap=100)
    assert len(chunks) >= 3
    assert all(len(c.text) <= 600 for c in chunks)
    indexes = [c.chunk_index for c in chunks]
    assert indexes == list(range(len(chunks)))


def test_overlap_actually_overlaps() -> None:
    pages = [PdfPage(1, "А" * 2000)]
    chunks = chunk_pages(pages, max_chars=500, overlap=100)
    for prev, nxt in zip(chunks[:-1], chunks[1:], strict=True):
        tail = prev.text[-50:]
        assert tail in nxt.text or nxt.text.startswith(tail[:30])


def test_multipage_chunking_tracks_starting_page() -> None:
    page1 = "Страница 1. " * 200
    page2 = "Страница 2. " * 200
    pages = [PdfPage(1, page1), PdfPage(2, page2)]
    chunks = chunk_pages(pages, max_chars=500, overlap=50)
    assert chunks[0].page_number == 1
    assert any(c.page_number == 2 for c in chunks)


def test_invalid_max_chars_raises() -> None:
    pages = [PdfPage(1, "text")]
    with pytest.raises(ValueError):
        chunk_pages(pages, max_chars=0)


def test_invalid_overlap_raises() -> None:
    pages = [PdfPage(1, "text")]
    with pytest.raises(ValueError):
        chunk_pages(pages, max_chars=100, overlap=100)
    with pytest.raises(ValueError):
        chunk_pages(pages, max_chars=100, overlap=-1)


def test_default_params_are_sane() -> None:
    assert DEFAULT_OVERLAP < DEFAULT_MAX_CHARS
    assert DEFAULT_OVERLAP > 0
