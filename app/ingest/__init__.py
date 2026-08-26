from __future__ import annotations

from app.ingest.docs import ingest_file
from app.ingest.pdf import ingest_pdf
from app.ingest.youtube import ingest_youtube
from app.models import IngestedSource


def ingest(kind: str, target: str) -> IngestedSource:
    if kind == "youtube":
        return ingest_youtube(target)
    if kind == "pdf":
        return ingest_pdf(target)
    if kind == "file":
        return ingest_file(target)
    raise ValueError(f"unsupported ingest kind: {kind}")
