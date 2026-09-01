# UAT 入口 · 从这里开始

```yaml
doc_id: KF-UAT-ENTRY-V0
as_of: 2026-09-01
status: OPEN · 唯一 Owner 开工门
audience: 本机使用者（你）
path: D:\KnowledgeForge\docs\audit\UAT_ENTRY_V0.md
```

> **唯一开工门。** 测业务 UAT 先打开本页；不要从工作总结、工程结案 UAT、或 08-28 日志进。

```text
本页（入口）
  → ① 启动车间（或 CLI 门禁）
  → ② 会话日志勾选 / 记结果
  → ③ 卡住再开 SOP
```

---

## 你现在在测什么

| | **本轮（要做）** | 不是本轮 |
|--|------------------|----------|
| 名称 | **用户业务消费 UAT** | 工程 Consume UAT |
| 状态 | **OPEN** | 已结案 `PASS_WITH_ISSUES` |
| 目的 | 大纲 + 正交 + 真问题 + 功能反馈 + **Skill 消费烟测** | 固定题库 15/15 签收 |
| 写结果 | [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md) | [`UAT_CONSUME_V0.md`](UAT_CONSUME_V0.md)（只查历史） |

冻结不变：H4 HOLD · SETV Scope HOLD · KF 不向 SETV 提需求。

**架构钉（测时记住）：** KF = **Skill 消费端**（`ds invoke`）；`voice` / `express` / ▶ 听讲解 = **legacy 暂留**。地图：[`../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md)。

---

## 三步开工

### ① 启动车间

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py ui
```

| 项 | 打开 / 期望 |
|----|-------------|
| 浏览器 | `http://127.0.0.1:8765` |
| 健康 | `http://127.0.0.1:8765/api/health` |
| 版本门禁 | `ok: true` · **`ui_version` ≥ `0.6.4`** · `taxonomy_outline` · `taxonomy_open_card` · `ko_narrate_preview` |

旧进程先停再启。  
专有内容用通道 **proprietary**（看 **access**，不看 taxonomy 根）。

可选 CLI Skill 门禁（不代替车间）：

```powershell
.\.venv\Scripts\python.exe main.py ds list
.\.venv\Scripts\python.exe main.py ds invoke S00 --text "NAS100 H1 回测值得沉淀"
```

### ② 打开填写本（勾选与记录只写这里）

→ [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md)

| 步 | 跳到日志里 | 做什么 | 勾完？ |
|----|------------|--------|--------|
| A | [开场门禁](UAT_SESSION_LOG_20260829.md#开场门禁) | 版本已升可略；新开一天再勾 | ☐ |
| B | [T6–T10 大纲](UAT_SESSION_LOG_20260829.md#t6t10--taxonomy-大纲优先) | 重组/检索大纲 · 双击 KO | ☐ |
| C | [T1–T5 正交](UAT_SESSION_LOG_20260829.md#t1t5--taxonomy--access-正交随后) | 捕获 taxonomy · 通道回归 | ☐ |
| D | [S-DS Skill 烟测](UAT_SESSION_LOG_20260829.md#s-ds--digital-self-skill-烟测) | S00 / S02（消费端） | ☐ |
| E | [轨 A 消费](UAT_SESSION_LOG_20260829.md#轨-a--消费记录sop-11) | ≥1 道真实业务题 | ☐ |
| F | [轨 B 反馈](UAT_SESSION_LOG_20260829.md#轨-b--分功能反馈) | 至少填「检索 / 重组」 | ☐ |

### ③ 不会操作时再开 SOP

→ [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md)

```text
启动 → 提问 → 检索 →（组卡/表达）→ 判定
  可用 → 记录
  不可用 → A/B/C/D → 记录
```

Skill 协议：[`../interop/DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md)

---

## 文件角色

| 角色 | 文件 | 何时看 |
|------|------|--------|
| **入口（本页）** | `docs/audit/UAT_ENTRY_V0.md` | **每次开测第一眼** |
| **填写本** | [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md) | 勾选 + 写记录 |
| **操作法** | [`CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md) | 忘步骤时 |
| Skill 消费 / phase-out | [`KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md) | 口令对照 |

章程细则：[`UAT_USER_CONSUME_V0.md`](UAT_USER_CONSUME_V0.md)

---

## 本轮勾选摘要

**大纲（ui≥0.6.4）** · T6–T10：双击最底层 KO 打开正文。  
**正交** · T1–T5。  
**Skill** · S-DS1 S00 分流 · S-DS2 S02 同语言朗读（可选；legacy ▶ 听讲解仍可用）。  
**业务** · 轨 A ≥1 题；轨 B 至少「检索 / 重组」。

---

## 不要从这里进（易混）

| 文件 | 为什么别当入口 |
|------|----------------|
| [`UAT_CONSUME_V0.md`](UAT_CONSUME_V0.md) | 工程 UAT **已结案** |
| [`UAT_SESSION_LOG_20260828.md`](UAT_SESSION_LOG_20260828.md) | 首轮签收，只读 |
| [`WORK_SUMMARY_20260829.md`](WORK_SUMMARY_20260829.md) | 工程总结；测法以本页为准 |
| [`TAXONOMY_VS_ACCESS_V0.md`](TAXONOMY_VS_ACCESS_V0.md) | SoT；测时按填写本勾即可 |
| [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) | 看板；入口链回本页 |

---

## 一条判定纪律

- Twitter / TTS / 长视频 ASR 久等 → **Ops**，不记 Archive FAIL  
- 答不上业务题 → 必须分 **A/B/C/D**（仅 D 可回 SETV）  
- 摩擦反馈 ≠ 解冻 H4 / 扩 SETV  
- Skill 门禁失败（L4 / `--live` / `--publish`）= **设计拒绝**，不是 Archive FAIL  
- 不要因 Skill 好听就要求 KF 变成第二个 Runtime  

测完：在填写本勾结果，或回聊天说 **T6–T10 / T1–T5 / S-DS / 轨 A** 结果。
