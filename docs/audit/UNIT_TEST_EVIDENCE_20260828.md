# Unit Test Evidence — Scenario Plays · 2026-08-28

```yaml
run_id: KF-UT-20260828
commit: c959eb8a422d83d6e73c44fbca7f8dde07901e1e
branch: main
remote: https://github.com/Marcowu7756/KnowledgeForge.git
pushed: true  # df32279..c959eb8 → origin/main
command: .\.venv\Scripts\python.exe -m pytest tests --ignore=tests/integration -ra --tb=line
result: 110 passed in 1.40s
slow_gate: 5 skipped (KF_RUN_SLOW unset)
raw_log: docs/audit/UNIT_TEST_RUN_20260828.txt
```

## Verdict

**All scenario unit tests green.** No failing cases in the four core plays, SETV adapters, access/export lanes, or UI shell. Slow integration remains gated (expected skip, not a defect).

## Per-play matrix

| Play | File(s) | Collected | Result | Notes / Evidence |
|------|---------|-----------|--------|------------------|
| **一 · 获取** | `tests/acquire/test_ingest_sources.py` | 11 | PASS | 本地 txt / 清洗切分 / 音频门禁（不跑 Whisper） |
| **一 · 生态 taxonomy** | `tests/acquire/test_ecosystem_taxonomy.py` | 12 | PASS | SETV/Factor/AShare 路径与分类 |
| **一 · SETV Snapshot** | `tests/acquire/test_setv_snapshot.py` | 5 | PASS | CARD → `memory_kind=state` · YAML roundtrip |
| **一 · SETV Evolution/Family** | `tests/acquire/test_setv_evolution_family.py` | 7 | PASS | L-XS / SETV-FAM / L-SA / kernel Evidence |
| **二 · 沉淀** | `tests/distill/test_knowledge_settle.py` | 11 | PASS | KU / KO / Expression / Harness |
| **三 · 定位** | `tests/locate/test_retrieve_compose.py` | 7 | PASS | KO embed 文本 · 向量索引 · Compose（无 LLM） |
| **三 · AccessPolicy** | `tests/locate/test_access_control.py` | 12 | PASS | restricted compose/export gates · dual-track |
| **三 · Export lanes** | `tests/locate/test_export_lanes.py` | 6 | PASS | general vs proprietary lane ceilings |
| **三 · UI shell** | `tests/locate/test_ui_shell.py` | 2 | PASS | health / version `0.4.0` |
| **三 · UI jobs/preview** | `tests/locate/test_ui_jobs_preview.py` | 4 | PASS | |
| **三 · Action plan fixes** | `tests/locate/test_action_plan_fixes.py` | 8 | PASS | |
| **三 · Embed write-back** | `tests/locate/test_embed_writeback.py` | 7 | PASS | |
| **四 · 重组** | `tests/reorganize/test_reconstruct.py` | 11 | PASS | Relation / Graph / Evolution / Views |
| **四 · Contrast cluster** | `tests/reorganize/test_contrast_cluster.py` | 6 | PASS | |
| **四 · Collect priority** | `tests/reorganize/test_collect_priority.py` | 1 | PASS | |
| **Slow smoke** | `tests/integration/test_slow_smoke.py` | 5 | SKIP | `KF_RUN_SLOW=1` 未设 · 非失败 |

**Total unit (excl. integration): 110 passed.**

## Problems found this run

| ID | Severity | Finding | Evidence | Disposition |
|----|----------|---------|----------|-------------|
| — | — | **None in unit suite** | `110 passed in 1.40s` · `UNIT_TEST_RUN_20260828.txt` | closed |
| OBS-01 | info | Slow BGE/Whisper smoke not executed | `SKIPPED … set KF_RUN_SLOW=1` ×5 | intentional gate · not a regression |
| OBS-02 | info | Console encoding shows mojibake for `·` / 中文 in PowerShell CLI prints | prior F-P3-01; pytest UTF-8 log file is clean | observe only · README already notes UTF-8 terminal |
| OBS-03 | info | Local smoke KO writes under `data/knowledge/restricted/setv/{families,evolutions}/` are gitignored | by design (runtime artifacts) | no commit of ingested cites |

## Pre-push known gaps (not unit failures)

These are product backlog items, **not** failing tests:

- HOLD residual: **H4 chunk-RAG** · SETV new axes/metrics/scopes
- ~~HOLD 一源多卡 · Manim · GNN~~ → LANDED (see `HOLD_THAW_SCHEDULE_V0.md`)
- ~~Audit watermark / encrypt~~ → LANDED `.kfexport`
- Maintain: delete-only SOP — `docs/ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md`

## Reproduce

```powershell
cd D:\KnowledgeForge
git checkout main
git pull
.\.venv\Scripts\python.exe -m pytest tests --ignore=tests/integration -ra --tb=line
# optional slow:
# $env:KF_RUN_SLOW=1; .\.venv\Scripts\python.exe -m pytest tests/integration -q
```

## GitHub

- Commit: [`c959eb8`](https://github.com/Marcowu7756/KnowledgeForge/commit/c959eb8a422d83d6e73c44fbca7f8dde07901e1e)
- Message: *Land SETV artifact adapters, AccessPolicy lanes, and UI export gates.*
