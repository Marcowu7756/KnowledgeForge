"""Regression: pipeline finalize must tolerate URL-only sources and off-root dest."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from app.models import IngestedSource, KnowledgeUnit
from app.pipeline import _finalize


def test_finalize_url_only_source_no_source_attr(tmp_path: Path, monkeypatch):
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
        title="URL only",
        source="https://www.youtube.com/watch?v=abc",
        type="youtube",
        summary="s",
        concepts=["a"],
        key_points=["b"],
    )
    with patch("app.pipeline.compress", return_value=unit):
        result = _finalize(src, dest_dir=tmp_path / "knowledge", index=False)
    assert result.markdown_path.is_file()


def test_finalize_off_root_dest_does_not_raise(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    (tmp_path / "raw").mkdir()
    outside = tmp_path / "outside_cards"
    outside.mkdir()

    src = IngestedSource(
        source_type="txt",
        title="Off root",
        text="local note text for compress.",
        path=str(tmp_path / "note.txt"),
    )
    Path(src.path).write_text(src.text, encoding="utf-8")
    unit = KnowledgeUnit(
        title="Off root",
        source=str(src.path),
        type="txt",
        summary="s",
        concepts=["a"],
        key_points=["b"],
    )
    with patch("app.pipeline.compress", return_value=unit):
        result = _finalize(src, dest_dir=outside, index=False)
    assert result.markdown_path.is_file()
    assert result.markdown_path.parent == outside
