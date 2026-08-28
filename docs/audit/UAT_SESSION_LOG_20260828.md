# Consume UAT Session Log — 2026-08-28

```yaml
uat_id: KF-UAT-CONSUME-V0
charter: UAT_CONSUME_V0.md
started: 2026-08-28
finished: 2026-08-28
operator: KF agent on Owner machine
status: COMPLETE
verdict: PASS_WITH_ISSUES
head: d5039da+ (docs/UAT this session)
```

Machine dump (local, not required in git): `data/_uat_u1_results.json` · `data/_uat_u3.json`

---

## U0 · Environment gate

| Check | Command / action | Result | Notes |
|-------|------------------|--------|-------|
| Slow smoke | `KF_RUN_SLOW=1 pytest tests/integration/test_slow_smoke.py -q` | **PASS** 5/5 | OBS-1 torch.jit warnings only |
| Units ≈ vectors | count `units.jsonl` vs `manifest.count` | **PASS** 114 = 114 | |
| AAPL retrieve smoke | `retrieve query "AAPL H4 State Snapshot" --lane proprietary --top 5` | **PASS** | Top-3 = AAPL W / H4 / D INST |
| UI bind | uvicorn `create_app` → `GET /api/health` | **PASS** | `ui_version=0.6.0` · `features.web_ui=true` · stages×5 |

**U0 verdict:** **PASS**

---

## U1 · Archive Consume

| ID | Query | Lane | Top-K (ids / titles) | Usable? | Class | Reason |
|----|-------|------|----------------------|---------|-------|--------|
| Q01 | AAPL H4 State Snapshot | proprietary | W · H4 · D AAPL INST (0.67+) | **yes** | usable | Top-3 AAPL INST closed loop |
| Q02 | AAPL W State Snapshot 2024 | proprietary | W · D · H4 AAPL | **yes** | usable | W ranked #1 |
| Q03 | AAPL D State Snapshot | proprietary | D · W · H4 AAPL | **yes** | usable | D ranked #1 |
| Q04 | GOLD H4 State Snapshot | proprietary | GOLD-H4 · SILVER · COPPER | **yes** | usable | GOLD INST #1 |
| Q05 | USDJPY H4 State Snapshot | proprietary | USDJPY-H4-2025 · 2024-2026 | **yes** | usable | USDJPY INST top |
| Q06 | EURUSD H4 2024 | proprietary | EURUSD evolution + snap 2024-2026 | **yes** | usable | EURUSD related top |
| Q07 | SETV-FAM-AAPL-TV-2024-WDH4 | proprietary | Family AAPL #1 + W/D/H4 snaps | **yes** | usable | Family resolvable |
| Q08 | US10Y USDJPY observation family | proprietary | FAM-OBS-US10Y-USDJPY #1 | **yes** | usable | OBS family hit |
| Q09 | SETV state contract measurement TS1 | proprietary | TS1 amendment · minimal invariant | **yes** | usable | Measurement layer |
| Q10 | USDJPY H4 experiment T1 evidence | proprietary | EXP-USDJPY-H4-2025-T1 #1 | **yes** | usable | Experiment layer |
| Q11 | SETV uncertainty language | proprietary | OWNER_CONFIRM · DESIGN · HOLD | **yes** | usable | Uncertainty layer |
| Q12 | FactorLib DLL Spec | proprietary | FactorLib readme · dll_spec | **yes** | usable | Cross-source FactorLib |
| Q13 | AShare runtime design | proprietary | design_ashare_runtime_v01 #1 | **yes** | usable | Cross-source AShareLib |
| Q14 | AAPL H4 State Snapshot | general | public/methodology only (≤0.49) | **yes** | usable | **Negative PASS** — no restricted leak |
| Q15 | Martian potato futures regime 2099 | proprietary | weak regime/english/EURUSD (~0.44–0.52) | **yes** | usable | **Negative PASS** — unrelated / keyword bleed only |

### Family compose (Q07+)

| Check | Result | Notes |
|-------|--------|-------|
| Family members W/D/H4 selectable | **PASS** | `GET /api/family/SETV-FAM-AAPL-TV-2024-WDH4` → INST W · D · H4 |
| Layout persist H1c | **PASS** | PUT/GET `artifact_id` + 3 `selected_paths` roundtrip |

### UI recheck (≥4)

