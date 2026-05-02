import asyncio
import json

from google import genai
from google.genai import types

from app.infrastructure.llm.base import LLMProvider

_PROMPT = """\
Ты — медицинский ассистент-аналитик.
Извлеки ВСЕ лабораторные показатели из документа.

Верни ТОЛЬКО валидный JSON объект вида:
{
  "source_type": "blood" | "urine" | "other" | "unknown",
  "indicators": [
    {
      "name": "<название на русском>",
      "value": "<значение строкой>",
      "unit": "<единица или null>",
      "reference": "<референс строкой или null>",
      "status": "low" | "normal" | "high" | "unknown"
    }
  ]
}

Правила:
- status определяй по сравнению value и reference
- Если значение ниже нижней границы — "low", выше верхней — "high", в норме — "normal"
- Если референс отсутствует или не удаётся сравнить — "unknown"
- Не добавляй пояснений, только JSON
"""


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def parse_analysis(self, file_bytes: bytes, mime_type: str) -> dict:
        response = await asyncio.to_thread(self._generate, file_bytes, mime_type)
        return json.loads(response)

    def _generate(self, file_bytes: bytes, mime_type: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                types.Part.from_text(text=_PROMPT),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        return response.text
