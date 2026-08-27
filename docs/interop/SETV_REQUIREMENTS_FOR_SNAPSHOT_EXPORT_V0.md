# SETV → KnowledgeForge · State Snapshot Adapter Requirements (for SETV project)

**Audience:** SETV Owner / next SETV Agent  
**From:** KnowledgeForge (`D:\KnowledgeForge`)  
**Date:** 2026-08-28  
**Aligns with:**  
- `D:\fxtrading\methodology\SETV_ARTIFACT_EXPORT_CONTRACT_V0.md` (AE-1…AE-6 · ISSUED→HOLD)  
- `D:\fxtrading\JForex\docs\handoff\HANDOFF_20260828_SETV_KNOWLEDGEFORGE_RELATION.md`  
- Owner Interpret HOLD: Export = Evidence Distribution Boundary · ≠ Runtime Interface  

\[
\boxed{KF\ =\ cite\text{-}only\ consumer}
\qquad
\boxed{SETV\ =\ producer}
\qquad
\boxed{no\ mutate\ \phi / C1\text{-}C5 / Atlas}
\]

---

## 0. Purpose of this document

KF has landed a **State Snapshot adapter** (cite-only) that turns existing Instance `CARD.md` into a KnowledgeObject with:

- `memory_kind: state`
- `setv_artifact` = Export Triple (AE-1)
- `access.classification: restricted`

This file tells SETV **what KF already consumes**, **what is optional**, and **what would require a new Owner word** (`OPEN KF INGEST` / `OPEN SCHEMA`) before SETV changes code or Contract.

**KF does not ask SETV to:**

- Amend Measurement / C1–C5 / TS-1  
- Reopen Explain / Forecast / Decision  
- Merge Atlas into KF  
- Implement KF storage / ACL / RAG inside `D:\fxtrading`

---

## 1. What KF already consumes (no SETV code change)

| Input | Status | KF action |
|-------|--------|-----------|
| Instance `CARD.md` with `Primary Instance id: SETV-INST-*` | ✅ exists | Deterministic parse → state KO |
| Family Evidence under `methodology/evidence/families/` | ✅ preferred `evidence_pointer` | Cite path in triple |
| Card path as `evidence_pointer` fallback | ✅ allowed by Export Contract §4 | Used when family pointer missing |
| Export Contract version string | ✅ const | Stamp `setv_artifact_export_v0@v0.0.0` |

**Sample that works today:**

```text
D:\fxtrading\methodology\SETV\research\instances\GBPJPY\H4\CARD.md
→ artifact_id SETV-INST-GBPJPY-H4-2024-2026
```

KF CLI (local):

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py setv snapshot `
  "D:\fxtrading\methodology\SETV\research\instances\GBPJPY\H4\CARD.md" `
  --setv-root "D:\fxtrading"
```

Discover all cards:

```powershell
.\.venv\Scripts\python.exe main.py setv snapshot `
  "D:\fxtrading\methodology\SETV\research\instances" `
  --setv-root "D:\fxtrading" --dry-run
```

---

## 2. Hard requirements for any SETV Artifact KF will cite

These are **already Contract-frozen** (AE-1). KF will reject / skip cards that violate them.

| # | Requirement | Why |
|---|-------------|-----|
| R1 | Stable `artifact_id` matching AE-4 grammar (`SETV-INST-{SYMBOL}-{TF}-{WINDOW}`) | No KF-invented IDs |
| R2 | Resolvable `evidence_pointer` (repo-relative `.md` that grounds the claim) | Cite-only fence |
| R3 | `export_contract_version: setv_artifact_export_v0@v0.0.0` (or newer after amend) | Handle versioning |
| R4 | Claim language stays in {observed, historical, descriptive, association, archival} | Export §5 |
| R5 | No Forecast / Decision / ranking language packaged as Artifact content | Forbidden frames |

**Card hygiene that helps KF (not Contract amend):**

| # | Soft requirement | Today |
|---|------------------|-------|
| H1 | Keep `Primary Instance id:` line machine-findable | ✅ GBPJPY card |
| H2 | Keep `Symbol:` / `Timeframe:` / `Window:` lines | ✅ |
| H3 | Prefer absolute-ish `methodology/evidence/...` pointers in Evidence section | ✅ |
| H4 | One CARD.md per Instance directory | ✅ convention |
| H5 | Status line (`OBSERVE · ARCHIVED`) near top | ✅ |

If H1–H4 break, KF skips with an error; SETV core need not change — fix Card template.

---

## 3. Optional SETV work (needs Owner word)

Owner Interpret currently: **Schema tool STOP** · **KF implementation STOP** until e.g. `OPEN KF INGEST` / `OPEN SCHEMA`.

| Option | Benefit to KF | SETV impact | Gate |
|--------|---------------|-------------|------|
| **O1 · Export sidecar JSON** next to CARD (`export.json` with AE-1 triple + optional fields) | Zero markdown scrape ambiguity | New file convention only · no φ change | `OPEN SCHEMA` or `OPEN KF INGEST` |
| **O2 · Manifest of exportable Instances** (`methodology/SETV/export/manifest_v0.jsonl`) | Bulk discover without rglob | Discovery layer · ≠ runtime | `OPEN KF INGEST` |
| **O3 · Mark `asset_class` explicitly on Card** | Distinguishes snapshot vs evolution cites of same INST id | Doc convention | soft / template |
| **O4 · Machine section anchors** (`## Identity` instead of only ```text blocks) | More robust parsers | Card template polish | soft |
| **O5 · Evolution / Family adapters** (same triple, different class) | Six-class coverage | Still cite-only | KF later · SETV already has loci |

