"""OPEN KF INGEST · manifest → sidecar parse."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.ingest.setv_artifact import (
    load_manifest_entries,
    parse_export_sidecar,
    run_manifest_ingest,
)

SETV = Path(r"D:\fxtrading")
MANIFEST = SETV / "methodology" / "SETV" / "export" / "manifest_v0.jsonl"
GOLD_SIDE = SETV / "methodology" / "SETV" / "research" / "instances" / "GOLD" / "H4" / "export.json"
EVO_SIDE = (
    SETV
    / "methodology"
    / "SETV"
    / "research"
    / "instances"
    / "GBPJPY"
    / "H4"
    / "export_evolution.json"
)
EDGE_SIDE = (
    SETV / "methodology" / "SETV" / "research" / "links" / "edges" / "L-XS-GJ-UJ.export.json"
)

pytestmark = pytest.mark.skipif(
    not MANIFEST.is_file(),
    reason="local SETV export manifest not present",
)


def test_parse_gold_export_sidecar():
    parsed = parse_export_sidecar(GOLD_SIDE, setv_root=SETV)
    assert parsed.artifact_id == "SETV-INST-GOLD-H4-2024-2026"
    assert parsed.asset_class == "snapshot"
    assert parsed.symbol == "GOLD"


def test_parse_evolution_and_edge_sidecars():
    evo = parse_export_sidecar(EVO_SIDE, setv_root=SETV)
    assert evo.asset_class == "evolution"
    assert evo.artifact_id.startswith("SETV-INST-GBPJPY")
    edge = parse_export_sidecar(EDGE_SIDE, setv_root=SETV)
    assert edge.artifact_id == "L-XS-GJ-UJ"
    assert edge.asset_class == "family"


def test_load_manifest_has_multiple_classes():
    entries = load_manifest_entries(MANIFEST)
    assert len(entries) >= 40
    classes = {e["asset_class"] for e in entries}
    assert "snapshot" in classes
    assert "evolution" in classes
    assert "family" in classes


def test_run_manifest_ingest_dry():
    batch = run_manifest_ingest(
        setv_root=SETV,
        manifest=MANIFEST,
        limit=8,
        dry_run=True,
    )
    assert len(batch.hits) == 8
    assert batch.results == []
