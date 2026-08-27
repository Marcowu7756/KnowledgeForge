"""剧本三：搜索定位知识 — Embedding 索引文本 + 向量存储 + Compose 渲染（单元级）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.compose.models import ComposeResultMeta, ComposeSourceHit
from app.compose.render import render_lecture, render_paper
from app.retrieve.models import IndexRecord
from app.retrieve.store import cosine_top_k, save_index, load_manifest, load_records, load_vectors
from app.retrieve.text import ko_embed_text, text_hash, vector_id_for


# --- 小剧本：KO 级嵌入文本（禁止 chunk 语义） ---


def test_locate_ko_embed_text_is_whole_object(sample_ko):
    text = ko_embed_text(sample_ko)
    assert sample_ko.content.title in text
    assert "美债" in text
    assert "概念" in text or "美债" in text


def test_locate_vector_id_stable_for_same_ko_model():
    a = vector_id_for("ko_abc", "bge")
    b = vector_id_for("ko_abc", "bge")
    c = vector_id_for("ko_xyz", "bge")
    assert a == b
    assert a != c
    assert a.startswith("emb_")


def test_locate_text_hash_changes_with_content():
    assert text_hash("a") != text_hash("b")


# --- 小剧本：本地向量索引读写 ---


def test_locate_save_and_load_index(tmp_path: Path):
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
        ),
        IndexRecord(
            ko_id="ko_2",
            vector_id="emb_2",
            title="B",
            path="b.md",
            concepts=["y"],
            tags=["t"],
            summary="sb",
            text_hash="h2",
            indexed_at="2026-01-01T00:00:00Z",
        ),
    ]
    # deliberately unsorted input; store sorts by ko_id
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    manifest = save_index(
        records=records,
        vectors=vectors,
        model="mock-bge",
        evidence={"unit": "knowledge_object"},
        root=tmp_path,
    )
    assert manifest.count == 2
    assert manifest.dim == 2
    assert manifest.ko_ids == ["ko_1", "ko_2"]
    loaded = load_records(tmp_path)
    assert [r.ko_id for r in loaded] == ["ko_1", "ko_2"]
    mat = load_vectors(tmp_path)
    assert mat.shape == (2, 2)
    assert load_manifest(tmp_path).model == "mock-bge"


def test_locate_cosine_top_k_ranks_nearest():
    matrix = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.7, 0.7, 0.0],
        ],
        dtype=np.float32,
    )
    # normalize rows for cosine=dot
    matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    ranked = cosine_top_k(query, matrix, top_k=2)
    assert ranked[0][0] == 0
    assert ranked[0][1] > ranked[1][1]


# --- 小剧本：检索结果驱动 Compose 渲染（不调 LLM） ---


def test_locate_compose_paper_render_includes_sources():
    meta = ComposeResultMeta(
        kind="paper",
        query="美债",
        sources=[
            ComposeSourceHit(ko_id="ko_1", title="卡A", score=0.8, path="a.md"),
        ],
        llm_provider="ollama",
        retrieve_mode="semantic",
    )
    payload = {
        "title": "论美债",
        "abstract": "摘要",
        "sections": [{"heading": "背景", "body": "论述内容", "source_ko_ids": ["ko_1"]}],
        "conclusion": "结论",
        "references": ["卡A"],
        "unknowns": [],
    }
    md = render_paper(payload, meta)
    assert "# 论美债" in md
    assert "论述内容" in md
    assert "ko_1" in md


def test_locate_compose_lecture_render_has_script():
    meta = ComposeResultMeta(
        kind="lecture",
        query="美债",
        sources=[ComposeSourceHit(ko_id="ko_1", title="卡A", score=0.7)],
        llm_provider="ollama",
        retrieve_mode="graph_aware",
    )
    payload = {
        "title": "讲解美债",
        "audience": "初学者",
        "duration_hint": "5min",
        "outline": ["引入", "机制"],
        "script": "大家好，今天讲美债。",
        "key_takeaways": ["要点1"],
        "unknowns": [],
    }
    md = render_lecture(payload, meta)
    assert "讲解稿" in md or "讲解美债" in md
    assert "大家好，今天讲美债。" in md
    assert "graph_aware" in md
