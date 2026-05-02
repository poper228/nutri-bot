import asyncio
import json

from groq import Groq

from app.infrastructure.llm.base import LLMProvider

_PARSE_PROMPT = """\
Ты — медицинский ассистент-аналитик.
Извлеки ВСЕ лабораторные показатели из текста анализа.

Верни ТОЛЬКО валидный JSON объект:
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
- status: сравни value с reference. Ниже нормы — "low", выше — "high", в норме — "normal", нет данных — "unknown"
- Никаких пояснений, только JSON
"""


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._client = Groq(api_key=api_key)
        self._model = model

    async def parse_analysis(self, file_bytes: bytes, mime_type: str) -> dict:
        text = file_bytes.decode("utf-8", errors="replace")
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=self._model,
            messages=[
                {"role": "system", "content": _PARSE_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        return json.loads(response.choices[0].message.content)

    async def generate_breakdown(self, system_prompt: str, user_message: str) -> str:
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
