from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.knowledge.object import KnowledgeObject
from app.knowledge.parse import load_knowledge_object
from app.reconstruct.build import build_graph
from app.reconstruct.load import ReconstructLoadError, collect_from_paths
from app.reconstruct.models import ConceptGraph


@dataclass
class EvolveResult:
    graph: ConceptGraph
    kos: list[KnowledgeObject]
    added_ko_ids: list[str]
    removed_ko_ids: list[str]
    unchanged_ko_ids: list[str]
    base_path: Path | None = None


def load_graph(path: str | Path) -> ConceptGraph:
    p = Path(path).expanduser().resolve()
    if p.is_dir():
        p = p / "concept_graph.json"
    if not p.is_file():
        raise ReconstructLoadError(f"concept_graph.json not found: {p}")
    return ConceptGraph.model_validate(json.loads(p.read_text(encoding="utf-8")))


def _index_kos_by_id() -> dict[str, KnowledgeObject]:
    from app import config
    from app.storage.index import global_jsonl_path, load_jsonl

    by_id: dict[str, KnowledgeObject] = {}
    for ko_json in config.PACKAGES_DIR.glob("*/knowledge_object.json"):
        try:
            obj = load_knowledge_object(ko_json)
            by_id[obj.id] = obj
        except Exception:  # noqa: BLE001
            continue

    for rec in load_jsonl(global_jsonl_path()):
        path = Path(str(rec.get("path") or ""))
        if not path.is_file():
            alt = config.ROOT / path
            path = alt if alt.is_file() else path
        if not path.is_file():
            continue
        try:
            obj = load_knowledge_object(path)
        except Exception:  # noqa: BLE001
            continue
        by_id.setdefault(obj.id, obj)
    return by_id


def evolve_graph(
    base: ConceptGraph,
    *,
    all_kos: list[KnowledgeObject],
    min_confidence: float = 0.0,
) -> EvolveResult:
    """Rebuild relation layer for the working KO set; preserve generation lineage."""
    working = sorted({o.id: o for o in all_kos}.values(), key=lambda o: o.id)
    before = set(base.source_ko_ids)
    after = {o.id for o in working}
    added = sorted(after - before)
    removed = sorted(before - after)
    unchanged = sorted(before & after)

    graph = build_graph(working, min_confidence=min_confidence, base=base)
    graph.evidence["delta"] = {
        "added_ko_ids": added,
        "removed_ko_ids": removed,
        "unchanged_ko_ids": unchanged,
        "base_generation": base.generation,
        "base_graph_id": base.id,
    }
    return EvolveResult(
        graph=graph,
        kos=working,
        added_ko_ids=added,
        removed_ko_ids=removed,
        unchanged_ko_ids=unchanged,
    )


def evolve_from_dir(
    reconstruct_dir: str | Path,
    *,
    add_paths: list[str | Path] | None = None,
    remove_ko_ids: list[str] | None = None,
    min_confidence: float = 0.0,
) -> EvolveResult:
    base_dir = Path(reconstruct_dir).expanduser().resolve()
    base = load_graph(base_dir)
    catalog = _index_kos_by_id()

    by_id: dict[str, KnowledgeObject] = {}
    missing: list[str] = []
    for kid in base.source_ko_ids:
        if kid in catalog:
            by_id[kid] = catalog[kid]
        else:
            missing.append(kid)

    if add_paths:
        for obj in collect_from_paths(add_paths):
            by_id[obj.id] = obj

    remove = set(remove_ko_ids or [])
    all_kos = [o for o in by_id.values() if o.id not in remove]
    if not all_kos:
        detail = f"missing base KOs: {missing[:5]}" if missing else "empty set"
        raise ReconstructLoadError(f"evolution has no resolvable KOs ({detail})")

    result = evolve_graph(base, all_kos=all_kos, min_confidence=min_confidence)
    result.base_path = base_dir
    if missing:
        result.graph.evidence.setdefault("warnings", [])
        if isinstance(result.graph.evidence["warnings"], list):
            result.graph.evidence["warnings"].append(
                f"unresolved_base_kos:{len(missing)}"
            )
    return result
