"""H1a · 一源多卡 family resolve + UI route smoke."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.ui.family_view import resolve_family_view
from app.ui.server import create_app


def test_resolve_aapl_family_multi_card():
    view = resolve_family_view(
        "SETV-FAM-AAPL-TV-2024-WDH4",
        lane="proprietary",
        limit=8,
    )
    assert view["ok"] is True
    assert view["family"]["artifact_id"] == "SETV-FAM-AAPL-TV-2024-WDH4"
    ids = {m["artifact_id"] for m in view["members"]}
    assert "SETV-INST-AAPL-W-2024" in ids
    assert "SETV-INST-AAPL-D-2024" in ids
    assert "SETV-INST-AAPL-H4-2024" in ids
    assert view["resolve"]["member_count"] == 3


def test_family_api_and_ui_markers():
    client = TestClient(create_app())
    h = client.get("/api/health")
    assert h.status_code == 200
    assert h.json()["ui_version"] == "0.5.2"
    assert h.json()["features"]["multi_card_h1a"] is True
    assert h.json()["features"]["multi_card_h1b"] is True
    assert h.json()["features"]["multi_card_h1c"] is True

    r = client.get(
        "/api/family/SETV-FAM-AAPL-TV-2024-WDH4",
        params={"lane": "proprietary"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["family"]["artifact_id"] == "SETV-FAM-AAPL-TV-2024-WDH4"
    assert len(body["members"]) == 3

    blocked = client.get(
        "/api/family/SETV-FAM-AAPL-TV-2024-WDH4",
        params={"lane": "general"},
    )
    assert blocked.status_code == 403

    page = client.get("/")
    assert page.status_code == 200
    assert b"multi-card-block" in page.content
    assert b"form-family" in page.content
    assert b"form-family-compose" in page.content


def test_compose_from_paths_h1b_skips_retrieve(monkeypatch):
    import json
    from unittest.mock import patch

    from app import config
    from app.compose.engine import compose_from_paths

    lecture_payload = {
        "title": "AAPL family",
        "script": "Observe AAPL W and H4 as archived state snapshots.",
        "outline": ["Family", "W", "H4"],
    }

    paths = [
        "data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_w_2024.md",
        "data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_h4_2024.md",
    ]
    monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
    with (
        patch(
            "app.compose.engine.complete_json",
            return_value=json.dumps(lecture_payload, ensure_ascii=False),
        ),
        patch("app.compose.engine.run_query") as rq,
    ):
        result = compose_from_paths(
            "AAPL W+H4",
            paths,
            kind="lecture",
            access_lane="proprietary",
        )
        rq.assert_not_called()
    assert result.draft_path.is_file()
    assert result.meta.evidence.get("source_mode") == "h1b_selected_paths"
    assert len(result.meta.sources) == 2


def test_compose_api_accepts_source_paths(monkeypatch):
    import json
    from unittest.mock import patch

    from app import config

    lecture_payload = {
        "title": "AAPL",
        "script": "H4 temporal snapshot only.",
        "outline": ["H4"],
    }
    monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
    client = TestClient(create_app())
    with patch(
        "app.compose.engine.complete_json",
        return_value=json.dumps(lecture_payload, ensure_ascii=False),
    ):
        r = client.post(
            "/api/compose",
            json={
                "query": "AAPL H4 only",
                "kind": "lecture",
                "access_lane": "proprietary",
                "source_paths": [
                    "data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_h4_2024.md"
                ],
                "async_job": False,
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["source_mode"] == "h1b_selected_paths"
    assert len(body["sources"]) == 1
    assert body["draft"]