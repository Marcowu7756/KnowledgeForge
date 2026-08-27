# KnowledgeForge · SETV Evolution / Family Adapters v0

**Status:** LANDED (code) · cite-only · no LLM  
**Contract:** SETV Artifact Export `setv_artifact_export_v0@v0.0.0` (AE-2)  
**Module:** `app/ingest/setv_artifact.py` (snapshot re-exported via `setv_snapshot.py`)

## CLI

```text
python main.py setv evolution <edge|evidence|dir> ... [--setv-root DIR] [--dry-run] [--limit N]
python main.py setv family    <fam|edge|dir>    ... [--setv-root DIR] [--dry-run] [--limit N]
python main.py setv snapshot  <CARD|dir>        ...   # existing AE-2 snapshot
```

## Asset class map

| Class | Sources discovered | Taxonomy leaf | Dest |
|-------|--------------------|---------------|------|
| `family` | `SETV_FAM_*.md`, `L-XS-*`, `L-SF-*` | State Family | `restricted/setv/families/` |
| `evolution` | `L-SA-*`, `L-KP-*`, `L-KR-*`, `EVIDENCE_*KERNEL_{PERSISTENCE,STABILITY,ROW_PERSISTENCE}*` | State Evolution | `restricted/setv/evolutions/` |
| `snapshot` | `CARD.md` | State Snapshot | `restricted/setv/snapshots/` |

Note: Contract AE-4 lists `L-SA-*` under family edges; KF maps **sample-evolution** edges (`L-SA`) to `evolution` because titles/semantics are window/kernel change, not multi-instance family containers. Cross-symbol / structure-family edges stay `family`.

## Pipeline

Same shape as Snapshot (`docs/interop/SETV_SNAPSHOT_ADAPTER_V0.md`):
deterministic parse → `ArtifactParse` → `KnowledgeUnit(memory_kind=state)` →
`data/knowledge/restricted/setv/{families|evolutions}/*.md`.

Snapshot remains available via `setv_snapshot.py` re-exports.


## Smoke (fxtrading)

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py setv family `
  "D:\fxtrading\methodology\SETV\research\links\edges\L-XS-GJ-UJ.md" `
  --setv-root "D:\fxtrading" --dry-run

.\.venv\Scripts\python.exe main.py setv evolution `
  "D:\fxtrading\methodology\evidence\EVIDENCE_20260820_KERNEL_PERSISTENCE_OBSERVE.md" `
  --setv-root "D:\fxtrading" --dry-run

.\.venv\Scripts\python.exe main.py setv family `
  "D:\fxtrading\methodology\evidence\families" `
  --setv-root "D:\fxtrading" --limit 3
```

## Tests

`tests/acquire/test_setv_evolution_family.py` · `tests/acquire/test_setv_snapshot.py`
