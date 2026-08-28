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
| FactorLib first batch | `ecosystem ingest` spec ×4 + retry | **4/4** OK (DLL Spec retry 2026-08-28) |
| AShareLib first batch | `ecosystem ingest --limit 5` | **5/5** OK |

## Problems / evidence

| ID | Finding | Evidence | Disposition |
|----|---------|----------|-------------|
| GAP-AAPL-CARD | AAPL W/D/H4 `CARD.md` lack `SETV-INST-*` Primary Instance id | bulk snapshot skipped=3 | ✅ **CLOSED** · SETV stamped · KF cited 3 snaps · [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md) |
| ALIGN-L-SA | Early KF markdown mapped `L-SA-*` → evolution; SETV sidecar stamps **family** | manifest `asset_class=family` for L-SA | Trust producer stamp under OPEN KF INGEST |
| OBS-FACTOR-CMAKE | Factor discover matched `CMakeLists.txt` via `**/*.txt` | dry-run before fix | Fixed: md-only + hard exclude |
| OBS-OLLAMA-500 | `FactorLib_DLL_Spec.md` LLM tcp reset | `_bulk_factorlib.txt` skip | ✅ retry `_retry_factorlib_dll_spec.txt` |

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

Full matrix: [`REQ_VS_LANDED_20260828.md`](REQ_VS_LANDED_20260828.md)

| Priority | Item | Class | Owner |
|----------|------|-------|-------|
| — | *(content-fill / A–C queue clear)* | — | — |
| HOLD residual | H4 chunk-RAG · SETV scope | HOLD | [`REQ_VS_LANDED_20260828.md`](REQ_VS_LANDED_20260828.md) §3 · [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md) · SCOPE Owner: `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |
| H1–H3 | 一源多卡 / Manim a+b+c / GNN | ✅ LANDED | same |

**NEXT = HOLD** · nail: [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md)  
Ops: [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) ✅ · Maintain delete: [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md) ✅  
AAPL: [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md) ✅  
Usage: B ✅ · C ✅ · Phase: [`PHASE_CONTENT_FILL_20260828.md`](PHASE_CONTENT_FILL_20260828.md)
