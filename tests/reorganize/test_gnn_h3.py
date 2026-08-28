"""H3 · offline GNN shadow scores on ConceptGraph."""

from __future__ import annotations

import json
from pathlib import Path

from app.reconstruct.gnn_offline import (
    SHADOW_NAME,
    concept_graph_to_nx,
    gnn_boost_enabled,
    load_shadow_scores,
    propagate_scores,
    run_offline_gnn,
)
from app.reconstruct.models import (
    ConceptGraph,
    EdgeEvidence,
    GraphEdge,
    GraphNode,
    RelationLayer,
)


def _toy_graph() -> ConceptGraph:
    return ConceptGraph(
        id="cg_h3",
        source_ko_ids=["ko_a", "ko_b", "ko_c"],
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
                    label="X",
                    confidence=0.9,
                    weight=1.0,
                    source_ko_ids=["ko_a", "ko_b"],
                    evidence=EdgeEvidence(rule_id="shared_concept_cross_ko", reason="t"),
                ),
                GraphEdge(
                    id="e2",
                    from_node="ko_ko_b",
                    to_node="ko_ko_c",
                    type="related",
                    kind="shared_concept",
                    label="Y",
                    confidence=0.8,
                    weight=1.0,
                    source_ko_ids=["ko_b", "ko_c"],
                    evidence=EdgeEvidence(rule_id="shared_concept_cross_ko", reason="t"),
                ),
            ]
        ),
    )


def test_propagate_from_seed_ranks_neighbors():
    g, _ = concept_graph_to_nx(_toy_graph())
    scores = propagate_scores(g, ["ko_a"], steps=6, alpha=0.85)
    assert scores["ko_a"] == max(scores.values())
    assert scores["ko_b"] > 0
    assert scores["ko_c"] > 0
    # 1-hop neighbor should retain mass after diffusion
    assert scores["ko_b"] > 0.1


def test_run_offline_writes_shadow(tmp_path: Path):
    out = tmp_path / SHADOW_NAME
    result = run_offline_gnn(_toy_graph(), seeds=["ko_a"], out_path=out)
    assert out.is_file()
    assert result.output_path == out
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema"] == "kf_gnn_shadow_v0"
    assert data["h3"].startswith("H3")
    loaded = load_shadow_scores(out)
    assert "ko_a" in loaded
    assert loaded["ko_b"] > 0


def test_gnn_boost_flag_default_off(monkeypatch):
    monkeypatch.delenv("KF_GNN_BOOST", raising=False)
    assert gnn_boost_enabled() is False
    monkeypatch.setenv("KF_GNN_BOOST", "1")
    assert gnn_boost_enabled() is True


def test_retrieve_blends_gnn_only_when_flag(tmp_path: Path, monkeypatch):
    import numpy as np
    from unittest.mock import patch

    from app.retrieve.models import IndexRecord
    from app.retrieve.query import retrieve_kos
    from app.retrieve.store import save_index

    records = [
        IndexRecord(
            ko_id="ko_a",
            vector_id="e0",
            title="seed A",
            path="a.md",
            concepts=["A"],
            tags=[],
            summary="s",
            text_hash="h0",
            indexed_at="t",
        ),
        IndexRecord(
            ko_id="ko_b",
            vector_id="e1",
            title="neighbor B",
            path="b.md",
            concepts=["B"],
            tags=[],
            summary="s",
            text_hash="h1",
            indexed_at="t",
        ),
    ]
    vectors = np.array([[1.0, 0.0], [0.9, 0.1]], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)

    shadow = tmp_path / SHADOW_NAME
    shadow.write_text(
        json.dumps(
            {
                "schema": "kf_gnn_shadow_v0",
                "scores": {"ko_a": 1.0, "ko_b": 0.9},
            }
        ),
        encoding="utf-8",
    )

    def fake_embed(_q: str):
        return np.array([1.0, 0.0], dtype=np.float32)

    monkeypatch.delenv("KF_GNN_BOOST", raising=False)
    with patch("app.retrieve.query.embed_query", side_effect=fake_embed):
        off = retrieve_kos(
            "seed",
            top_k=2,
            index_dir=tmp_path,
            gnn_shadow_path=shadow,
            gnn_weight=0.5,
        )
    assert off.evidence.get("gnn_boost_enabled") is False
    assert not any("gnn_shadow=" in w for h in off.hits for w in h.why)

    monkeypatch.setenv("KF_GNN_BOOST", "1")
    with patch("app.retrieve.query.embed_query", side_effect=fake_embed):
        on = retrieve_kos(
            "seed",
            top_k=2,
            index_dir=tmp_path,
            gnn_shadow_path=shadow,
            gnn_weight=0.5,
        )
    assert on.evidence.get("gnn_boost_enabled") is True
    assert any("gnn_shadow=" in w for h in on.hits for w in h.why)
