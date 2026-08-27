from __future__ import annotations

from pathlib import Path

from app import config
from app.knowledge.object import KnowledgeObject
from app.knowledge.parse import load_knowledge_object
from app.storage.index import global_jsonl_path, load_jsonl


class ReconstructLoadError(RuntimeError):
    """Could not collect KnowledgeObjects for reconstruction."""


def _resolve_card(path: Path) -> Path:
    path = path.expanduser()
    if not path.is_absolute():
        path = (config.ROOT / path).resolve()
    else:
        path = path.resolve()
    return path


def load_ko_from_path(path: str | Path) -> KnowledgeObject:
    p = _resolve_card(Path(path))
    if not p.is_file():
        raise ReconstructLoadError(f"not found: {p}")
    return load_knowledge_object(p)


def collect_from_paths(paths: list[str | Path]) -> list[KnowledgeObject]:
    objs: list[KnowledgeObject] = []
    seen: set[str] = set()
    for raw in paths:
        obj = load_ko_from_path(raw)
        if obj.id in seen:
            continue
        seen.add(obj.id)
        objs.append(obj)
    return objs


def collect_from_packages(packages_root: str | Path | None = None) -> list[KnowledgeObject]:
    root = Path(packages_root) if packages_root else config.PACKAGES_DIR
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ReconstructLoadError(f"packages dir missing: {root}")
    paths = sorted(root.glob("*/knowledge_object.json"))
    return collect_from_paths(paths)


def collect_from_index(
    *,
    subdir: str | None = None,
    tag: str | None = None,
    concept: str | None = None,
    limit: int | None = None,
) -> list[KnowledgeObject]:
    records = load_jsonl(global_jsonl_path())
    if not records:
        raise ReconstructLoadError(
            "knowledge index empty — run: python main.py index rebuild"
        )

    filtered: list[dict] = []
    for rec in records:
        path = str(rec.get("path") or "")
        if subdir:
            needle = f"/{subdir.strip('/').replace(chr(92), '/')}/"
            norm = "/" + path.replace("\\", "/")
            if needle not in norm and not path.replace("\\", "/").startswith(
                f"data/knowledge/{subdir}"
            ):
                # also allow direct folder match
                if f"knowledge/{subdir}/" not in path.replace("\\", "/"):
                    continue
        if tag and tag not in (rec.get("tags") or []):
            continue
        if concept and concept not in (rec.get("concepts") or []):
            continue
        filtered.append(rec)

    # Prefer richer / filter-aligned records before applying limit (not jsonl order)
    def _priority(rec: dict) -> tuple:
        concepts = list(rec.get("concepts") or [])
        tags = list(rec.get("tags") or [])
        score = len(concepts) * 2 + len(tags)
        if concept and concept in concepts:
            score += 20
        if tag and tag in tags:
            score += 10
        if str(rec.get("summary") or "").strip():
            score += 1
        # higher score first; stable path tie-break
        return (-score, str(rec.get("path") or ""))

    filtered.sort(key=_priority)

    if limit is not None:
        filtered = filtered[:limit]

    objs: list[KnowledgeObject] = []
    errors: list[str] = []
    seen: set[str] = set()
    for rec in filtered:
        path = Path(str(rec["path"]))
        if not path.is_file():
            # try relative to repo root
            alt = config.ROOT / path
            path = alt if alt.is_file() else path
        if not path.is_file():
            errors.append(str(rec.get("path")))
            continue
        try:
            obj = load_knowledge_object(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{rec.get('path')}: {exc}")
            continue
        if obj.id in seen:
            continue
        seen.add(obj.id)
        objs.append(obj)

    if not objs:
        detail = "; ".join(errors[:5]) if errors else "no matching index records"
        raise ReconstructLoadError(f"no KnowledgeObjects loaded ({detail})")
    return sorted(objs, key=lambda o: o.id)
