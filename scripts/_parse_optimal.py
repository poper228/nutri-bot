"""One-off script: parse nutritionist's optimal ranges table → JSON file."""
import json
import re
import zipfile
from pathlib import Path

from groq import Groq

from app.core.config import get_settings

DOCX_PATH = Path("lections/таблица анализы.docx")
OUT_PATH = Path("app/services/analysis/optimal_ranges.json")

PROMPT = (
    "Извлеки оптимальные значения показателей из таблицы нутрициолога.\n"
    "Для каждого показателя верни объект. Числовой диапазон — укажи min и max.\n"
    "Только нижняя граница ('от 60', 'более X') — только min.\n"
    "Только верхняя ('менее 3', 'до 2') — только max.\n"
    "Качественное описание ('середина', 'к верху') — min/max = null, заполни note.\n\n"
    "Верни JSON: {\"ranges\": [{\"name\": str, \"aliases\": [str], "
    "\"optimal_min\": float|null, \"optimal_max\": float|null, "
    "\"unit\": str|null, \"note\": str|null}]}\n\n"
    "Только JSON."
)


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode()
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    text = extract_docx_text(DOCX_PATH)
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key.get_secret_value())

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    data = json.loads(response.choices[0].message.content)
    ranges = data.get("ranges", data) if isinstance(data, dict) else data

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(ranges, ensure_ascii=False, indent=2))
    print(f"Saved {len(ranges)} ranges to {OUT_PATH}")

    # Preview
    for r in ranges[:10]:
        print(f"  {r['name']}: min={r['optimal_min']} max={r['optimal_max']} note={r['note']}")


if __name__ == "__main__":
    main()
