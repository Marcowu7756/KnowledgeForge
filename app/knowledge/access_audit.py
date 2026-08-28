"""Append-only access governance audit trail.

Records retrieve / compose / expression / export decisions so restricted
proprietary assets (SETV · FactorLib · AShareLib) have a local evidence log.

Default: ON (KF_ACCESS_AUDIT=0 to disable). Never leaves the machine.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app import config

AuditAction = Literal[
    "retrieve",
    "compose",
    "expression",
    "export",
]

AuditOutcome = Literal["allow", "deny", "filter", "warning"]

_LOCK = threading.Lock()


def audit_enabled() -> bool:
    raw = (os.getenv("KF_ACCESS_AUDIT") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def audit_dir() -> Path:
    return Path(getattr(config, "AUDIT_DIR", config.DATA_DIR / "audit"))


class AccessAuditEvent(BaseModel):
    """One governance decision (or batch summary)."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    ts: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    action: AuditAction
    outcome: AuditOutcome
    classification: str = ""
    source_project: str = ""
    ko_id: str = ""
    path: str = ""
    lane: str = ""
    llm_provider: str = ""
    mode: str = ""
    reason: str = ""
    query: str = ""
    detail: dict[str, Any] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False, sort_keys=True)


def append_access_event(event: AccessAuditEvent) -> Path | None:
    """Append one JSONL line under data/audit/access/YYYYMMDD.jsonl."""
    if not audit_enabled():
        return None
    day = event.ts[:8] if len(event.ts) >= 8 else datetime.now(timezone.utc).strftime(
        "%Y%m%d"
    )
    dest = audit_dir() / "access"
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{day}.jsonl"
    line = event.to_jsonl() + "\n"
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    return path


def record_access(
    *,
    action: AuditAction,
    outcome: AuditOutcome,
    classification: str = "",
    source_project: str = "",
    ko_id: str = "",
    path: str = "",
    lane: str = "",
    llm_provider: str = "",
    mode: str = "",
    reason: str = "",
    query: str = "",
    detail: dict[str, Any] | None = None,
) -> AccessAuditEvent | None:
    if not audit_enabled():
        return None
    event = AccessAuditEvent(
        action=action,
        outcome=outcome,
        classification=classification,
        source_project=source_project,
        ko_id=ko_id,
        path=path,
        lane=lane,
        llm_provider=llm_provider,
        mode=mode,
        reason=reason,
        query=(query or "")[:200],
        detail=detail or {},
    )
    append_access_event(event)
    return event


def record_retrieve_summary(
    *,
    query: str,
    lane: str | None,
    ceiling: str | None,
    total: int,
    allowed: int,
    denied_by_class: dict[str, int],
) -> AccessAuditEvent | None:
    denied = sum(denied_by_class.values())
    outcome: AuditOutcome = "filter" if denied else "allow"
    return record_access(
        action="retrieve",
        outcome=outcome,
        lane=lane or "",
        classification=ceiling or "",
        query=query,
        reason="index_filter" if denied else "ok",
        detail={
            "total_index": total,
            "allowed": allowed,
            "denied": denied,
            "denied_by_class": denied_by_class,
            "ceiling": ceiling,
        },
    )


def record_compose_filter(
    *,
    query: str,
    lane: str | None,
    llm_provider: str,
    allowed_ids: list[str],
    blocked: list[tuple[str, str]],
) -> AccessAuditEvent | None:
    """blocked = [(ko_id, classification), ...]"""
    if not blocked and not allowed_ids:
        return None
    outcome: AuditOutcome = "filter" if blocked else "allow"
    for ko_id, classification in blocked:
        record_access(
            action="compose",
            outcome="deny",
            classification=classification,
            ko_id=ko_id,
            lane=lane or "",
            llm_provider=llm_provider,
            query=query,
            reason="compose_ineligible",
        )
    return record_access(
        action="compose",
        outcome=outcome,
        lane=lane or "",
        llm_provider=llm_provider,
        query=query,
        reason="batch",
        detail={
            "allowed": len(allowed_ids),
            "blocked": len(blocked),
            "allowed_ids": allowed_ids[:20],
            "blocked_ids": [b[0] for b in blocked[:20]],
        },
    )


def record_gate(
    *,
    action: AuditAction,
    gate: Any,
    path: str = "",
    source_project: str = "",
    external: bool = False,
) -> AccessAuditEvent | None:
    allowed = bool(getattr(gate, "allowed", False))
    warning = str(getattr(gate, "warning", "") or "")
    if allowed and warning:
        outcome: AuditOutcome = "warning"
    elif allowed:
        outcome = "allow"
    else:
        outcome = "deny"
    return record_access(
        action=action,
        outcome=outcome,
        classification=str(getattr(gate, "classification", "") or ""),
        source_project=source_project,
        path=path,
        mode=str(getattr(gate, "mode", "") or ""),
        reason=str(getattr(gate, "reason", "") or ("ok" if allowed else "blocked")),
        detail={"external": external, "warning": warning},
    )


def read_access_events(
    *,
    day: str | None = None,
    limit: int = 200,
    action: AuditAction | None = None,
) -> list[AccessAuditEvent]:
    """Read recent events (newest last). For tests / CLI inspection."""
    dest = audit_dir() / "access"
    if not dest.is_dir():
        return []
    if day:
        files = [dest / f"{day}.jsonl"]
    else:
        files = sorted(dest.glob("*.jsonl"))
    events: list[AccessAuditEvent] = []
    for path in files:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                ev = AccessAuditEvent.model_validate(row)
            except Exception:
                continue
            if action and ev.action != action:
                continue
            events.append(ev)
    if limit and len(events) > limit:
        return events[-limit:]
    return events
