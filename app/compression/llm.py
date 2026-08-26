from __future__ import annotations

from typing import Protocol

from app import config
from app.models import KnowledgeUnit


class Compressor(Protocol):
    name: str

    def compress(self, text: str, *, title: str, source_type: str) -> KnowledgeUnit:
        ...


def compress(text: str, *, title: str = "", source_type: str = "notes") -> KnowledgeUnit:
    """Provider-agnostic entry. Swap LLM_PROVIDER without changing callers."""
    return get_compressor().compress(text, title=title, source_type=source_type)


def get_compressor() -> Compressor:
    provider = config.LLM_PROVIDER
    if provider not in config.SUPPORTED_PROVIDERS:
        raise ValueError(
            f"unknown LLM_PROVIDER={provider!r}; "
            f"expected one of {config.SUPPORTED_PROVIDERS}"
        )
    return _StubCompressor(provider)


class _StubCompressor:
    """Phase 0 placeholder. Phase 1 wires OpenAI / Gemini / Ollama / DeepSeek."""

    def __init__(self, name: str) -> None:
        self.name = name

    def compress(self, text: str, *, title: str, source_type: str) -> KnowledgeUnit:
        raise NotImplementedError(
            f"Phase 1: LLM provider {self.name!r} is selected but not wired yet. "
            "Set keys in .env, then implement compress() in app/compression/llm.py."
        )
