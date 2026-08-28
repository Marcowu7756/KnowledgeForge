"""Class C · Relation Gap — edge hygiene + soft graph-boost gating."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.knowledge.object import ContentBlock, KnowledgeObject
from app.knowledge.taxonomy import TaxonomyBlock
from app.reconstruct.build import build_graph
from app.reconstruct.edge_hygiene import (
    allow_shared_fanout,
    is_informative_shared_label,
)
from app.reconstruct.models import (
    ConceptGraph,
    EdgeEvidence,
    GraphEdge,
    GraphNode,
    RelationLayer,
)
from app.retrieve.models import IndexRecord
from app.retrieve.query import _graph_neighbor_scores, retrieve_kos
from app.retrieve.store import save_index


def _ko(kid: str, title: str, concepts: list[str], tags: list[str] | None = None) -> KnowledgeObject:
    return KnowledgeObject(
        id=kid,
        unit_id=kid,
        content=ContentBlock(
            title=title,
            summary=title,
            atomic_concepts=concepts,
            tags=tags or [],
        ),
        taxonomy=TaxonomyBlock(path=["专有知识", "SETV", "State Snapshot"]),
    )


def test_hygiene_rejects_generic_labels():
    assert not is_informative_shared_label("SETV")
    assert not is_informative_shared_label("(none)")
    assert not is_informative_shared_label("cite-only")
    assert not is_informative_shared_label("H4")
    assert is_informative_shared_label("GOLD")
    assert is_informative_shared_label("kernel persistence")


def test_hygiene_fanout_cap():
    assert allow_shared_fanout(2, kind="shared_concept")
    assert allow_shared_fanout(8, kind="shared_concept")
    assert not allow_shared_fanout(9, kind="shared_concept")
    assert allow_shared_fanout(12, kind="shared_tag")
    assert not allow_shared_fanout(13, kind="shared_tag")


def test_build_skips_setv_clique_keeps_informative():
    kos = [
        _ko("a", "GOLD H4", ["SETV", "GOLD", "H4"], ["setv", "cite-only", "gold-h4"]),
        _ko("b", "EURUSD H4", ["SETV", "EURUSD", "H4"], ["setv", "cite-only", "eurusd-h4"]),
        _ko("c", "GOLD D", ["SETV", "GOLD", "D"], ["setv", "cite-only", "gold-d"]),
    ]
    graph = build_graph(kos, min_confidence=0.0)
    shared = [e for e in graph.relations.edges if e.kind == "shared_concept"]
    labels = {e.label.lower() for e in shared}
    assert "setv" not in labels
    assert "h4" not in labels
    assert "gold" in labels  # a↔c via GOLD
    assert not any(
        e.label.lower() == "setv" for e in graph.relations.edges if e.kind == "shared_tag"
    )


def test_graph_boost_skips_none_label():
    graph = ConceptGraph(
        id="cg_c",
        nodes=[
            GraphNode(id="ko_ko_a", kind="knowledge_object", label="A", ko_ids=["ko_a"]),
            GraphNode(id="ko_ko_b", kind="knowledge_object", label="B", ko_ids=["ko_b"]),
        ],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e_none",
                    from_node="ko_ko_a",
                    to_node="ko_ko_b",
                    type="related",
                    kind="shared_concept",
                    label="(none)",
                    confidence=0.9,
                    source_ko_ids=["ko_a", "ko_b"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_a", "ko_b"],
                    ),
                )
            ]
        ),
    )
    scores = _graph_neighbor_scores(graph, ["ko_a"], allowed={"ko_a", "ko_b"})
    assert "ko_b" not in scores


def test_retrieve_zero_overlap_drops_soft_boost(tmp_path: Path):
    records = [
        IndexRecord(
            ko_id="ko_seed",
            vector_id="e0",
            title="美债",
            path="a.md",
            concepts=["美债"],
            tags=["金融"],
            summary="s",
            text_hash="h0",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_noise",
            vector_id="e1",
            title="网球公开赛",
            path="b.md",
            concepts=["网球"],
            tags=["体育"],
            summary="s",
            text_hash="h1",
            indexed_at="t",
        ),
    ]
    vectors = np.array([[1.0, 0.0], [0.85, 0.1]], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)

    graph = ConceptGraph(
        id="cg_noise",
        nodes=[],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e_soft",
                    from_node="ko_ko_seed",
                    to_node="ko_ko_noise",
                    type="related",
                    kind="shared_concept",
                    label="无关概念",
                    confidence=0.95,
                    source_ko_ids=["ko_seed", "ko_noise"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_seed", "ko_noise"],
                    ),
                )
            ]
        ),
    )

    def fake_embed(_q: str):
        return np.array([1.0, 0.0], dtype=np.float32)

    with patch("app.retrieve.query.embed_query", side_effect=fake_embed):
        result = retrieve_kos(
            "美债",
            top_k=2,
            index_dir=tmp_path,
            graph=graph,
            semantic_pool=2,
            graph_weight=0.5,
        )
    by_id = {h.ko_id: h for h in result.hits}
    noise = by_id["ko_noise"]
    assert noise.graph_score == 0.0
    assert not any("graph_boost=" in w for w in noise.why)


def test_retrieve_generic_tf_token_alone_no_soft_boost(tmp_path: Path):
    """Bare H4 in query must not unlock soft boost via unrelated instrument edges."""
    records = [
        IndexRecord(
            ko_id="ko_usd",
            vector_id="e0",
            title="USDJPY H4",
            path="a.md",
            concepts=["USDJPY", "H4"],
            tags=["setv"],
            summary="s",
            text_hash="h0",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_eur",
            vector_id="e1",
            title="EURUSD H4",
            path="b.md",
            concepts=["EURUSD", "H4"],
            tags=["setv"],
            summary="s",
            text_hash="h1",
            indexed_at="t",
        ),
    ]
    vectors = np.array([[1.0, 0.0], [0.9, 0.05]], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)
    graph = ConceptGraph(
        id="cg_tf",
        nodes=[],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e_eur",
                    from_node="ko_ko_usd",
                    to_node="ko_ko_eur",
                    type="related",
                    kind="shared_concept",
                    label="EURUSD",
                    confidence=0.9,
                    source_ko_ids=["ko_usd", "ko_eur"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_usd", "ko_eur"],
                    ),
                )
            ]
        ),
    )

    def fake_embed(_q: str):
        return np.array([1.0, 0.0], dtype=np.float32)

    with patch("app.retrieve.query.embed_query", side_effect=fake_embed):
        result = retrieve_kos(
            "USDJPY H4",
            top_k=2,
            index_dir=tmp_path,
            graph=graph,
            semantic_pool=2,
            graph_weight=0.5,
        )
    by_id = {h.ko_id: h for h in result.hits}
    # EURUSD edge label does not hit query; H4 alone is generic → no soft boost
    assert by_id["ko_eur"].graph_score == 0.0


def test_retrieve_label_hit_allows_soft_boost(tmp_path: Path):
    # Pool > seed count so a non-seed neighbor can receive boost.
    records = [
        IndexRecord(
            ko_id="ko_a",
            vector_id="e0",
            title="GOLD H4 snap",
            path="a.md",
            concepts=["GOLD", "H4"],
            tags=["setv"],
            summary="s",
            text_hash="h0",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_f1",
            vector_id="e1",
            title="filler one",
            path="f1.md",
            concepts=["filler1"],
            tags=["x"],
            summary="s",
            text_hash="h1",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_f2",
            vector_id="e2",
            title="filler two",
            path="f2.md",
            concepts=["filler2"],
            tags=["x"],
            summary="s",
            text_hash="h2",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_b",
            vector_id="e3",
            title="GOLD D snap",
            path="b.md",
            concepts=["GOLD", "D"],
            tags=["setv"],
            summary="s",
            text_hash="h3",
            indexed_at="t",
        ),
    ]
    # Rank: a > f1 > f2 > b  → seeds = top3 (a,f1,f2); b gets graph boost
    vectors = np.array(
        [[1.0, 0.0], [0.95, 0.05], [0.9, 0.1], [0.7, 0.2]],
        dtype=np.float32,
    )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)
    graph = ConceptGraph(
        id="cg_gold",
        nodes=[],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e_gold",
                    from_node="ko_ko_a",
                    to_node="ko_ko_b",
                    type="related",
                    kind="shared_concept",
                    label="GOLD",
                    confidence=0.9,
                    source_ko_ids=["ko_a", "ko_b"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_a", "ko_b"],
                    ),
                )
            ]
        ),
    )

    def fake_embed(_q: str):
        return np.array([1.0, 0.0], dtype=np.float32)

    with patch("app.retrieve.query.embed_query", side_effect=fake_embed):
        result = retrieve_kos(
            "GOLD H4",
            top_k=2,
            index_dir=tmp_path,
            graph=graph,
            semantic_pool=4,
            graph_weight=0.5,
        )
    by_id = {h.ko_id: h for h in result.hits}
    assert "ko_b" in by_id
    assert by_id["ko_b"].graph_score > 0
    assert any("graph_boost=" in w and "label_hit" in w for w in by_id["ko_b"].why)
