# Consume UAT v0 — KnowledgeForge

```yaml
uat_id: KF-UAT-CONSUME-V0
as_of: 2026-08-28
status: COMPLETE · PASS_WITH_ISSUES
split: Archive PASS · Ops ISSUE
authority: Owner
next_after: business-side consumption · HOLD H4/SCOPE
session_log: UAT_SESSION_LOG_20260828.md
owner_interpret: OWNER_INTERPRET_UAT_SPLIT_20260828.md
```

\[
\boxed{\mathrm{Integration\ SETTLED}\neq\mathrm{Product\ sign\text{-}off}}
\qquad
\boxed{\mathrm{UAT = Consume\ Archive}}
\qquad
\boxed{\mathrm{only\ D}\rightarrow\mathrm{SETV}}
\]

## 1. Judgment (nail)

| Layer | Status | Meaning |
|-------|--------|---------|
| Dev / Unit | green | shippable engineering |
| Integration | **SETTLED 19/19** | settle→express wiring green |
| **Consume UAT** | this document | Archive value acceptance |
| Product completeness / H4 chat | non-goal | not a UAT gate |

**Engineering close is real.** Doable reqs LANDED; OBS≠blocker; residual HOLD (H4 / SETV-SCOPE / DEFER-MANIM-BEATS) is intentional.

**Product UAT is not claimed by 19/19.** Matrix + slow smoke do **not** prove live network, real LLM, real TTS, Web UI E2E, or “archive answers real questions.”

**This UAT** = Owner-driven **Consume** of the forming SETV State Archive (Family · Instance · Evidence) via CLI + Web UI, with A/B/C/D gap classification.

