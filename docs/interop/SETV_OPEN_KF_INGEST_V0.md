# KnowledgeForge · SETV OPEN KF INGEST + AE-2 Completeness v0

**Status:** LANDED · cite-only · no LLM for SETV artifacts  
**Gate:** SETV `OWNER_CONFIRM_20260828_OPEN_SCHEMA_AUTHORIZE_IMPLEMENT`

## Preferred path

```powershell
python main.py setv ingest --setv-root D:\fxtrading [--class snapshot|…] [--dry-run]
```

Uses `methodology/SETV/export/manifest_v0.jsonl` → sidecars (`export.json` / `export_evolution.json` / `export_family.json` / `L-*.export.json`).

**Validated:** 45/45 manifest entries ingested 2026-08-28.

## Markdown / class CLIs (fallback + AE-2 remainder)

| Command | Sources |
|---------|---------|
| `setv snapshot` | CARD / `export.json` |
| `setv evolution` | kernel edges · `export_evolution.json` |
| `setv family` | FAM · L-XS · sidecars |
| `setv measurement` | State Contract fascicles |
| `setv experiment` | `SETV_EXP_*` packs |
| `setv uncertainty` | Uncertainty Language / OWNER_CONFIRM |

## Known gaps

- AAPL W/D/H4 CARD lack `SETV-INST-*` → skip on markdown snapshot; family sidecar covers container
- Producer stamps `L-SA-*` as **family**; trust sidecar over KF markdown heuristic
- measurement/experiment/uncertainty not yet in SETV manifest (markdown cite only)

See also: `SETV_SNAPSHOT_ADAPTER_V0.md`, `SETV_EVOLUTION_FAMILY_ADAPTER_V0.md`, `docs/audit/CONTENT_FILL_20260828.md`
