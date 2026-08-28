# KF Consume Evidence · AAPL Per-TF INST — 2026-08-28

```yaml
run_id: KF-AAPL-CONSUME-20260828
class: A · Producer Gap → CLOSED on KF side
producer: SETV (no KF id invention)
manifest_lines: 48
```

## Producer (SETV · already landed)

| ID | Sidecar | Evidence |
|----|---------|----------|
| `SETV-INST-AAPL-W-2024` | `AAPL/W/export.json` | `EVIDENCE_…_AAPL_W_2024_IT.md` |
| `SETV-INST-AAPL-D-2024` | `AAPL/D/export.json` | `EVIDENCE_…_AAPL_D_2024_IT.md` |
| `SETV-INST-AAPL-H4-2024` | `AAPL/H4/export.json` | `EVIDENCE_…_AAPL_H4_2024_IT.md` |

Family container unchanged: `SETV-FAM-AAPL-TV-2024-WDH4`. No recompute / stitch / measurement amend.

## KF cite

```powershell
.\.venv\Scripts\python.exe main.py setv ingest --setv-root D:\fxtrading --class snapshot --no-index
# matched=16 skipped=0 · includes 3× AAPL
.\.venv\Scripts\python.exe main.py index rebuild --subdir restricted
.\.venv\Scripts\python.exe main.py index rebuild
.\.venv\Scripts\python.exe main.py retrieve index --from-index --no-write-back-packages
```

| Check | Result |
|-------|--------|
| KO paths | `data/knowledge/restricted/setv/snapshots/snapshot_setv_inst_aapl_{w,d,h4}_2024.md` |
| Global units | **114** (+3 AAPL snaps) |
| Retrieve `AAPL H4 State Snapshot` · proprietary | Top-3 = AAPL W / H4 / D INST snaps |

Packet: [`PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md`](../interop/PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md) → **CLOSED** (acceptance met).

**NEXT = HOLD** (producer word). No further SETV scope expansion from KF.
