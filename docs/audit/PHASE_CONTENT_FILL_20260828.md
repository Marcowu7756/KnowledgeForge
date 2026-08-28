# KnowledgeForge · Phase: Content Fill → Access Governance

**Date:** 2026-08-28  
**Head:** `43d7e3f`  
**Status:** Content Fill **LANDED** · Access Governance **LANDED** · next = **Knowledge Gap Discovery (usage)**

权威需求矩阵：[`REQ_VS_LANDED_20260828.md`](REQ_VS_LANDED_20260828.md)

---

## Phase ladder

```text
Foundation
   ↓
P0  KnowledgeObject / Harness       CLOSED
   ↓
P1  Expression                      CLOSED
   ↓
P2  Reconstruction                  LANDED
   ↓
P3  Retrieval                       LANDED
   ↓
Content Fill                        ✅
   ↓
Access Governance                   ✅ (audit + .kfexport)
   ↓
Knowledge Gap Discovery             ← 当前
   ↓
Future SETV Evolution (producer-led)
```

**Core invariant (validated):**

```text
SETV ≠ KnowledgeForge
SETV → KnowledgeForge  (cite-only · producer stamp > consumer heuristic)
```

Future loop (do not rush SETV complexity):

```text
SETV → KF → Accumulation → Gap taxonomy → SETV Research (when warranted)
```

---

## Content Fill — closed evidence

| Source | Result | Mode |
|--------|--------|------|
| SETV manifest + sidecars | **45/45** | cite-only · no LLM |
| SETV AE-2 remainder | measurement 2 · experiment 2 · uncertainty 3 | cite-only |
| FactorLib | **4/4** | LLM compress |
| AShareLib | **5/5** | LLM compress |

SETV is no longer “snapshot only” — it is **Observation + Method + Evidence + Uncertainty** as a knowledge source.

Cross-ecosystem shape:

```text
                    KnowledgeForge (accumulation)
                              ▲
              ┌───────────────┼───────────────┐
              │               │               │
            SETV          FactorLib       AShareLib
```

Evidence log: [`CONTENT_FILL_20260828.md`](CONTENT_FILL_20260828.md)

---

## Principles (hold)

| Principle | Example |
|-----------|---------|
| Producer identity > consumer inference | AAPL CARD skip — no KF-invented `SETV-INST-*` |
| Producer stamp > KF heuristic | `L-SA-*` → trust sidecar `asset_class=family` |
| Restricted = real proprietary assets | SETV + Factor + AShare now in `data/knowledge/restricted/` |
| Do not over-classify to secret | restricted remains retrieve-able under policy |

---

## Knowledge gap taxonomy (use for all future issues)

| Class | Meaning | Owner | Example |
|-------|---------|-------|---------|
| **A · Producer Gap** | SETV/ecosystem never produced the artifact | Producer | AAPL per-TF `SETV-INST-*` sidecars |
| **B · Knowledge Gap** | Produced but not correctly settled in KF | KF ingest/index | Artifact exists but KO missing / wrong taxonomy |
| **C · Relation Gap** | Both sides exist, no edge | Reconstruct / Relation | XAUUSD state ↔ US10Y state unlinked |
| **D · Representation Gap** | Settled but questions still unanswerable | SETV research (after KF proves need) | P/D/V insufficient to distinguish states |

**Do not** label everything “SETV missing data.” Classify first.

---

## Priority queue (post–Content Fill)

| # | Item | Owner | Status |
|---|------|-------|--------|
| 1 | **Access governance closure** — restricted default, secret isolation, local/cloud/compose/export ceilings, **audit trail** | KF | ✅ audit + encrypted export |
| 2 | AShareLib first batch | KF ops | ✅ **5/5** |
| 3 | FactorLib `FactorLib_DLL_Spec.md` retry | KF ops | ✅ **4/4** |
| 4 | AAPL per-TF INST sidecar | SETV producer | ✅ stamped · KF cited · [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md) |
| 5 | Watermark / encrypt export | KF | ✅ `.kfexport` Fernet + watermark header |

**Explicitly not now:** expand SETV output scope. First make existing SETV knowledge **retrievable, relatable, reconstructable**; let usage surface gaps.

Usage: B ✅ · C ✅ · AAPL ✅ · Ops ✅  
**NEXT = HOLD** — [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md)

---

## Access governance — what “closed” means

Already in code (`app/knowledge/access.py`, UI lanes, `/api/export`):

- retrieve ceiling by lane (general → internal, proprietary → restricted)
- compose eligibility (restricted → local track)
- expression / export gates (local_only, deny secret)

Still to land for “closure”:

- ~~structured **access audit**~~ → ✅
- ~~encrypted export~~ → ✅
- ~~operational runbook for restricted bulk + index rebuild~~ → ✅ [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md)
- ~~usage evidence~~ → ✅ B/C + AAPL retrieve

See [`REQ_VS_LANDED_20260828.md`](REQ_VS_LANDED_20260828.md).

---

## SETV boundary (diagram)

```text
SETV
  │
  ├─ manifest_v0.jsonl
  ├─ sidecars (AE-1)
  ├─ State Contract / TS-1
  ├─ Experiment Evidence
  └─ Uncertainty Evidence
        │
        ▼  cite-only · no LLM · no ID invention
KnowledgeForge
        │
        ▼
KO → Retrieve → Reconstruct → (Compose under policy)
```
