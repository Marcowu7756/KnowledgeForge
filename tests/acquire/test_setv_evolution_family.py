"""SETV Evolution / Family adapters — cite-only AE-2."""

from __future__ import annotations

from pathlib import Path

from app.ingest.setv_artifact import (
    ingest_artifact,
    parse_evolution_artifact,
    parse_family_artifact,
    run_artifact_ingest,
    unit_from_artifact,
)
from app.knowledge.parse import load_unit_from_markdown
from app.storage.markdown import render_markdown

SAMPLE_FAMILY_EDGE = """# Edge · L-XS-DEMO-UJ · DEMOUSD-H4 ↔ USDJPY-H4

**Graph:** [`../LINK_GRAPH.md`](../LINK_GRAPH.md)
**Type:** cross_symbol · Type B
**AUTHORIZE:** Link Expansion B

## Connects

Cards: DEMOUSD · USDJPY

## Question

Under one phi, how do path masses differ?

## Observation (not forecast)

USDJPY: fewer flash L<=1 vs DEMOUSD. Same language · different ecology weighting.

## Forbidden

Ranking · Predict · Explain leakage · Decision.
"""

SAMPLE_FAMILY_DOC = """# Observation Family · DEMO TV 2024

**Family ID:** `SETV-FAM-DEMO-TV-2024-WDH4`
**Schema:** `setv_observation_family_v0`
**Status:** **ESTABLISHED** · Container / instance registry

## Underlying identity (registry key)

| Field | Value |
|-------|--------|
| Symbol | **DEMOUSD** |
| Window | 2024-01-01 → 2024-12-31 |

## Independent instances

| Instance | Artifact | T |
|----------|----------|---|
| DEMO-W | raw/... | 53 |
"""

SAMPLE_EVOLUTION_EDGE = """# Edge · L-SA-DEMO-23-2426 · DEMO Sample Evolution

**Type:** sample · Phase 4 B3

## Connects

SETV-INST-DEMOUSD-H4-2023 ↔ SETV-INST-DEMOUSD-H4-2024-2026

## Question

Same Symbol+TF: is ontology stable?

## Observation

Gamma taxonomy held. Mix drifted. Language holds · ecology mix not constant.

## Forbidden

Bar Stitch · Forecast · Sample merge · Ranking.
"""

SAMPLE_KERNEL_EVIDENCE = """# EVIDENCE · Kernel Persistence OBSERVE · 2026-08-20

**Status:** DESCRIPTIVE · **OBSERVE** · half-life **NOT COMPUTED**
**method_id:** `R3.kernel_persistence_observe`
**JSON:** [`research_runs/kernel_persistence/demo.json`](research_runs/kernel_persistence/demo.json)

Question: under one Instance, how long does the ecological transition structure persist?

Answer, on this pack: S3 role persists through the populated sample.

## 1. S3 role persists

| Instance | tau=1 | tau=4 |
|----------|------:|------:|
| DEMOUSD 2024–2026 | 0.039 | 0.049 |

The residence attractor is not a year-specific dialect.
"""


def test_parse_family_edge(tmp_path: Path):
    path = tmp_path / "L-XS-DEMO-UJ.md"
    path.write_text(SAMPLE_FAMILY_EDGE, encoding="utf-8")
    parsed = parse_family_artifact(path)
    assert parsed.artifact_id == "L-XS-DEMO-UJ"
    assert parsed.asset_class == "family"
    assert "ecology" in " ".join(parsed.descriptive_points).lower() or parsed.descriptive_points


def test_parse_family_doc(tmp_path: Path):
    path = tmp_path / "SETV_FAM_DEMO_TV_2024_WDH4.md"
    path.write_text(SAMPLE_FAMILY_DOC, encoding="utf-8")
    parsed = parse_family_artifact(path)
    assert parsed.artifact_id == "SETV-FAM-DEMO-TV-2024-WDH4"
    assert parsed.symbol == "DEMOUSD"
    unit = unit_from_artifact(parsed)
    assert unit.memory_kind == "state"
    assert unit.setv_artifact.asset_class == "family"
    assert unit.taxonomy.path[:3] == ["专有知识", "SETV", "State Family"]


def test_parse_evolution_edge(tmp_path: Path):
    path = tmp_path / "L-SA-DEMO-23-2426.md"
    path.write_text(SAMPLE_EVOLUTION_EDGE, encoding="utf-8")
    parsed = parse_evolution_artifact(path)
    assert parsed.artifact_id == "L-SA-DEMO-23-2426"
    assert parsed.asset_class == "evolution"
    assert any("SETV-INST-DEMOUSD" in x for x in parsed.link_ids)


def test_parse_kernel_evidence(tmp_path: Path):
    path = tmp_path / "EVIDENCE_20260820_KERNEL_PERSISTENCE_OBSERVE.md"
    path.write_text(SAMPLE_KERNEL_EVIDENCE, encoding="utf-8")
    parsed = parse_evolution_artifact(path)
    assert parsed.artifact_id.startswith("EVIDENCE_")
    assert "KERNEL_PERSISTENCE" in parsed.artifact_id
    unit = unit_from_artifact(parsed)
    assert unit.setv_artifact.asset_class == "evolution"
    assert unit.taxonomy.path[:3] == ["专有知识", "SETV", "State Evolution"]


def test_family_yaml_roundtrip(tmp_path: Path):
    path = tmp_path / "SETV_FAM_DEMO.md"
    path.write_text(SAMPLE_FAMILY_DOC, encoding="utf-8")
    unit = unit_from_artifact(parse_family_artifact(path))
    out = tmp_path / "ko.md"
    out.write_text(render_markdown(unit), encoding="utf-8")
    loaded = load_unit_from_markdown(out)
    assert loaded.setv_artifact.asset_class == "family"
    assert loaded.setv_artifact.artifact_id == "SETV-FAM-DEMO-TV-2024-WDH4"


def test_ingest_evolution_writes_restricted(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    monkeypatch.setattr(config, "INDEX_ENABLED", False)
    path = tmp_path / "L-SA-DEMO-23-2426.md"
    path.write_text(SAMPLE_EVOLUTION_EDGE, encoding="utf-8")
    result = ingest_artifact(path, asset_class="evolution", dry_run=False, index=False)
    assert result.markdown_path.is_file()
    assert "evolution" in result.markdown_path.as_posix()
    assert "restricted" in result.markdown_path.as_posix()


def test_discover_family_and_evolution(tmp_path: Path):
    edges = tmp_path / "links" / "edges"
    edges.mkdir(parents=True)
    (edges / "L-XS-DEMO-UJ.md").write_text(SAMPLE_FAMILY_EDGE, encoding="utf-8")
    (edges / "L-SA-DEMO-23-2426.md").write_text(SAMPLE_EVOLUTION_EDGE, encoding="utf-8")
    fam_dir = tmp_path / "families"
    fam_dir.mkdir()
    (fam_dir / "SETV_FAM_DEMO_TV_2024_WDH4.md").write_text(
        SAMPLE_FAMILY_DOC, encoding="utf-8"
    )
    ev = tmp_path / "evidence"
    ev.mkdir()
    (ev / "EVIDENCE_20260820_KERNEL_PERSISTENCE_OBSERVE.md").write_text(
        SAMPLE_KERNEL_EVIDENCE, encoding="utf-8"
    )

    fam = run_artifact_ingest([tmp_path], asset_class="family", dry_run=True)
    evo = run_artifact_ingest([tmp_path], asset_class="evolution", dry_run=True)
    assert len(fam.hits) == 2  # L-XS + SETV_FAM
    assert len(evo.hits) == 2  # L-SA + KERNEL evidence
