from pathlib import Path

import io

import pdfplumber

from app.infrastructure.llm.base import LLMProvider
from app.services.analysis.schemas import ParsedAnalysis

_EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _extract_pdf_text(source: Path | bytes) -> str:
    opener = pdfplumber.open(source if isinstance(source, Path) else io.BytesIO(source))
    pages = []
    with opener as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


class AnalysisParser:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def parse_file(self, path: Path) -> ParsedAnalysis:
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            text = _extract_pdf_text(path)
            if not text.strip():
                raise ValueError("PDF contains no extractable text (scanned image?)")
            raw = await self._llm.parse_analysis(text.encode(), "text/plain")
        elif suffix in _EXT_TO_MIME:
            mime = _EXT_TO_MIME[suffix]
            raw = await self._llm.parse_analysis(path.read_bytes(), mime)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        return ParsedAnalysis.model_validate(raw)

    async def parse_bytes(self, data: bytes, mime_type: str) -> ParsedAnalysis:
        if mime_type == "application/pdf":
            text = _extract_pdf_text(data)
            if not text.strip():
                raise ValueError("PDF contains no extractable text (scanned image?)")
            raw = await self._llm.parse_analysis(text.encode(), "text/plain")
        else:
            raw = await self._llm.parse_analysis(data, mime_type)
        return ParsedAnalysis.model_validate(raw)
