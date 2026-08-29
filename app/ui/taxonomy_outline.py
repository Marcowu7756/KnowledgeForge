"""Taxonomy outline for UI — Excel-like group tree (orthogonal to access lane)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from app import config
from app.knowledge.access import (
    AccessLane,
    is_retrievable,
    lane_retrieve_ceiling,
    resolve_policy,
)
from app.knowledge.taxonomy import TaxonomyBlock
from app.storage.index import global_jsonl_path

AccessLaneName = Literal["general", "proprietary"]


def _access_from_record(rec: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    access = rec.get("access") if isinstance(rec.get("access"), dict) else {}
    classification = str(access.get("classification") or rec.get("classification") or "public")
    policy_raw = access.get("policy") if isinstance(access.get("policy"), dict) else {}
    return classification, policy_raw or {}


def _taxonomy_path(rec: dict[str, Any]) -> list[str]:
    tax = rec.get("taxonomy")
    if isinstance(tax, dict) and tax.get("path"):
        return TaxonomyBlock(path=tax.get("path")).path
    if isinstance(tax, list):
        return TaxonomyBlock(path=tax).path
    if rec.get("taxonomy_path"):
        return TaxonomyBlock(path=rec.get("taxonomy_path")).path
    return []


def _empty_node(label: str, prefix: list[str]) -> dict[str, Any]:
    return {
        "label": label,
        "prefix": list(prefix),
        "prefix_key": "/".join(prefix),
        "count": 0,
        "children": [],
        "cards": [],
    }


def _find_or_create_child(parent: dict[str, Any], label: str, prefix: list[str]) -> dict[str, Any]:
    for child in parent["children"]:
        if child["label"] == label:
            return child
    node = _empty_node(label, prefix)
    parent["children"].append(node)
    return node


def _sort_tree(node: dict[str, Any]) -> None:
    node["children"].sort(key=lambda c: (c["label"] or "").lower())
    node["cards"].sort(key=lambda c: (c.get("title") or "").lower())
    for child in node["children"]:
        _sort_tree(child)


def load_unit_records(jsonl_path: Path | None = None) -> list[dict[str, Any]]:
    path = jsonl_path or global_jsonl_path()
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def build_taxonomy_outline(
    *,
    access_lane: AccessLaneName | AccessLane = "general",
    records: list[dict[str, Any]] | None = None,
    include_uncategorized: bool = True,
) -> dict[str, Any]:
    """Build a nested outline: group by taxonomy.path, filtered by access lane."""
    lane = (access_lane or "general").strip().lower()  # type: ignore[assignment]
    if lane not in {"general", "proprietary"}:
        lane = "general"
    ceiling = lane_retrieve_ceiling(lane)  # type: ignore[arg-type]
    rows = records if records is not None else load_unit_records()

    root = _empty_node("", [])
    uncategorized = _empty_node("(未分类)", ["(未分类)"])
    denied = 0
    included = 0

    for rec in rows:
        classification, policy_raw = _access_from_record(rec)
        if not is_retrievable(
            classification,
            max_level=ceiling,  # type: ignore[arg-type]
            policy=resolve_policy(classification, policy_raw or None),
        ):
            denied += 1
            continue
        path = _taxonomy_path(rec)
        card = {
            "id": str(rec.get("id") or ""),
            "title": str(rec.get("title") or rec.get("id") or ""),
            "path": str(rec.get("path") or ""),
            "classification": classification,
            "source_project": str(
                (rec.get("access") or {}).get("source_project")
                if isinstance(rec.get("access"), dict)
                else rec.get("source_project")
                or ""
            ),
            "taxonomy_path": path,
        }
        included += 1
        if not path:
            if include_uncategorized:
                uncategorized["cards"].append(card)
                uncategorized["count"] += 1
            continue
        node = root
        for i, seg in enumerate(path):
            prefix = path[: i + 1]
            node = _find_or_create_child(node, seg, prefix)
            node["count"] += 1
        node["cards"].append(card)

    children = list(root["children"])
    if include_uncategorized and uncategorized["count"]:
        children.append(uncategorized)
    _sort_tree(root)
    for child in children:
        _sort_tree(child)

    return {
        "ok": True,
        "access_lane": lane,
        "ceiling": ceiling,
        "included": included,
        "denied": denied,
        "total_indexed": len(rows),
        "roots": children,
        "source": str(global_jsonl_path()),
    }


def cards_under_prefix(
    outline: dict[str, Any],
    prefix: list[str] | str,
) -> list[dict[str, Any]]:
    """Collect all cards under a prefix (descendants)."""
    if isinstance(prefix, str):
        prefix = [p for p in prefix.replace("\\", "/").split("/") if p]
    if not prefix:
        cards: list[dict[str, Any]] = []

        def walk(nodes: list[dict[str, Any]]) -> None:
            for n in nodes:
                cards.extend(n.get("cards") or [])
                walk(n.get("children") or [])

        walk(outline.get("roots") or [])
        return cards

    nodes = outline.get("roots") or []
    target: dict[str, Any] | None = None
    for i, seg in enumerate(prefix):
        found = None
        for n in nodes:
            if n.get("label") == seg:
                found = n
                break
        if found is None:
            return []
        target = found
        nodes = found.get("children") or []
        if i == len(prefix) - 1:
            break
    if target is None:
        return []
    out: list[dict[str, Any]] = list(target.get("cards") or [])

    def walk(n: dict[str, Any]) -> None:
        for c in n.get("children") or []:
            out.extend(c.get("cards") or [])
            walk(c)

    walk(target)
    return out
