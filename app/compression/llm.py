from __future__ import annotations

from typing import Protocol

from app import config
from app.compression.parse import extract_json_object, knowledge_unit_from_payload
from app.compression.prompt import COMPRESS_SYSTEM, build_user_prompt
from app.models import KnowledgeUnit, SourceType


class Compressor(Protocol):
    name: str

    def compress(
        self,
        text: str,
        *,
        title: str,
        source_type: str,
        source: str | None = None,
        url: str | None = None,
    ) -> KnowledgeUnit:
        ...


def compress(
    text: str,
    *,
    title: str = "",
    source_type: str = "notes",
    source: str | None = None,
    url: str | None = None,
) -> KnowledgeUnit:
    """Provider-agnostic entry. Swap LLM_PROVIDER without changing callers."""
    return get_compressor().compress(
        text,
        title=title,
        source_type=source_type,
        source=source,
        url=url,
    )


def get_compressor() -> Compressor:
    provider = config.LLM_PROVIDER
    if provider not in config.SUPPORTED_PROVIDERS:
        raise ValueError(
            f"unknown LLM_PROVIDER={provider!r}; "
            f"expected one of {config.SUPPORTED_PROVIDERS}"
        )
    factories = {
        "ollama": OllamaCompressor,
        "openai": OpenAICompressor,
        "deepseek": DeepSeekCompressor,
        "gemini": GeminiCompressor,
    }
    return factories[provider]()


def complete_json(system: str, user: str) -> str:
    """Provider-agnostic JSON completion used by compress/derive."""
    compressor = get_compressor()
    return compressor._complete(system, user)  # type: ignore[attr-defined]


class _BaseCompressor:
    name: str
    model: str

    def compress(
        self,
        text: str,
        *,
        title: str,
        source_type: str,
        source: str | None = None,
        url: str | None = None,
    ) -> KnowledgeUnit:
        typed: SourceType = source_type if source_type in (
            "youtube",
            "bilibili",
            "twitter",
            "pdf",
            "docx",
            "md",
            "txt",
            "web",
            "audio",
            "notes",
        ) else "notes"
        raw = self._complete(
            COMPRESS_SYSTEM,
            build_user_prompt(title or "untitled", typed, text),
        )
        payload = extract_json_object(raw)
        return knowledge_unit_from_payload(
            payload,
            source=source or title or typed,
            source_type=typed,
            url=url,
            fallback_title=title or "untitled",
        )

    def _complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class OllamaCompressor(_BaseCompressor):
    name = "ollama"

    def __init__(self) -> None:
        self.model = config.OLLAMA_MODEL

    def _complete(self, system: str, user: str) -> str:
        from ollama import Client

        client = Client(host=config.OLLAMA_HOST)
        response = client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            format="json",
            options={
                "temperature": 0.2,
                "num_ctx": 32768,
                "num_predict": 8192,
            },
        )
        return response["message"]["content"]


class OpenAICompressor(_BaseCompressor):
    name = "openai"

    def __init__(self) -> None:
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is empty; set it in .env")
        self.model = config.OPENAI_MODEL
        self._api_key = config.OPENAI_API_KEY
        self._base_url: str | None = None

    def _complete(self, system: str, user: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        response = client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError(f"{self.name} returned empty content")
        return content


class DeepSeekCompressor(OpenAICompressor):
    name = "deepseek"

    def __init__(self) -> None:
        if not config.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is empty; set it in .env")
        self.model = config.DEEPSEEK_MODEL
        self._api_key = config.DEEPSEEK_API_KEY
        self._base_url = config.DEEPSEEK_BASE_URL


class GeminiCompressor(_BaseCompressor):
    name = "gemini"

    def __init__(self) -> None:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is empty; set it in .env")
        self.model = config.GEMINI_MODEL

    def _complete(self, system: str, user: str) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("gemini returned empty content")
        return text
