from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(os.getenv("KF_ROOT", str(Path(__file__).resolve().parent.parent))).expanduser().resolve()
load_dotenv(ROOT / ".env")

MODELS_DIR = ROOT / "models"
HF_HOME = Path(os.getenv("HF_HOME", str(MODELS_DIR / ".hf"))).expanduser()
if not HF_HOME.is_absolute():
    HF_HOME = ROOT / HF_HOME
DATA_DIR = ROOT / "data"
INBOX_DIR = DATA_DIR / "inbox"
RAW_DIR = DATA_DIR / "raw"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
RESTRICTED_DIR = DATA_DIR / "restricted"
EXPRESSION_DIR = DATA_DIR / "expression"
PACKAGES_DIR = DATA_DIR / "packages"
RECONSTRUCT_DIR = DATA_DIR / "reconstruct"
RETRIEVE_DIR = DATA_DIR / "retrieve"
COMPOSE_DIR = DATA_DIR / "compose"
VOICES_DIR = DATA_DIR / "voices"
AUDIT_DIR = DATA_DIR / "audit"
UI_DIR = DATA_DIR / "ui"

# Neighbor Digital Self (consume Skills; do not become that Runtime).
DIGITAL_SELF_ROOT = Path(
    os.getenv("DIGITAL_SELF_ROOT", r"D:\DigitalSelf")
).expanduser().resolve()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

# Whisper ASR fallback when YouTube has no captions.
WHISPER_MODEL = os.getenv(
    "WHISPER_MODEL",
    str(MODELS_DIR / "faster-whisper-medium"),
).strip() or str(MODELS_DIR / "faster-whisper-medium")
_WHISPER_LANG = os.getenv("WHISPER_LANGUAGE", "").strip()
WHISPER_LANGUAGE = _WHISPER_LANG or None

# Local embedding model for RAG (Phase 2). Path preferred over Hub id.
EMBED_MODEL_PATH = os.getenv(
    "EMBED_MODEL_PATH",
    str(MODELS_DIR / "bge-small-zh-v1.5"),
).strip() or str(MODELS_DIR / "bge-small-zh-v1.5")

# Local voice-clone TTS (F5-TTS). Optional local ckpt dir under models/.
TTS_MODEL_PATH = os.getenv("TTS_MODEL_PATH", str(MODELS_DIR / "F5-TTS")).strip()
VOCOS_MODEL_PATH = os.getenv(
    "VOCOS_MODEL_PATH",
    str(MODELS_DIR / "vocos-mel-24khz"),
).strip()
TTS_VOICE_NAME = os.getenv("TTS_VOICE_NAME", "").strip()
TTS_ENGINE = os.getenv("TTS_ENGINE", "clone").strip().lower()  # clone | system
TTS_NFE_STEP = int(os.getenv("TTS_NFE_STEP", "16") or "16")

# PaddleOCR / pix2tex local caches (Phase 1b OCR)
PADDLEX_CACHE_HOME = os.getenv(
    "PADDLEX_CACHE_HOME",
    str(MODELS_DIR / "paddlex"),
).strip() or str(MODELS_DIR / "paddlex")
PIX2TEX_MODEL_PATH = os.getenv(
    "PIX2TEX_MODEL_PATH",
    str(MODELS_DIR / "pix2tex"),
).strip() or str(MODELS_DIR / "pix2tex")
PADDLE_OCR_LANG = os.getenv("PADDLE_OCR_LANG", "ch").strip() or "ch"
PADDLE_PDX_MODEL_SOURCE = os.getenv("PADDLE_PDX_MODEL_SOURCE", "bos").strip() or "bos"

# Prefer local weights; set HF_HUB_OFFLINE=1 in .env after models are pulled.
HF_HUB_OFFLINE = os.getenv("HF_HUB_OFFLINE", "").strip()
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "").strip()

# Local-first policy: default LLM is Ollama; cloud keys are optional fallback.
LOCAL_FIRST = os.getenv("LOCAL_FIRST", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Twitter/X API v2 (optional — single tweet URLs work without a token).
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# Optional but important: attach catalog indexes to knowledge outputs.
INDEX_ENABLED = os.getenv("INDEX_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

SUPPORTED_PROVIDERS = ("openai", "gemini", "ollama", "deepseek")
SUPPORTED_FILE_TYPES = (".pdf", ".md", ".txt", ".docx")
SUPPORTED_IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def _bootstrap_local_env() -> None:
    from app.local_models import apply_offline_env

    apply_offline_env()


_bootstrap_local_env()
