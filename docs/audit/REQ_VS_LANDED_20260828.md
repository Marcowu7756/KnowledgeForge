# Requirements vs Landed — 2026-08-28 refresh (post-H1c)

```yaml
as_of: 2026-08-28
head_pushed: 73d8d33
workspace: uncommitted H1–H3 thaw + H2c mpl + C/Ops/AAPL on top of 73d8d33
branch: main
rule: 未关闭项不宣称 FIXED；未落地仅列仍 intentional 的缺口；Producer Gap 不由 KF 发明 ID
posture: NEXT = HOLD on SETV scope · tech HOLD residual = H4 · POSTURE_NAIL_20260828.md
```

## Verdict

```text
P0 / P1 / Content Fill / Access / AAPL INST / A·B·C·Ops
  → CLOSED

P2 Reconstruction / P3 Retrieval
  → LANDED · AAPL retrieve VERIFIED

HOLD thaw (Owner word · 2026-08-28)
  → H1 一源多卡     ✅ a+b+c
  → H2 Manim        ✅ a+b+c (mpl_v0 second renderer)
  → H3 GNN          ✅ a+b+c (boost opt-in)
  → H4 chunk-RAG    ⏸ still HOLD

Unlanded (intentional · only)
  → H4 chunk-RAG (+ doctrine amend)
  → HOLD-SETV-SCOPE (consume-first · prove D)

Next value
  → consume SETV state archive · classify A/B/C/D on real failures
  → only D · Representation re-enters SETV
  → optional Owner thaw: H4
```

---

## 1. Capability matrix (需求 → 落地)

| Requirement | Source | Landed? | Evidence |
|-------------|--------|---------|----------|
| KO + Harness (P0) | SETV audit | ✅ | `compile` / packages |
| Expression (P1) | SETV audit | ✅ | express · Manim `manim_v0` + golden · H2c `mpl_v0` |
| Reconstruction (P2) | SETV audit | ✅ | reconstruct + contrast + edge hygiene |
| Retrieval (P3) | SETV audit | ✅ | retrieve index/query · graph affinity · optional GNN blend |
| Access classification + retrieve filter | §8 / handoff | ✅ | `access.py` |
| Dual-track LLM compose eligibility | AccessPolicy | ✅ | restricted → local_only |
| UI lanes general vs proprietary | Export gates | ✅ | UI lane-bar |
| Plaintext external export gate | Export | ✅ | `/api/export` blocks local_only |
| Access audit trail | Priority 1 | ✅ | `ACCESS_AUDIT_V0.md` · `data/audit/access/` |
| Encrypted export + watermark | Priority 1/5 | ✅ | `.kfexport` · `ENCRYPTED_EXPORT_V0.md` |
| SETV snapshot / evolution / family cite | AE-2 | ✅ | adapters + sidecars |
| SETV measurement / experiment / uncertainty | AE-2 remainder | ✅ | CLIs + cites |
| OPEN KF INGEST (manifest) | SETV OPEN SCHEMA | ✅ | producer manifest **48** · KF ingest OK |
| FactorLib first-batch design docs | Content fill | ✅ | **4/4** specs |
| AShareLib first-batch design docs | Content fill | ✅ | **5/5** |
| Gap taxonomy A/B/C/D | Phase doc | ✅ | `PHASE_CONTENT_FILL_20260828.md` |
| AAPL per-TF `SETV-INST-*` + sidecars | **A · Producer** | ✅ | SETV stamp · KF 3 cites · [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md) |
| Nested restricted index (findable KOs) | **B · Knowledge** | ✅ | `rglob` rebuild · [`USAGE_EVIDENCE_B_20260828.md`](USAGE_EVIDENCE_B_20260828.md) |
| Soft graph / edge hygiene | **C · Relation** | ✅ | [`USAGE_EVIDENCE_C_20260828.md`](USAGE_EVIDENCE_C_20260828.md) |
| Ops runbook ingest→index→audit→encrypt | Ops | ✅ | [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) |
| SETV → KF → retrieve closed loop (AAPL) | Strategy | ✅ | Top-3 AAPL INST on `AAPL H4 State Snapshot` |
| Source settle→express matrix (non-Cartesian) | Integration | ✅ | [`INTEGRATION_SOURCE_MATRIX_20260828.md`](INTEGRATION_SOURCE_MATRIX_20260828.md) · 13/13 |
| Knowledge maintain delete-only | Ops / UI | ✅ | [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md) · `knowledge delete` · UI 沉淀 |
| 一源多卡 | HOLD→H1 | ✅ **H1a+b+c** | UI v0.5.2 · family + select compose + `data/ui` layout persist |
| Manim 实渲染 | HOLD→H2 | ✅ **H2a+b+c** | `manim_v0` · golden · **`mpl_v0`** · Pillow fallback |
| GNN | HOLD→H3 | ✅ **H3a+b+c** | offline diffusion · shadow JSON · `KF_GNN_BOOST` opt-in |
| chunk-RAG / 聊天窗产品化 | HOLD→H4 | ⏸ | frozen · needs doctrine amend |
| SETV new axes / metrics / scopes / instance types | HOLD | ⏸ | frozen · do not ask after AAPL success |

---

## 2. Content inventory (local · as of nail)

