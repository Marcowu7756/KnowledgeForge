"""Knowledge maintenance — delete only (no invent / no in-place edit).

Add & update = re-acquire / re-ingest. This module only removes junk or
unimportant settled cards and prunes indexes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import config
from app.storage.index import (
    global_jsonl_path,
    global_markdown_path,
    load_jsonl,
    load_local_json,
    local_json_path,
    local_markdown_path,
    save_jsonl,
    save_local_json,
    write_markdown_index,
)

_PROTECTED_NAMES = {"INDEX.MD", "README.MD"}


@dataclass
class DeleteItem:
    target: str
    path: str = ""
    id: str = ""
    title: str = ""
    deleted_file: bool = False
    pruned_global_index: bool = False
    pruned_local_index: bool = False
    pruned_retrieve: bool = False
    error: str = ""


@dataclass
class DeleteReport:
    ok: bool
    dry_run: bool
    items: list[DeleteItem] = field(default_factory=list)
    audit_path: str = ""

    @property
    def deleted_count(self) -> int:
        return sum(1 for i in self.items if i.deleted_file and not i.error)


class MaintainError(RuntimeError):
    """Knowledge maintain failed."""


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _rel_under_root(path: Path) -> str:
    try:
        return _norm(path.resolve().relative_to(config.ROOT.resolve()))
    except ValueError:
        return _norm(path.resolve())


def resolve_knowledge_card(raw: str) -> Path:
    """Resolve id or path to a knowledge .md under data/knowledge (sandbox)."""
    text = (raw or "").strip()
    if not text:
        raise MaintainError("path or id required")

    knowledge = config.KNOWLEDGE_DIR.resolve()
    candidate = Path(text).expanduser()
    if not candidate.is_absolute():
        under_root = (config.ROOT / candidate).resolve()
        under_know = (knowledge / candidate).resolve()
        if under_root.is_file():
            candidate = under_root
        elif under_know.is_file():
            candidate = under_know
        else:
            # treat as unit id — scan index then filesystem stem
            found = _find_by_id(text)
            if found is None:
                raise MaintainError(f"knowledge card not found: {text}")
            candidate = found
    else:
        candidate = candidate.resolve()

    if not candidate.is_file():
        raise MaintainError(f"not a file: {candidate}")
    if candidate.suffix.lower() != ".md":
        raise MaintainError(f"only .md knowledge cards can be deleted: {candidate}")
    if candidate.name.upper() in _PROTECTED_NAMES:
        raise MaintainError(f"protected file cannot be deleted: {candidate.name}")

    try:
        candidate.relative_to(knowledge)
    except ValueError as exc:
        raise MaintainError(
            f"delete only allowed under {knowledge} (got {candidate})"
        ) from exc
    return candidate


def _find_by_id(unit_id: str) -> Path | None:
    needle = unit_id.strip()
    for rec in load_jsonl(global_jsonl_path()):
        if str(rec.get("id") or "") == needle:
            rel = str(rec.get("path") or "")
            if not rel:
                continue
            path = Path(rel)
            if not path.is_absolute():
                path = (config.ROOT / rel).resolve()
            if path.is_file():
                return path
    # filesystem fallback: yaml id is expensive; match stem contains id
    if knowledge_dir := config.KNOWLEDGE_DIR:
        if knowledge_dir.is_dir():
            for p in knowledge_dir.rglob("*.md"):
                if p.name.upper() in _PROTECTED_NAMES:
                    continue
                if needle in p.stem:
                    text = p.read_text(encoding="utf-8", errors="ignore")[:800]
                    if f"id: {needle}" in text or f'id: "{needle}"' in text:
                        return p.resolve()
    return None


def _card_meta(path: Path) -> tuple[str, str]:
    """Return (id, title) best-effort from card head."""
    text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    unit_id = path.stem
    title = path.stem
    for line in text.splitlines():
        if line.startswith("id:") and " " in line:
            unit_id = line.split(":", 1)[1].strip().strip('"').strip("'") or unit_id
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip('"').strip("'") or title
        if line.startswith("# "):
            title = line[2:].strip() or title
            break
    return unit_id, title


def _paths_match(record_path: str, target: Path) -> bool:
    rp = _norm(record_path)
    tp = _norm(target.resolve())
    rel = _rel_under_root(target)
    return rp == tp or rp == rel


def prune_global_index(targets: list[Path]) -> int:
    path = global_jsonl_path()
    records = load_jsonl(path)
    before = len(records)
    kept = [
        r
        for r in records
        if not any(_paths_match(str(r.get("path") or ""), t) for t in targets)
    ]
    if len(kept) == before:
        return 0
    save_jsonl(path, kept)
    write_markdown_index(
        global_markdown_path(),
        kept,
        title="KnowledgeForge Index",
        relative_to=global_markdown_path().parent,
    )
    return before - len(kept)


def prune_local_indexes(targets: list[Path]) -> int:
    changed = 0
    parents = {t.parent.resolve() for t in targets}
    for dest in parents:
        json_path = local_json_path(dest)
        if not json_path.is_file():
            continue
        records = load_local_json(json_path)
        before = len(records)
        kept = [
            r
            for r in records
            if not any(_paths_match(str(r.get("path") or ""), t) for t in targets)
        ]
        if len(kept) == before:
            continue
        title = f"Knowledge Index — {dest.name}"
        save_local_json(json_path, kept, title=title)
        write_markdown_index(
            local_markdown_path(dest),
            kept,
            title=title,
            relative_to=dest,
        )
        changed += before - len(kept)
    return changed


def prune_retrieve_index(targets: list[Path], *, unit_ids: set[str]) -> int:
    """Drop matching rows from retrieve vectors (keeps matrix aligned)."""
    try:
        from app.retrieve.store import (
            load_records,
            load_vectors,
            save_index,
        )
    except Exception:
        return 0

    try:
        records = load_records()
        vectors = load_vectors()
    except Exception:
        return 0
    if not records:
        return 0

    target_rels = set()
    for t in targets:
        target_rels.add(_rel_under_root(t))
        target_rels.add(_norm(t.resolve()))

    keep_idx: list[int] = []
    for i, rec in enumerate(records):
        rp = _norm(rec.path or "")
        if rec.ko_id in unit_ids or rp in target_rels or any(
            rp.endswith(t.name) and _norm(t) in rp for t in targets
        ):
            continue
        # also match knowledge_md path loosely
        drop = False
        for rel in target_rels:
            if rp == rel or rp.endswith("/" + Path(rel).name):
                drop = True
                break
        if drop:
            continue
        keep_idx.append(i)

    removed = len(records) - len(keep_idx)
    if removed <= 0:
        return 0
    if vectors.size and len(vectors) == len(records):
        new_vectors = vectors[keep_idx]
    else:
        import numpy as np

        new_vectors = np.zeros((0, 0), dtype="float32")
        if keep_idx and vectors.size:
            new_vectors = vectors[keep_idx]
    new_records = [records[i] for i in keep_idx]
    model = ""
    try:
        from app.retrieve.store import load_manifest

        model = load_manifest().model
    except Exception:
        model = "unknown"
    save_index(records=new_records, vectors=new_vectors, model=model, evidence={"pruned_by": "maintain.delete"})
    return removed


def _write_audit(report: DeleteReport) -> Path:
    audit_dir = config.AUDIT_DIR / "maintain"
    audit_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = audit_dir / f"{day}.jsonl"
    payload = {
        "ts": _stamp(),
        "kind": "knowledge.delete",
        "dry_run": report.dry_run,
        "deleted_count": report.deleted_count,
        "items": [
            {
                "target": i.target,
                "path": i.path,
                "id": i.id,
                "title": i.title,
                "deleted_file": i.deleted_file,
                "error": i.error,
            }
            for i in report.items
        ],
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def delete_knowledge(
    targets: list[str],
    *,
    dry_run: bool = False,
    prune_retrieve: bool = True,
) -> DeleteReport:
    """Delete settled knowledge cards. No create / no update."""
    if not targets:
        raise MaintainError("at least one path or id required")

    resolved: list[tuple[str, Path, str, str]] = []
    items: list[DeleteItem] = []
    for raw in targets:
        try:
            path = resolve_knowledge_card(raw)
            unit_id, title = _card_meta(path)
            resolved.append((raw, path, unit_id, title))
        except MaintainError as exc:
            items.append(DeleteItem(target=raw, error=str(exc)))

    # unique by path
    seen: set[str] = set()
    unique: list[tuple[str, Path, str, str]] = []
    for raw, path, unit_id, title in resolved:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append((raw, path, unit_id, title))

    ids = {uid for _, _, uid, _ in unique}

    if dry_run:
        for raw, path, unit_id, title in unique:
            items.append(
                DeleteItem(
                    target=raw,
                    path=_rel_under_root(path),
                    id=unit_id,
                    title=title,
                    deleted_file=False,
                )
            )
        report = DeleteReport(ok=not any(i.error for i in items), dry_run=True, items=items)
        report.audit_path = str(_write_audit(report))
        return report

    for raw, path, unit_id, title in unique:
        item = DeleteItem(
            target=raw,
            path=_rel_under_root(path),
            id=unit_id,
            title=title,
        )
        try:
            path.unlink()
            item.deleted_file = True
        except OSError as exc:
            item.error = str(exc)
        items.append(item)

    deleted_paths = [p for _, p, _, _ in unique if not p.exists()]

    if deleted_paths:
        prune_global_index(deleted_paths)
        prune_local_indexes(deleted_paths)
        for item in items:
            if item.deleted_file:
                item.pruned_global_index = True
                item.pruned_local_index = True
        if prune_retrieve:
            n = prune_retrieve_index(deleted_paths, unit_ids=ids)
            if n:
                for item in items:
                    if item.deleted_file:
                        item.pruned_retrieve = True

    report = DeleteReport(ok=False, dry_run=False, items=items)
    failed = [i for i in items if i.error]
    succeeded = [i for i in items if i.deleted_file]
    report.ok = len(failed) == 0 and bool(succeeded)
    report.audit_path = str(_write_audit(report))
    return report


def report_as_dict(report: DeleteReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "dry_run": report.dry_run,
        "deleted_count": report.deleted_count,
        "audit_path": report.audit_path,
        "items": [
            {
                "target": i.target,
                "path": i.path,
                "id": i.id,
                "title": i.title,
                "deleted_file": i.deleted_file,
                "pruned_global_index": i.pruned_global_index,
                "pruned_local_index": i.pruned_local_index,
                "pruned_retrieve": i.pruned_retrieve,
                "error": i.error,
            }
            for i in report.items
        ],
    }
