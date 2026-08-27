"""Taxonomy hierarchy + ecosystem design-doc ingest."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.compression.parse import knowledge_unit_from_payload
from app.ingest.ecosystem import discover_design_docs
from app.knowledge.parse import load_unit_from_markdown
from app.knowledge.taxonomy import (
    TaxonomyBlock,
    build_taxonomy_for_ingest,
    default_taxonomy_for_project,
    project_profile,
)
from app.reconstruct.build import build_graph
from app.reconstruct.views import reconstruct_view
from app.retrieve.text import ko_embed_text
from app.storage.markdown import render_markdown
from app.models import KnowledgeUnit


SETV_DOC = """# SETV State Discipline

When trend breaks, wait for reconfirm before re-entry.
Invalidation: regime flip without volume confirmation.
"""


def test_taxonomy_chain_matches_prefix():
    tax = TaxonomyBlock(path=["生物", "动物", "哺乳动物", "灵长类", "人"])
    assert tax.canonical == "生物/动物/哺乳动物/灵长类/人"
    assert tax.matches_prefix(["生物", "动物"])
    assert not tax.matches_prefix(["生物", "植物"])
    assert tax.leaf == "人"


def test_taxonomy_project_default_root():
    root = default_taxonomy_for_project("setv")
    assert root.path[:2] == ["专有知识", "SETV"]


def test_taxonomy_build_for_ingest_merges_path_and_llm():
    tax = build_taxonomy_for_ingest(
        project="setv",
        source_path=r"D:\fxtrading\setv\docs\methodology\state_transition.md",
        llm_path=["方法论", "状态转换"],
    )
    assert tax.path[0] == "专有知识"
    assert tax.path[1] == "SETV"
    assert "状态转换" in tax.path


def test_taxonomy_yaml_roundtrip(tmp_path: Path):
    unit = KnowledgeUnit(
        title="层级卡",
        source="unit-test",
        type="notes",
        summary="summary",
        taxonomy=TaxonomyBlock(path=["专有知识", "SETV", "方法论"]),
    )
    path = tmp_path / "card.md"
    path.write_text(render_markdown(unit), encoding="utf-8")
    loaded = load_unit_from_markdown(path)
    assert loaded.taxonomy.path == ["专有知识", "SETV", "方法论"]


def test_taxonomy_embed_text_includes_chain(sample_ko):
    sample_ko.taxonomy = TaxonomyBlock(path=["金融", "宏观", "美债"])
    text = ko_embed_text(sample_ko)
    assert "分类:" in text
    assert "金融 > 宏观 > 美债" in text


def test_taxonomy_graph_and_view(two_kos):
    for obj in two_kos:
        obj.taxonomy = TaxonomyBlock(path=["金融", "宏观", obj.content.title[:4] or "主题"])
    graph = build_graph(two_kos)
    tax_nodes = [n for n in graph.nodes if n.kind == "theme" and n.meta.get("taxonomy_path")]
    assert tax_nodes
    view = reconstruct_view(graph, two_kos, view="taxonomy")
    assert view.view_type == "taxonomy"
    assert view.sections


def test_ecosystem_discover_docs(tmp_path: Path):
    docs = tmp_path / "setv" / "docs"
    docs.mkdir(parents=True)
    (docs / "methodology.md").write_text(SETV_DOC, encoding="utf-8")
    raw = docs / "raw"
    raw.mkdir(parents=True)
    (raw / "secret.txt").write_text("nope", encoding="utf-8")
    hits = discover_design_docs([docs], project="setv")
    names = {h.path.name for h in hits}
    assert "methodology.md" in names
    assert "secret.txt" not in names


def test_ecosystem_payload_taxonomy_merge():
    payload = {
        "title": "SETV Method",
        "summary": "State-first discipline with invalidation rules.",
        "concepts": ["状态", "失效"],
        "key_points": ["先状态后指标"],
        "taxonomy_path": ["方法论", "状态转换"],
    }
    unit = knowledge_unit_from_payload(
        payload,
        source="design.md",
        source_type="md",
        url=None,
        fallback_title="SETV Method",
        taxonomy=build_taxonomy_for_ingest(
            project="setv",
            source_path="docs/methodology/state.md",
            llm_path=["方法论", "状态转换"],
        ),
    )
    assert unit.taxonomy.path[0] == "专有知识"
    assert "状态转换" in unit.taxonomy.path


def test_project_profile_has_dest_and_focus():
    profile = project_profile("factorlib")
    assert profile["dest_subdir"] == "restricted/factorlib"
    assert "raw parameters" in profile["compress_focus"].lower()
