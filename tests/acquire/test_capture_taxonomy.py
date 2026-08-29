"""Generic capture taxonomy is orthogonal to access.classification."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from app.knowledge.parse import load_unit_from_markdown
from app.knowledge.taxonomy import (
    TaxonomyBlock,
    clamp_taxonomy_path,
    default_taxonomy_for_capture,
)
from app.models import IngestedSource, KnowledgeUnit
from app.pipeline import _finalize


def test_default_taxonomy_for_capture_youtube_four_segments():
    tax = default_taxonomy_for_capture("youtube", leaf_title="孙宇晨与景甜的3000万彩礼争议")
    assert tax.path[:3] == ["公开媒体", "捕获", "YouTube"]
    assert tax.path[3] == "孙宇晨与景甜的3000万彩礼争议"
    assert tax.depth == 4


def test_default_taxonomy_for_capture_clamps_leaf_and_depth():
    long_title = "字" * 80
    tax = default_taxonomy_for_capture("bilibili", leaf_title=long_title)
    assert tax.path[:3] == ["公开媒体", "捕获", "Bilibili"]
    assert tax.depth <= 5
    assert tax.path[-1].endswith("…")
    assert len(tax.path[-1]) <= 48


def test_clamp_taxonomy_path_max_five():
    assert clamp_taxonomy_path(["a", "b", "c", "d", "e", "f"]) == ["a", "b", "c", "d", "e"]


def test_finalize_assigns_capture_taxonomy_and_public_access(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    (tmp_path / "raw").mkdir()
    (tmp_path / "knowledge").mkdir()

    src = IngestedSource(
        source_type="youtube",
        title="URL only",
        text="hello world transcript content enough.",
        url="https://www.youtube.com/watch?v=abc",
        path=None,
        metadata={"video_id": "abc"},
    )
    unit = KnowledgeUnit(
        title="Capture Orthogonality Card",
        source="https://www.youtube.com/watch?v=abc",
        type="youtube",
        summary="s",
        concepts=["a"],
        key_points=["b"],
    )
    assert not unit.taxonomy.path
    with patch("app.pipeline.compress", return_value=unit):
        result = _finalize(src, dest_dir=tmp_path / "knowledge", index=False)

    loaded = load_unit_from_markdown(result.markdown_path)
    assert loaded.taxonomy.path[:3] == ["公开媒体", "捕获", "YouTube"]
    assert loaded.taxonomy.path[-1] == "Capture Orthogonality Card"
    assert loaded.access.classification == "public"


def test_finalize_does_not_overwrite_existing_taxonomy(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    (tmp_path / "raw").mkdir()
    (tmp_path / "knowledge").mkdir()

    src = IngestedSource(
        source_type="youtube",
        title="Preset",
        text="hello world transcript content enough.",
        url="https://www.youtube.com/watch?v=def",
    )
    preset = TaxonomyBlock(path=["自定义域", "子类", "主题"])
    unit = KnowledgeUnit(
        title="Preset Leaf",
        source="https://www.youtube.com/watch?v=def",
        type="youtube",
        summary="s",
        concepts=["a"],
        key_points=["b"],
        taxonomy=preset,
    )
    with patch("app.pipeline.compress", return_value=unit):
        result = _finalize(src, dest_dir=tmp_path / "knowledge", index=False)

    loaded = load_unit_from_markdown(result.markdown_path)
    assert loaded.taxonomy.path == ["自定义域", "子类", "主题"]
    assert loaded.access.classification == "public"
