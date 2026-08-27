from __future__ import annotations

from pathlib import Path

from app import config
from app.local_models import ocr_ready
from app.models import IngestedSource

_OCR_ENGINE: object | None = None

_IMAGE_SUFFIXES = {ext.lower() for ext in config.SUPPORTED_IMAGE_TYPES}


class ImageIngestError(RuntimeError):
    """Raised when an image cannot be OCR'd locally."""


def _require_ocr_ready() -> None:
    if not ocr_ready():
        raise ImageIngestError(
            "PaddleOCR models missing — run: python main.py models pull --only ocr"
        )


def _get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is not None:
        return _OCR_ENGINE
    _require_ocr_ready()
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:  # pragma: no cover
        raise ImageIngestError(
            "paddleocr not installed. Run: pip install paddleocr"
        ) from exc

    from app.local_models import apply_paddle_env

    apply_paddle_env()
    _OCR_ENGINE = PaddleOCR(
        lang=config.PADDLE_OCR_LANG,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    return _OCR_ENGINE


def _lines_from_result(payload: object) -> list[str]:
    lines: list[str] = []

    def _walk(node: object) -> None:
        if node is None:
            return
        if isinstance(node, str):
            text = node.strip()
            if text:
                lines.append(text)
            return
        if isinstance(node, dict):
            for key in ("rec_text", "text", "transcription"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    lines.append(value.strip())
            for key in ("rec_texts", "texts", "lines"):
                value = node.get(key)
                if isinstance(value, list):
                    for item in value:
                        _walk(item)
            for value in node.values():
                if isinstance(value, (dict, list, tuple)):
                    _walk(value)
            return
        if isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)

    _walk(payload)
    # Preserve order, drop duplicates.
    seen: set[str] = set()
    ordered: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            ordered.append(line)
    return ordered


def ingest_image(path: str | Path) -> IngestedSource:
    """OCR a local image into plain text (offline PaddleOCR)."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise ImageIngestError(f"not a file: {file_path}")
    if file_path.suffix.lower() not in _IMAGE_SUFFIXES:
        raise ImageIngestError(
            f"unsupported image type: {file_path.suffix} "
            f"(supported: {', '.join(sorted(_IMAGE_SUFFIXES))})"
        )

    engine = _get_ocr_engine()
    try:
        result = engine.predict(str(file_path))
    except AttributeError:
        result = engine.ocr(str(file_path))

    lines = _lines_from_result(result)
    if not lines:
        raise ImageIngestError(f"OCR produced no text: {file_path}")

    return IngestedSource(
        source_type="image",
        title=file_path.stem,
        text="\n".join(lines),
        path=str(file_path),
        metadata={
            "ocr_engine": "paddleocr",
            "ocr_lang": config.PADDLE_OCR_LANG,
            "line_count": len(lines),
        },
    )
