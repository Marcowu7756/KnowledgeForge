# Content Fill Evidence — 2026-08-28

```yaml
run_id: KF-FILL-20260828
branch: main
setv_root: D:\fxtrading
```

## Landed this round

| Stream | Action | Result |
|--------|--------|--------|
| OPEN KF INGEST | `main.py setv ingest --setv-root D:\fxtrading` | **45/45** via `manifest_v0.jsonl` → sidecars |
| AE-2 measurement | State Contract + TS-1 | **2** cites |
| AE-2 experiment | SETV-EXP GBPJPY + USDJPY | **2** cites |
| AE-2 uncertainty | DESIGN + OWNER_CONFIRM ×2 | **3** cites |
| Markdown bulk (pre-manifest) | snapshot/family/evolution scrape | 13+17+10 (AAPL CARD skip noted) |
| FactorLib first batch | `ecosystem ingest --limit 5` | **3/4** OK · 1 Ollama 500 skip (DLL Spec) |
| AShareLib first batch | `ecosystem ingest --limit 5` | **5/5** OK |

## Problems / evidence

| ID | Finding | Evidence | Disposition |
|----|---------|----------|-------------|
| GAP-AAPL-CARD | AAPL W/D/H4 `CARD.md` lack `SETV-INST-*` Primary Instance id | bulk snapshot skipped=3 | Producer gap · family covered via `export_family.json` / `SETV-FAM-*` · no KF-invented INST ids |
| ALIGN-L-SA | Early KF markdown mapped `L-SA-*` → evolution; SETV sidecar stamps **family** | manifest `asset_class=family` for L-SA | Trust producer stamp under OPEN KF INGEST |
| OBS-FACTOR-CMAKE | Factor discover matched `CMakeLists.txt` via `**/*.txt` | dry-run before fix | Fixed: md-only + hard exclude |
| OBS-OLLAMA-500 | `FactorLib_DLL_Spec.md` LLM call dropped (tcp reset) | `_bulk_factorlib.txt` skip | retry with smaller doc / restart Ollama |

## Commands

```powershell
.\.venv\Scripts\python.exe main.py setv ingest --setv-root D:\fxtrading --no-index
.\.venv\Scripts\python.exe main.py setv measurement ... --setv-root D:\fxtrading --no-index
.\.venv\Scripts\python.exe main.py setv experiment "D:\fxtrading\methodology\evidence\families" --setv-root D:\fxtrading --no-index
.\.venv\Scripts\python.exe main.py setv uncertainty ... --setv-root D:\fxtrading --no-index
.\.venv\Scripts\python.exe main.py ecosystem ingest factorlib "D:\fxtrading\FactorLibDLL" --limit 5 --no-index
.\.venv\Scripts\python.exe main.py ecosystem ingest asharelib "D:\fxtrading\docs\design" --limit 8 --no-index
```

## Still open (non-HOLD)

- AShareLib first-batch completion (after Factor LLM)
- Index rebuild for restricted SETV cites (optional)
- AAPL per-TF INST sidecars (SETV producer)
- Watermark / encrypt export
