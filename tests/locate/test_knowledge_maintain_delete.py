"""Knowledge maintain — delete-only."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config
from app.knowledge.maintain import (
    MaintainError,
    delete_knowledge,
    resolve_knowledge_card,
)
from app.storage.index import global_jsonl_path, load_jsonl, save_jsonl
from app.ui.server import create_app


def _write_card(path: Path, *, unit_id: str, title: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# {title}

```yaml
id: {unit_id}
title: {title}
type: notes
tags: ["maintain-test"]
```

## Core Idea

Junk card for delete test.
""",
        encoding="utf-8",
    )
    return path


def test_resolve_rejects_outside_knowledge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    (tmp_path / "knowledge").mkdir()
    outside = tmp_path / "other.md"
    outside.write_text("# x\n", encoding="utf-8")
    with pytest.raises(MaintainError, match="under"):
        resolve_knowledge_card(str(outside))


def test_delete_knowledge_prunes_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    knowledge = tmp_path / "knowledge"
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(config, "RETRIEVE_DIR", tmp_path / "retrieve")
    (tmp_path / "retrieve").mkdir()

    card = _write_card(
        knowledge / "junk_card.md",
        unit_id="junkid001abc",
        title="Junk Card",
    )
    rel = card.relative_to(tmp_path).as_posix()
    save_jsonl(
        global_jsonl_path(),
        [
            {
                "id": "junkid001abc",
                "title": "Junk Card",
                "path": rel,
                "type": "notes",
                "tags": [],
                "concepts": [],
            },
            {
                "id": "keepme002def",
                "title": "Keep",
                "path": "data/knowledge/keep.md",
                "type": "notes",
                "tags": [],
                "concepts": [],
            },
        ],
    )

    report = delete_knowledge([str(card)], dry_run=False, prune_retrieve=False)
    assert report.ok is True
    assert report.deleted_count == 1
    assert not card.exists()
    remaining = load_jsonl(global_jsonl_path())
    assert all(r.get("id") != "junkid001abc" for r in remaining)
    assert any(r.get("id") == "keepme002def" for r in remaining)


def test_delete_dry_run_keeps_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    knowledge = tmp_path / "knowledge"
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    card = _write_card(knowledge / "stay.md", unit_id="stay001xyzabc", title="Stay")
    report = delete_knowledge([str(card)], dry_run=True)
    assert report.ok is True
    assert report.deleted_count == 0
    assert card.exists()


def test_delete_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    knowledge = tmp_path / "knowledge"
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    card = _write_card(knowledge / "api_junk.md", unit_id="apijunk01xyz", title="API Junk")
    client = TestClient(create_app())
    h = client.get("/api/health")
    assert h.json()["features"]["knowledge_delete"] is True
    r = client.request(
        "DELETE",
        "/api/knowledge",
        json={"paths": [str(card)], "prune_retrieve": False},
    )
    assert r.status_code == 200
    assert r.json()["deleted_count"] == 1
    assert not card.exists()
    page = client.get("/")
    assert b"maintain-block" in page.content
