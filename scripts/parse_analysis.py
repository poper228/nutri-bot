import argparse
import asyncio
import json
from pathlib import Path

from app.infrastructure.llm.factory import get_llm_provider
from app.services.analysis.parser import AnalysisParser

STATUS_EMOJI = {"low": "🔻", "high": "🔺", "normal": "✅", "unknown": "❓"}


async def run(path: Path) -> None:
    parser = AnalysisParser(llm=get_llm_provider())
    result = await parser.parse_file(path)

    print(f"\nТип анализа: {result.source_type}")
    print(f"Показателей: {len(result.indicators)}\n")

    for ind in result.indicators:
        emoji = STATUS_EMOJI.get(ind.status, "❓")
        ref = f"  [норма: {ind.reference}]" if ind.reference else ""
        unit = f" {ind.unit}" if ind.unit else ""
        print(f"{emoji}  {ind.name}: {ind.value}{unit}{ref}")

    print("\n--- JSON ---")
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse lab analysis file with Gemini Vision.")
    ap.add_argument("path", type=Path, help="Path to PDF or image file.")
    args = ap.parse_args()
    asyncio.run(run(args.path))


if __name__ == "__main__":
    main()
