# Requirements vs Landed — 2026-08-28 refresh

```yaml
as_of: 2026-08-28
head: 43d7e3f
branch: main
rule: 未关闭项不宣称 FIXED；HOLD 不启动；Producer Gap 不由 KF 发明 ID
```

## Verdict

```text
Architecture / Access / SETV cite-ingest / Content Fill first batch
  → largely LANDED

Next value
  → use accumulated KOs (retrieve / reconstruct)
  → classify gaps A/B/C/D
  → SETV only for confirmed Producer Gaps (AAPL INST open)
```

---

## 1. Capability matrix

| Requirement | Source | Landed? | Evidence |
|-------------|--------|---------|----------|
| KO + Harness (P0) | SETV audit | ✅ | `compile` / packages |
| Expression (P1) | SETV audit | ✅ | express · Manim DEFER HOLD |
| Reconstruction (P2) | SETV audit | ✅ | reconstruct + contrast |
| Retrieval (P3) | SETV audit | ✅ | retrieve index/query |
| Access classification + retrieve filter | §8 / handoff | ✅ | `access.py` |
| Dual-track LLM compose eligibility | AccessPolicy | ✅ | restricted → local_only |
| UI lanes general vs proprietary | Export gates | ✅ | UI v0.4 lane-bar |
| Plaintext external export gate | Export | ✅ | `/api/export` blocks local_only |
| Access audit trail | Priority 1 | ✅ | `ACCESS_AUDIT_V0.md` · `data/audit/access/` |
| Encrypted export + watermark | Priority 1/5 | ✅ | `.kfexport` · `ENCRYPTED_EXPORT_V0.md` |
| SETV snapshot cite-only | AE-2 | ✅ | `setv snapshot` / ingest |
| SETV evolution / family | AE-2 | ✅ | adapters + sidecars |
| SETV measurement / experiment / uncertainty | AE-2 remainder | ✅ | CLIs + cites |
| OPEN KF INGEST (manifest) | SETV OPEN SCHEMA | ✅ | 45/45 · `SETV_OPEN_KF_INGEST_V0.md` |
| FactorLib first-batch design docs | Content fill | ✅ | **4/4** specs |
| AShareLib first-batch design docs | Content fill | ✅ | **5/5** |
| Gap taxonomy A/B/C/D | Phase doc | ✅ | `PHASE_CONTENT_FILL_20260828.md` |
| AAPL per-TF `SETV-INST-*` + sidecars | Producer | ⏸ **A** | packet issued · still absent on SETV |
| Restricted bulk index rebuild runbook | Ops | 🟡 | index rebuild works · runbook thin |
| Make SETV KOs “live” (retrieve/reconstruct usage) | Strategy | ✅ B · [`USAGE_EVIDENCE_B_20260828.md`](USAGE_EVIDENCE_B_20260828.md) · C soft edges remain |
| 一源多卡 / Manim 实渲染 / GNN / chunk-RAG | HOLD | ⏸ | frozen |

---

## 2. Content inventory (local restricted)

| Tree | Approx KO `.md` | Notes |
|------|-----------------|-------|
| SETV snapshots | 14 | AAPL ×3 still missing (Producer) |
| SETV families | 23 | includes L-SA as family (producer stamp) |
| SETV evolutions | 16 | |
| SETV measurements | 2 | Contract + TS-1 |
| SETV experiments | 2 | GBPJPY + USDJPY EXP |
| SETV uncertainties | 3 | DESIGN + OWNER_CONFIRM |
| FactorLib | 6 | 4 specs + earlier README-class |
| AShareLib | 11 | 5 first-batch + prior smoke |

SETV OPEN KF INGEST: **45/45** sidecars. AE-2 remainder cites beyond manifest: +7.

---

## 3. Open gaps (classified)

| ID | Class | Requirement | Landed | Owner | Next |
|----|-------|-------------|--------|-------|------|
| GAP-AAPL-CARD | **A · Producer** | Per-TF INST id + `export.json` | Family only | SETV | [`PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md`](../interop/PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md) |
| GAP-USAGE-RETRIEVE | **B/C · Knowledge/Relation** | Existing SETV KOs queryable & related | ✅ B fixed (nested index) · C soft edges open | KF | [`USAGE_EVIDENCE_B_20260828.md`](USAGE_EVIDENCE_B_20260828.md) |
| GAP-OPS-RUNBOOK | Ops | Documented bulk ingest + index rebuild | Commands in docs · no single runbook | KF | short ops page |
| — | HOLD | 一源多卡 / Manim / GNN / chunk-RAG | Not started | — | do not start |

---

## 4. SETV ↔ KF contract posture

| SETV word | KF action | Status |
|-----------|-----------|--------|
| ACK CONSUMER READY | Cite Cards | ✅ |
| OPEN SCHEMA | Prefer sidecars | ✅ |
| OPEN KF INGEST | `setv ingest` manifest | ✅ |
| HOLD on runtime bind / Measurement amend | No mutate / no receipt | ✅ held |
| AAPL INST stamps | Wait producer | ⏸ open |

---

## 5. What *not* to do next

- Expand SETV research scope because KF “wants more classes”
- Invent `SETV-INST-AAPL-*` inside KF
- Promote restricted → secret (blocks normal retrieve)
- Unfreeze HOLD items without Owner word

---

## 6. Recommended next (ordered)

1. ~~**KF usage pass**~~ → ✅ B closed · see USAGE_EVIDENCE_B  
2. **C · Relation** — tighten graph boost / low-confidence edge hygiene  
3. **Ops runbook** — ingest → index rebuild → audit → encrypt  
4. **SETV A** — AAPL INST packet  
5. HOLD remains HOLD  

---

## 7. Stale handoff corrections

| Handoff line was | Now |
|------------------|-----|
| Factor 3/4 | **4/4** |
| Access encrypt 待 | **LANDED** `.kfexport` |
| AAPL open without packet | Packet **issued** (`PRODUCER_GAP_…`) |
| Unit tests “92” | Re-run: **129** unit (excl. slow) @ this refresh |

Docs updated: this file · `HANDOFF_20260827.md` §10–12 · `PHASE_CONTENT_FILL_20260828.md`