| ID | UI stage 检索 | Match CLI? | Notes |
|----|---------------|------------|-------|
| Q01 | PASS | yes | Top AAPL W/H4/D |
| Q04 | PASS | yes | GOLD #1 |
| Q07 | PASS | yes | Family #1 |
| Q12 | PASS | yes | FactorLib top |

**U1 verdict:** **PASS** · 15/15 usable · A=0 B=0 C=0 D=0

---

## U2 · Live thin smoke

| Path | Action | Result | Blocker / notes |
|------|--------|--------|-----------------|
| Twitter single | CLI + UI capture NASA status | **ISSUE** | CLI: connection reset; UI 400 `tweet not found or not public` — syndication/network · not Archive fail |
| Local file settle | `main.py file` fixture md | **PASS** | → `data/knowledge/uat_local_settle_md.md` |
| LLM distill | `compile --from-card` + Ollama `qwen2.5:14b` | **PASS** | package `20260828T122334Z_97e25cd0` |
| Express animate | `animate --fast --renderer auto` AAPL H4 | **PASS** | `renderer=manim_v0` · GIF written |
| Renderer golden/auto | `animate --golden` | **PASS** | manim_v0 · H2b golden GIF |
| TTS narrate | `compile --narrate --fast` | **ISSUE** | expression ok · GIF ok · **audio skipped** (schema only, no wav) |

**U2 verdict:** **PASS_WITH_ISSUES** · no Archive/integration blocker; live Twitter + TTS wav residual

---

## U3 · Web UI five stages

| Stage | Walked? | OK? | Notes |
|-------|---------|-----|-------|
| 获取 Capture | API `/api/capture` file | **yes** | ok=True |
| 沉淀 Distill | API `/api/compile` | **yes** | package returned |
| 重组 Reconstruct | API `/api/reconstruct` from_index | **yes** | ok=True |
| 检索 Retrieve | API `/api/retrieve` | **yes** | hits=3 proprietary |
| 表达 Express | API `/api/compose` lecture | **yes** | draft + output_dir |
| Job fail readable | async capture missing file | **yes** | `status=error` · path message |
| Layout persist | PUT/GET multi-card | **yes** | see U1 |

**U3 verdict:** **PASS** (API-level five-stage; browser shell health already U0)

---

## U4 · Day-2 ops

| Check | Result | Notes |
|-------|--------|-------|
| Access audit events present | **PASS** | `data/audit/access/20260828.jsonl` · **160** events · retrieve/compose trails |
| `.kfexport` encrypt + decrypt | **PASS** | AAPL H4 → `.kfexport` → `_uat_decrypt_aapl_h4.md` 2681 bytes |
| `knowledge delete --dry-run` | **PASS** | fixture card planned · maintain audit written |

**U4 verdict:** **PASS**

---

## U5 · Disposition board

| Metric | Value |
|--------|-------|
| Usable rows | **15 / 15** |
| A count | **0** |
| B count | **0** |
| C count | **0** |
| D count | **0** |
| Negative controls (Q14/Q15) | **both PASS** |

### Tickets

| Class | ID / summary | Owner | Action |
|-------|--------------|-------|--------|
| ops/live | Twitter syndication unreliable in this session | KF ops | retry later / Bearer timeline if needed · **not** SETV scope |
| ops/express | Narrate path skips audio wav (schema only) | KF | observe · optional TTS env check · **not** H4 thaw |
| — | No A/B/C/D Archive gaps from fixed bank | — | **do not** expand SETV scope |

### Owner sign-off

```text
Composite:   PASS_WITH_ISSUES
Archive:     PASS     (15/15 · A/B/C/D=0 · lifecycle U4)
Ops:         ISSUE     (Twitter syndication · TTS wav) — not Archive
Signed:      Owner interpret 2026-08-28
             OWNER_INTERPRET_UAT_SPLIT_20260828.md
Next:        business-side consumption
Forbidden:  Matrix expand · THAW H4 · SETV scope expand from UAT
```

**U5 status:** **COMPLETE** · Owner split nailed

---

## Pointers updated

- [`OWNER_INTERPRET_UAT_SPLIT_20260828.md`](OWNER_INTERPRET_UAT_SPLIT_20260828.md)
- [`UAT_CONSUME_V0.md`](UAT_CONSUME_V0.md)
- [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md)
- [`HANDOFF_20260827.md`](../HANDOFF_20260827.md) §10
