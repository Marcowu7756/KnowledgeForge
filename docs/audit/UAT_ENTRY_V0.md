# UAT 入口 · 从这里开始

```yaml
doc_id: KF-UAT-ENTRY-V0
as_of: 2026-08-31
status: OPEN · Owner 入口
audience: 本机使用者（你）
head: main @ 64598cb+
```

**只读这一页就能开工。** 下面三份按需点开，不要先翻工程结案文。

---

## 你现在在测什么

| | 本轮（要做） | 不是本轮 |
|--|--------------|----------|
| 名称 | **用户业务消费 UAT** | 工程 Consume UAT |
| 状态 | **OPEN** | 已结案 `PASS_WITH_ISSUES` |
| 目的 | 用 Archive 答真问题 + 填功能反馈 | 固定题库 15/15 签收 |
| 文件 | 见下「三份必开」 | [`UAT_CONSUME_V0.md`](UAT_CONSUME_V0.md)（只查历史） |

冻结不变：H4 HOLD · SETV Scope HOLD · KF 不向 SETV 提需求。

---

## 三步开工

### ① 启动车间

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py ui
```

浏览器：`http://127.0.0.1:8765`  
健康：`http://127.0.0.1:8765/api/health` → `ok: true` · **`ui_version` ≥ `0.6.1`** · `taxonomy_outline: true`  
（旧进程需先停掉再启，否则版本仍是 0.6.0。）

专有内容（SETV 等）检索用通道 **proprietary**（看的是 access，不是 taxonomy 根）。

### ② 打开会话日志（勾选与记录写这里）

→ [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md)

建议顺序：

| 顺序 | 块 | 做什么 |
|------|-----|--------|
| 1 | 开场门禁 | 已 PASS 可略；新开一天再勾 |
| 2 | **T6–T10** | 重组/检索左侧大纲（本轮优先） |
| 3 | **T1–T5** | taxonomy / 通道正交烟测 |
| 4 | 轨 A | 真实业务题一行一行记 |
| 5 | 轨 B | 用过的功能填级（OK/摩擦/…） |

### ③ 不会操作时打开 SOP

→ [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md)

```text
启动 → 提问 → 检索 →（组卡/表达）→ 判定
  可用 → 记录
  不可用 → A/B/C/D → 记录
```

---

## 三份必开（角色）

| 角色 | 文件 | 何时看 |
|------|------|--------|
| **入口（本页）** | [`UAT_ENTRY_V0.md`](UAT_ENTRY_V0.md) | 每次开测第一眼 |
| **填写本** | [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md) | 勾选 + 写记录 |
| **操作法** | [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md) | 忘了步骤时 |

章程（规则细则，不必每题重读）：[`UAT_USER_CONSUME_V0.md`](UAT_USER_CONSUME_V0.md)

---

## 本轮优先勾选（摘要）

**大纲（先做 · 需 ui≥0.6.1）：**

- T6 重组有左侧大纲  
- T7 点节点 → taxonomy 重建  
- T8 检索有大纲；切 proprietary 树变  
- T9 选分组后检索限定该支  
- T10 本组卡片可预览  

**正交（可随后）：** T1–T5 见会话日志。

**业务主线：** 轨 A 至少 1 道真问题；轨 B 至少填「检索 / 重组」各一行。

---

## 不要从这里进（易混）

| 文件 | 为什么别当入口 |
|------|----------------|
| [`UAT_CONSUME_V0.md`](UAT_CONSUME_V0.md) | 工程 UAT **已结案** |
| [`UAT_SESSION_LOG_20260828.md`](UAT_SESSION_LOG_20260828.md) | 首轮签收日志，只读 |
| [`WORK_SUMMARY_20260829.md`](WORK_SUMMARY_20260829.md) | 工程总结，不是测法 |
| [`TAXONOMY_VS_ACCESS_V0.md`](TAXONOMY_VS_ACCESS_V0.md) | SoT 说明；测时按日志勾即可 |

---

## 一条判定纪律

- Twitter / TTS / 长视频 ASR 久等 → **Ops**，不记 Archive FAIL  
- 答不上业务题 → 必须分 **A/B/C/D**（仅 D 可回 SETV）  
- 摩擦反馈 ≠ 解冻 H4 / 扩 SETV  

测完：在会话日志勾结果，或直接回聊天说 T6–T10 / 轨 A 结果。
