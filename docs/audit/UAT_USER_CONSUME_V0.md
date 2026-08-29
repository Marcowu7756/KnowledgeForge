# User Consume UAT v0 — 业务侧消费

```yaml
uat_id: KF-UAT-USER-CONSUME-V0
as_of: 2026-08-29
status: OPEN
sop: docs/ops/CONSUME_USER_HANDBOOK_V0.md
prior: KF-UAT-CONSUME-V0 COMPLETE · PASS_WITH_ISSUES
freeze: H4 HOLD · SETV Scope HOLD · KF 不向 SETV 提需求
session_log: UAT_SESSION_LOG_20260829.md
```

\[
\boxed{\mathrm{Engineering\ UAT}\neq\mathrm{User\ Consume}}
\qquad
\boxed{\mathrm{NEXT = 真实业务问题}}
\qquad
\boxed{\mathrm{only\ D}\rightarrow\mathrm{SETV}}
\]

## 1. 双轨：怎么用 + 怎么反馈

本轮文档分两轨，**都要写**，缺一不可：

| 轨 | 写什么 | 写在哪 |
|----|--------|--------|
| **A · 消费主线** | 真实业务题 → 检索 → 判定 usable / A/B/C/D | 会话日志「消费记录」 |
| **B · 功能反馈** | 对本机 UI/CLI 各能力的体感（好用 / 别扭 / 坏了） | 会话日志「分功能反馈」 |

- **A** 回答：Archive 能不能答业务题（知识资产判定）。
- **B** 回答：车间五段 + 启动/维护用起来怎样（产品体感；**不等于**扩架构 backlog）。

反馈分级（每项选一）：

| 级 | 含义 |
|----|------|
| **未用** | 本轮没碰到 |
| **OK** | 能完成任务，无明显摩擦 |
| **摩擦** | 能用，但慢 / 难懂 / 易错 |
| **阻塞** | 想用但做不成（写清现象） |
| **Ops 已知** | 已知 Twitter / TTS 类问题，不记 Archive FAIL |

自由文：一句话即可；可写「希望怎样」，**不**据此自动解冻 H4 / 扩 SETV。

## 2. 与首轮 Consume UAT 的关系

| | 首轮 [`UAT_CONSUME_V0.md`](UAT_CONSUME_V0.md) | **本轮（用户）** |
|--|-----------------------------------------------|------------------|
| 目的 | 验收 Archive 可消费（固定题库） | **用 Archive 答真实业务问题** + **功能反馈** |
| 题源 | 锁定 Q01–Q15 | 使用者自拟（可检验的一句） |
| 判定 | 签收 `PASS_WITH_ISSUES` | 每题 usable / A/B/C/D + 分功能反馈表 |
| 架构 | 禁止扩 Matrix / 解冻 H4 | **同禁**；按 SOP 走，不扩架构 |

权威拆分：[`OWNER_INTERPRET_UAT_SPLIT_20260828.md`](OWNER_INTERPRET_UAT_SPLIT_20260828.md) · 看板 [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md)。

## 3. 怎么跑（轨 A）

严格执行 [`CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md)：

```text
启动 → 提问 → 检索 →（组卡/表达）→ 判定
  可用 → 记录
  不可用 → A/B/C/D → 记录
```

用过的功能，在同一次会话里补写轨 B（不必每题重复；本轮至少填一次「用过的段」）。

全部写入 [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md)。

## 4. 开场前（轻量门禁）

失败则停；**不要**记 Archive FAIL。

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py ui
# 浏览器 http://127.0.0.1:8765 · 可选 GET /api/health → ok:true · ui_version≥0.6.0
```

对照烟测（可选）：

```powershell
.\.venv\Scripts\python.exe main.py retrieve query "AAPL H4 State Snapshot" --lane proprietary --top 5
```

`classification=restricted`（或专有 `source_project`）时用通道 **proprietary**。勿把 taxonomy 根「专有知识」与通道绑死 —— [`TAXONOMY_VS_ACCESS_V0.md`](TAXONOMY_VS_ACCESS_V0.md)。

### 4b · Taxonomy 正交冒烟（本轮加）

在获取/检索之外抽空做会话日志 **T1–T5**（见 [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md)）：确认新捕获卡有 `公开媒体 > 捕获 > …` 四段树，且 access 仍为 public；proprietary 仍能查 SETV。

## 5. Gap 分类（轨 A · 不可用时恰好一类）

| 类 | 含义 | 处置 |
|----|------|------|
| **usable** | Top-K / 组卡 / 表达能答 | 记 win |
| **A** 产方 | 产方从未产出 | 记票；不扩 SETV |
| **B** 知识 | 有物，KF 沉淀/索引错 | KF 修 |
| **C** 关系 | 两卡在，无边 | 重组 / 关系 |
| **D** 表示 | 已沉淀仍答不上 | **唯一**可回 SETV（Owner 确认后） |

Twitter / TTS → **Ops 已知**，不改轨 A 的 Archive 判定。

## 6. 功能反馈范围（轨 B）

与 [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) 五段对齐；会话日志内各有一块填写区：

| 段 | 用户看到的名字 | 反馈时想什么 |
|----|----------------|--------------|
| 启动 / 健康 | 打开车间 | 能否起来、健康检查是否清楚 |
| Capture | 获取 | 文件 / 链 / Twitter 等入口是否好用 |
| Distill | 沉淀 | compile / 包结果 / 维护删除是否好懂 |
| Reconstruct | 重组 | 建图、view 是否帮到理解 |
| Retrieve | 检索 | 通道、Top-K、标题是否够判定 |
| Family | 组卡 | Family 勾选 / 多卡是否顺手 |
| Express | 表达 | lecture / GIF / 无声是否可接受 |
| 整体 | 车间壳 | 导航、任务、失败信息是否可读 |

## 7. 禁止

- 扩 Integration Matrix / 新切片凑 PASS
- `THAW HOLD-CHUNK-RAG` · SETV 新轴 / 新 INST 类型
- 在 KF 发明 `SETV-INST-*`
- 因消费不顺或「摩擦」反馈向 SETV 提需求
- 因 Twitter/TTS 改 Archive
- 把轨 B「希望有聊天窗」当成解冻 H4 的依据

## 8. Operator one-liner

> 首轮 Archive 已 PASS · 本轮一边用真实问题消费一边填分功能反馈 · 仅 D 回 SETV · 不解冻 H4。
