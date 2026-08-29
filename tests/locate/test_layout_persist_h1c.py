"""H1c · multi-card layout persist (data/ui + API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import config
from app.ui import layout_persist
from app.ui.server import create_app


def test_layout_persist_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UI_DIR", tmp_path / "ui")
    saved = layout_persist.save_layout(
        artifact_id="SETV-FAM-AAPL-TV-2024-WDH4",
        selected_paths=[
            "data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_w_2024.md",
            "data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_h4_2024.md",
        ],
        compose_query="AAPL family observe",
        compose_kind="paper",
    )
    assert saved["schema"] == layout_persist.SCHEMA
    assert saved["h1"] == "H1c"
    assert (tmp_path / "ui" / "multi_card_layout.json").is_file()

    loaded = layout_persist.load_layout()
    assert loaded["artifact_id"] == "SETV-FAM-AAPL-TV-2024-WDH4"
    assert len(loaded["selected_paths"]) == 2
    assert loaded["compose_kind"] == "paper"

    cleared = layout_persist.clear_layout()
    assert cleared["artifact_id"] == ""
    assert not (tmp_path / "ui" / "multi_card_layout.json").exists()


def test_layout_api_and_ui_markers(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UI_DIR", tmp_path / "ui")
    client = TestClient(create_app())

    h = client.get("/api/health")
    assert h.status_code == 200
    assert h.json()["ui_version"] == "0.6.1"
    assert h.json()["features"]["multi_card_h1c"] is True

    empty = client.get("/api/ui/layout/multi-card")
    assert empty.status_code == 200
    assert empty.json()["layout"]["artifact_id"] == ""

    put = client.put(
        "/api/ui/layout/multi-card",
        json={
            "artifact_id": "SETV-FAM-AAPL-TV-2024-WDH4",
            "selected_paths": [
                "data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_d_2024.md"
            ],
            "compose_query": "D only",
            "compose_kind": "lecture",
        },
    )
    assert put.status_code == 200
    assert put.json()["layout"]["artifact_id"] == "SETV-FAM-AAPL-TV-2024-WDH4"

    got = client.get("/api/ui/layout/multi-card")
    assert got.json()["layout"]["compose_query"] == "D only"
    assert len(got.json()["layout"]["selected_paths"]) == 1

    deleted = client.delete("/api/ui/layout/multi-card")
    assert deleted.status_code == 200
    assert deleted.json()["layout"]["artifact_id"] == ""

    page = client.get("/")
    assert page.status_code == 200
    assert b"family-layout-save" in page.content
    assert b"family-layout-clear" in page.content
    assert b"multi-card-layout-status" in page.content
