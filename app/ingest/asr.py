from __future__ import annotations

from pathlib import Path

from app import config
from app.local_models import whisper_ready


class AsrError(RuntimeError):
    """Local Whisper ASR failed."""


_AUDIO_SUFFIX = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in _AUDIO_SUFFIX


def transcribe_file(path: str | Path) -> tuple[str, str]:
    """Transcribe a local audio file with faster-whisper.

    Returns (text, language_tag) where language_tag looks like whisper:zh:model.
    """
    audio = Path(path).expanduser().resolve()
    if not audio.is_file():
        raise AsrError(f"audio file not found: {audio}")
    if not is_audio_file(audio):
        raise AsrError(f"unsupported audio type: {audio.suffix}")
    if not whisper_ready():
        raise AsrError(
            "whisper model not ready — run: python main.py models pull --only whisper"
        )

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover
        raise AsrError("faster-whisper not installed") from exc

    print(
        f"[asr] Whisper {config.WHISPER_MODEL} on {audio.name} …",
        flush=True,
    )
    model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(audio),
        language=config.WHISPER_LANGUAGE,
        vad_filter=True,
    )
    lines = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
    if not lines:
        raise AsrError(f"ASR produced empty transcript for {audio}")
    lang = getattr(info, "language", None) or (config.WHISPER_LANGUAGE or "auto")
    return "\n".join(lines), f"whisper:{lang}:{config.WHISPER_MODEL}"
