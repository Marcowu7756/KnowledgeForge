"""剧本二：沉淀知识 — KU/KO/Expression/Harness（单元级）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.expression.derive import derive_audio_from_ko, derive_visual_from_ko
from app.harness.artifact import Artifact, sha256_file, write_json
from app.harness.validator import ValidationError, validate_artifact
from app.knowledge.object import from_knowledge_unit, relations_from_unit
from app.knowledge.parse import load_knowledge_object, load_unit_from_markdown, write_knowledge_object
from app.models import KnowledgeUnit


# --- 小剧本：Markdown 卡 → KU ---


def test_distill_parse_markdown_card_sections(tmp_card: Path):
    unit = load_unit_from_markdown(tmp_card)
    assert unit.title == "美债与美元信用"
    assert "美债" in unit.concepts
    assert unit.mechanisms
    assert unit.relationships
    assert unit.summary


def test_distill_crlf_markdown_still_parses(tmp_path: Path):
    text = (
        "# 标题\r\n\r\n"
        "```yaml\r\nid: abc123def456\r\ntitle: 标题\r\ntype: notes\r\n```\r\n\r\n"
        "## Core Idea\r\n\r\n摘要内容。\r\n\r\n"
        "## Concepts\r\n\r\n- 概念A\r\n- 概念B\r\n"
    )
    path = tmp_path / "crlf.md"
    path.write_bytes(text.encode("utf-8"))
    unit = load_unit_from_markdown(path)
    assert unit.summary.startswith("摘要")
    assert unit.concepts == ["概念A", "概念B"]


# --- 小剧本：KU → KnowledgeObject ---


def test_distill_ku_to_knowledge_object(sample_unit: KnowledgeUnit):
    obj = from_knowledge_unit(sample_unit)
    assert obj.id.startswith("ko_")
    assert obj.content.title == sample_unit.title
    assert obj.content.atomic_concepts == sample_unit.concepts
    assert obj.relations  # parsed from mechanisms/relationships
    assert obj.schema_version == "0.1"


def test_distill_relations_from_arrows(sample_unit: KnowledgeUnit):
    edges = relations_from_unit(sample_unit)
    assert any(e.from_node and e.to_node for e in edges)
    assert any("美债" in e.from_node or "美债" in e.to_node for e in edges)


def test_distill_roundtrip_knowledge_object_json(tmp_path: Path, sample_ko):
    dest = tmp_path / "knowledge_object.json"
    write_knowledge_object(sample_ko, dest)
    loaded = load_knowledge_object(dest)
    assert loaded.id == sample_ko.id
    assert loaded.content.title == sample_ko.content.title


def test_distill_load_ko_from_markdown_card(tmp_card: Path):
    obj = load_knowledge_object(tmp_card)
    assert obj.content.atomic_concepts
    assert obj.source.mode == "from_card"


# --- 小剧本：KO → ExpressionObject（不渲染 GIF/TTS） ---


def test_distill_visual_expression_from_ko_structure(sample_ko):
    vx = derive_visual_from_ko(sample_ko)
    assert vx.type == "animation"
    assert vx.source_ko == sample_ko.id
    assert vx.storyboard
    assert vx.evidence.derived_from == sample_ko.id
    assert vx.evidence.compile_source in {"ko_structure", "ko_fallback"}


def test_distill_audio_expression_script_from_ko(sample_ko):
    ax = derive_audio_from_ko(sample_ko)
    assert ax.type == "narration"
    assert ax.source_ko == sample_ko.id
    assert len(ax.script) >= 10
    assert ax.evidence.derived_from == sample_ko.id


# --- 小剧本：Harness artifact 校验 ---


def test_distill_artifact_checksum_and_validate(tmp_path: Path):
    path = write_json(tmp_path / "source.json", {"mode": "test", "ok": True})
    art = Artifact.from_path("source", path)
    assert art.checksum == sha256_file(path)
    assert art.bytes > 0
    validate_artifact(art)


def test_distill_artifact_too_small_rejected(tmp_path: Path):
    path = tmp_path / "tiny.json"
    path.write_text("{}", encoding="utf-8")
    art = Artifact.from_path("knowledge_object", path)
    with pytest.raises(ValidationError):
        validate_artifact(art)
