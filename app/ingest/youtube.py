from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)
from yt_dlp import YoutubeDL

from app import config
from app.models import IngestedSource

_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)"
    r"([A-Za-z0-9_-]{11})"
)

# Prefer Chinese when available, then English, then anything listed.
_LANG_PRIORITY = ("zh-Hans", "zh-CN", "zh", "zh-Hant", "zh-TW", "en", "en-US", "en-GB")


class YouTubeIngestError(RuntimeError):
    """Raised when a YouTube URL cannot be turned into extractable text."""


def extract_video_id(url: str) -> str:
    url = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    match = _VIDEO_ID_RE.search(url)
    if not match:
        raise YouTubeIngestError(f"not a recognizable YouTube URL: {url}")
    return match.group(1)


def _fetch_metadata(url: str) -> dict[str, Any]:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise YouTubeIngestError(f"yt-dlp returned no metadata for {url}")
    return info


def _caption_text(video_id: str) -> tuple[str, str] | None:
    """Return (transcript_text, language_code) or None if unavailable."""
    api = YouTubeTranscriptApi()
    try:
        listing = api.list(video_id)
    except (TranscriptsDisabled, VideoUnavailable, Exception):
        return None

    try:
        transcript = listing.find_transcript(_LANG_PRIORITY)
    except NoTranscriptFound:
        try:
            transcript = next(iter(listing))
        except StopIteration:
            return None

    fetched = transcript.fetch()
    lines = [snippet.text.strip() for snippet in fetched if snippet.text.strip()]
    if not lines:
        return None
    return "\n".join(lines), transcript.language_code


def _download_audio(url: str, dest_dir: Path) -> Path:
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
        raise YouTubeIngestError(f"audio download failed for {url}")
    path = dest_dir / f"{video_id}.mp3"
    if not path.exists():
        # yt-dlp may leave another extension if postprocess skipped.
        matches = list(dest_dir.glob(f"{video_id}.*"))
        if not matches:
            raise YouTubeIngestError(f"audio file missing after download: {url}")
        path = matches[0]
    return path


def _asr_text(url: str, video_id: str) -> tuple[str, str]:
    """Download audio and transcribe with faster-whisper."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover
        raise YouTubeIngestError(
            "no captions and faster-whisper is not installed"
        ) from exc

    with tempfile.TemporaryDirectory(prefix="kf_yt_") as tmp:
        audio_path = _download_audio(url, Path(tmp))
        # CPU is reliable on Windows + AMD; float32 for small/base models.
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
        if not lines:
            raise YouTubeIngestError(f"ASR produced empty transcript for {video_id}")
        lang = getattr(info, "language", None) or config.WHISPER_LANGUAGE or "asr"
        return "\n".join(lines), f"whisper:{lang}:{config.WHISPER_MODEL}"


def ingest_youtube(url: str) -> IngestedSource:
    """Fetch title/description + captions (or ASR fallback)."""
    video_id = extract_video_id(url)
    canonical = f"https://www.youtube.com/watch?v={video_id}"

    info = _fetch_metadata(canonical)
    title = (info.get("title") or video_id).strip()
    description = (info.get("description") or "").strip()
    channel = (info.get("channel") or info.get("uploader") or "").strip()
    duration = info.get("duration")

    caption = _caption_text(video_id)
    if caption is not None:
        body, language = caption
        source_kind = "captions"
    else:
        print(
            f"[youtube] no captions; Whisper ASR "
            f"model={config.WHISPER_MODEL} ...",
            flush=True,
        )
        body, language = _asr_text(canonical, video_id)
        source_kind = "asr"

    parts = [
        f"# {title}",
        f"Channel: {channel}" if channel else "",
        f"URL: {canonical}",
        "",
        "## Description",
        description or "(none)",
        "",
        f"## Transcript ({language})",
        body,
    ]
    text = "\n".join(part for part in parts if part is not None)

    return IngestedSource(
        source_type="youtube",
        title=title,
        text=text,
        url=canonical,
        metadata={
            "video_id": video_id,
            "channel": channel,
            "duration_sec": duration,
            "transcript_language": language,
            "transcript_source": source_kind,
            "description_chars": len(description),
            "transcript_chars": len(body),
        },
    )