Cross-links: [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) · [`WORK_SUMMARY_20260828.md`](WORK_SUMMARY_20260828.md) · [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) · **消费 SOP** [`CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md) · [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) · [`PHASE_CONTENT_FILL_20260828.md`](PHASE_CONTENT_FILL_20260828.md)

---

## 2. Pass criteria (all required)

1. **U0** environment gate PASS
2. **≥12** fixed-bank questions executed (retrieve ± reconstruct / family / express); each row has usable / A / B / C / D
3. **Web UI** five stages each walked once (获取→沉淀→重组→检索→表达)
4. **U2** live thin smoke: no blocking failure; credential-known limits logged OK
5. **U4** Day-2: access audit events present · `.kfexport` roundtrip · `knowledge delete --dry-run` works
6. Owner sign-off on session log: `PASS` | `PASS_WITH_ISSUES` | `FAIL` · only **D** re-enters SETV

**Not fail conditions:** OBS-1 · H4 frozen · Math-To-Manim absent · non-Cartesian matrix · SETV axes not expanded.

---

## 3. Gap taxonomy

| Class | Meaning | Owner | Disposition |
|-------|---------|-------|-------------|
| **usable** | Question answered from Top-K / family / express | — | count as win |
| **A · Producer Gap** | Artifact never produced | SETV | ticket · **no** instant scope expand |
| **B · Knowledge Gap** | Artifact exists; KF settle/index wrong | KF | fix ingest/index |
| **C · Relation Gap** | Both exist; no edge | KF | reconstruct / relation |
| **D · Representation Gap** | Settled but still unanswerable | SETV research | **only** class that returns to SETV evolution |

Do **not** label everything “SETV missing data.” Classify first.

---

## 4. Bans (UAT window)

- No Matrix expansion / new Integration slice for PASS count
- No `THAW HOLD-CHUNK-RAG` · no SETV new axes / metrics / INST types
- No Math-To-Manim / `manim_beats` wire as UAT items
- OBS-1 is not a blocker
- Do not invent `SETV-INST-*` in KF
- Do not rewrite the question bank mid-run to force PASS

---

## 5. Stages

### U0 · Environment gate

```powershell
cd D:\KnowledgeForge
$env:KF_RUN_SLOW = "1"
.\.venv\Scripts\python.exe -m pytest tests/integration/test_slow_smoke.py -q --tb=line
.\.venv\Scripts\python.exe -c "import json; from pathlib import Path; u=sum(1 for _ in open('data/knowledge/index/units.jsonl',encoding='utf-8')); m=json.loads(Path('data/retrieve/manifest.json').read_text(encoding='utf-8')); print('units',u,'vectors',m['count'])"
.\.venv\Scripts\python.exe main.py retrieve query "AAPL H4 State Snapshot" --lane proprietary --top 5
# UI: .\.venv\Scripts\python.exe main.py ui   → http://127.0.0.1:8765 health ok
```

Expect: slow smoke green · units ≈ vectors ≈ **114** · Top-3 AAPL W/H4/D INST · UI binds localhost.

**Gate fail → stop UAT; fix env; do not mark Archive FAIL.**

### U1 · Archive Consume (fixed bank)

Run **exactly** the bank in §6. CLI primary; re-check ≥4 rows in Web UI 检索.

Per row log: query · lane · Top-5 · usable? · class · one-line reason.

### U2 · Live thin smoke (19/19 gaps)

One success path each (or logged blocker):

| Path | Minimum action |
|------|----------------|
| Twitter single | public status URL · CLI or UI (no Bearer) |
| Local file | one md/txt settle (pdf/image if available) |
| LLM distill | one `compile` or `ecosystem` with real Ollama if present |
| Express | one card `animate --fast` |
| Renderer | `animate --golden` **or** auto chain lands manim/mpl/pillow |

Do **not** expand Integration matrix for this.

### U3 · Web UI five stages

Checkbox against [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) Acceptance: Capture · Distill · Reconstruct · Retrieve · Express. Jobs readable on fail · layout persist OK. Non-goals: React SPA · LAN · chunk-RAG chat.

### U4 · Day-2 ops

Per [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) §5–7: access audit tail · `.kfexport` encrypt/decrypt · `knowledge delete --dry-run`.

### U5 · Disposition + sign-off

Fill session log board: usable % · A/B/C/D counts · Owner verdict · next actions limited to fix B/C · producer A · SETV only for D.

Update pointers: [`HANDOFF_20260827.md`](../HANDOFF_20260827.md) §10 · [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md).

---

## 6. Fixed question bank (≥12)

Bank locked before run. Do not swap mid-session.

| ID | Query | Lane | Expect (usable if…) |
|----|-------|------|---------------------|
| Q01 | `AAPL H4 State Snapshot` | proprietary | Top includes AAPL H4 / W / D INST snaps |
| Q02 | `AAPL W State Snapshot 2024` | proprietary | AAPL W INST near top |
| Q03 | `AAPL D State Snapshot` | proprietary | AAPL D INST near top |
| Q04 | `GOLD H4 State Snapshot` | proprietary | GOLD H4 INST snap present |
| Q05 | `USDJPY H4 State Snapshot` | proprietary | USDJPY H4 INST snap(s) present |
| Q06 | `EURUSD H4 2024` | proprietary | EURUSD INST / family related |
| Q07 | `SETV-FAM-AAPL-TV-2024-WDH4` | proprietary | Family card / members resolvable |
| Q08 | `US10Y USDJPY observation family` | proprietary | OBS family or US10Y/USDJPY snaps |
| Q09 | `SETV state contract measurement TS1` | proprietary | measurement card in Top-K |
| Q10 | `USDJPY H4 experiment T1 evidence` | proprietary | experiment card in Top-K |
| Q11 | `SETV uncertainty language` | proprietary | uncertainty card in Top-K |
| Q12 | `FactorLib DLL Spec` | proprietary | FactorLib conclusion card |
| Q13 | `AShare runtime design` | proprietary | AShareLib design card |
| Q14 | `AAPL H4 State Snapshot` | **general** | **Negative:** must **not** leak restricted AAPL INST as if general |
| Q15 | `Martian potato futures regime 2099` | proprietary | **Negative:** empty or weak / unrelated Top-K |

**UI recheck (minimum 4):** Q01 · Q04 · Q07 · Q12.

**Family compose (U1 extension):** after Q07, open family multi-card for `SETV-FAM-AAPL-TV-2024-WDH4` (CLI family view or Web UI) · confirm W/D/H4 members selectable.

---

## 7. Operator one-liner

> Integration 已 SETTLED · Consume UAT = 用 Archive 答真问题并分 A/B/C/D · 仅 D 回 SETV · 不扩 Matrix / 不解冻 H4。

## 8. Session result (2026-08-28)

| Gate | Result |
|------|--------|
| U0–U4 | PASS (U2 ops residuals) |
| U1 bank | **15/15 usable** · A/B/C/D = 0 · negatives PASS |
| Composite | `PASS_WITH_ISSUES` |
| **Archive / Knowledge Core** | **PASS** |
| **Operations** | **ISSUE** · Twitter syndication · TTS wav |
| Owner interpret | [`OWNER_INTERPRET_UAT_SPLIT_20260828.md`](OWNER_INTERPRET_UAT_SPLIT_20260828.md) |
| NEXT | business-side consumption · H4 HOLD · SETV scope HOLD |

**ISSUES must not be read as Archive defect.**

**Follow-on (OPEN):** **入口** [`UAT_ENTRY_V0.md`](UAT_ENTRY_V0.md) · 用户业务消费 [`UAT_USER_CONSUME_V0.md`](UAT_USER_CONSUME_V0.md) · [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md) · SOP [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md)。