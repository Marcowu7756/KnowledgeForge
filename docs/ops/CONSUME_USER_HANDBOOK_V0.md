# SOP · 消费 Archive v0

```yaml
sop_id: KF-SOP-CONSUME-V0
audience: 本机使用者
as_of: 2026-08-28
replaces: handbook list style
freeze: H4 HOLD · SETV Scope HOLD · KF 不向 SETV 提需求
```

**主线（全章按此顺序执行，勿跳步）：**

```text
§4 启动
  → §5 提问
    → §6 检索
      → §7 组卡 / 重组（需要时）
        → §8 表达（需要时）
          → §9 使用与判定
                ├── 可用 → §11 记录 → 结束
                └── 不可用 → §10 分类 Gap → §11 记录
```

**UAT 入口（Owner 从这里进）：** [`UAT_ENTRY_V0.md`](../audit/UAT_ENTRY_V0.md)  
**本轮填写本：** [`UAT_SESSION_LOG_20260829.md`](../audit/UAT_SESSION_LOG_20260829.md)（勾选 T6–T10 / T1–T5 · 轨 A/B）  
章程：[`UAT_USER_CONSUME_V0.md`](../audit/UAT_USER_CONSUME_V0.md)。  
首轮签收（已结案，勿当入口）：[`UAT_CONSUME_V0.md`](../audit/UAT_CONSUME_V0.md) · [`UAT_SESSION_LOG_20260828.md`](../audit/UAT_SESSION_LOG_20260828.md)。  
入库、索引、加密、删除：[`OPS_RUNBOOK_V0.md`](OPS_RUNBOOK_V0.md)。

---

## 1. 目的

用已沉淀的 Knowledge Archive（约 114 KO：SETV Family / Instance / Evidence）回答**真实业务问题**，并在答不上时留下可分类的 Gap。

不是验收「功能是否齐全」，不是扩 SETV，不是解冻 H4。

`PASS_WITH_ISSUES` = Archive PASS + Ops ISSUE（Twitter / TTS）。**不表示 Archive 有功能缺陷。**

---

## 2. 范围

| 在范围内 | 不在范围内 |
|---------|------------|
| 对本机 Archive 提问、检索、组卡、表达 | 修改已沉淀卡正文 |
| 专有通道查阅 SETV / FactorLib / AShareLib | 在 KF 发明 `SETV-INST-*` |
| 答不上时填 A/B/C/D | 向 SETV 提范围 / 新轴 / 新 Instance 类型 |
| 删除垃圾卡（见维护 SOP） | 开 chunk-RAG 聊天窗 |
| | 因 Twitter/TTS 失败改 Archive |

---

## 3. 角色

| 角色 | 职责 |
|------|------|
| 提问人 | 按主线走完一题；判定可用与否 |
| 记录人 | 可与提问人同一人；写 §11 一行 |
| KF | 仅在 **B / C** 时修沉淀或关系 |
| SETV | 仅当记录为 **D** 且 Owner 确认后才进入演化讨论 |

KF **不**因消费不顺向 SETV 提需求。

---

## 4. 启动

每次开用执行一次。失败则停本 SOP，先修环境，**不要**记 Archive FAIL。

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py ui
```

浏览器打开 `http://127.0.0.1:8765`。可选：`/api/health` 中 `ok: true`、`ui_version` ≥ `0.6.1`、`taxonomy_outline: true`。

检索通道按 **access**，不按 taxonomy 根：`classification=restricted`（或专有 `source_project`）用通道 **proprietary**。`general` 检不出 restricted 卡，属设计而非故障。  
内容树（纲举目张）是另一轴：`taxonomy.path`，目标 4–5 段 —— 见 [`TAXONOMY_VS_ACCESS_V0.md`](../audit/TAXONOMY_VS_ACCESS_V0.md)。重组/检索左侧有大纲分组（Excel-like）。

进入主线 §5。

---

## 5. 提问

写**一句可检验**的问题，再进入 §6。

| 合格 | 不合格 |
|------|--------|
| AAPL 2024 H4 状态快照是什么？ | 帮我看看市场 |
| GOLD H4 Instance 在 Archive 里吗？ | 系统还能做什么？ |

问题写不清，后面 Top-K 无法判定「命中」。

---

## 6. 检索

本 SOP 的**主入口**。

**UI：** 车间 → **检索** → 通道 proprietary → 输入 §5 的问题 → Top 5。

**CLI：**

```powershell
.\.venv\Scripts\python.exe main.py retrieve query "§5 的问题" --lane proprietary --top 5
```

阅读 Top-K 的**标题与路径**。问的是 AAPL H4 Instance，就要看到对应 snapshot，而不是「有点像」的其它标的。

进入 §7（需要多卡或关系）或直接 §8 / §9。

---

## 7. 组卡 / 重组

