"""A8 deep: cross-KO explicit ``vs`` contrast linking and contrast view clustering."""

from __future__ import annotations

from pathlib import Path

from app.knowledge.parse import load_knowledge_object
from app.reconstruct.build import build_graph
from app.reconstruct.contrast import (
    collect_contrast_links,
    contrast_clusters_from_edges,
    parse_contrast_line,
)
from app.reconstruct.views import reconstruct_view
from app.retrieve.query import _graph_neighbor_scores
from tests.conftest import SAMPLE_CARD, SAMPLE_CARD_B


def _contrast_cards(tmp_path: Path) -> list:
    card_a = SAMPLE_CARD.replace(
        "## Relationship\n\n- 美债收益率上升 → 美股疲软",
        "## Relationship\n\n- 美债 vs 石油美元\n- 美债收益率上升 → 美股疲软",
    )
    path_a = tmp_path / "card_a.md"
    path_b = tmp_path / "card_b.md"
    path_a.write_text(card_a, encoding="utf-8")
    path_b.write_text(SAMPLE_CARD_B, encoding="utf-8")
    return [load_knowledge_object(p) for p in (path_a, path_b)]


def test_a8_parse_contrast_line_variants():
    assert parse_contrast_line("- 美债 vs 石油美元") == ("美债", "石油美元", "vs")
    assert parse_contrast_line("A 对比 B") == ("A", "B", "对比")
    assert parse_contrast_line("no separator") is None


def test_a8_collect_contrast_links_resolves_cross_ko(tmp_path: Path):
    kos = _contrast_cards(tmp_path)
    title_index = {k.content.title.lower(): k.id for k in kos}
    concept_index: dict[str, set[str]] = {}
    for obj in kos:
        for concept in obj.content.atomic_concepts:
            concept_index.setdefault(concept.lower(), set()).add(obj.id)

    links = collect_contrast_links(
        kos,
        title_index=title_index,
        concept_index=concept_index,
    )
    assert len(links) == 1
    link = links[0]
    assert {link.ko_a, link.ko_b} == {kos[0].id, kos[1].id}
    assert "vs" in link.label or link.left == "美债"


def test_a8_build_graph_emits_contrast_cross_ko_edge(tmp_path: Path):
    kos = _contrast_cards(tmp_path)
    graph = build_graph(kos)
    contrast_edges = [e for e in graph.relations.edges if e.kind == "contrast_cross_ko"]
    assert contrast_edges
    edge = contrast_edges[0]
    assert edge.evidence.rule_id == "contrast_cross_ko"
    assert edge.confidence >= 0.8
    assert set(edge.source_ko_ids) >= {kos[0].id, kos[1].id}


def test_a8_contrast_view_clusters_linked_kos(tmp_path: Path):
    kos = _contrast_cards(tmp_path)
    graph = build_graph(kos)
    view = reconstruct_view(graph, kos, view="contrast")
    assert view.view_type == "contrast"
    assert view.sections
    section = view.sections[0]
    assert section.kind in {"contrast_cluster", "contrast_pair"}
    assert set(section.ko_ids) == {kos[0].id, kos[1].id}


def test_a8_graph_neighbor_boost_includes_contrast_cross_ko(tmp_path: Path):
    from app.reconstruct.models import ConceptGraph, EdgeEvidence, GraphEdge, RelationLayer

    kos = _contrast_cards(tmp_path)
    graph = ConceptGraph(
        id="cg_contrast_only",
        nodes=[],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e_contrast",
                    from_node=f"ko_{kos[0].id}",
                    to_node=f"ko_{kos[1].id}",
                    type="contrasts",
                    kind="contrast_cross_ko",
                    label="美债 vs 石油美元",
                    confidence=0.84,
                    source_ko_ids=[kos[0].id, kos[1].id],
                    evidence=EdgeEvidence(
                        rule_id="contrast_cross_ko",
                        reason="test",
                        sources=[kos[0].id, kos[1].id],
                    ),
                )
            ]
        ),
    )
    scores = _graph_neighbor_scores(
        graph,
        [kos[0].id],
        min_confidence=0.5,
        allowed={k.id for k in kos},
    )
    assert kos[1].id in scores
    assert "contrast_cross_ko" in scores[kos[1].id][1]


def test_a8_contrast_clusters_union_find():
    class Edge:
        def __init__(self, kind: str, source_ko_ids: list[str], from_node: str, to_node: str):
            self.kind = kind
            self.source_ko_ids = source_ko_ids
            self.from_node = from_node
            self.to_node = to_node

    edges = [
        Edge("contrast_cross_ko", ["a", "b", "c"], "ko_a", "ko_b"),
        Edge("contrast_cross_ko", ["c", "d"], "ko_c", "ko_d"),
    ]
    clusters = contrast_clusters_from_edges(edges, ko_ids={"a", "b", "c", "d"})
    merged = next(m for m in clusters.values() if len(m) >= 3)
    assert merged == {"a", "b", "c", "d"}
