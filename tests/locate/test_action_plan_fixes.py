"""Additional unit tests for ACTION_PLAN A1–A5 / A8."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.compose.validate import ComposePayloadError, validate_compose_payload
from app.derive.render import render_physics_derive
from app.retrieve.models import IndexRecord
from app.retrieve.query import _graph_neighbor_scores, _query_overlap, retrieve_kos
from app.retrieve.store import embeddings_path, save_index
from app.reconstruct.models import (
    ConceptGraph,
    EdgeEvidence,
    GraphEdge,
    GraphNode,
    RelationLayer,
)
from app.reconstruct.rules import RULES, infer_relation_type


def test_a1_manim_beats_marked_defer_not_wired():
    md = render_physics_derive(
        {
            "title": "牛顿",
            "manim_beats": [{"scene": "s1", "on_screen": "ball", "narration": "fall"}],
        },
        parent_path="x.md",
    )
    assert "DEFER" in md
    assert "not_wired_to_expression" in md


def test_a2_compose_payload_paper_ok():
    validate_compose_payload(
        "paper",
        {
            "title": "T",
            "abstract": "A",
            "sections": [{"heading": "H", "body": "B"}],
        },
    )


def test_a2_compose_payload_paper_missing_sections():
    with pytest.raises(ComposePayloadError) as ei:
        validate_compose_payload("paper", {"title": "T", "abstract": "A", "sections": []})
    assert "sections" in str(ei.value)


def test_a2_compose_payload_lecture_requires_script():
    with pytest.raises(ComposePayloadError):
        validate_compose_payload(
            "lecture",
            {"title": "T", "outline": ["a"], "script": ""},
        )


def test_a5_save_index_writes_embeddings_sidecar(tmp_path: Path):
    records = [
        IndexRecord(
            ko_id="ko_1",
            vector_id="emb_1",
            title="A",
            path="a.md",
            concepts=["x"],
            tags=["t"],
            summary="sa",
            text_hash="h1",
            indexed_at="2026-01-01T00:00:00Z",
        )
    ]
    vectors = np.array([[1.0, 0.0]], dtype=np.float32)
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)
    side = embeddings_path(tmp_path)
    assert side.is_file()
    data = json.loads(side.read_text(encoding="utf-8"))
    assert data["refs"]["ko_1"]["vector_id"] == "emb_1"
    assert data["refs"]["ko_1"]["status"] == "ready"


def test_a4_query_overlap_and_graph_only_in_pool():
    rec = IndexRecord(
        ko_id="ko_a",
        vector_id="e",
        title="美债与美元",
        concepts=["美债", "美元"],
        tags=["金融"],
    )
    assert _query_overlap("美债 风险", rec) > 0

    graph = ConceptGraph(
        id="cg_t",
        nodes=[
            GraphNode(id="ko_ko_a", kind="knowledge_object", label="A", ko_ids=["ko_a"]),
            GraphNode(id="ko_ko_b", kind="knowledge_object", label="B", ko_ids=["ko_b"]),
            GraphNode(id="ko_ko_c", kind="knowledge_object", label="C", ko_ids=["ko_c"]),
        ],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e1",
                    from_node="ko_ko_a",
                    to_node="ko_ko_b",
                    type="related",
                    kind="shared_concept",
                    label="美元",
                    confidence=0.9,
                    source_ko_ids=["ko_a", "ko_b"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_a", "ko_b"],
                    ),
                ),
                GraphEdge(
                    id="e2",
                    from_node="ko_ko_a",
                    to_node="ko_ko_c",
                    type="related",
                    kind="shared_concept",
                    label="噪声",
                    confidence=0.9,
                    source_ko_ids=["ko_a", "ko_c"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_a", "ko_c"],
                    ),
                ),
            ]
        ),
    )
    scores = _graph_neighbor_scores(
        graph, ["ko_a"], min_confidence=0.5, allowed={"ko_a", "ko_b"}
    )
    assert "ko_b" in scores
    assert "ko_c" not in scores


def test_a4_retrieve_kos_no_out_of_pool_candidates(tmp_path: Path):
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
            ko_id="ko_near",
            vector_id="e1",
            title="美元信用",
            path="b.md",
            concepts=["美元", "美债"],
            tags=["金融"],
            summary="s",
            text_hash="h1",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_far",
            vector_id="e2",
            title="无关主题",
            path="c.md",
            concepts=["网球"],
            tags=["体育"],
            summary="s",
            text_hash="h2",
            indexed_at="t",
        ),
    ]
    vectors = np.array(
        [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]],
        dtype=np.float32,
    )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)

    graph = ConceptGraph(
        id="cg_x",
        nodes=[],
        relations=RelationLayer(
            edges=[
                GraphEdge(
                    id="e_far",
                    from_node="ko_ko_seed",
                    to_node="ko_ko_far",
                    type="related",
                    kind="shared_concept",
                    label="假共享",
                    confidence=0.95,
                    source_ko_ids=["ko_seed", "ko_far"],
                    evidence=EdgeEvidence(
                        rule_id="shared_concept_cross_ko",
                        reason="t",
                        sources=["ko_seed", "ko_far"],
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
    hit_ids = {h.ko_id for h in result.hits}
    assert "ko_far" not in hit_ids
    assert result.evidence.get("graph_boost_in_pool_only") is True


def test_a8_vs_and_inter_ko_rule_registered():
    assert infer_relation_type("区别于对手", "related") == "contrasts"
    assert "prerequisite_inter_ko" in RULES
