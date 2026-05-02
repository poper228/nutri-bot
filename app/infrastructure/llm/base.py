from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM backend."""

    @abstractmethod
    async def parse_analysis(self, file_bytes: bytes, mime_type: str) -> dict:
        """Extract lab indicators from file, return raw dict."""

    @abstractmethod
    async def generate_breakdown(self, system_prompt: str, user_message: str) -> str:
        """Generate free-form text given system + user message."""
