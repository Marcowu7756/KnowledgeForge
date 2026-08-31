# KnowledgeForge 工作总结 — 2026-08-29～08-31

```yaml
summary_id: KF-WORK-SUMMARY-20260829-31
repo: https://github.com/Marcowu7756/KnowledgeForge
branch: main
head: 8237931
content_commits: 86e8086 · 4959e19
as_of: 2026-08-31
posture: GOVERNANCE FREEZE · Archive PASS / Ops ISSUE · NEXT = Owner UAT smoke
```

---

## 一、一句话

在冻结前提下完成 **业务侧 UAT 开局**、钉死 **Taxonomy ≠ Access**、通用获取自动挂 4 段内容树，并在 **重组 + 检索** 两侧落地 Excel 式可折叠分类大纲；工程自测绿并已推 GitHub，待 Owner 勾 T1–T10。

---

## 二、起点（交接冻结）

| 层 | 状态 |
|----|------|
| Engineering | CLOSED · Integration 19/19 |
| Archive | **PASS** |
| Ops | **ISSUE**（Twitter / TTS） |
| H4 / SETV Scope | **HOLD** |
| NEXT | **业务侧消费** · KF 不向 SETV 提需求 |

`PASS_WITH_ISSUES` = Archive PASS + Ops ISSUE（不是 Archive 缺陷）。

---

## 三、本轮交付（已 push）

| Commit | 内容 |
|--------|------|
| `86e8086` | Taxonomy / Access 正交：捕获自动 `taxonomy.path`；SoT + SOP/UAT 去耦合 |
| `6a2946f` | 审计 disposition 记 push head |
| `4959e19` | 重组+检索 taxonomy 大纲 UI · `taxonomy_prefix` 限定检索 · ui **0.6.1** |
| `8237931` | 大纲 UI 审计记 push head |

仓库：https://github.com/Marcowu7756/KnowledgeForge · `main` @ **`8237931`**

---

## 四、能力落地

### 1. 用户业务 UAT 双轨（文档）

- 章程 [`UAT_USER_CONSUME_V0.md`](UAT_USER_CONSUME_V0.md)
- 会话日志 [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md)
- SOP [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md)：轨 A 消费判定 · 轨 B 分功能反馈

### 2. 获取确认（Owner 试用 · 本地）

| 源 | 结果 |
|----|------|
| YouTube 长片 `ESKhQFTL0Ps` | 成功（无字幕 → ASR，耗时长；进度钉 35% 属 UX） |
| YouTube `9MDhq9UO-Fk` | 成功 |
| Bilibili `BV1es411R7SK` | 成功 |

Owner 反馈：除长视频时长外，其他正常。

### 3. Taxonomy ≠ Access（正交钉）

| 轴 | 含义 | 默认例 |
|----|------|--------|
| **taxonomy.path** | 内容树 4–5 段（纲举目张） | `公开媒体 > 捕获 > YouTube > {标题}` |
| **access.classification** | 流动边界 | 通用捕获仍 **public** |

- SoT：[`TAXONOMY_VS_ACCESS_V0.md`](TAXONOMY_VS_ACCESS_V0.md)
- 审计：[`TAXONOMY_ACCESS_SPLIT_AUDIT_20260829.md`](TAXONOMY_ACCESS_SPLIT_AUDIT_20260829.md)
- 管道：空 path 才补；**不**从树根推导 access
- 通道话术改为按 **classification=restricted**，不再「专有知识一律 proprietary」

### 4. Taxonomy 大纲 UI（Excel Group）

| 面 | 行为 |
|----|------|
| 重组 | 左侧可折叠大纲 → 填 `taxonomy_prefix` → view=taxonomy 重建 |
| 检索 | 同大纲 → 前缀限定语义检索 + 本组卡片列表 |

- API：`/api/taxonomy/tree` · `/api/taxonomy/cards`
- Health：`ui_version=0.6.1` · `features.taxonomy_outline=true`
- 审计：[`TAXONOMY_OUTLINE_UI_AUDIT_20260829.md`](TAXONOMY_OUTLINE_UI_AUDIT_20260829.md)

---

## 五、测试与审计套路（本轮执行）

每次改动均按：文档 → 单元 → 集成 → 审计 → 推 GitHub → 更新 UAT → Owner 测。

| 波次 | 单元 | 集成 |
|------|------|------|
| Taxonomy/Access 正交 | 166 passed | 14 pass · 5 slow skip |
| Outline UI | **169 passed** | **14 pass · 5 slow skip** |

冻结未破：无 H4 解冻、无 SETV 扩 scope、无 access←taxonomy 推导。

---

## 六、文档地图（本轮相关）

| 用途 | 文件 |
|------|------|
| SoT 正交 | [`TAXONOMY_VS_ACCESS_V0.md`](TAXONOMY_VS_ACCESS_V0.md) |
| 正交审计 | [`TAXONOMY_ACCESS_SPLIT_AUDIT_20260829.md`](TAXONOMY_ACCESS_SPLIT_AUDIT_20260829.md) |
| 大纲审计 | [`TAXONOMY_OUTLINE_UI_AUDIT_20260829.md`](TAXONOMY_OUTLINE_UI_AUDIT_20260829.md) |
| 用户 UAT | [`UAT_USER_CONSUME_V0.md`](UAT_USER_CONSUME_V0.md) · [`UAT_SESSION_LOG_20260829.md`](UAT_SESSION_LOG_20260829.md) |
| 消费 SOP | [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md) |
| UI | [`../ui/WEB_UI_v0.md`](../ui/WEB_UI_v0.md) |
| 看板 | [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md) |

本地 `data/_uat_*` / `_tax_*` 运行痕迹未入库（符合卫生）。

---

## 七、待 Owner

重启 UI 后勾会话日志：

- **T1–T5**：正交 / 捕获 taxonomy / 通道回归  
- **T6–T10**：重组+检索大纲分组  

健康：`GET /api/health` → `ui_version` ≥ `0.6.1` · `taxonomy_outline: true`。

---

## 八、下一触发器

继续 **业务问题消费 → Gap A/B/C/D**。仅 **D** 可回 SETV；摩擦（长视频 ASR 进度、Twitter/TTS）记 Ops，不改 Archive 判定。

> **业务 UAT 开局 · Taxonomy 与 Access 正交落地 · 大纲分组 UI 可测 · NEXT = Owner 从 [`UAT_ENTRY_V0.md`](UAT_ENTRY_V0.md) 进 T1–T10。**
