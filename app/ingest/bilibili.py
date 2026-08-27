from __future__ import annotations

import re
from typing import Any

import requests

from app import config
from app.ingest.video_common import (
    VideoIngestError,
    asr_transcribe,
    download_subtitles,
    fetch_metadata,
)
from app.models import IngestedSource

_BV_RE = re.compile(
    r"(?:bilibili\.com/video/(BV[\w]+)|bilibili\.com/video/av(\d+)|b23\.tv/[\w]+)"
)
# Bilibili AI / human subs vary by uploader; prefer Chinese.
_LANG_PRIORITY = ("ai-zh", "zh-Hans", "zh-CN", "zh", "zh-Hant", "en", "en-US")
_BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KnowledgeForge/0.2",
    "Referer": "https://www.bilibili.com",
}


class BilibiliIngestError(VideoIngestError):
    """Raised when a Bilibili URL cannot be turned into extractable text."""


def is_bilibili_url(url: str) -> bool:
    url = url.strip().lower()
    return "bilibili.com" in url or "b23.tv" in url


def extract_bilibili_id(url: str) -> str | None:
    url = url.strip()
    match = _BV_RE.search(url)
    if not match:
        return None
    return match.group(1) or f"av{match.group(2)}"


def _canonical_url(url: str, info: dict[str, Any]) -> str:
    webpage = (info.get("webpage_url") or info.get("original_url") or url).strip()
    if "bilibili.com" in webpage or "b23.tv" in webpage:
        return webpage
    video_id = info.get("id") or extract_bilibili_id(url) or "unknown"
    return f"https://www.bilibili.com/video/{video_id}"


def _fetch_view(bvid: str) -> dict[str, Any]:
    resp = requests.get(
        "https://api.bilibili.com/x/web-interface/view",
        params={"bvid": bvid},
        headers=_BILI_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("code") != 0 or not payload.get("data"):
        raise BilibiliIngestError(f"Bilibili view API failed for {bvid}")
    return payload["data"]


def _parse_bilibili_subtitle_json(payload: dict[str, Any]) -> str:
    body = payload.get("body") or []
    lines = [item.get("content", "").strip() for item in body if item.get("content")]
    return "\n".join(line for line in lines if line)


def _bilibili_api_subtitles(bvid: str) -> tuple[str, str] | None:
    """Fetch CC/AI subtitles from Bilibili player API when available."""
    view = _fetch_view(bvid)
    pages = view.get("pages") or []
    if not pages:
        return None
    cid = pages[0].get("cid")
    aid = view.get("aid")
    if not cid or not aid:
        return None

    resp = requests.get(
        "https://api.bilibili.com/x/player/wbi/v2",
        params={"aid": aid, "cid": cid},
        headers=_BILI_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    player = resp.json()
    if player.get("code") != 0:
        return None

    subtitles = (player.get("data") or {}).get("subtitle", {}).get("subtitles") or []
    if not subtitles:
        return None

    by_lang = {item.get("lan"): item for item in subtitles if item.get("lan")}
    for lang in _LANG_PRIORITY:
        item = by_lang.get(lang)
        if not item:
            continue
        sub_url = (item.get("subtitle_url") or "").strip()
        if not sub_url:
            continue
        if sub_url.startswith("//"):
            sub_url = f"https:{sub_url}"
        sub_resp = requests.get(sub_url, headers=_BILI_HEADERS, timeout=30)
        sub_resp.raise_for_status()
        text = _parse_bilibili_subtitle_json(sub_resp.json())
        if text.strip():
            return text, lang

    for item in subtitles:
        sub_url = (item.get("subtitle_url") or "").strip()
        if not sub_url:
            continue
        if sub_url.startswith("//"):
            sub_url = f"https:{sub_url}"
        sub_resp = requests.get(sub_url, headers=_BILI_HEADERS, timeout=30)
        sub_resp.raise_for_status()
        text = _parse_bilibili_subtitle_json(sub_resp.json())
        if text.strip():
            return text, str(item.get("lan") or "sub")
    return None


def ingest_bilibili(url: str) -> IngestedSource:
    """Fetch title/description + subtitles (or Whisper ASR fallback)."""
    url = url.strip()
    if not is_bilibili_url(url):
        raise BilibiliIngestError(f"not a recognizable Bilibili URL: {url}")

    info = fetch_metadata(url)
    canonical = _canonical_url(url, info)
    video_id = str(info.get("id") or extract_bilibili_id(url) or "unknown")
    bvid = str(info.get("bvid") or extract_bilibili_id(url) or video_id)
    title = (info.get("title") or video_id).strip()
    description = (info.get("description") or "").strip()
    uploader = (info.get("uploader") or info.get("channel") or "").strip()
    duration = info.get("duration")

    subtitle = None
    if bvid.startswith("BV"):
        subtitle = _bilibili_api_subtitles(bvid)
    if subtitle is None:
        subtitle = download_subtitles(canonical, lang_priority=_LANG_PRIORITY)
    if subtitle is not None:
        body, language = subtitle
        source_kind = "subtitles"
    else:
        print(
            f"[bilibili] no subtitles; Whisper ASR "
            f"model={config.WHISPER_MODEL} ...",
            flush=True,
        )
        body, language = asr_transcribe(canonical, label="bilibili")
        source_kind = "asr"

    parts = [
        f"# {title}",
        f"Uploader: {uploader}" if uploader else "",
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
        source_type="bilibili",
        title=title,
        text=text,
        url=canonical,
        metadata={
            "video_id": video_id,
            "bvid": bvid,
            "uploader": uploader,
            "duration_sec": duration,
            "transcript_language": language,
            "transcript_source": source_kind,
            "description_chars": len(description),
            "transcript_chars": len(body),
        },
    )
