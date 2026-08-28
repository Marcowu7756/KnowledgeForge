# Producer Gap · AAPL per-TF Instance ID + snapshot sidecars

```yaml
gap_id: GAP-AAPL-CARD
class: A · Producer Gap
from: KnowledgeForge (cite-only consumer)
to: SETV Owner / Export tooling
date: 2026-08-28
status: OPEN · KF will not invent INST IDs
```

\[
\boxed{Producer\ Identity > Consumer\ Inference}
\qquad
\boxed{KF\ =\ cite\text{-}only}
\qquad
\boxed{no\ SETV\text{-}INST\ invention}
\]

---

## 1. What KF already has

| Artifact | Status in KF |
|----------|--------------|
| `SETV-FAM-AAPL-TV-2024-WDH4` via `export_family.json` | ✅ family cite |
| `L-SF-AAPL` edge sidecar | ✅ family cite |
| AAPL W / D / H4 as **State Snapshot** KOs | ❌ skipped — no `SETV-INST-*` |

Family container is settled. Per-TF **snapshot** cites are blocked.

---

## 2. Evidence of the gap

Paths (SETV producer tree — cite only):

```text
methodology/SETV/research/instances/AAPL/W/CARD.md
methodology/SETV/research/instances/AAPL/D/CARD.md
methodology/SETV/research/instances/AAPL/H4/CARD.md
```

Each CARD has Symbol/TF/Evidence/Status but **no**:

- `Primary Instance id: SETV-INST-…`
- sibling `export.json` snapshot sidecar

Family registry (`SETV_FAM_AAPL_TV_2024_WDH4`) names members `AAPL-W|D|H4` and window **2024-01-01 → 2024-12-31**, but does not stamp AE-4 instance ids.

`manifest_v0.jsonl` lists family export only — no AAPL snapshot rows.

KF bulk markdown snapshot: **skipped=3** (AAPL W/D/H4). See `docs/audit/CONTENT_FILL_20260828.md`.

---

## 3. What SETV should issue (Owner AUTHORIZE / export tool)

### 3.1 Proposed `artifact_id` grammar (AE-4)

Window key from family identity: **2024** (calendar pack already used in Evidence filenames `*_2024_IT`).

| TF | Proposed id (Owner must confirm) |
|----|----------------------------------|
| W | `SETV-INST-AAPL-W-2024` |
| D | `SETV-INST-AAPL-D-2024` |
| H4 | `SETV-INST-AAPL-H4-2024` |

These are **proposals for SETV**, not KF assignments. If Atlas already uses a different stamp, use that — do not invent a parallel namespace.

### 3.2 CARD hygiene (machine-findable)

Add one line near Identity / top table, matching GBPJPY/GOLD cards:

```text
Primary Instance id: SETV-INST-AAPL-H4-2024
```

(and W / D equivalents).

### 3.3 Snapshot sidecar (OPEN SCHEMA already authorized)

Next to each CARD, emit `export.json` like GOLD:

```json
{
  "schema": "setv_artifact_export_sidecar_v0",
  "export_contract_version": "setv_artifact_export_v0@v0.0.0",
  "artifact_id": "SETV-INST-AAPL-H4-2024",
  "evidence_pointer": "methodology/evidence/EVIDENCE_20260818_AAPL_H4_2024_IT.md",
  "asset_class": "snapshot",
  "assembled_at": "YYYYMMDDTHHMMSSZ",
  "card_path": "methodology/SETV/research/instances/AAPL/H4/CARD.md",
  "symbol": "AAPL",
  "timeframe": "H4",
  "window": "2024-01-01 → 2024-12-31",
  "status": "OBSERVE · Evidence ARCHIVED · ≠ Forecast · ≠ Decision",
  "evidence_paths": [
    "methodology/evidence/EVIDENCE_20260818_AAPL_H4_2024_IT.md",
    "methodology/evidence/families/SETV_FAM_AAPL_TV_2024_WDH4.md"
  ],
  "neq": ["Signal", "Execution", "TradingDecision", "Runtime", "Explain", "Forecast", "Ranking", "MultiTFFusion", "Predict"],
  "governance": {
    "mutates_measurement": false,
    "cite_only": true,
    "authorize": "OPEN SCHEMA / IMPLEMENT · OWNER_CONFIRM_20260828_OPEN_SCHEMA_AUTHORIZE_IMPLEMENT.md"
  }
}
```

Repeat for W / D with matching Evidence pointers.

### 3.4 Manifest

Append three snapshot lines to `methodology/SETV/export/manifest_v0.jsonl`.

---

## 4. What KF will do after SETV lands

```powershell
.\.venv\Scripts\python.exe main.py setv ingest --setv-root D:\fxtrading --class snapshot
# or markdown fallback:
.\.venv\Scripts\python.exe main.py setv snapshot `
  "D:\fxtrading\methodology\SETV\research\instances\AAPL" `
  --setv-root D:\fxtrading
```

Expect three new restricted State Snapshot KOs. No SETV mutation from KF. No receipt written back into `D:\fxtrading`.

---

## 5. Explicit non-asks

- Do **not** ask KF to synthesize INST ids from folder names
- Do **not** fuse W/D/H4 into one snapshot
- Do **not** reopen Measurement / Forecast for this gap

---

## 6. Acceptance checklist (SETV)

- [ ] Owner confirms three `SETV-INST-AAPL-{W|D|H4}-2024` (or alternate AE-4 stamps)
- [ ] Each CARD has `Primary Instance id:`
- [ ] Each TF dir has `export.json` (`asset_class=snapshot`)
- [ ] `manifest_v0.jsonl` lists the three snapshots
- [ ] KF `setv ingest --class snapshot` cites all three without skip
