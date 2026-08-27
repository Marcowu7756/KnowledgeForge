from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["pending", "running", "ok", "fail", "skipped"]


class TaskStep(BaseModel):
    """One deterministic step in a harness run."""

    name: str
    status: TaskStatus = "pending"
    started: datetime | None = None
    finished: datetime | None = None
    error: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    def mark_running(self) -> None:
        self.status = "running"
        self.started = datetime.now(timezone.utc)
        self.error = None

    def mark_ok(self, *, artifacts: list[str] | None = None, meta: dict[str, Any] | None = None) -> None:
        self.status = "ok"
        self.finished = datetime.now(timezone.utc)
        if artifacts:
            self.artifacts = artifacts
        if meta:
            self.meta.update(meta)

    def mark_fail(self, error: str) -> None:
        self.status = "fail"
        self.finished = datetime.now(timezone.utc)
        self.error = error

    def mark_skipped(self, reason: str) -> None:
        self.status = "skipped"
        self.finished = datetime.now(timezone.utc)
        self.meta["reason"] = reason


class TaskRun(BaseModel):
    """Full harness run state (auditable)."""

    id: str
    source: str
    status: TaskStatus = "pending"
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished: datetime | None = None
    steps: list[TaskStep] = Field(default_factory=list)
    package_dir: str = ""
    error: str | None = None

    def step(self, name: str) -> TaskStep:
        for item in self.steps:
            if item.name == name:
                return item
        item = TaskStep(name=name)
        self.steps.append(item)
        return item

    def mark_running(self) -> None:
        self.status = "running"

    def mark_ok(self) -> None:
        self.status = "ok"
        self.finished = datetime.now(timezone.utc)

    def mark_fail(self, error: str) -> None:
        self.status = "fail"
        self.finished = datetime.now(timezone.utc)
        self.error = error
