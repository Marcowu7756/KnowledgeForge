from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from app import config


class VideoIngestError(RuntimeError):
    """Raised when a video URL cannot be turned into extractable text."""


def fetch_metadata(url: str) -> dict[str, Any]:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise VideoIngestError(f"yt-dlp returned no metadata for {url}")
    return info


def download_audio(url: str, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(dest_dir / "%(id)s.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id") if info else None
    if not video_id:
        raise VideoIngestError(f"audio download failed for {url}")
    path = dest_dir / f"{video_id}.mp3"
    if not path.exists():
        matches = list(dest_dir.glob(f"{video_id}.*"))
        if not matches:
            raise VideoIngestError(f"audio file missing after download: {url}")
        path = matches[0]
    return path


def asr_transcribe(url: str, *, label: str) -> tuple[str, str]:
    """Download audio and transcribe with faster-whisper."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover
        raise VideoIngestError(
            f"no subtitles and faster-whisper is not installed ({label})"
        ) from exc

    with tempfile.TemporaryDirectory(prefix=f"kf_{label}_") as tmp:
        audio_path = download_audio(url, Path(tmp))
        model = WhisperModel(
            config.WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
        )
        segments, info = model.transcribe(
            str(audio_path),
            language=config.WHISPER_LANGUAGE,
            vad_filter=True,
        )
        lines = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
        if not lines and config.WHISPER_LANGUAGE:
            segments, info = model.transcribe(
                str(audio_path),
                language=None,
                vad_filter=True,
            )
            lines = [
                seg.text.strip() for seg in segments if seg.text and seg.text.strip()
            ]
        if not lines:
            raise VideoIngestError(f"ASR produced empty transcript for {url}")
        lang = getattr(info, "language", None) or config.WHISPER_LANGUAGE or "asr"
        return "\n".join(lines), f"whisper:{lang}:{config.WHISPER_MODEL}"


_SRT_TIME_RE = re.compile(
    r"^\d+\s*$|^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}\s*$"
)


def parse_srt(content: str) -> str:
    lines: list[str] = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or _SRT_TIME_RE.match(line):
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _subtitle_candidates(tmp_dir: Path, lang: str) -> list[Path]:
    patterns = [
        f"*.{lang}.srt",
        f"*.{lang}.vtt",
        f"*-{lang}.srt",
        f"*-{lang}.vtt",
    ]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(tmp_dir.glob(pattern))
    return found


def download_subtitles(
    url: str,
    *,
    lang_priority: tuple[str, ...],
) -> tuple[str, str] | None:
    """Download subtitles via yt-dlp; return (text, language) or None."""
    with tempfile.TemporaryDirectory(prefix="kf_sub_") as tmp_name:
        tmp_dir = Path(tmp_name)
        outtmpl = str(tmp_dir / "sub")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitlesformat": "srt/best",
            "outtmpl": outtmpl,
        }
        with YoutubeDL(opts) as ydl:
            ydl.download([url])

        for lang in lang_priority:
            for path in _subtitle_candidates(tmp_dir, lang):
                text = parse_srt(path.read_text(encoding="utf-8", errors="ignore"))
                if text.strip():
                    return text, lang

        for path in sorted(tmp_dir.glob("*.srt")) + sorted(tmp_dir.glob("*.vtt")):
            text = parse_srt(path.read_text(encoding="utf-8", errors="ignore"))
            if text.strip():
                stem = path.stem
                lang = stem.split(".")[-1] if "." in stem else "sub"
                return text, lang
    return None
