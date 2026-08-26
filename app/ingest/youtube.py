from __future__ import annotations

from app.models import IngestedSource


def ingest_youtube(url: str) -> IngestedSource:
    """Phase 1: fetch title, description, captions, then return extracted text."""
    raise NotImplementedError(
        "Phase 1: YouTube ingest is not wired yet. "
        f"Planned: title + description + captions from {url}"
    )
