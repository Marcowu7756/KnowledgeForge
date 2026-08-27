"""SETV State Snapshot adapter — cite-only CARD → memory_kind=state KO."""

from __future__ import annotations

from pathlib import Path

from app.ingest.setv_snapshot import (
    ingest_snapshot_card,
    parse_instance_card,
    run_snapshot_ingest,
    unit_from_snapshot,
)
from app.knowledge.parse import load_unit_from_markdown
from app.storage.markdown import render_markdown

SAMPLE_CARD = """# Instance Card · DEMO · H4 · ARCHIVED

**Status:** OBSERVE · Evidence ARCHIVED · ≠ Forecast

```text
Instance Card

Identity
-----------
Symbol: DEMOUSD · FX:DEMOUSD
Timeframe: H4
State Version: S0–S6 (φ frozen)
Type: A · Single Ecology
Primary Instance id: SETV-INST-DEMOUSD-H4-2024-2026
Family / Inst card: methodology/evidence/families/SETV_INST_DEMOUSD_H4_2024_2026.md
Window: 2024-01-02 → 2026-08-19 · T=100

Current
-----------
S_t profile: Observation Instance (historical describe)
  → methodology/evidence/EVIDENCE_DEMO.md

Residence
-----------
P(S0)≈0.4 · archival description only

Transition
-----------
K = P(S'|S): descriptive kernel cite only
  → methodology/evidence/EVIDENCE_KERNEL_DEMO.md

Status
-----------
OBSERVE · ARCHIVED

Evidence pointers (canonical)
-----------
methodology/evidence/families/SETV_INST_DEMOUSD_H4_2024_2026.md
methodology/evidence/EVIDENCE_DEMO.md

Links
-----------
Graph edges: L-XS-DEMO-UJ
```

**Fence:** Archive only · Forecast FORBIDDEN.
"""


def test_parse_instance_card(tmp_path: Path):
    card = tmp_path / "CARD.md"
    card.write_text(SAMPLE_CARD, encoding="utf-8")
    parsed = parse_instance_card(card)
    assert parsed.artifact_id == "SETV-INST-DEMOUSD-H4-2024-2026"
    assert "families/SETV_INST_DEMOUSD" in parsed.evidence_pointer
    assert parsed.symbol == "DEMOUSD"
    assert parsed.timeframe == "H4"
    assert "L-XS-DEMO-UJ" in parsed.link_ids


def test_unit_from_snapshot_is_state_memory(tmp_path: Path):
    card = tmp_path / "CARD.md"
    card.write_text(SAMPLE_CARD, encoding="utf-8")
    parsed = parse_instance_card(card)
    unit = unit_from_snapshot(parsed)
    assert unit.memory_kind == "state"
    assert unit.access.classification == "restricted"
    assert unit.setv_artifact is not None
    assert unit.setv_artifact.artifact_id.startswith("SETV-INST-")
    assert unit.taxonomy.path[:3] == ["专有知识", "SETV", "State Snapshot"]
    assert "predict" not in unit.summary.lower()


def test_snapshot_yaml_roundtrip(tmp_path: Path):
    card = tmp_path / "CARD.md"
    card.write_text(SAMPLE_CARD, encoding="utf-8")
    parsed = parse_instance_card(card)
    unit = unit_from_snapshot(parsed)
    out = tmp_path / "ko.md"
    out.write_text(render_markdown(unit), encoding="utf-8")
    loaded = load_unit_from_markdown(out)
    assert loaded.memory_kind == "state"
    assert loaded.setv_artifact is not None
    assert loaded.setv_artifact.artifact_id == unit.setv_artifact.artifact_id
    assert loaded.setv_artifact.evidence_pointer == unit.setv_artifact.evidence_pointer


def test_ingest_snapshot_writes_restricted(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    monkeypatch.setattr(config, "INDEX_ENABLED", False)
    card = tmp_path / "CARD.md"
    card.write_text(SAMPLE_CARD, encoding="utf-8")
    result = ingest_snapshot_card(card, dry_run=False, index=False)
    assert result.markdown_path.is_file()
    assert "restricted" in result.markdown_path.as_posix()
    assert result.unit.memory_kind == "state"


def test_discover_and_dry_run(tmp_path: Path):
    inst = tmp_path / "instances" / "DEMO" / "H4"
    inst.mkdir(parents=True)
    (inst / "CARD.md").write_text(SAMPLE_CARD, encoding="utf-8")
    batch = run_snapshot_ingest([inst.parent.parent], dry_run=True)
    assert len(batch.hits) == 1
    assert batch.results == []
