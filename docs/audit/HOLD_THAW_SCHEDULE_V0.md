# HOLD Thaw Schedule v0 — 一源多卡 / Manim / GNN / chunk-RAG

```yaml
status: H1a+b+c + H2a+b+c + H3a/b/c LANDED · H4 still HOLD
as_of: 2026-08-28
thaw: … · 「H2c」→ Matplotlib second renderer (mpl_v0)
```

\[
\boxed{\mathrm{H1a{+}H1b{+}H1c\ LANDED}}
\qquad
\boxed{\mathrm{H2a{+}H2b{+}H2c\ LANDED}}
\qquad
\boxed{\mathrm{H3\ LANDED}}
\qquad
\boxed{\mathrm{H4\ HOLD}}
\]

---

## Ordered thaw

| Slot | ID | Item | Status |
|------|-----|------|--------|
| **H1** | HOLD-YIYUAN | 一源多卡 | ✅ **H1a+b+c LANDED** |
| **H2** | HOLD-MANIM | Manim 实渲染 | ✅ **H2a+b+c LANDED** |
| **H3** | HOLD-GNN | GNN | ✅ H3a+b+c |
| **H4** | HOLD-CHUNK-RAG | chunk-RAG | ⏸ HOLD |

```text
H1 ✅ → H2 ✅ → H3 ✅ → H4 ⏸
```

### H1 landing evidence

| Slice | Proof |
|-------|-------|
| H1a | `family_view.py` · `GET /api/family/{id}` · multi-card UI |
| H1b | `compose_from_paths` · `source_paths` ·「Compose 所选」 |
| H1c | `layout_persist.py` · `GET/PUT/DELETE /api/ui/layout/multi-card` · `data/ui/multi_card_layout.json` · UI restore |

### H2 landing evidence

| Slice | Proof |
|-------|-------|
| H2a | `render_manim.py` · `--renderer` · `manim_wired` |
| H2b | frozen schema `golden_h2b.py` · `tests/locate/test_manim_h2b_golden.py` · `animate --golden` |
| H2c | `render_mpl.py` · `mpl_v0` · `--renderer mpl` · auto: manim→mpl→pillow |

### H3 landing evidence

| Slice | Proof |
|-------|-------|
| H3a | `app/reconstruct/gnn_offline.py` · symmetric normalized diffusion |
| H3b | `gnn eval --graph DIR` → `gnn_shadow_scores.json` |
| H3c | `KF_GNN_BOOST=1` + `--gnn-shadow` / beside graph · else **no blend** |
| Test | `tests/reorganize/test_gnn_h3.py` |
| Smoke | reconstruct dir → 80 KO nodes · shadow written |

**Default retrieve unchanged** without `KF_GNN_BOOST=1`.

---

## Per-item schedule cards

### H1 · 一源多卡 (`HOLD-YIYUAN`) — H1a+b+c done

| Field | Content |
|-------|---------|
| Meaning | One capture/source → multiple settled KOs shown together (family / multi-TF / multi-view) |
| Status | **H1a+H1b+H1c LANDED** |
| Unfreeze | Owner `开始落地吧` + `H1b` + `H1c` (2026-08-28) |
| H1c | persist family id · selected paths · compose fields · no ontology invent |
| Out of scope still | Manim editor · chunk chat · inventing KOs from layout |

### H2 · Manim 实渲染 (`HOLD-MANIM`) — H2a+b+c done

| Field | Content |
|-------|---------|
| Meaning | Real Manim (or approved renderer) produces GIF/MP4 from expression beats |
| Status | **H2a+H2b+H2c LANDED** |
| Unfreeze | Owner `H2 Manim` + `H2b` + `H2c` (2026-08-28) |
| H2b | frozen golden · `animate --golden` · soft GIF bounds (not byte-exact) |
| H2c | Matplotlib `mpl_v0` · CLI/`KF_ANIMATE_RENDERER=mpl` · auto fallback after Manim |
| Still DEFER | Derive `manim_beats` → expression (remain `not_wired_to_expression`) |
| External ref | Math To Manim = **renderer reference only** · no product path · [`RENDERER_REF_MATH_TO_MANIM_20260828.md`](RENDERER_REF_MATH_TO_MANIM_20260828.md) |
| Out of scope | Full scene IDE · cloud render farm · LLM→`scene.py` |

### H3 · GNN (`HOLD-GNN`) — H3a+b+c done

| Field | Content |
|-------|---------|
| Meaning | Learned / propagated scores over ConceptGraph (beyond rule edges) |
| Status | **H3a+b+c LANDED** · production default remains shadow-only |
| Unfreeze | Owner `H3` (2026-08-28) |
| CLI | `main.py gnn eval --graph DIR` |
| Blend | only `KF_GNN_BOOST=1` |
| Out of scope | torch-geometric zoo · replacing producer stamps |

### H4 · chunk-RAG (`HOLD-CHUNK-RAG`)

| Field | Content |
|-------|---------|
| Meaning | Chunk-level retrieval / chat-window productization |
| Why HOLD now | Doctrine: **retrieve unit = whole KO**; UI non-goal “not a second RAG chat” |
| Unfreeze trigger | Owner **explicitly** amends doctrine; and KO-level retrieve proven insufficient for a class of asks (with evidence) |
| Phase plan | **H4a** design note (unit dualism + audit) · **H4b** chunk index sidecar · **H4c** `retrieve --unit chunk` opt-in · default KO unchanged |
| Depends on | Doctrine amendment doc · access audit for chunk path · no silent default flip |
| Out of scope | Replacing KO compose with raw chunk paste as system of record |
| Owner thaw line | `THAW HOLD-CHUNK-RAG H4a` + doctrine amendment pointer |
| Doctrine nail | [`HOLD_CHUNK_RAG_H4_NAIL_20260828.md`](HOLD_CHUNK_RAG_H4_NAIL_20260828.md) · KO = SoT · chunk opt-in only · SETV no action |

---

## Calendar posture (relative, not calendar dates)

| Window | Focus | HOLD actions |
|--------|-------|--------------|
| **Now** | H1–H3 complete · continue consume | Residual: **H4** only (doctrine) |
| **After expression review** | — | H2c already landed (`mpl_v0`) |
| **After sustained C/D residuals** | Graph research review | H3 already landed · revisit boost |
| **Only on doctrine change** | Dual retrieve design | Maybe **H4a** |

No wall-clock dates — slots advance on **evidence + Owner thaw**, not sprint pressure.

---

## Anti-patterns

- Thawing H4 because “RAG is industry default”
- Starting H3 because graph “looks cool” after AAPL success
- Bundling H1+H2+H3 in one PR
- Treating this schedule as a commitment to ship all four

---

## Cross-links

- Nail: [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md)
- Matrix: [`REQ_VS_LANDED_20260828.md`](REQ_VS_LANDED_20260828.md)
- UI non-goals: [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md)
- Audit origin: [`SETV_AUDIT_20260827.md`](SETV_AUDIT_20260827.md) F-P2-03 / F-P3-02
