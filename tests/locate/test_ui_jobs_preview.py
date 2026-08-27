"""Tests for async jobs + safe artifact preview."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import config
from app.ui.server import create_app


def test_job_submit_and_poll_fake_action(monkeypatch):
    client = TestClient(create_app())

    def fake_capture(kind, target, progress=None):
        if progress:
            progress(40, "fake")
            progress(100, "done")
        return {"ok": True, "title": "t", "knowledge": "k.md", "raw": "r", "concepts": 1}

    monkeypatch.setattr("app.ui.actions.run_capture", fake_capture)
    r = client.post("/api/capture", json={"kind": "file", "target": "x.md", "async_job": True})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # poll until done
    for _ in range(50):
        snap = client.get(f"/api/jobs/{job_id}").json()
        if snap["status"] in {"done", "error"}:
            break
    assert snap["status"] == "done"
    assert snap["result"]["ok"] is True
    assert snap["progress"] == 100


def test_preview_markdown_under_data(tmp_path: Path, monkeypatch):
    data = tmp_path / "data"
    compose = data / "compose" / "demo"
    compose.mkdir(parents=True)
    md = compose / "LECTURE.md"
    md.write_text("# hello preview\n", encoding="utf-8")

    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "COMPOSE_DIR", data / "compose")
    monkeypatch.setattr(config, "EXPRESSION_DIR", data / "expression")
    (data / "expression").mkdir(exist_ok=True)

    client = TestClient(create_app())
    r = client.get("/api/preview", params={"path": str(md)})
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "text"
    assert "hello preview" in body["text"]


def test_preview_rejects_outside_data(tmp_path: Path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    outside = tmp_path / "secret.md"
    outside.write_text("nope", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "ROOT", tmp_path)

    client = TestClient(create_app())
    r = client.get("/api/preview", params={"path": str(outside)})
    assert r.status_code == 403