**Not requested:**

- Binding runtime SETV↔KF  
- Streaming state into KF  
- Putting Observation Envelope raw OHLCV into KF as State Memory  
- Ranking / Promotion fields for KF

---

## 4. Boundary checklist — does SETV need to modify?

| Area | Need change? | Notes |
|------|--------------|-------|
| Measurement Layer | **No** | Untouched |
| State Contract C1–C5 / TS-1 | **No** | Untouched |
| Atlas compute / Edges | **No** | Producer remains SETV |
| Observation Envelope / schema_registry | **No** for Snapshot v0 | Envelope is Raw Observation path · ≠ Artifact Export |
| Instance CARD / Evidence markdown | **No required** · optional hygiene H1–H5 | Already sufficient for GBPJPY sample |
| Artifact Export Contract v0 | **No amend** for KF Card cite | Already ISSUED |
| JSON exporter / schema tool | **Optional** O1–O2 | Only after Owner `OPEN SCHEMA` / `OPEN KF INGEST` |
| FactorLib coupling | **No** | Orthogonal consumer |
| Commit of Export freeze | SETV-side governance | KF does not decide |

**Verdict:** SETV **does not need core modifications** for KF Snapshot adapter v0.  
Needed from SETV is only: **continue publishing Instance Cards + Evidence with stable IDs**. Optional tooling improves robustness after a new Owner authorize word.

---

## 5. What KF guarantees back to SETV

| Guarantee | Detail |
|-----------|--------|
| Cite-only | Never write into `D:\fxtrading` |
| No φ reinterpretation | Adapter is deterministic extract · no LLM on Snapshot path |
| Restricted ACL | Snapshot KOs default `restricted` + `local_only` + `memory_kind=state` |
| Dual-track LLM | Cloud compose filters restricted; local may use |
| ID fidelity | `setv_artifact.artifact_id` preserved; KF unit id = hash(artifact_id) |
| Claim fence | Lines matching predict/forecast/buy/sell… dropped |

---

## 6. Suggested SETV Owner replies (pick one)

1. **`ACK CONSUMER READY`** — Cards as-is are enough; KF may cite; SETV stays HOLD on tools. ← **received 2026-08-28** (GOLD H4 sample validated)  
2. **`OPEN KF INGEST`** — Authorize optional manifest / discoverability polish (still ≠ runtime bind).  
3. **`OPEN SCHEMA`** — Authorize `export.json` sidecar schema next to CARD.  
4. **`HOLD`** — No SETV action; KF may still cite existing Cards under Export Contract (consumer-side only).

**Canonical cite sample:** `SETV-INST-GOLD-H4-2024-2026` · Window 2024–2026（含 2024；无单独「黄金 2024」卡）.

---

## 7. Read order for SETV Agent

1. This file  
2. `SETV_ARTIFACT_EXPORT_CONTRACT_V0.md`  
3. `OWNER_INTERPRET_20260828_ARTIFACT_EXPORT_CONTRACT_V0_HOLD.md`  
4. Sample Card: `methodology/SETV/research/instances/GBPJPY/H4/CARD.md`  
5. KF adapter: `D:\KnowledgeForge\app\ingest\setv_snapshot.py`  
6. KF design note: `docs/interop/SETV_SNAPSHOT_ADAPTER_V0.md`

---

*KF → SETV requirements · Snapshot adapter v0 · cite-only · 2026-08-28*
