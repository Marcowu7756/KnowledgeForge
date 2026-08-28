"""rebuild_index must recurse into nested restricted trees (SETV cites)."""

from __future__ import annotations

from pathlib import Path

from app.storage.index import rebuild_index
from app.storage.markdown import write_knowledge_unit
from app.models import KnowledgeUnit
from app.knowledge.access import AccessBlock, default_policy_for


def test_rebuild_subdir_recurses_nested_cards(tmp_path: Path, monkeypatch):
    from app import config

    knowledge = tmp_path / "knowledge"
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(config, "INDEX_ENABLED", True)
    monkeypatch.setattr(config, "ROOT", tmp_path)

    nested = knowledge / "restricted" / "setv" / "snapshots"
    nested.mkdir(parents=True)
    unit = KnowledgeUnit(
        id="abc123def456",
        title="Nested SETV Cite",
        source="test",
        type="md",
        summary="nested",
        concepts=["SETV"],
        tags=["setv"],
        access=AccessBlock(
            classification="restricted",
            source_project="setv",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        ),
    )
    write_knowledge_unit(unit, dest_dir=nested, filename_stem="nested_cite")

    written = rebuild_index(subdir="restricted")
    assert "global_jsonl" in written
    text = written["global_jsonl"].read_text(encoding="utf-8")
    assert "nested_cite" in text or "Nested SETV" in text
    assert "restricted" in text
