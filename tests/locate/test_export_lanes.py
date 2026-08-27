"""Export / expression gates + UI access lanes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.knowledge.access import (
    AccessBlock,
    check_export_gate,
    check_expression_gate,
    default_policy_for,
    is_retrievable,
    lane_retrieve_ceiling,
)
from app.knowledge.path_access import gate_export, resolve_access_for_path
from app.retrieve.models import IndexRecord
from app.retrieve.query import retrieve_kos
from app.retrieve.store import save_index
from unittest.mock import patch


def test_lane_ceilings():
    assert lane_retrieve_ceiling("general") == "internal"
    assert lane_retrieve_ceiling("proprietary") == "restricted"


def test_export_external_blocks_local_only():
    pol = default_policy_for("restricted")
    local = check_export_gate("restricted", policy=pol, external=False)
    assert local.allowed
    ext = check_export_gate("restricted", policy=pol, external=True)
    assert not ext.allowed
    assert ext.reason == "local_only_blocks_external"


def test_expression_controlled_blocks_external():
    pol = default_policy_for("restricted")
    assert check_expression_gate("restricted", policy=pol, external=False).allowed
    assert not check_expression_gate("restricted", policy=pol, external=True).allowed


def test_export_warning_allows_external_with_warning():
    pol = default_policy_for("internal")
    gate = check_export_gate("internal", policy=pol, external=True)
    assert gate.allowed
    assert gate.warning


def test_path_hint_resolves_setv_snapshot(tmp_path: Path):
    p = tmp_path / "knowledge" / "restricted" / "setv" / "snapshots" / "x.md"
    p.parent.mkdir(parents=True)
    p.write_text("# x\n", encoding="utf-8")
    # resolve uses absolute path hints
    access = resolve_access_for_path(p)
    assert access.classification == "restricted"
    assert access.source_project == "setv"
    _, expr, exp = gate_export(p, external=True)
    assert not expr.allowed or not exp.allowed


def test_retrieve_general_lane_excludes_restricted(tmp_path: Path):
    records = [
        IndexRecord(
            ko_id="ko_pub",
            vector_id="emb_1",
            title="Public Note",
            path="a.md",
            classification="public",
        ),
        IndexRecord(
            ko_id="ko_res",
            vector_id="emb_2",
            title="SETV GOLD Snapshot",
            path="b.md",
            classification="restricted",
            access_policy=default_policy_for("restricted").model_dump(),
        ),
    ]
    vectors = np.array([[1.0, 0.0], [0.99, 0.01]], dtype=np.float32)
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)

    with patch(
        "app.retrieve.query.embed_query",
        return_value=np.array([1.0, 0.0], dtype=np.float32),
    ):
        general = retrieve_kos("GOLD", top_k=5, index_dir=tmp_path, access_lane="general")
        proprietary = retrieve_kos(
            "GOLD", top_k=5, index_dir=tmp_path, access_lane="proprietary"
        )

    g_ids = {h.ko_id for h in general.hits}
    p_ids = {h.ko_id for h in proprietary.hits}
    assert "ko_pub" in g_ids
    assert "ko_res" not in g_ids
    assert "ko_res" in p_ids
