# Requirements vs Landed — 2026-08-28 refresh (post–Web UI + renderer nail)

```yaml
as_of: 2026-08-28
head_pushed: 4283392
workspace: clean after Web UI v0.6 + H4/SCOPE/renderer nails
branch: main
rule: 未关闭项不宣称 FIXED；未落地仅列仍 intentional 的缺口；Producer Gap 不由 KF 发明 ID
posture: NEXT = HOLD · consume · residual intentional only (H4 · SCOPE · manim_beats DEFER · Math-To-Manim OUT)
```

## Verdict

```text
P0 / P1 / Content Fill / Access / AAPL INST / A·B·C·Ops
  → CLOSED

P2 Reconstruction / P3 Retrieval
  → LANDED · AAPL retrieve VERIFIED

HOLD thaw (Owner word · 2026-08-28)
  → H1 一源多卡     ✅ a+b+c
  → H2 Manim/mpl    ✅ a+b+c (renderer chain)
  → H3 GNN          ✅ a+b+c (boost opt-in)
  → H4 chunk-RAG    ⏸ still HOLD

Product surface
  → Local Web UI browser-first  ✅ v0.6 · WEB_UI_v0.md

Expression contract (nailed · no bend)
  → KO → ExpressionObject → Beats → Renderer → Artifact
  → Renderers: manim_v0 → mpl_v0 → Pillow (GIF 主路径)
  → derive manim_beats → Expression  ⏸ DEFER
  → Math To Manim product path       ❌ not a KF requirement

Unlanded (intentional · only)
  → H4 chunk-RAG (+ doctrine amend)                    · KF
  → HOLD-SETV-SCOPE (Owner Interpret nailed · prove D) · SETV
  → DEFER-MANIM-BEATS (not wired · observe)
  → Math To Manim = External Renderer Reference / No Product Path

Next value
  → consume SETV state archive · classify A/B/C/D on real failures
  → only D · Representation re-enters SETV
  → optional Owner thaw: H4
  → manim_beats / richer media only on consume evidence (or video-cost collapse)

Integration (re-run post–Web UI / HOLD nails)
  → SETTLED · 19/19 PASS · no new blocker · CLOSE
  → evidence: INTEGRATION_RERUN_AUDIT_20260828.md
  → NOT a new Integration slice · NOT HOLD door opening
```

---

## 1. Capability matrix (需求 → 落地)