| Tree | KO `.md` (approx) | Notes |
|------|-------------------|-------|
| SETV snapshots | **17** | includes AAPL W/D/H4 INST |
| SETV families | 23 | includes L-SA as family (producer stamp) |
| SETV evolutions | 16 | |
| SETV measurements | 2 | Contract + TS-1 |
| SETV experiments | 2 | GBPJPY + USDJPY EXP |
| SETV uncertainties | 3 | DESIGN + OWNER_CONFIRM |
| SETV ecosystem docs (root) | 5 | glossary / schema / … |
| FactorLib | ~5–7 | 4/4 first-batch specs + extras |
| AShareLib | ~8–10 | 5/5 first-batch + prior |
| **Global `units.jsonl`** | **114** | retrieve vectors **114** · dim 512 |
| SETV producer `manifest_v0.jsonl` | **48** | +3 AAPL snapshot rows |

Archive character: forming **SETV State Archive** (Family + Instance + Evidence), not scattered files.

---

## 3. 未落地（仅此表 · intentional）

| ID | Class | Requirement | Why unlanded | Owner | Gate |
|----|-------|-------------|--------------|-------|------|
| HOLD-CHUNK-RAG | HOLD **H4** | Chunk-RAG / chat product | Frozen · whole-KO retrieve remains default | — | Owner `THAW HOLD-CHUNK-RAG` + **doctrine amend** |
| HOLD-SETV-SCOPE | HOLD | New SETV axes / metrics / scopes / INST types | Consume-first after AAPL | SETV | Usage must prove **D · Representation** |

**Already closed this thaw (not unlanded):**

| ID | Closed | Evidence |
|----|--------|----------|
| HOLD-YIYUAN | ✅ H1a+b+c | family API · compose selected · layout persist |
| HOLD-MANIM | ✅ H2a+b+c | `manim_v0` · golden · **`mpl_v0`** · Pillow |
| HOLD-GNN | ✅ H3a+b+c | `gnn_offline` · shadow · opt-in boost |

**No open A / B / C / Ops tickets.** Residual HOLD = **H4** (+ SETV scope).

Thaw progress: **H1 ✅ → H2 ✅ → H3 ✅ → H4 ⏸**.

---

## 4. Recently closed gaps (for audit trail)

| ID | Class | Closed how | Evidence |
|----|-------|------------|----------|
| GAP-AAPL-CARD | A | SETV stamped INST + sidecars · KF cite | [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md) · [`PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md`](../interop/PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md) |
| GAP-INDEX-SHALLOW | B | `rebuild_index` → `rglob` | [`USAGE_EVIDENCE_B_20260828.md`](USAGE_EVIDENCE_B_20260828.md) |
| GAP-SOFT-GRAPH | C | edge hygiene + affinity gate | [`USAGE_EVIDENCE_C_20260828.md`](USAGE_EVIDENCE_C_20260828.md) |
| GAP-OPS-RUNBOOK | Ops | thin runbook | [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) |
| HOLD-YIYUAN | H1 | multi-card + select compose + layout persist | UI v0.5.2 · `layout_persist.py` · `test_multi_card_h1a` / `test_layout_persist_h1c` |
| HOLD-MANIM | H2a+b+c | Manim + golden + Matplotlib second renderer | `render_manim.py` · `render_mpl.py` · `test_manim_h2*` |
| HOLD-GNN | H3 | offline diffusion + shadow + opt-in blend | `gnn_offline.py` · `test_gnn_h3.py` |

---

## 5. SETV ↔ KF contract posture

| SETV word | KF action | Status |
|-----------|-----------|--------|
| ACK CONSUMER READY | Cite Cards | ✅ |
| OPEN SCHEMA | Prefer sidecars | ✅ |
| OPEN KF INGEST | `setv ingest` manifest | ✅ (48 lines on producer) |
| HOLD on runtime bind / Measurement amend | No mutate / no receipt | ✅ held |
| AAPL INST stamps | Wait producer | ✅ closed |
| NEXT = HOLD | No SETV scope expansion ask | ✅ nailed · [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) |

---

## 6. What *not* to do next

- Expand SETV research scope because KF “wants more classes”
- Invent `SETV-INST-*` inside KF
- Promote restricted → secret (blocks normal retrieve)
- Unfreeze H4 without Owner word + doctrine amend
- Treat “114 units” as a growth KPI — growth follows proven **D** gaps only
- Bundle H4 with unrelated expression work

---

## 7. Recommended next (ordered)

1. **Consume** — use Family + Instance + Evidence in KF; observe what questions fail  
2. On each failure → classify **A / B / C / D** before coding or asking SETV  
3. Only **D · Representation** re-opens SETV evolution discussion  
4. Optional tech: Owner `THAW HOLD-CHUNK-RAG` + doctrine amend — see [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md)  
5. Optional hygiene: commit local H1–H3 + H2c + C/Ops/AAPL docs when Owner wants git sync  

Program board: [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) · thaw: [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md) · ops: [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) · maintain: [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md)

---

## 8. Stale corrections

| Old claim | Now |
|-----------|-----|
| Factor 3/4 | **4/4** |
| Access encrypt 待 | **LANDED** `.kfexport` |
| AAPL Producer Gap OPEN | **CLOSED** |
| C soft edges open | **CLOSED** |
| Ops runbook thin | **LANDED** |
| Manifest 45/45 | Producer **48** (+ AAPL ×3) · KF cite OK |
| 一源多卡 / Manim / GNN all HOLD | **H1+H2+H3 LANDED** · residual **H4 / SETV-SCOPE** |
| H1c open | **H1c LANDED** · `data/ui/multi_card_layout.json` |
| H2c open | **H2c LANDED** · `mpl_v0` · auto manim→mpl→pillow |
| Next = more SETV ingest | **NEXT = HOLD** on SETV scope · consume archive |

Docs of record: this file · `HANDOFF_20260827.md` §10 · `POSTURE_NAIL_20260828.md` · `HOLD_THAW_SCHEDULE_V0.md` · `CONTENT_FILL_20260828.md`
