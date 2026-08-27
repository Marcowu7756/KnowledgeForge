from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app import config
from app.knowledge.object import KnowledgeObject
from app.reconstruct.build import build_graph
from app.reconstruct.evolve import evolve_from_dir
from app.reconstruct.load import (
    ReconstructLoadError,
    collect_from_index,
    collect_from_packages,
    collect_from_paths,
)
from app.reconstruct.models import ConceptGraph, ReconstructedView
from app.reconstruct.rules import RULES_VERSION
from app.reconstruct.views import reconstruct_view


@dataclass
class ReconstructResult:
    output_dir: Path
    graph: ConceptGraph
    view: ReconstructedView | None
    graph_path: Path
    view_path: Path | None
    report_path: Path
    kos: list[KnowledgeObject]
    evolved: bool = False
    delta: dict | None = None


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, model) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8")
    return path


def _write_report(
    dest: Path,
    *,
    graph: ConceptGraph,
    view: ReconstructedView | None,
    kos: list[KnowledgeObject],
    delta: dict | None = None,
) -> Path:
    lines = [
        f"# Reconstruction — {graph.id}",
        "",
        "```yaml",
        "kind: reconstruction",
        f"graph_id: {graph.id}",
        f"generation: {graph.generation}",
        f"created: {graph.created.isoformat()}",
        f"updated: {graph.updated.isoformat()}",
        f"ko_count: {len(kos)}",
        f"nodes: {graph.relations.stats.get('nodes', len(graph.nodes))}",
        f"edges: {graph.relations.stats.get('edges', len(graph.relations.edges))}",
        f"rules_version: {graph.relations.rules_version}",
        f"view: {view.view_type if view else 'none'}",
        f"view_fingerprint: {view.stability.get('fingerprint') if view else ''}",
        "```",
        "",
        "## Source KnowledgeObjects",
        "",
    ]
    for obj in kos:
        lines.append(f"- `{obj.id}` — {obj.content.title}")
    lines.extend(["", "## Relation stats", ""])
    for key, val in sorted(graph.relations.stats.items()):
        lines.append(f"- {key}: {val}")
    top = sorted(graph.relations.edges, key=lambda e: (-e.confidence, e.id))[:10]
    if top:
        lines.extend(["", "## Top relations (by confidence)", ""])
        for e in top:
            lines.append(
                f"- `{e.confidence:.2f}` [{e.kind}/{e.evidence.rule_id}] "
                f"{e.from_node} → {e.to_node} ({e.label})"
            )
    if delta:
        lines.extend(["", "## Evolution delta", ""])
        lines.append(f"- added: {delta.get('added_ko_ids')}")
        lines.append(f"- removed: {delta.get('removed_ko_ids')}")
        lines.append(f"- unchanged: {len(delta.get('unchanged_ko_ids') or [])}")
    if view is not None:
        lines.extend(["", f"## View: {view.view_type}", "", f"**{view.title}**", ""])
        if view.stability:
            lines.append(f"- fingerprint: `{view.stability.get('fingerprint')}`")
            lines.append("")
        for sec in view.sections:
            lines.append(f"### {sec.title}")
            lines.append("")
            if sec.rationale:
                lines.append(f"_Why: {sec.rationale}_")
                lines.append("")
            for note in sec.notes:
                lines.append(f"- {note}")
            lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def _persist(
    *,
    out: Path,
    graph: ConceptGraph,
    kos: list[KnowledgeObject],
    view: str | None,
    seed: str,
    evolved: bool,
    delta: dict | None,
) -> ReconstructResult:
    out.mkdir(parents=True, exist_ok=True)
    graph_path = _write_json(out / "concept_graph.json", graph)
    view_obj: ReconstructedView | None = None
    view_path: Path | None = None
    if view:
        view_obj = reconstruct_view(graph, kos, view=view, seed=seed)
        view_path = _write_json(out / "reconstructed_view.json", view_obj)

    report_path = _write_report(
        out / "RECONSTRUCT.md",
        graph=graph,
        view=view_obj,
        kos=kos,
        delta=delta,
    )
    evidence = {
        "pipeline": "reconstruct_v0.2",
        "reconstruct_version": graph.reconstruct_version,
        "rules_version": RULES_VERSION,
        "graph_id": graph.id,
        "generation": graph.generation,
        "view_id": view_obj.id if view_obj else None,
        "view_fingerprint": view_obj.stability.get("fingerprint") if view_obj else None,
        "source_ko_ids": graph.source_ko_ids,
        "stats": graph.relations.stats,
        "method": graph.evidence.get("method"),
        "evolved": evolved,
        "delta": delta,
    }
    (out / "evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return ReconstructResult(
        output_dir=out,
        graph=graph,
        view=view_obj,
        graph_path=graph_path,
        view_path=view_path,
        report_path=report_path,
        kos=kos,
        evolved=evolved,
        delta=delta,
    )


def run_reconstruct(
    *,
    paths: list[str] | None = None,
    from_index: bool = False,
    from_packages: bool = False,
    subdir: str | None = None,
    tag: str | None = None,
    concept: str | None = None,
    limit: int | None = None,
    view: str | None = "theme",
    seed: str = "",
    dest_dir: Path | None = None,
    min_confidence: float = 0.0,
    evolve_dir: str | Path | None = None,
    add_paths: list[str] | None = None,
    remove_ko_ids: list[str] | None = None,
) -> ReconstructResult:
    """P2: Multiple KO → Relation Layer → Graph → Reconstructed View."""
    if evolve_dir:
        evo = evolve_from_dir(
            evolve_dir,
            add_paths=add_paths or paths,
            remove_ko_ids=remove_ko_ids,
            min_confidence=min_confidence,
        )
        graph = evo.graph
        kos = evo.kos
        delta = graph.evidence.get("delta")
        out = (
            Path(dest_dir)
            if dest_dir
            else config.RECONSTRUCT_DIR / f"{_stamp()}_{uuid4().hex[:8]}"
        )
        return _persist(
            out=out,
            graph=graph,
            kos=kos,
            view=view,
            seed=seed,
            evolved=True,
            delta=delta if isinstance(delta, dict) else None,
        )

    if paths:
        kos = collect_from_paths(paths)
    elif from_packages:
        kos = collect_from_packages()
    elif from_index:
        kos = collect_from_index(
            subdir=subdir,
            tag=tag,
            concept=concept,
            limit=limit,
        )
    else:
        raise ReconstructLoadError(
            "specify paths, --from-index, --from-packages, or --evolve DIR"
        )

    kos = sorted(kos, key=lambda o: o.id)
    graph = build_graph(kos, min_confidence=min_confidence)
    out = (
        Path(dest_dir)
        if dest_dir
        else config.RECONSTRUCT_DIR / f"{_stamp()}_{uuid4().hex[:8]}"
    )
    return _persist(
        out=out,
        graph=graph,
        kos=kos,
        view=view,
        seed=seed,
        evolved=False,
        delta=None,
    )
