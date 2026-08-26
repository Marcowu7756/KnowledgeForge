from __future__ import annotations

from pathlib import Path

from app.models import IngestedSource


def ingest_pdf(path: str | Path) -> IngestedSource:
    """Phase 2: extract text from a local PDF."""
    raise NotImplementedError(
        f"Phase 2: PDF ingest is not wired yet. Planned source: {path}"
    )
