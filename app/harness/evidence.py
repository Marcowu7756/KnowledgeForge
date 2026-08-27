from __future__ import annotations

from pathlib import Path

from app import config
from app.harness.artifact import sha256_file
from app.knowledge.object import ModelVersions
from app.local_models import configured_path, readiness


HARNESS_VERSION = "harness_v0.1"


def capture_model_versions() -> ModelVersions:
    """Freeze currently configured local intelligence versions for evidence."""
    rows = readiness()
    whisper = configured_path("whisper")
    embed = configured_path("embed")
    tts = configured_path("tts")
    vocos = configured_path("vocos")
    ocr = configured_path("ocr")
    return ModelVersions(
        llm=config.OLLAMA_MODEL,
        llm_provider=config.LLM_PROVIDER,
        asr=str(whisper) if whisper else config.WHISPER_MODEL,
        embed=str(embed) if embed else config.EMBED_MODEL_PATH,
        tts=str(tts) if tts else config.TTS_MODEL_PATH,
        vocos=str(vocos) if vocos else config.VOCOS_MODEL_PATH,
        ocr=str(ocr) if ocr else config.PADDLEX_CACHE_HOME,
        harness=HARNESS_VERSION,
    )


def file_hash(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return sha256_file(path)
