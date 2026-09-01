# KF · Digital Self Skill unit consume — 2026-09-01

```yaml
doc_id: KF-AUDIT-DS-SKILL-UNIT-20260901
as_of: 2026-09-01
surface: KF consume only (main.py ds / app.interop.digital_self)
producer: D:\DigitalSelf
verdict: UNIT_FAST = 29 passed · S02_LIVE = 2 passed · ISSUES = DS-I1 HIGH (deposit/transfer L4 gap)
```

## Scope

按 [`DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md) / catalog 暴露的 Skills **逐一**在 KF 端测：

| Skill | 测什么 |
|-------|--------|
| catalog / `ds list` | 五 Skill 在目录 |
| **S00** | useful / important / garbage / alias |
| **S06** | YouTube 计划 · 通用 browser · `--live` 拒 · 缺 `--intent` |
| **S15** | setv/mt5/ashare 计划 · L4 · `--live` 拒 · deposit/transfer 缺口 |
| **S16** | W0 · publish/W4 拒 · FACT 门 · alias |
| **S02** | 缺 `-o` · live zh/en（`KF_RUN_SLOW=1`） |

不测 / 不做：Playwright 真开页 · MT5 真下单 · 在 KF 内改 DS Runtime。

---

## Results

### Fast unit (`pytest tests/interop/test_digital_self_skills.py`)

```text
29 passed · 2 skipped (S02 live) · 2026-09-01
log: data/_ds_skill_unit_20260901.log (local · not committed)
```

### CLI smoke (KF venv)

| Call | Result |
|------|--------|
| `ds list` | ok |
| `ds invoke S06 --intent "打开 YouTube 搜 NVIDIA" --url https://www.youtube.com` | **ok** · `live=false` · plan open+extract |
| `ds invoke S15 … --action deposit` | **ok=true（缺口）** · 未拒 |
| `ds invoke S15 … --action transfer` | **ok=true（缺口）** · 未拒 |

### S02 live

见本节末「S02 live」行（本审计写入时随跑更新）。

---

## Issues（记录）

| ID | Severity | Skill | Finding | Owner |
|----|----------|-------|---------|-------|
| **DS-I1** | **HIGH** | S15 | Catalog / SoT 写 `deposit` · `transfer` 应 `L4_NO_AUTHORIZABLE_PATH`；DS `authority.L4_ACTIONS` 实际是 `transfer_money`，**无 `deposit` / `transfer`**。KF 调用 `--action deposit|transfer` 现返回 **ok plan**。 | **Digital Self** 修 `is_l4` 别名或扩集合；KF 文档已标 gap |
| **DS-I2** | MED | S02 / S06 | 缺必填参数时 argparse 打 stderr usage、**stdout 空**，违反「stdout = one JSON」。KF 已归一为 `ok:false error=DS_INVOKE_EMPTY_STDOUT`。 | **DS** 宜改成 JSON error；KF 消费侧已兜底 |
| **DS-I3** | LOW | S06 | YouTube 仅为 **plan**（open/search/… 动词表），无真浏览 — **符合** consume 合同，不是缺陷 | — |
| **KF-I1** | INFO | consume | 初测对 empty stdout 抛 `DigitalSelfError`；已改为结构化 `DS_INVOKE_EMPTY_STDOUT` | KF **已修** |

---

## Per-skill verdict

| Skill | Fast unit | Notes |
|-------|-----------|-------|
| S00 AttentionGate | **PASS** | garbage/useful/important/alias |
| S06 Browser / YouTube | **PASS** | plan only · live deny · missing intent → structured error |
| S15 ResearchOp | **PASS with ISSUE** | L4 核心动词拒；**deposit/transfer 别名缺口 = DS-I1** |
| S16 Compose | **PASS** | publish/W4/FACT 门 |
| S02 ReadAloud | missing `-o` **PASS** · live **见下** | |

### S02 live

```text
KF_RUN_SLOW=1 · test_s02_zh_live_read_aloud · test_s02_en_live_read_aloud
2 passed in ~85s · 2026-09-01
log: data/_ds_skill_s02_live_20260901.log (local · not committed)
zh → voice=me · en → voice=me_en · OK
```

**Overall:** Fast **29 passed** · S02 live **2 passed** · Issues **DS-I1 (HIGH)** · **DS-I2 (MED, KF兜底)** · YouTube/Browser plan **PASS**.
---

## Hard stops still hold

```text
KF ↛ Playwright live
KF ↛ MT5 place_order (denied)
KF ↛ auto-publish
KF ↛ rewrite DS Runtime
```

**NEXT for DS:** close **DS-I1** (deposit/transfer → L4 deny) · optional JSON on argparse fail (**DS-I2**).  
**NEXT for KF:** keep consume tests red-flagging DS-I1 until producer fixes.

*KF · DS skill unit consume audit · 2026-09-01*
