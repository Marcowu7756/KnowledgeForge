"""剧本四：重组知识 — Relation / Graph / View / Evolution（单元级）。"""

from __future__ import annotations

from pathlib import Path

from app.reconstruct.build import build_graph, stable_graph_id
from app.reconstruct.evolve import evolve_graph
from app.reconstruct.rules import (
    RULES,
    confidence_for,
    infer_relation_type,
    make_evidence,
)
from app.reconstruct.views import reconstruct_view, stability_fingerprint


# --- 小剧本：关系质量规则 ---


def test_reorganize_relation_rules_have_confidence_ladder():
    assert RULES["intra_ko_explicit"].base_confidence > RULES["shared_tag_cross_ko"].base_confidence
    assert confidence_for("intra_ko_explicit") >= 0.9
    assert confidence_for("shared_tag_cross_ko") < 0.5


def test_reorganize_infer_relation_type_from_label():
    assert infer_relation_type("导致上涨", "related") == "causes"
    assert infer_relation_type("A vs B", "related") == "contrasts"
    assert infer_relation_type("", "depends_on") == "depends_on"


def test_reorganize_edge_evidence_carries_rule():
    ev = make_evidence("shared_concept_cross_ko", sources=["ko_a", "ko_b"], detail="美债")
    assert ev.rule_id == "shared_concept_cross_ko"
    assert "ko_a" in ev.sources
    assert "美债" in ev.reason


# --- 小剧本：多 KO → ConceptGraph ---


def test_reorganize_build_graph_from_multiple_kos(two_kos):
    graph = build_graph(two_kos)
    assert len(graph.source_ko_ids) == 2
    assert graph.nodes
    assert graph.relations.edges
    assert graph.relations.stats["kos"] == 2
    # shared concept 美元 should create cross-KO link or shared nodes
    kinds = {e.kind for e in graph.relations.edges}
    assert "intra_ko" in kinds or "ko_mentions" in kinds
    assert all(e.confidence > 0 for e in graph.relations.edges)
    assert all(e.evidence.rule_id for e in graph.relations.edges)


def test_reorganize_graph_id_deterministic(two_kos):
    g1 = build_graph(two_kos)
    g2 = build_graph(list(reversed(two_kos)))
    assert g1.id == g2.id == stable_graph_id([o.id for o in two_kos])


def test_reorganize_min_confidence_filters_soft_edges(two_kos):
    full = build_graph(two_kos, min_confidence=0.0)
    strict = build_graph(two_kos, min_confidence=0.8)
    assert strict.relations.stats["edges"] <= full.relations.stats["edges"]
    assert all(e.confidence >= 0.8 for e in strict.relations.edges)


# --- 小剧本：Graph Evolution ---


def test_reorganize_evolve_adds_ko(two_kos):
    base = build_graph(two_kos[:1])
    evo = evolve_graph(base, all_kos=two_kos)
    assert evo.graph.generation == base.generation + 1
    assert evo.added_ko_ids == [two_kos[1].id]
    assert two_kos[0].id in evo.unchanged_ko_ids
    delta = evo.graph.evidence["delta"]
    assert delta["base_graph_id"] == base.id


# --- 小剧本：Reconstructed Views ---


def test_reorganize_theme_view_stable(two_kos):
    graph = build_graph(two_kos)
    v1 = reconstruct_view(graph, two_kos, view="theme")
    v2 = reconstruct_view(graph, two_kos, view="theme")
    assert v1.id == v2.id
    assert v1.stability["fingerprint"] == v2.stability["fingerprint"]
    assert v1.sections
    assert all(s.rationale for s in v1.sections)


def test_reorganize_concept_view_needs_seed(two_kos):
    graph = build_graph(two_kos)
    view = reconstruct_view(graph, two_kos, view="concept", seed="美债")
    assert view.view_type == "concept"
    assert view.seed == "美债"
    assert view.sections


def test_reorganize_learning_path_has_stages(two_kos):
    graph = build_graph(two_kos)
    view = reconstruct_view(graph, two_kos, view="learning_path")
    assert view.view_type == "learning_path"
    assert len(view.sections) >= 1
    fp = stability_fingerprint(view)
    assert len(fp["fingerprint"]) == 40  # sha1 hex


def test_reorganize_contrast_view_type_registered(two_kos):
    graph = build_graph(two_kos)
    view = reconstruct_view(graph, two_kos, view="contrast")
    assert view.view_type == "contrast"
    assert view.evidence.get("view") == "contrast"
