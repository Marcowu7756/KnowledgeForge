from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.models import KnowledgeUnit, SourceType
from app.knowledge.taxonomy import TaxonomyBlock, taxonomy_from_payload

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class CompressParseError(ValueError):
    """LLM output could not be turned into a KnowledgeUnit."""


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    return [str(value).strip()] if str(value).strip() else []


def extract_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if not text:
        raise CompressParseError("empty LLM response")

    candidates: list[str] = []
    fence = _JSON_FENCE.search(text)
    if fence:
        candidates.append(fence.group(1))
    obj = _JSON_OBJECT.search(text)
    if obj:
        candidates.append(obj.group(0))
    candidates.append(text)

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(data, dict):
            return data
        last_error = CompressParseError(f"JSON root is {type(data).__name__}, expected object")
    raise CompressParseError(f"could not parse Knowledge Unit JSON: {last_error}")


def knowledge_unit_from_payload(
    payload: dict[str, Any],
    *,
    source: str,
    source_type: SourceType,
    url: str | None,
    fallback_title: str,
    taxonomy: TaxonomyBlock | None = None,
) -> KnowledgeUnit:
    title = str(payload.get("title") or fallback_title).strip() or fallback_title
    summary = str(
        payload.get("summary")
        or payload.get("core_idea")
        or payload.get("coreIdea")
        or ""
    ).strip()
    if not summary:
        raise CompressParseError("LLM JSON missing required field: summary")

    tax = taxonomy or taxonomy_from_payload(
        payload.get("taxonomy_path") or payload.get("taxonomy")
    )

    try:
        return KnowledgeUnit(
            title=title,
            source=source,
            type=source_type,
            url=url,
            summary=summary,
            concepts=_as_str_list(payload.get("concepts")),
            definitions=_as_str_list(payload.get("definitions")),
            key_points=_as_str_list(payload.get("key_points")),
            mechanisms=_as_str_list(payload.get("mechanisms")),
            relationships=_as_str_list(payload.get("relationships")),
            timeline=_as_str_list(payload.get("timeline")),
            claims=_as_str_list(payload.get("claims")),
            evidence=_as_str_list(payload.get("evidence")),
            formulas=_as_str_list(payload.get("formulas")),
            examples=_as_str_list(payload.get("examples")),
            prerequisites=_as_str_list(payload.get("prerequisites")),
            unknowns=_as_str_list(payload.get("unknowns")),
            tags=_as_str_list(payload.get("tags")),
            taxonomy=tax,
        )
    except ValidationError as exc:
        raise CompressParseError(str(exc)) from exc
