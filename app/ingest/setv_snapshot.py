"""SETV State Snapshot adapter — thin re-export of setv_artifact (AE-2 snapshot).

Prefer ``app.ingest.setv_artifact`` for evolution / family / shared ingest.
"""

from __future__ import annotations

from app.ingest.setv_artifact import (  # noqa: F401
    ArtifactBatchResult,
    ArtifactParse,
    SnapshotBatchResult,
    SnapshotParse,
    discover_instance_cards,
    ingest_snapshot_card,
    parse_instance_card,
    run_snapshot_ingest,
    unit_from_snapshot,
)

__all__ = [
    "ArtifactBatchResult",
    "ArtifactParse",
    "SnapshotBatchResult",
    "SnapshotParse",
    "discover_instance_cards",
    "ingest_snapshot_card",
    "parse_instance_card",
    "run_snapshot_ingest",
    "unit_from_snapshot",
]
