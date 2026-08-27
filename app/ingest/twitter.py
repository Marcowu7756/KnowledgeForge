from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any

import requests

from app import config
from app.models import IngestedSource

_TWEET_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)"
)
_SYNDICATION = "https://cdn.syndication.twimg.com/tweet-result"
_API_BASE = "https://api.twitter.com/2"


class TwitterIngestError(RuntimeError):
    """Raised when a Twitter/X URL or timeline cannot be ingested."""


def syndication_token(tweet_id: str) -> str:
    """Token required by Twitter's public syndication CDN (JS Number.toString(36))."""
    value = (int(tweet_id) / 1e15) * math.pi
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if value == 0:
        base36 = "0"
    else:
        integer = int(value)
        fraction = value - integer
        if integer == 0:
            base36 = "0"
        else:
            digits: list[str] = []
            n = integer
            while n:
                n, rem = divmod(n, 36)
                digits.append(chars[rem])
            base36 = "".join(reversed(digits))
        if fraction:
            base36 += "."
            for _ in range(12):
                fraction *= 36
                digit = int(fraction)
                base36 += chars[digit]
                fraction -= digit
                if fraction == 0:
                    break
    return re.sub(r"(0+|\.)", "", base36)


def extract_tweet_id(url: str) -> str:
    url = url.strip()
    if re.fullmatch(r"\d+", url):
        return url
    match = _TWEET_URL_RE.search(url)
    if not match:
        raise TwitterIngestError(f"not a recognizable tweet URL: {url}")
    return match.group(1)


def is_twitter_url(url: str) -> bool:
    url = url.strip().lower()
    return "twitter.com" in url or "x.com" in url


def _fetch_tweet_syndication(tweet_id: str) -> dict[str, Any]:
    resp = requests.get(
        _SYNDICATION,
        params={
            "id": tweet_id,
            "lang": "zh",
            "token": syndication_token(tweet_id),
        },
        timeout=30,
        headers={"User-Agent": "KnowledgeForge/0.2"},
    )
    if resp.status_code == 404:
        raise TwitterIngestError(f"tweet not found or not public: {tweet_id}")
    resp.raise_for_status()
    payload = resp.json()
    if not payload or not payload.get("text"):
        raise TwitterIngestError(f"empty syndication payload for tweet {tweet_id}")
    return payload