仅当 §6 单卡不够时执行，否则跳过。

**组卡（Family）：** 例如查询 `SETV-FAM-AAPL-TV-2024-WDH4`，勾选 W / D / H4 成员。

**重组：** 关系看不清时，UI **重组**，或：

```powershell
.\.venv\Scripts\python.exe main.py reconstruct --from-index --taxonomy-prefix "专有知识/SETV" --view taxonomy --limit 40
```

然后回到 §6 带图检索，或进入 §8 / §9。

---

## 8. 表达

仅当需要讲义、GIF、lecture/paper 时执行，否则跳过。

**UI：** **表达**。  
**CLI：** `animate <card.md> --fast --renderer auto`

无 wav / narrate 无声：记为 Ops ISSUE，**不**改变 §9 的 Archive 判定。Twitter 获取失败同理（见附录 B）。

进入 §9。

---

## 9. 使用与判定

用 §6（及 §7/§8）的结果尝试回答 §5。

| 判定 | 下一章 |
|------|--------|
| 能回答 | **usable** → §11 |
| 不能回答 | **不可跳过 §10** |

禁止在未分类前改系统、扩 SETV、解冻 H4。

---

## 10. 分类 Gap

仅 §9 为「不能回答」时填写**恰好一类**：

| 类 | 问自己 | 处置 |
|----|--------|------|
| **A** 产方 | 这件事产方是否从未产出？ | 记票；不扩 SETV 范围 |
| **B** 知识 | 文件其实在，KF 没沉淀对 / 索引错？ | KF 修 |
| **C** 关系 | 两张卡都在，只是没连上？ | 重组 / 关系 |
| **D** 表示 | 卡已在、问题仍无答案（表示力不够）？ | **唯一**可回 SETV |

缺一张卡 ≠ 自动 Discovery。不知道「当时为什么这么定」≠ 自动开 Memory。先完成分类，再进入 §11。

---

## 11. 记录

写入 [`UAT_SESSION_LOG_20260829.md`](../audit/UAT_SESSION_LOG_20260829.md)：

1. **轨 A（每题一行）** — 然后可回到 §5 问下一题，或结束本轮。

```text
日期 | 问题 | 通道 | Top-1 标题 | 可用? | 类 | 一句话原因
```

类：`usable` / `A` / `B` / `C` / `D`。

2. **轨 B（分功能反馈）** — 本轮用过的段必填级（未用 / OK / 摩擦 / 阻塞 / Ops 已知）+ 一句话；结束前填 B8 总评。  
   功能反馈**不**自动变成扩架构或解冻 H4；阻塞项记入会话 Tickets 供 KF 观察。

---

## 12. 结束条件

| 情况 | 结束方式 |
|------|---------|
| 可用 | §11 后结束该题 |
| 已分类 | §11 后结束该题；B/C 交 KF；A 记产方；D 待 Owner，KF 仍不指挥 SETV |
| §4 失败 | 停 SOP，修环境 |

---

## 附录 A · 对照题（系统未坏时的烟测）

业务题优先。需要确认检索仍绿时可用：

- `AAPL H4 State Snapshot` · proprietary  
- `GOLD H4 State Snapshot` · proprietary  
- `SETV-FAM-AAPL-TV-2024-WDH4` · proprietary  

负例：同一 AAPL 句用 **general**，不应出现 restricted AAPL Instance。

---

## 附录 B · 已知 Ops ISSUE

| 现象 | 不记为 |
|------|--------|
| Twitter 单帖失败 / 非公开 | Archive 缺陷 |
| narrate 无 wav | Archive 缺陷 |
| torch.jit 警告 | 故障 |

归入 Ops；主线 §9 仍只根据 Archive 是否答上题来判定。

---

## 附录 C · 相关 SOP / 文档

| 主题 | 文档 |
|------|------|
| 入库 / 索引 / 导出 / 删除 | [`OPS_RUNBOOK_V0.md`](OPS_RUNBOOK_V0.md) |
| 只删不改 | [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](KNOWLEDGE_MAINTAIN_DELETE_V0.md) |
| 界面五段 | [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) |
| 治理冻结 | [`OWNER_INTERPRET_UAT_SPLIT_20260828.md`](../audit/OWNER_INTERPRET_UAT_SPLIT_20260828.md) |
| Taxonomy ≠ Access | [`TAXONOMY_VS_ACCESS_V0.md`](../audit/TAXONOMY_VS_ACCESS_V0.md) |
| **UAT 入口** | [`UAT_ENTRY_V0.md`](../audit/UAT_ENTRY_V0.md) |
| 用户业务 UAT | [`UAT_USER_CONSUME_V0.md`](../audit/UAT_USER_CONSUME_V0.md) · [`UAT_SESSION_LOG_20260829.md`](../audit/UAT_SESSION_LOG_20260829.md) |
