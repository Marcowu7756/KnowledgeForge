from __future__ import annotations

import hashlib
import json
from collections import defaultdict

from app.knowledge.object import KnowledgeObject
from app.reconstruct.models import (
    RECONSTRUCT_VERSION,
    ConceptGraph,
    ReconstructedView,
    ViewSection,
)
from app.reconstruct.rules import RULES_VERSION


def _ko_map(kos: list[KnowledgeObject]) -> dict[str, KnowledgeObject]:
    return {o.id: o for o in kos}


def _concept_nodes(graph: ConceptGraph) -> list:
    return [n for n in graph.nodes if n.kind == "concept"]


def stable_view_id(graph_id: str, view_type: str, seed: str) -> str:
    payload = json.dumps(
        {
            "graph_id": graph_id,
            "view": view_type,
            "seed": seed or "",
            "v": RECONSTRUCT_VERSION,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"rv_{digest}"


def stability_fingerprint(view: ReconstructedView) -> dict:
    structural = {
        "view_type": view.view_type,
        "seed": view.seed,
        "graph_id": view.graph_id,
        "source_ko_ids": list(view.source_ko_ids),
        "sections": [
            {
                "title": s.title,
                "kind": s.kind,
                "ko_ids": list(s.ko_ids),
                "node_ids": list(s.node_ids),
            }
            for s in view.sections
        ],
    }
    raw = json.dumps(structural, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "fingerprint": hashlib.sha1(raw.encode("utf-8")).hexdigest(),
        "deterministic": True,
        "rules_version": RULES_VERSION,
        "reconstruct_version": RECONSTRUCT_VERSION,
    }


def _finalize(
    view: ReconstructedView,
    *,
    graph: ConceptGraph,
    seed: str,
) -> ReconstructedView:
    view.source_ko_ids = sorted(view.source_ko_ids)
    view.graph_id = graph.id
    view.seed = seed
    view.id = stable_view_id(graph.id, view.view_type, seed)
    # Stable section / list ordering already applied by builders
    view.stability = stability_fingerprint(view)
    view.evidence = {
        **view.evidence,
        "reconstruct_version": RECONSTRUCT_VERSION,
        "rules_version": RULES_VERSION,
        "explainable": True,
        "fingerprint": view.stability["fingerprint"],
    }
    return view


def view_by_theme(
    graph: ConceptGraph,
    kos: list[KnowledgeObject],
    *,
    seed: str = "",
) -> ReconstructedView:
    """Cluster KOs by shared tags / dominant concepts — deterministic."""
    by_id = _ko_map(kos)
    tag_clusters: dict[str, list[str]] = defaultdict(list)
    for obj in sorted(kos, key=lambda o: o.id):
        tags = sorted(obj.content.tags) if obj.content.tags else ["untagged"]
        primary = tags[0]
        if seed:
            blob = " ".join(tags) + " " + obj.content.title
            if seed not in blob:
                continue
        tag_clusters[primary].append(obj.id)

    for theme in tag_clusters:
        tag_clusters[theme] = sorted(set(tag_clusters[theme]))

    if seed:
        ordered = sorted(
            tag_clusters.items(),
            key=lambda kv: (0 if seed in kv[0] else 1, -len(kv[1]), kv[0]),
        )
    else:
        ordered = sorted(tag_clusters.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    sections: list[ViewSection] = []
    for theme, ko_ids in ordered:
        titles = [by_id[k].content.title for k in ko_ids if k in by_id]
        concept_counts: dict[str, int] = defaultdict(int)
        for kid in ko_ids:
            obj = by_id.get(kid)
            if not obj:
                continue
            for c in obj.content.atomic_concepts:
                concept_counts[c] += 1
        shared = sorted(
            [c for c, n in concept_counts.items() if n >= 2],
            key=lambda c: (-concept_counts[c], c),
        )[:8]
        # High-confidence cross edges among cluster KOs
        cluster_set = set(ko_ids)
        bridge = [
            e
            for e in graph.relations.edges
            if e.kind in {"shared_concept", "shared_tag"}
            and e.confidence >= 0.5
            and set(e.source_ko_ids) <= cluster_set
        ]
        bridge.sort(key=lambda e: (-e.confidence, e.id))
        sections.append(
            ViewSection(
                title=theme,
                kind="theme_cluster",
                ko_ids=ko_ids,
                node_ids=[],
                edges=[e.id for e in bridge[:12]],
                notes=[
                    f"KOs: {len(ko_ids)}",
                    *(f"card: {t}" for t in titles[:6]),
                    *(f"shared: {c}" for c in shared),
                    *(
                        f"bridge[{e.confidence:.2f}]: {e.label}"
                        for e in bridge[:5]
                    ),
                ],
                rationale=(
                    f"Primary tag '{theme}' groups {len(ko_ids)} KOs; "
                    f"shared concepts={len(shared)}; "
                    f"qualified bridges={len(bridge)}"
                ),
            )
        )

    view = ReconstructedView(
        view_type="theme",
        title=f"Theme reconstruction ({len(sections)} clusters)",
        seed=seed,
        graph_id=graph.id,
        source_ko_ids=list(graph.source_ko_ids),
        sections=sections,
        evidence={
            "view": "theme",
            "method": "sorted_primary_tag_cluster+shared_concepts+confidence_bridges",
        },
    )
    return _finalize(view, graph=graph, seed=seed)


def view_by_concept(
    graph: ConceptGraph,
    kos: list[KnowledgeObject],
    *,
    seed: str,
) -> ReconstructedView:
    """Ego-neighborhood around a seed concept across KOs."""
    if not seed.strip():
        raise ValueError("concept view requires --seed CONCEPT")

    by_id = _ko_map(kos)
    seed_l = seed.strip().lower()
    matched_nodes = sorted(
        [
            n
            for n in _concept_nodes(graph)
            if seed_l in n.label.lower() or n.label.lower() in seed_l
        ],
        key=lambda n: (-len(n.ko_ids), n.id),
    )
    if not matched_nodes:
        ko_hits = sorted(
            o.id
            for o in kos
            if seed_l in o.content.title.lower()
            or seed_l in (o.content.summary or "").lower()
            or any(seed_l in c.lower() for c in o.content.atomic_concepts)
        )
        sections = [
            ViewSection(
                title=seed,
                kind="concept_search",
                ko_ids=ko_hits,
                notes=[f"no graph node; text match in {len(ko_hits)} KOs"],
                rationale=f"Fallback text search for seed '{seed}' across titles/summaries/concepts",
            )
        ]
    else:
        sections = []
        for node in matched_nodes[:5]:
            related_edges = sorted(
                [
                    e
                    for e in graph.relations.edges
                    if e.from_node == node.id or e.to_node == node.id
                ],
                key=lambda e: (-e.confidence, e.id),
            )
            neighbor_ids = set()
            for e in related_edges:
                neighbor_ids.add(e.from_node)
                neighbor_ids.add(e.to_node)
            neighbor_ids.discard(node.id)
            sections.append(
                ViewSection(
                    title=node.label,
                    kind="concept_neighborhood",
                    node_ids=[node.id, *sorted(neighbor_ids)[:20]],
                    ko_ids=sorted(node.ko_ids),
                    edges=[e.id for e in related_edges[:30]],
                    notes=[
                        f"appears_in_kos: {len(node.ko_ids)}",
                        *(
                            f"ko: {by_id[k].content.title}"
                            for k in sorted(node.ko_ids)
                            if k in by_id
                        ),
                        f"edges: {len(related_edges)}",
                        *(
                            f"edge[{e.confidence:.2f}/{e.evidence.rule_id}]: "
                            f"{e.kind} {e.label}"
                            for e in related_edges[:5]
                        ),
                    ],
                    rationale=(
                        f"Neighborhood of concept node '{node.label}' "
                        f"({node.id}) ranked by edge confidence"
                    ),
                )
            )

    view = ReconstructedView(
        view_type="concept",
        title=f"Concept view: {seed}",
        seed=seed,
        graph_id=graph.id,
        source_ko_ids=list(graph.source_ko_ids),
        sections=sections,
        evidence={
            "view": "concept",
            "method": "concept_neighborhood_confidence_ranked",
        },
    )
    return _finalize(view, graph=graph, seed=seed)


def view_by_learning_path(
    graph: ConceptGraph,
    kos: list[KnowledgeObject],
    *,
    seed: str = "",
) -> ReconstructedView:
    """Order KOs into a learning path using prerequisites + relation weight."""
    prereq_count = {o.id: len(o.content.prerequisites) for o in kos}
    outbound = defaultdict(int)
    inbound_prereq = defaultdict(int)
    for e in graph.relations.edges:
        if e.kind == "intra_ko":
            for kid in e.source_ko_ids:
                outbound[kid] += 1
        if e.kind == "prerequisite":
            for kid in e.source_ko_ids:
                inbound_prereq[kid] += 1

    def sort_key(o: KnowledgeObject) -> tuple:
        seed_l = seed.lower()
        seed_hit = 0
        if seed:
            seed_hit = (
                0
                if seed_l in o.content.title.lower()
                or any(seed_l in c.lower() for c in o.content.atomic_concepts)
                else 1
            )
        return (
            seed_hit,
            prereq_count.get(o.id, 0),
            -outbound.get(o.id, 0),
            o.content.title,
            o.id,
        )

    ordered = sorted(kos, key=sort_key)

    n = len(ordered)
    stages = [
        ("Foundation", ordered[: max(1, n // 3)]),
        ("Core mechanisms", ordered[max(1, n // 3) : max(2, 2 * n // 3)]),
        ("Advanced / synthesis", ordered[max(2, 2 * n // 3) :]),
    ]
    sections: list[ViewSection] = []
    for title, group in stages:
        if not group:
            continue
        sections.append(
            ViewSection(
                title=title,
                kind="learning_stage",
                ko_ids=[o.id for o in group],
                notes=[
                    (
                        f"{i + 1}. {o.content.title} "
                        f"(prereq={prereq_count.get(o.id, 0)}, "
                        f"out={outbound.get(o.id, 0)})"
                    )
                    for i, o in enumerate(group)
                ],
                rationale=(
                    f"Stage '{title}' ordered by prerequisite count, "
                    f"then outbound relation density, then title"
                ),
            )
        )

    view = ReconstructedView(
        view_type="learning_path",
        title="Learning path reconstruction",
        seed=seed,
        graph_id=graph.id,
        source_ko_ids=list(graph.source_ko_ids),
        sections=sections,
        evidence={
            "view": "learning_path",
            "method": "prerequisite_count+relation_outbound+stable_title_tiebreak",
        },
    )
    return _finalize(view, graph=graph, seed=seed)


def reconstruct_view(
    graph: ConceptGraph,
    kos: list[KnowledgeObject],
    *,
    view: str,
    seed: str = "",
) -> ReconstructedView:
    if view == "theme":
        return view_by_theme(graph, kos, seed=seed)
    if view == "concept":
        return view_by_concept(graph, kos, seed=seed)
    if view in {"path", "learning_path", "learning"}:
        return view_by_learning_path(graph, kos, seed=seed)
    raise ValueError(f"unknown view type: {view} (use theme|concept|learning_path)")
