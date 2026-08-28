"""Access governance audit trail — append-only JSONL under data/audit/access/."""

from __future__ import annotations

from pathlib import Path

from app.knowledge.access import check_export_gate, default_policy_for
from app.knowledge.access_audit import (
    AccessAuditEvent,
    append_access_event,
    audit_enabled,
    read_access_events,
    record_access,
    record_compose_filter,
    record_gate,
    record_retrieve_summary,
)
from app.knowledge.path_access import gate_export


def test_append_and_read_access_event(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setenv("KF_ACCESS_AUDIT", "1")
    ev = record_access(
        action="export",
        outcome="deny",
        classification="restricted",
        source_project="setv",
        path="data/knowledge/restricted/setv/x.md",
        reason="local_only_blocks_external",
        mode="local_only",
    )
    assert ev is not None
    day = ev.ts[:8]
    rows = read_access_events(day=day, action="export")
    assert any(r.id == ev.id and r.outcome == "deny" for r in rows)


def test_audit_can_be_disabled(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setenv("KF_ACCESS_AUDIT", "0")
    assert not audit_enabled()
    assert (
        record_access(action="retrieve", outcome="allow", query="x") is None
    )


def test_retrieve_summary_and_compose_filter(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setenv("KF_ACCESS_AUDIT", "1")
    record_retrieve_summary(
        query="SETV state",
        lane="proprietary",
        ceiling="restricted",
        total=10,
        allowed=7,
        denied_by_class={"secret": 2, "restricted": 1},
    )
    record_compose_filter(
        query="SETV state",
        lane="proprietary",
        llm_provider="openai",
        allowed_ids=["a"],
        blocked=[("b", "restricted")],
    )
    rows = read_access_events()
    assert any(r.action == "retrieve" and r.outcome == "filter" for r in rows)
    assert any(r.action == "compose" and r.outcome == "deny" for r in rows)


def test_gate_export_writes_audit(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    monkeypatch.setenv("KF_ACCESS_AUDIT", "1")
    card = (
        tmp_path
        / "knowledge"
        / "restricted"
        / "setv"
        / "snapshots"
        / "demo.md"
    )
    card.parent.mkdir(parents=True)
    card.write_text(
        "# Demo\n\n```yaml\nid: demo1\ntitle: Demo\nsource: t\ntype: notes\n"
        "access:\n  classification: restricted\n  source_project: setv\n```\n\n"
        "## Core Idea\n\nx\n",
        encoding="utf-8",
    )
    access, expr, exp = gate_export(card, external=True)
    assert access.classification == "restricted"
    assert not exp.allowed
    rows = read_access_events(action="export")
    assert any(r.outcome == "deny" and "setv" in (r.source_project or r.path) for r in rows)


def test_record_gate_warning(tmp_path: Path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setenv("KF_ACCESS_AUDIT", "1")
    gate = check_export_gate(
        "internal",
        policy=default_policy_for("internal"),
        external=True,
    )
    assert gate.allowed and gate.warning
    ev = record_gate(action="export", gate=gate, path="x.md", external=True)
    assert ev is not None
    assert ev.outcome == "warning"
