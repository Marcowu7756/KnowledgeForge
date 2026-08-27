from __future__ import annotations

from pathlib import Path

from app.ingest.errors import FileIngestError
from app.models import IngestedSource


def _extract_with_pdfplumber(path: Path) -> tuple[str, int]:
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append(text)
        page_count = len(pdf.pages)
    return "\n\n".join(pages), page_count


def _extract_with_pypdf(path: Path) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(text)
    return "\n\n".join(pages), len(reader.pages)


def ingest_pdf(path: str | Path) -> IngestedSource:
    """Extract text from a local PDF. Source file is never modified."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise FileIngestError(f"not a file: {file_path}")
    if file_path.suffix.lower() != ".pdf":
        raise FileIngestError(f"expected .pdf, got: {file_path.suffix}")

    engine = "pdfplumber"
    try:
        text, page_count = _extract_with_pdfplumber(file_path)
    except Exception:
        engine = "pypdf"
        try:
            text, page_count = _extract_with_pypdf(file_path)
        except Exception as exc:  # noqa: BLE001
            raise FileIngestError(f"PDF extract failed: {file_path}: {exc}") from exc

    text = text.strip()
    if not text:
        raise FileIngestError(
            f"no extractable text in PDF (scanned/image-only?): {file_path}"
        )

    return IngestedSource(
        source_type="pdf",
        title=file_path.stem,
        text=text,
        path=str(file_path),
        metadata={
            "bytes": file_path.stat().st_size,
            "suffix": ".pdf",
            "pages": page_count,
            "engine": engine,
            "read_only_source": True,
        },
    )