def _fetch_tweet_api(tweet_id: str) -> dict[str, Any]:
    data = _api_get(
        f"/tweets/{tweet_id}",
        params={
            "tweet.fields": "created_at,public_metrics,lang,referenced_tweets",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )
    tweet = data.get("data") or {}
    if not tweet.get("text"):
        raise TwitterIngestError(f"Twitter API returned no text for {tweet_id}")
    users = {
        u.get("id"): u for u in (data.get("includes") or {}).get("users") or []
    }
    author = users.get(tweet.get("author_id"), {})
    return {
        "text": tweet.get("text"),
        "created_at": tweet.get("created_at"),
        "public_metrics": tweet.get("public_metrics") or {},
        "id_str": tweet_id,
        "user": {
            "screen_name": author.get("username") or "unknown",
            "name": author.get("name") or "",
        },
    }


def _fetch_tweet(tweet_id: str) -> dict[str, Any]:
    try:
        return _fetch_tweet_syndication(tweet_id)
    except TwitterIngestError:
        if config.TWITTER_BEARER_TOKEN.strip():
            return _fetch_tweet_api(tweet_id)
        raise


def _format_tweet_block(payload: dict[str, Any], *, tweet_id: str | None = None) -> str:
    user = payload.get("user") or {}
    screen = user.get("screen_name") or user.get("name") or "unknown"
    created = payload.get("created_at") or ""
    text = (payload.get("text") or "").strip()
    tid = tweet_id or str(payload.get("id_str") or payload.get("id") or "")
    url = f"https://x.com/{screen}/status/{tid}" if tid else ""
    metrics = payload.get("public_metrics") or {}
    metric_bits = []
    for key in ("like_count", "retweet_count", "reply_count", "quote_count"):
        if key in metrics:
            metric_bits.append(f"{key}={metrics[key]}")
    lines = [
        f"## @{screen} — {created}",
        f"URL: {url}" if url else "",
        text,
    ]
    if metric_bits:
        lines.append("Metrics: " + ", ".join(metric_bits))
    quoted = payload.get("quoted_tweet") or payload.get("quoted_status")
    if isinstance(quoted, dict) and quoted.get("text"):
        lines.extend(["", "### Quoted", quoted.get("text", "").strip()])
    return "\n".join(line for line in lines if line)


def _tweet_title(payload: dict[str, Any], tweet_id: str) -> str:
    user = payload.get("user") or {}
    screen = user.get("screen_name") or user.get("name") or "unknown"
    text = (payload.get("text") or "").strip().replace("\n", " ")
    preview = text[:72] + ("…" if len(text) > 72 else "")
    return f"@{screen}: {preview or tweet_id}"


def ingest_twitter(url: str) -> IngestedSource:
    """Ingest one public tweet (no API key required)."""
    tweet_id = extract_tweet_id(url)
    payload = _fetch_tweet(tweet_id)
    user = payload.get("user") or {}
    screen = user.get("screen_name") or user.get("name") or "unknown"
    canonical = f"https://x.com/{screen}/status/{tweet_id}"
    title = _tweet_title(payload, tweet_id)
    body = _format_tweet_block(payload, tweet_id=tweet_id)
    text = "\n".join(
        [
            f"# {title}",
            f"URL: {canonical}",
            "",
            body,
        ]
    )
    return IngestedSource(
        source_type="twitter",
        title=title,
        text=text,
        url=canonical,
        metadata={
            "tweet_id": tweet_id,
            "author": screen,
            "created_at": payload.get("created_at"),
            "ingest_mode": "syndication",
        },
    )


def _require_bearer() -> str:
    token = config.TWITTER_BEARER_TOKEN.strip()
    if not token:
        raise TwitterIngestError(
            "TWITTER_BEARER_TOKEN is required for timeline/search. "
            "Single tweet URLs work without it."
        )
    return token


def _api_get(path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    token = _require_bearer()
    resp = requests.get(
        f"{_API_BASE}{path}",
        params=params or {},
        timeout=30,
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == 401:
        raise TwitterIngestError("Twitter API unauthorized — check TWITTER_BEARER_TOKEN")
    if resp.status_code == 404:
        raise TwitterIngestError("Twitter API resource not found")
    resp.raise_for_status()
    return resp.json()


def _resolve_username(username: str) -> str:
    handle = username.lstrip("@").strip()
    if not handle:
        raise TwitterIngestError("username is empty")
    data = _api_get(f"/users/by/username/{handle}", params={"user.fields": "name"})
    user = data.get("data") or {}
    user_id = user.get("id")
    if not user_id:
        raise TwitterIngestError(f"user not found: @{handle}")
    return str(user_id)


def fetch_timeline(username: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Fetch recent tweets for a user via Twitter API v2."""
    user_id = _resolve_username(username)
    limit = max(1, min(limit, 100))
    data = _api_get(
        f"/users/{user_id}/tweets",
        params={
            "max_results": limit,
            "tweet.fields": "created_at,public_metrics,lang,referenced_tweets",
            "exclude": "retweets,replies",
        },
    )
    return list(data.get("data") or [])


def ingest_twitter_timeline(username: str, *, limit: int = 10) -> IngestedSource:
    """Batch recent tweets into one signal digest for compression."""
    handle = username.lstrip("@").strip()
    tweets = fetch_timeline(handle, limit=limit)
    if not tweets:
        raise TwitterIngestError(f"no recent tweets for @{handle}")

    blocks = [
        f"# Twitter signals — @{handle}",
        f"Fetched: {datetime.now(timezone.utc).isoformat()}",
        f"Count: {len(tweets)}",
        "",
        "Compress into a signal digest: themes, claims, links, and what changed recently.",
        "",
    ]
    for tweet in tweets:
        tid = str(tweet.get("id") or "")
        created = tweet.get("created_at") or ""
        text = (tweet.get("text") or "").strip()
        metrics = tweet.get("public_metrics") or {}
        blocks.extend(
            [
                f"## {created} — {tid}",
                f"URL: https://x.com/{handle}/status/{tid}",
                text,
                "Metrics: "
                + ", ".join(f"{k}={v}" for k, v in metrics.items())
                if metrics
                else "",
                "",
            ]
        )

    return IngestedSource(
        source_type="twitter",
        title=f"Twitter signals — @{handle}",
        text="\n".join(block for block in blocks if block is not None),
        url=f"https://x.com/{handle}",
        metadata={
            "author": handle,
            "tweet_count": len(tweets),
            "tweet_ids": [str(t.get("id")) for t in tweets if t.get("id")],
            "ingest_mode": "timeline",
        },
    )
