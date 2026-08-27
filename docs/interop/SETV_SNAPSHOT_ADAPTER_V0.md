# KnowledgeForge · SETV State Snapshot Adapter v0

**Status:** LANDED (code) · cite-only · no LLM  
**Contract:** SETV Artifact Export `setv_artifact_export_v0@v0.0.0`  
**CLI:** `python main.py setv snapshot <CARD.md|dir> ... [--setv-root DIR] [--dry-run] [--limit N]`

## Model

| Field | Value |
|-------|-------|
| `memory_kind` | `state` (vs default `semantic`) |
| `setv_artifact` | AE-1 triple |
| `access` | restricted / setv / local_only |
| `taxonomy` | `专有知识 > SETV > State Snapshot > {SYMBOL} > {TF}` |

## Pipeline

```text
SETV Instance CARD.md
        │  deterministic parse (no LLM)
        ▼
SnapshotParse (id, pointer, symbol, tf, evidence…)
        │
        ▼
KnowledgeUnit (memory_kind=state)
        │
        ▼
data/knowledge/restricted/setv/snapshots/*.md
```

## Non-goals

- Mutate SETV / rewrite φ  
- Ingest raw OHLCV Observation Envelope as State Memory  
- Evolution / Family asset classes (later adapters)  
- Cloud compose of restricted snapshots (filtered by access policy)

## Canonical sample (ACK CONSUMER READY · 2026-08-28)

SETV-side confirmation: core unchanged; Cards sufficient for AE-1.

| Field | GOLD H4 |
|-------|---------|
| artifact_id | `SETV-INST-GOLD-H4-2024-2026` |
| evidence_pointer | `methodology/SETV/research/instances/GOLD/H4/CARD.md` (no family file → Card fallback) |
| Window | 2024-01-01 → 2026-08-20 · T=4078（含 2024，无单独「黄金 2024」Instance） |
| KF unit id | `ebcd8e917819` |
| KO path | `data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_gold_h4_2024_2026.md` |

Also validated: `SETV-INST-GBPJPY-H4-2024-2026`.

`export.json` / manifest remain **STOP** until Owner `OPEN SCHEMA` / `OPEN KF INGEST`.

## Tests

`tests/acquire/test_setv_snapshot.py`

## SETV-facing requirements

See [`SETV_REQUIREMENTS_FOR_SNAPSHOT_EXPORT_V0.md`](SETV_REQUIREMENTS_FOR_SNAPSHOT_EXPORT_V0.md).
