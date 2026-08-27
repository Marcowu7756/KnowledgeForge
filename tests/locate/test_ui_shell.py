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
    assert "capture" in body["stages"]

    page = client.get("/")
    assert page.status_code == 200
    assert b"KnowledgeForge" in page.content


def test_ui_status_endpoint():
    client = TestClient(create_app())
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    assert "paths" in data
