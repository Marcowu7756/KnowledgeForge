from __future__ import annotations

from pathlib import Path

from app.ingest.asr import AsrError, is_audio_file, transcribe_file
from app.ingest.errors import FileIngestError
from app.models import IngestedSource


class AudioIngestError(FileIngestError):
    """Local audio ingest failed."""


def ingest_audio(path: str | Path) -> IngestedSource:
    """Independent audio source → transcript text for knowledge compression."""
    audio = Path(path).expanduser().resolve()
    if not audio.is_file():
        raise AudioIngestError(f"audio file not found: {audio}")
    if not is_audio_file(audio):
        raise AudioIngestError(
            f"unsupported audio type {audio.suffix}; "
            "use .wav .mp3 .m4a .flac .ogg .webm"
        )

    try:
        text, language = transcribe_file(audio)
    except AsrError as exc:
        raise AudioIngestError(str(exc)) from exc

    title = audio.stem.replace("_", " ").strip() or "Audio note"
    return IngestedSource(
        title=title,
        source_type="audio",
        path=str(audio),
        url=None,
        text=text,
        metadata={
            "transcript_language": language,
            "transcript_source": "whisper",
            "transcript_chars": len(text),
            "audio_suffix": audio.suffix.lower(),
            "audio_bytes": audio.stat().st_size,
        },
    )
