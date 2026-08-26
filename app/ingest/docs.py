from __future__ import annotations

from pathlib import Path

from app.models import IngestedSource


def ingest_file(path: str | Path) -> IngestedSource:
    """Phase 2: extract text from MD / TXT / DOCX (and PDF via ingest_pdf)."""
    raise NotImplementedError(
        f"Phase 2: file ingest is not wired yet. Planned source: {path}"
    )
