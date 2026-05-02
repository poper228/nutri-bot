from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM backend. Returns raw dict; service layer validates with Pydantic."""

    @abstractmethod
    async def parse_analysis(self, file_bytes: bytes, mime_type: str) -> dict:
        """Send file to LLM and return parsed JSON as dict."""
