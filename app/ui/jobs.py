"""In-process async job queue for long UI operations."""

from __future__ import annotations

import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

ProgressFn = Callable[[int, str], None]
JobFn = Callable[[ProgressFn], Any]


@dataclass
class Job:
    id: str
    action: str
    status: str = "queued"  # queued|running|done|error
    progress: int = 0
    message: str = "queued"
    result: Any = None
    error: str | None = None
    created: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )


class JobStore:
    def __init__(self, *, max_workers: int = 2) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="kf-ui")

    def submit(self, action: str, fn: JobFn) -> Job:
        job = Job(id=uuid4().hex[:12], action=action)
        with self._lock:
            self._jobs[job.id] = job
        self._pool.submit(self._run, job.id, fn)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def snapshot(self, job_id: str) -> dict[str, Any] | None:
        job = self.get(job_id)
        if job is None:
            return None
        return self._snapshot_job(job)

    def list_snapshots(
        self,
        *,
        limit: int = 50,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        if action:
            jobs = [j for j in jobs if j.action == action]
        jobs.sort(key=lambda j: j.updated, reverse=True)
        cap = max(1, min(int(limit), 200))
        return [self._snapshot_job(j) for j in jobs[:cap]]

    def _snapshot_job(self, job: Job) -> dict[str, Any]:
        return {
            "id": job.id,
            "action": job.action,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "result": job.result,
            "error": job.error,
            "created": job.created,
            "updated": job.updated,
        }

    def _touch(self, job: Job, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(job, k, v)
        job.updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _run(self, job_id: str, fn: JobFn) -> None:
        job = self.get(job_id)
        if job is None:
            return

        def progress(pct: int, message: str) -> None:
            with self._lock:
                self._touch(
                    job,
                    status="running",
                    progress=max(0, min(100, int(pct))),
                    message=message,
                )

        with self._lock:
            self._touch(job, status="running", progress=1, message="starting")
        try:
            result = fn(progress)
            with self._lock:
                self._touch(
                    job,
                    status="done",
                    progress=100,
                    message="done",
                    result=result,
                    error=None,
                )
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._touch(
                    job,
                    status="error",
                    progress=job.progress,
                    message="failed",
                    error=str(exc),
                    result={"traceback": traceback.format_exc(limit=8)},
                )


# Process-wide store (UI is local single-user)
STORE = JobStore()


def wait_briefly() -> None:
    """Tiny yield so UI polls see intermediate states in fast jobs."""
    time.sleep(0.05)