| Requirement | Source | Landed? | Evidence |
|-------------|--------|---------|----------|
| KO + Harness (P0) | SETV audit | ✅ | `compile` / packages |
| Expression (P1) | SETV audit | ✅ | express · contract CLOSED · GIF 优先 |
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
| Source settle→express matrix (non-Cartesian) | Integration | ✅ | [`INTEGRATION_SOURCE_MATRIX_20260828.md`](INTEGRATION_SOURCE_MATRIX_20260828.md) · 13/13 · re-run audit [`INTEGRATION_RERUN_AUDIT_20260828.md`](INTEGRATION_RERUN_AUDIT_20260828.md) · **19/19** w/ slow |
| Knowledge maintain delete-only | Ops / UI | ✅ | [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md) · `knowledge delete` · Web UI 沉淀 |
| 一源多卡 | HOLD→H1 | ✅ **H1a+b+c** | Web UI · family + select compose + `data/ui` layout persist |
| Local Web UI (browser-first) | Product surface | ✅ | [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) · `ui_version` **0.6.0** · `--desktop` optional · Twitter/X capture |
| Manim / mpl as **Renderer** (H2) | HOLD→H2 | ✅ **H2a+b+c** | `manim_v0` → `mpl_v0` → Pillow · not Expression compiler |
| GNN | HOLD→H3 | ✅ **H3a+b+c** | offline diffusion · shadow JSON · `KF_GNN_BOOST` opt-in |
| derive `manim_beats` → Expression | Expression DEFER | ⏸ | `not_wired_to_expression` · observe only |
| Math To Manim / LLM→`scene.py` | External ref | ❌ N/A | **No product path** · [`RENDERER_REF_MATH_TO_MANIM_20260828.md`](RENDERER_REF_MATH_TO_MANIM_20260828.md) |
| chunk-RAG / 聊天窗产品化 | HOLD→H4 | ⏸ | doctrine nail · [`HOLD_CHUNK_RAG_H4_NAIL_20260828.md`](HOLD_CHUNK_RAG_H4_NAIL_20260828.md) |
| SETV new axes / metrics / scopes / instance types | HOLD | ⏸ | Owner Interpret nailed · `OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |

---

## 2. Content inventory (local · refresh)

| Tree | KO `.md` (approx) | Notes |
|------|-------------------|-------|
| SETV snapshots | **17** | includes AAPL W/D/H4 INST |
| SETV families | **24** | includes L-SA as family (producer stamp) |
| SETV evolutions | **17** | |
| SETV measurements | **3** | |
| SETV experiments | **3** | |
| SETV uncertainties | **4** | |
| SETV ecosystem docs (root) | **6** | glossary / schema / … |
| FactorLib | **6** | 4/4 first-batch specs + extras |
| AShareLib | **11** | 5/5 first-batch + prior |
| **Knowledge tree `.md` total** | **132** | under `data/knowledge/` |
| **Global `units.jsonl`** | **114** | `data/knowledge/index/units.jsonl` |
| Retrieve vectors | **114** · dim **512** | `data/retrieve/manifest.json` |
| SETV producer `manifest_v0.jsonl` | **48** | +3 AAPL snapshot rows |

Archive character: forming **SETV State Archive** (Family + Instance + Evidence), not scattered files.  
`132` disk cards vs `114` indexed units is expected (non-unit / nested / not-yet-indexed docs); growth is **not** a KPI.

---

## 3. 未落地（仅此表 · intentional）

| ID | Class | Requirement | Why unlanded | Owner | Gate |
|----|-------|-------------|--------------|-------|------|
| HOLD-CHUNK-RAG | HOLD **H4** | Chunk-RAG / chat product | Frozen · whole-KO retrieve = doctrine · KO = SoT | KF | Owner `THAW HOLD-CHUNK-RAG` + doctrine amend + KO-insufficiency evidence · [`HOLD_CHUNK_RAG_H4_NAIL_20260828.md`](HOLD_CHUNK_RAG_H4_NAIL_20260828.md) |
| HOLD-SETV-SCOPE | HOLD | New SETV axes / metrics / scopes / INST types | Consume-first after AAPL · **Owner Interpret nailed** | SETV | Usage must prove **D · Representation** · producer `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |
| DEFER-MANIM-BEATS | DEFER | Wire derive `manim_beats` → Expression | Renderer≠compiler · keep Semantic→Beats→Renderer | — | Consume evidence that Pillow/current beats cannot express needed process |
| REF-MATH-TO-MANIM | OUT | Math To Manim product integration | External renderer reference only | — | **Never a slice** unless Owner reopens after cost/evidence bar |

**Already closed this thaw (not unlanded):**

| ID | Closed | Evidence |
|----|--------|----------|
| HOLD-YIYUAN | ✅ H1a+b+c | family API · compose selected · layout persist |
| HOLD-MANIM | ✅ H2a+b+c | renderer chain · **not** LLM→`scene.py` |
| HOLD-GNN | ✅ H3a+b+c | `gnn_offline` · shadow · opt-in boost |
| WEB-UI-BROWSER | ✅ v0.6 | browser-first · `WEB_UI_v0.md` · maintain delete |

**No open A / B / C / Ops tickets.** Residual HOLD = **H4** (+ SETV scope). Soft DEFER = manim_beats wire. Explicit OUT = Math To Manim product path.

Thaw progress: **H1 ✅ → H2 ✅ → H3 ✅ → H4 ⏸**.

---

## 4. Recently closed gaps (for audit trail)

