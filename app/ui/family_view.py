"""H1a · 一源多卡 — resolve a SETV family (or explicit paths) to read-only card previews."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from app import config
from app.knowledge.access import is_retrievable, lane_retrieve_ceiling, resolve_policy
from app.knowledge.parse import load_unit_from_markdown
from app.knowledge.path_access import resolve_access_for_path
from app.models import KnowledgeUnit

_INST_RE = re.compile(r"SETV-INST-([A-Z0-9]+)-", re.I)
_FAM_RE = re.compile(r"SETV-FAM-([A-Z0-9]+)-", re.I)


def _rel_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(config.ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _excerpt(text: str, limit: int = 2400) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 1] + "…"


def _unit_passes_lane(unit: KnowledgeUnit, lane: str) -> bool:
    ceiling = lane_retrieve_ceiling(lane)  # type: ignore[arg-type]
    return is_retrievable(
        unit.access.classification,
        max_level=ceiling,  # type: ignore[arg-type]
        policy=resolve_policy(unit.access.classification, unit.access.policy),
    )


def _symbol_from_unit(unit: KnowledgeUnit) -> str:
    aid = ""
    if unit.setv_artifact and unit.setv_artifact.artifact_id:
        aid = unit.setv_artifact.artifact_id
    m = _FAM_RE.search(aid) or _INST_RE.search(aid)
    if m:
        return m.group(1).upper()
    path = list(unit.taxonomy.path or [])
    if len(path) >= 4 and path[1].upper() == "SETV":
        # Family: … State Family · SYMBOL ; Snapshot: … State Snapshot · SYMBOL · TF
        return str(path[3]).upper()
    for c in unit.concepts:
        if re.fullmatch(r"[A-Z]{2,}[A-Z0-9]*", c.strip()):
            return c.strip().upper()
    return ""


def _card_payload(path: Path, unit: KnowledgeUnit, *, excerpt_chars: int) -> dict[str, Any]:
    access = resolve_access_for_path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    art = unit.setv_artifact
    return {
        "ko_id": f"ko_{unit.id}" if not str(unit.id).startswith("ko_") else str(unit.id),
        "unit_id": unit.id,
        "artifact_id": art.artifact_id if art else "",
        "asset_class": art.asset_class if art else "",
        "title": unit.title,
        "path": _rel_path(path),
        "taxonomy_path": list(unit.taxonomy.path or []),
        "classification": access.classification,
        "source_project": access.source_project or "",
        "preview_url": f"/api/preview?path={quote(path.resolve().as_posix())}",
        "excerpt": _excerpt(text, excerpt_chars),
    }


def _iter_knowledge_md() -> list[Path]:
    root = config.KNOWLEDGE_DIR
    if not root.is_dir():
        return []
    out: list[Path] = []
    for f in root.rglob("*.md"):
        if f.name.upper() == "INDEX.MD" or f.name.lower() in {"readme.md", "changelog.md"}:
            continue
        out.append(f)
    return out


def find_unit_by_artifact_id(artifact_id: str) -> tuple[Path, KnowledgeUnit] | None:
    want = artifact_id.strip()
    if not want:
        return None
    for path in _iter_knowledge_md():
        try:
            unit = load_unit_from_markdown(path)
        except Exception:
            continue
        art = unit.setv_artifact
        if art and art.artifact_id == want:
            return path, unit
    return None


def _member_snapshots_for_symbol(symbol: str, *, lane: str, exclude: Path) -> list[tuple[Path, KnowledgeUnit]]:
    symbol = symbol.upper()
    found: list[tuple[Path, KnowledgeUnit]] = []
    for path in _iter_knowledge_md():
        if path.resolve() == exclude.resolve():
            continue
        try:
            unit = load_unit_from_markdown(path)
        except Exception:
            continue
        if not _unit_passes_lane(unit, lane):
            continue
        art = unit.setv_artifact
        if not art or art.asset_class != "snapshot":
            continue
        if _symbol_from_unit(unit) != symbol:
            continue
        found.append((path, unit))

    def sort_key(item: tuple[Path, KnowledgeUnit]) -> tuple[int, str]:
        path, unit = item
        tax = list(unit.taxonomy.path or [])
        tf = tax[-1].upper() if tax else ""
        order = {"W": 0, "D": 1, "H4": 2, "H1": 3}.get(tf, 9)
        return (order, path.name.lower())

    found.sort(key=sort_key)
    return found


def resolve_family_view(
    artifact_id: str,
    *,
    lane: Literal["general", "proprietary"] = "proprietary",
    limit: int = 8,
    excerpt_chars: int = 2400,
) -> dict[str, Any]:
    """Resolve family artifact → family card + member snapshot cards (read-only)."""
    hit = find_unit_by_artifact_id(artifact_id)
    if hit is None:
        raise FileNotFoundError(f"family artifact not found: {artifact_id}")
    fam_path, fam_unit = hit
    if not _unit_passes_lane(fam_unit, lane):
        raise PermissionError(
            f"family blocked by lane={lane} classification={fam_unit.access.classification}"
        )

    notes: list[str] = []
    members: list[dict[str, Any]] = []
    strategy = "taxonomy_symbol+snapshot"

    # Prefer explicit SETV-INST ids mentioned in family markdown
    body = fam_path.read_text(encoding="utf-8", errors="replace")
    inst_ids = sorted(set(re.findall(r"SETV-INST-[A-Z0-9-]+", body, flags=re.I)))
    if inst_ids:
        strategy = "body_inst_ids"
        for iid in inst_ids:
            m = find_unit_by_artifact_id(iid)
            if m is None:
                notes.append(f"missing cite for {iid}")
                continue
            mp, mu = m
            if not _unit_passes_lane(mu, lane):
                notes.append(f"lane-blocked {iid}")
                continue
            members.append(_card_payload(mp, mu, excerpt_chars=excerpt_chars))
            if len(members) >= limit:
                break

    if not members:
        symbol = _symbol_from_unit(fam_unit)
        if not symbol:
            notes.append("no symbol derived from family card")
        else:
            notes.append(f"symbol={symbol}")
            for mp, mu in _member_snapshots_for_symbol(symbol, lane=lane, exclude=fam_path):
                members.append(_card_payload(mp, mu, excerpt_chars=excerpt_chars))
                if len(members) >= limit:
                    break

    return {
        "ok": True,
        "h1": "H1a",
        "mode": "read_only_multi_card",
        "lane": lane,
        "family": _card_payload(fam_path, fam_unit, excerpt_chars=excerpt_chars),
        "members": members,
        "resolve": {"strategy": strategy, "notes": notes, "member_count": len(members)},
    }


def resolve_explicit_cards(
    paths: list[str],
    *,
    lane: Literal["general", "proprietary"] = "proprietary",
    excerpt_chars: int = 2400,
) -> dict[str, Any]:
    """Preview an explicit ordered list of knowledge card paths (H1b precursor)."""
    cards: list[dict[str, Any]] = []
    notes: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_absolute():
            path = (config.ROOT / path).resolve()
        else:
            path = path.resolve()
        try:
            path.relative_to(config.DATA_DIR.resolve())
        except ValueError:
            notes.append(f"outside data/: {raw}")
            continue
        if not path.is_file():
            notes.append(f"missing: {raw}")
            continue
        try:
            unit = load_unit_from_markdown(path)
        except Exception as exc:
            notes.append(f"parse failed {raw}: {exc}")
            continue
        if not _unit_passes_lane(unit, lane):
            notes.append(f"lane-blocked: {raw}")
            continue
        cards.append(_card_payload(path, unit, excerpt_chars=excerpt_chars))
    return {
        "ok": True,
        "h1": "H1a",
        "mode": "explicit_paths",
        "lane": lane,
        "family": None,
        "members": cards,
        "resolve": {"strategy": "explicit_paths", "notes": notes, "member_count": len(cards)},
    }
