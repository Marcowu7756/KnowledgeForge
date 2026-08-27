"""Write retrieve EmbeddingRef fields back into package ``knowledge_object.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.knowledge.object import EmbeddingRef, KnowledgeObject
from app.knowledge.parse import load_knowledge_object, write_knowledge_object


@dataclass
class EmbeddingWritebackReport:
    attempted: int = 0
    updated: int = 0
    skipped: int = 0
    missing: int = 0
    paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_package_ko_index(packages_root: Path | None = None) -> dict[str, Path]:
    """Map ``ko_id`` → ``.../packages/<run>/knowledge_object.json``."""
    root = (packages_root or config.PACKAGES_DIR).expanduser().resolve()
    if not root.is_dir():
        return {}
    index: dict[str, Path] = {}
    for ko_path in sorted(root.glob("*/knowledge_object.json")):
        try:
            payload = json.loads(ko_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ko_id = str(payload.get("id") or "").strip()
        if ko_id:
            index[ko_id] = ko_path
    return index


def resolve_package_ko_path(
    obj: KnowledgeObject,
    *,
    packages_root: Path | None = None,
    ko_index: dict[str, Path] | None = None,
    source_path: Path | None = None,
) -> Path | None:
    """Locate the on-disk package KO JSON for ``obj``, if any."""
    root = (packages_root or config.PACKAGES_DIR).expanduser().resolve()

    if source_path is not None:
        src = source_path.expanduser().resolve()
        if src.is_file() and src.name == "knowledge_object.json":
            return src

    index = ko_index if ko_index is not None else build_package_ko_index(root)
    if obj.id in index:
        return index[obj.id]

    package_id = str(obj.evidence.package_id or "").strip()
    if package_id:
        candidate = root / package_id / "knowledge_object.json"
        if candidate.is_file():
            return candidate
    return None


def _embedding_matches(existing: EmbeddingRef, desired: EmbeddingRef) -> bool:
    return (
        existing.status == desired.status == "ready"
        and existing.model == desired.model
        and existing.vector_id == desired.vector_id
        and bool(existing.vector_id)
    )


def write_embedding_ref_to_package(
    obj: KnowledgeObject,
    dest: Path,
    *,
    dry_run: bool = False,
) -> bool:
    """Merge ``obj.embedding`` into an existing package KO file. Returns True if written."""
    if obj.embedding.status != "ready" or not obj.embedding.vector_id:
        return False

    on_disk = load_knowledge_object(dest)
    if _embedding_matches(on_disk.embedding, obj.embedding):
        return False

    on_disk.embedding = EmbeddingRef(
        model=obj.embedding.model,
        vector_id=obj.embedding.vector_id,
        status="ready",
    )
    on_disk.lifecycle.updated = datetime.now(timezone.utc)
    on_disk.lifecycle.version += 1
    if not dry_run:
        write_knowledge_object(on_disk, dest)
    return True


def write_embedding_refs_to_packages(
    kos: list[KnowledgeObject],
    *,
    source_paths: dict[str, Path] | None = None,
    packages_root: Path | None = None,
    dry_run: bool = False,
) -> EmbeddingWritebackReport:
    """After retrieve index, persist embedding refs onto package KOs."""
    report = EmbeddingWritebackReport()
    ko_index = build_package_ko_index(packages_root)
    src_map = source_paths or {}

    for obj in kos:
        if obj.embedding.status != "ready":
            report.skipped += 1
            continue
        report.attempted += 1
        dest = resolve_package_ko_path(
            obj,
            packages_root=packages_root,
            ko_index=ko_index,
            source_path=src_map.get(obj.id),
        )
        if dest is None:
            report.missing += 1
            continue
        try:
            if write_embedding_ref_to_package(obj, dest, dry_run=dry_run):
                report.updated += 1
                report.paths.append(dest.as_posix())
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"{obj.id}: {exc}")
    return report