| ID | Class | Closed how | Evidence |
|----|-------|------------|----------|
| GAP-AAPL-CARD | A | SETV stamped INST + sidecars · KF cite | [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md) · [`PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md`](../interop/PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md) |
| GAP-INDEX-SHALLOW | B | `rebuild_index` → `rglob` | [`USAGE_EVIDENCE_B_20260828.md`](USAGE_EVIDENCE_B_20260828.md) |
| GAP-SOFT-GRAPH | C | edge hygiene + affinity gate | [`USAGE_EVIDENCE_C_20260828.md`](USAGE_EVIDENCE_C_20260828.md) |
| GAP-OPS-RUNBOOK | Ops | thin runbook | [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) |
| HOLD-YIYUAN | H1 | multi-card + select compose + layout persist | `layout_persist.py` · `test_multi_card_h1a` / `test_layout_persist_h1c` |
| HOLD-MANIM | H2a+b+c | Manim + golden + Matplotlib second renderer | `render_manim.py` · `render_mpl.py` · `test_manim_h2*` |
| HOLD-GNN | H3 | offline diffusion + shadow + opt-in blend | `gnn_offline.py` · `test_gnn_h3.py` |
| WEB-UI-PIVOT | Product | browser-first local Web UI | [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) · `ui_version` 0.6.0 · `test_ui_shell.py` |
| NAIL-RENDERER-REF | Posture | Math To Manim = ref only | [`RENDERER_REF_MATH_TO_MANIM_20260828.md`](RENDERER_REF_MATH_TO_MANIM_20260828.md) |
| NAIL-SETV-SCOPE | Posture | Owner HOLD-SETV-SCOPE | `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |

---

## 5. SETV ↔ KF contract posture

| SETV word | KF action | Status |
|-----------|-----------|--------|
| ACK CONSUMER READY | Cite Cards | ✅ |
| OPEN SCHEMA | Prefer sidecars | ✅ |
| OPEN KF INGEST | `setv ingest` manifest | ✅ (48 lines on producer) |
| HOLD on runtime bind / Measurement amend | No mutate / no receipt | ✅ held |
| AAPL INST stamps | Wait producer | ✅ closed |
| NEXT = HOLD | No SETV scope expansion ask | ✅ nailed · [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) · producer `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |

Expression nail (KF-internal):

\[
\boxed{
\mathrm{KO}
\rightarrow
\mathrm{ExpressionObject}
\rightarrow
\mathrm{Beats}
\rightarrow
\mathrm{Renderer}
\rightarrow
\mathrm{Artifact}
}
\]

Renderer follows Expression. Not Semantic → LLM → Manim code.

---

## 6. What *not* to do next

- Expand SETV research scope because KF “wants more classes”
- Invent `SETV-INST-*` inside KF
- Promote restricted → secret (blocks normal retrieve)
- Unfreeze H4 without Owner word + doctrine amend
- Treat “114 units” / “132 md” as a growth KPI — growth follows proven **D** gaps only
- Bundle H4 with unrelated expression work
- Chase **Math To Manim** / LLM→`scene.py` / bend Expression around Manim
- Wire derive `manim_beats` without consume evidence

---

## 7. Recommended next (ordered)

1. **Consume** — use Family + Instance + Evidence in KF; observe what questions fail  
2. On each failure → classify **A / B / C / D** before coding or asking SETV  
3. Only **D · Representation** re-opens SETV evolution discussion  
4. Optional tech: Owner `THAW HOLD-CHUNK-RAG` + doctrine amend — see [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md)  
5. Optional hygiene: commit local Web UI pivot + renderer-ref note when Owner wants git sync  

Program board: [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) · thaw: [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md) · Web UI: [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) · renderer ref: [`RENDERER_REF_MATH_TO_MANIM_20260828.md`](RENDERER_REF_MATH_TO_MANIM_20260828.md) · ops: [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) · maintain: [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md)

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
| H1c / H2c open | **LANDED** |
| Windows desktop-default UI | **Web UI browser-first v0.6** · `WINDOWS_UI_v0` superseded |
| Manim missing / need Math To Manim | **H2 renderer exists** · Math To Manim = **ref only / no product path** |
| Next = more SETV ingest | **NEXT = HOLD** on SETV scope · consume archive |
| Workspace “uncommitted H1–H3 on 73d8d33” | Head **b2fb214** pushed · local Web UI + renderer nail uncommitted |

Docs of record: this file · `HANDOFF_20260827.md` §10 · `POSTURE_NAIL_20260828.md` · `HOLD_THAW_SCHEDULE_V0.md` · `WEB_UI_v0.md` · `RENDERER_REF_MATH_TO_MANIM_20260828.md` · `CONTENT_FILL_20260828.md`
