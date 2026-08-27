"""Minimal compose payload contract (paper / lecture)."""

from __future__ import annotations

from typing import Any


class ComposePayloadError(ValueError):
    """LLM payload failed the compose schema contract."""


def validate_compose_payload(kind: str, payload: dict[str, Any]) -> None:
    """Raise ComposePayloadError with a multi-line message if invalid."""
    kind = (kind or "").strip().lower()
    errors: list[str] = []
    if not isinstance(payload, dict):
        raise ComposePayloadError("payload must be a JSON object")

    title = str(payload.get("title") or "").strip()
    if not title:
        errors.append("missing required field: title")

    if kind == "paper":
        abstract = str(payload.get("abstract") or "").strip()
        if not abstract:
            errors.append("missing required field: abstract")
        sections = payload.get("sections")
        if not isinstance(sections, list) or not sections:
            errors.append("missing required field: sections (non-empty list)")
        else:
            for i, sec in enumerate(sections):
                if not isinstance(sec, dict):
                    errors.append(f"sections[{i}] must be an object")
                    continue
                if not str(sec.get("heading") or "").strip():
                    errors.append(f"sections[{i}].heading required")
                if not str(sec.get("body") or "").strip():
                    errors.append(f"sections[{i}].body required")
    elif kind == "lecture":
        script = str(payload.get("script") or "").strip()
        if not script:
            errors.append("missing required field: script")
        outline = payload.get("outline")
        if not isinstance(outline, list) or not outline:
            errors.append("missing required field: outline (non-empty list)")
    else:
        errors.append(f"unknown compose kind: {kind}")

    if errors:
        raise ComposePayloadError("\n".join(errors))
