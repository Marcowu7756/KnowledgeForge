# Action Plan — SETV Findings (Easy → Hard)

```yaml
plan_id: KF-AP-20260827
source: docs/audit/SETV_AUDIT_20260827.md
rule: 先易后难；未关闭项不宣称 FIXED；HOLD 项不启动
```

## Already closed (before this plan)

| ID | Item | Status |
| --- | --- | --- |
| F-P0-01 | gitignore / runtime dirs | ✅ DONE |
| F-P0-02 | GitHub remote + push | ✅ DONE |

## Ordered backlog

| # | Finding | Difficulty | Action | Status |
| --- | --- | --- | --- | --- |
| **A1** | F-P2-03 derive Manim 易误读 | 易 | DEFER / `not_wired_to_expression` | ✅ DONE |
| **A2** | F-P1-02 compose 缺字段 | 易 | `validate_compose_payload` → `FAILED.md` | ✅ DONE |
| **A3** | F-P1-03 index limit 截断 | 易-中 | 元数据丰富度优先后再 limit | ✅ DONE |
| **A4** | F-P1-01 graph boost 噪音 | 中 | boost 仅 semantic pool + query overlap | ✅ DONE |
| **A5** | F-P2-02 EmbeddingRef 未落盘 | 中 | sidecar + package KO write-back | ✅ DONE |
| **A6** | F-P2-04 ASR 路径不一 | 中 | voice / video / youtube → `ingest.asr` | ✅ DONE |
| **A7** | F-P2-01 无集成测 | 难 | `tests/integration` + `@pytest.mark.slow` | ✅ DONE |
| **A8** | F-P1-04 跨卡边偏软 | 难 | vs 解析 + inter-KO prerequisite + `contrast_cross_ko` 聚类 | ✅ DONE |
| **A9** | F-P3-01 控制台乱码 | 观察 | README UTF-8 终端说明 | ✅ DONE |
| — | F-P3-02 UI/多卡/renderer | HOLD→部分解冻 | Windows UI v0 scaffold（一源多卡仍 HOLD） | 🟡 UI shell ACTIVE |

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
# → unit green; 2 slow skipped unless KF_RUN_SLOW=1
```

## Next (optional, not this plan)

- Real Whisper wav fixture under `tests/integration/` — ✅ present
- Package-level EmbeddingRef write-back — ✅ `retrieve index` updates `data/packages/*/knowledge_object.json`
