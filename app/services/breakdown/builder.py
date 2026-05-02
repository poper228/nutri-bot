from dataclasses import dataclass
from pathlib import Path

from app.infrastructure.llm.base import LLMProvider
from app.services.analysis.optimal_checker import apply_optimal_ranges
from app.services.analysis.parser import AnalysisParser
from app.services.analysis.schemas import LabIndicator, ParsedAnalysis
from app.services.lectures.retriever import LectureRetriever, RetrievalResult

_SYSTEM_PROMPT = """\
Ты — ассистент нутрициолога Жени. Твоя задача — написать понятный разбор лабораторных анализов клиента.

Правила:
- Опирайся ТОЛЬКО на предоставленный контекст из лекций нутрициолога
- Объясняй простым языком, без медицинского жаргона
- Для каждого отклонения: что это значит, возможные причины, нутрициологические рекомендации
- Если в лекциях нет информации по показателю — честно скажи об этом
- Не ставь диагнозы, не назначай лечение — только нутрициологические рекомендации
- Пиши структурированно, с разделами по каждому отклонению
"""

_STATUS_LABEL = {"low": "ниже нормы 🔻", "high": "выше нормы 🔺"}


@dataclass
class BreakdownResult:
    analysis: ParsedAnalysis
    rag_chunks: list[RetrievalResult]
    text: str


class BreakdownBuilder:
    def __init__(
        self,
        parser: AnalysisParser,
        retriever: LectureRetriever,
        llm: LLMProvider,
        rag_top_k: int = 5,
    ) -> None:
        self._parser = parser
        self._retriever = retriever
        self._llm = llm
        self._rag_top_k = rag_top_k

    async def build_from_bytes(self, data: bytes, mime_type: str) -> BreakdownResult:
        analysis = await self._parser.parse_bytes(data, mime_type)
        return await self._build(analysis)

    async def build(self, analysis_path: Path) -> BreakdownResult:
        analysis = await self._parser.parse_file(analysis_path)
        return await self._build(analysis)

    async def _build(self, analysis: ParsedAnalysis) -> BreakdownResult:
        analysis = apply_optimal_ranges(analysis)
        abnormal = [i for i in analysis.indicators if i.status in ("low", "high")]
        rag_chunks = await self._retrieve_context(abnormal)
        user_message = self._build_user_message(analysis, abnormal, rag_chunks)
        text = await self._llm.generate_breakdown(_SYSTEM_PROMPT, user_message)
        return BreakdownResult(analysis=analysis, rag_chunks=rag_chunks, text=text)

    async def _retrieve_context(self, abnormal: list[LabIndicator]) -> list[RetrievalResult]:
        seen_ids: set[tuple[int, int]] = set()
        chunks: list[RetrievalResult] = []

        for indicator in abnormal:
            suffix = "дефицит недостаток" if indicator.status == "low" else "повышение избыток причины"
            query = f"{indicator.name} {suffix}"
            results = await self._retriever.search(query, top_k=self._rag_top_k)
            for r in results:
                key = (r.lecture_id, r.chunk_index)
                if key not in seen_ids:
                    seen_ids.add(key)
                    chunks.append(r)

        return chunks

    def _build_user_message(
        self,
        analysis: ParsedAnalysis,
        abnormal: list[LabIndicator],
        rag_chunks: list[RetrievalResult],
    ) -> str:
        lines: list[str] = []

        lines.append(f"ТИП АНАЛИЗА: {analysis.source_type}")
        lines.append(f"ВСЕГО ПОКАЗАТЕЛЕЙ: {len(analysis.indicators)}")
        lines.append("")

        if abnormal:
            lines.append("ОТКЛОНЕНИЯ ОТ НОРМЫ:")
            for ind in abnormal:
                label = _STATUS_LABEL.get(ind.status, ind.status)
                ref = f" (норма: {ind.reference})" if ind.reference else ""
                unit = f" {ind.unit}" if ind.unit else ""
                lines.append(f"  - {ind.name}: {ind.value}{unit} — {label}{ref}")
        else:
            lines.append("Все показатели в норме.")

        lines.append("")

        if rag_chunks:
            lines.append("КОНТЕКСТ ИЗ ЛЕКЦИЙ НУТРИЦИОЛОГА:")
            for i, chunk in enumerate(rag_chunks, 1):
                lines.append(f"\n[{i}] (лекция {chunk.lecture_id}, стр. {chunk.page_number}):")
                lines.append(chunk.text[:800])
        else:
            lines.append("Контекст из лекций не найден.")

        lines.append("")
        lines.append("Напиши подробный нутрициологический разбор по отклонениям.")

        return "\n".join(lines)
