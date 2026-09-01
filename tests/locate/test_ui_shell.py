"""UI shell smoke tests (no server listen)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.ui.server import create_app


def test_ui_health_and_home():
    client = TestClient(create_app())
    h = client.get("/api/health")
    assert h.status_code == 200
    body = h.json()
    assert body["product"] == "KnowledgeForge"
    assert body["ui_version"] == "0.6.4"
    assert body["features"]["web_ui"] is True
    assert body["features"]["taxonomy_outline"] is True
    assert body["ui"]["surface"] == "web"
    assert "capture" in body["stages"]
    assert "access_lanes" in body
    assert body["access_lanes"]["general"]["ceiling"] == "internal"
    assert "setv" in body["access_lanes"]["proprietary"]["projects"]
    assert body["features"]["multi_card_h1a"] is True
    assert body["features"]["multi_card_h1b"] is True

    page = client.get("/")
    assert page.status_code == 200
    assert b"KnowledgeForge" in page.content
    assert b"Web UI" in page.content
    assert b"twitter" in page.content
    assert b"stage-tasks" in page.content
    assert b"compose-preview" in page.content
    assert b"lane-bar" in page.content
    assert b"data-lane=\"proprietary\"" in page.content
    assert b"form-family-compose" in page.content
    assert b"settings-bind-url" in page.content


def test_ui_status_endpoint():
    client = TestClient(create_app())
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    assert "paths" in data
