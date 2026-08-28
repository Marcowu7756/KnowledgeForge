# KnowledgeForge · OPEN KF INGEST · SETV sidecars / manifest

**Status:** **AUTHORIZED** (SETV Owner `OPEN KF INGEST` · 2026-08-28)  
**SETV policy:** `D:\fxtrading\methodology\SETV\export\KF_INGEST_V0.md`  
**SETV confirm:** `D:\fxtrading\methodology\evidence\OWNER_CONFIRM_20260828_OPEN_KF_INGEST.md`

\[
\boxed{prefer\ sidecar}
\qquad
\boxed{manifest \rightarrow KO}
\qquad
\boxed{cite\text{-}only}
\qquad
\boxed{no\ SETV\ writeback}
\]

## CLI

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py setv ingest `
  --setv-root "D:\fxtrading" `
  --dry-run --limit 5

.\.venv\Scripts\python.exe main.py setv ingest `
  --setv-root "D:\fxtrading" `
  --class snapshot --limit 10
```

Default manifest: `<setv-root>/methodology/SETV/export/manifest_v0.jsonl`.

## Code

- `app/ingest/setv_artifact.py` · `parse_export_sidecar` · `run_manifest_ingest`
- Class adapters still scrape markdown when sidecars absent; directory discover **prefers** sidecars when present.

## Tests

`tests/acquire/test_setv_kf_ingest.py`

---

*KF · OPEN KF INGEST · 2026-08-28*
