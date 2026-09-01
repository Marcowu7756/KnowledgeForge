# User Consume Session Log — 2026-08-29

```yaml
uat_id: KF-UAT-USER-CONSUME-V0
role: 填写本（不是入口）
entry: UAT_ENTRY_V0.md
charter: UAT_USER_CONSUME_V0.md
sop: docs/ops/CONSUME_USER_HANDBOOK_V0.md
started: 2026-08-29
finished: —
operator: Owner / user
status: OPEN
verdict: —
```

> **本文件不是入口。** 开测先读 [`UAT_ENTRY_V0.md`](UAT_ENTRY_V0.md)，再回到这里勾选与记录。

本地运行痕迹（不入库）：`data/_uat_*` 等。

### 本页目录（按此顺序填）

| # | 块 | 跳转 |
|---|-----|------|
| 1 | 开场门禁 | [↓](#开场门禁) |
| 2 | **T6–T10** 大纲（优先） | [↓](#t6t10--taxonomy-大纲优先) |
| 3 | **T1–T5** 正交（随后） | [↓](#t1t5--taxonomy--access-正交随后) |
| 4 | **S-DS** Skill 烟测 | [↓](#s-ds--digital-self-skill-烟测) |
| 5 | 轨 A 业务题 | [↓](#轨-a--消费记录sop-11) |
| 6 | 轨 B 功能反馈 | [↓](#轨-b--分功能反馈) |
| — | 旁证：获取已成功 | [↓](#旁证获取确认已完成) |

---

<a id="开场门禁"></a>

## 开场门禁

| Check | Result | Notes |
|-------|--------|-------|
| UI `main.py ui` → `http://127.0.0.1:8765` | **PASS**（08-29）· 听讲解 / Skill 测前请 **重启** | `/api/health` · **ui_version ≥ 0.6.4** · `taxonomy_outline` · `taxonomy_open_card` · `ko_narrate_preview` |
| 可选：`AAPL H4 State Snapshot` proprietary Top-5 | ☐ | 期望 AAPL W/H4/D 近顶 |
| units ≈ vectors | ☐ | 开场快照：units **115** · vectors **114**（差 1；检索仍绿可继续，勿记 Archive FAIL） |

**门禁 verdict：** **PASS**（UI 已用；测大纲前确认版本已升）

---

<a id="t6t10--taxonomy-大纲优先"></a>

## T6–T10 · Taxonomy 大纲（优先）

审计：[`TAXONOMY_OUTLINE_UI_AUDIT_20260829.md`](TAXONOMY_OUTLINE_UI_AUDIT_20260829.md)。需 **重启 UI**（`ui_version` ≥ 0.6.3 · `taxonomy_outline` · `taxonomy_open_card`）。

| # | 动作 | 期望 | Owner 结果 |
|---|------|------|------------|
| T6 | 车间 → **重组**：左侧出现分类大纲 | 可折叠节点 · 有 count | **OK** · 「很好，就是我期望的」 |
| T7 | 点某一节点 → 前缀填入 → 视图 taxonomy → 重建 | job 成功 · result 含该 prefix | ☐ |
| T8 | 车间 → **检索**：左侧同样大纲 | 与访问层联动（切 proprietary 树变） | ☐ |
| T9 | 选 `公开媒体/捕获` 后检索短查询 | 命中限定在该支（或明确无命中） | ☐ |
| T10 | 展开到最底层带 **KO** 的知识节点 → **双击** | 预览弹层打开知识内容 | ☐ 复测 ui≥0.6.3 |

---

<a id="t1t5--taxonomy--access-正交随后"></a>

## T1–T5 · Taxonomy / Access 正交（随后）

工程已推：capture 自动 `taxonomy.path`（4 段）· access 仍独立。SoT [`TAXONOMY_VS_ACCESS_V0.md`](TAXONOMY_VS_ACCESS_V0.md) · 审计 [`TAXONOMY_ACCESS_SPLIT_AUDIT_20260829.md`](TAXONOMY_ACCESS_SPLIT_AUDIT_20260829.md)。

| # | 动作 | 期望 | Owner 结果 |
|---|------|------|------------|
| T1 | 打开任一已回填卡（如 `孙宇晨与景甜的3000万彩礼争议.md`） | 有 `taxonomy.path: [公开媒体, 捕获, YouTube, …]` · **无**被迫改 access | ☐ |
| T2 | UI 获取一条**短** YouTube 或 Bilibili（有字幕更好） | 新卡 4 段 taxonomy · `classification` 仍 public（可缺省不写） | ☐ |
| T3 | 检索通道 **general** 查刚获取标题关键词 | 能命中公开卡 | ☐ |
| T4 | 检索通道 **proprietary** 查 `AAPL H4 State Snapshot` | 仍命中 restricted SETV（回归） | ☐ |
| T5 | 轨 B：获取 / 检索各填一级 | 摩擦仅记体验；勿因 taxonomy 根说「专有」 | ☐ |

**工程预检（agent）：** unit 169+ · outline API + UI landed · derive_audio 同语言 · ds interop 8 passed。

---

<a id="s-ds--digital-self-skill-烟测"></a>

## S-DS · Digital Self Skill 烟测（消费端）

SoT：[`../interop/DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md) · phase-out：[`../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md)。  
KF **只调用** DS；不抄 Runtime。legacy `voice speak` / ▶ 听讲解仍可用，不必本轮砍掉。

| # | 动作 | 期望 | Owner 结果 |
|---|------|------|------------|
| S-DS1 | `main.py ds list` | 列出 S00/S02/S06/S15/S16（或目录等价） | ☐ |
| S-DS2 | `ds invoke S00 --text "NAS100 H1 回测值得沉淀"` | JSON · `class` 合理 · 非空 stdout | ☐ |
| S-DS3 | `ds invoke S02 --text "核心观点先读出来。" --language zh -o data\expression\_ds_s02.wav` | `ok` · wav 写出 · 同语言（zh→me） | ☐ |
| S-DS4 | （可选）`ds invoke S06 --live …` 或 S15 `place_order` / S16 `--publish` | **拒绝**（设计门禁，非 Archive FAIL） | ☐ |

---

<a id="旁证获取确认已完成"></a>

## 旁证：获取确认（已完成 · 不必重测）

| 源 | 证据 | 结果 |
|----|------|------|
| YouTube `ESKhQFTL0Ps`（约 49min · 无字幕 → ASR） | raw `20260829T014910Z_ESKhQFTL0Ps.txt` · KO `孙宇晨与景甜的3000万彩礼争议.md` | **成功** · 耗时长（时长+Whisper） |
| YouTube `9MDhq9UO-Fk` | job `226e1498e82d` done · raw `20260829T040412Z_9MDhq9UO-Fk.txt` · KO `total_war_three_kingdoms_…十大隐藏细节.md` | **成功** |
| Bilibili `BV1es411R7SK` p16 | job `8112bbe6f781` done · raw `20260829T042252Z_BV1es411R7SK_p16.txt` · KO `真三国无双7猛将传星彩攻略.md` | **成功** |

---

<a id="轨-a--消费记录sop-11"></a>

## 轨 A · 消费记录（SOP §11）

格式：`日期 | 问题 | 通道 | Top-1 标题 | 可用? | 类 | 一句话原因`  
类：`usable` / `A` / `B` / `C` / `D`

| # | 日期 | 问题 | 通道 | Top-1 标题 | 可用? | 类 | 一句话原因 |
|---|------|------|------|------------|-------|-----|------------|
| 1 | | | proprietary | | | | |
| 2 | | | proprietary | | | | |
| 3 | | | proprietary | | | | |
| 4 | | | proprietary | | | | |
| 5 | | | proprietary | | | | |

（不够再加行。）

---

<a id="轨-b--分功能反馈"></a>

## 轨 B · 分功能反馈

级：**未用** / **OK** / **摩擦** / **阻塞** / **Ops 已知**  
「一句话」写现象或希望；摩擦/阻塞请尽量带复现一句。

### B0 · 启动 / 健康

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| 启动 `main.py ui` | **OK** | 本轮已用上车间 |
| 浏览器打开 `127.0.0.1:8765` | **OK** | |
| `/api/health` 或首屏是否清楚「活着」 | **OK** | agent 侧 health ok |
| 其它（端口占用、venv 等） | **未用** | |

### B1 · 获取 Capture

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| 本地文件获取 | **未用** | |
| YouTube | **OK**（长片摩擦） | 成功落卡；约 49min 无字幕走 ASR 时进度久停 35%，属时长非故障 |
| Bilibili | **OK** | 成功落卡 · job done 100% |
| Twitter / X 单条（若用） | **未用** | |
| 音频 / 图（若用） | **未用** | |
| 任务进度 / 失败信息是否可读 | **摩擦** | 长 YouTube ASR 期间进度钉在 35%，易误判卡住；结果最终 ok |
| **Owner 总评（获取）** | **OK** | 「除 YouTube 因时长较长外，其他都正常，很好」 |

### B2 · 沉淀 Distill

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| compile / 沉淀出包 | | |
| 包结果是否好找、好懂 | | |
| 维护 · 删除（若用） | | |
| LLM 选择 / 本机 Ollama（若用） | | |

### B3 · 重组 Reconstruct

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| 从索引建图 / 出 view | | |
| Taxonomy 大纲分组 | **OK** | 「很好，就是我期望的」 |
| 点 KO 打开正文 | **摩擦→修** | 期望可直接点开；已落 0.6.2 |
| 关系是否帮你理解业务题 | | |
| 结果是否好读 | | |

### B4 · 检索 Retrieve（主入口）

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| 通道 proprietary / general 是否好选 | | |
| Taxonomy 大纲 + 点开知识 | **OK / 待复测** | 大纲形态符合期望；打开正文需重启 UI≥0.6.2 复测 |
| Top-K 标题/路径是否够判定「命中」 | | |
| 相关度/排序体感 | | |
| 负例感（general 不漏专有）若试过 | | |

### B5 · 组卡 Family

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| Family 查找 / 打开 | | |
| 勾选成员（如 W/D/H4） | | |
| 多卡布局 / 持久（若用） | | |

### B6 · 表达 Express

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| lecture / paper 草稿 | | |
| animate / GIF | | |
| 配音 / wav（若用） | | |
| renderer 选择或自动结果 | | |

### B7 · 车间整体 / 壳

| 项 | 级 | 一句话反馈 |
|----|-----|------------|
| 五段导航是否好找 | | |
| 每段「一个主任务」是否清楚 | | |
| Job 失败是否可读 | | |
| 设置 / 版本信息 | | |
| 整体一句（最想改的一件事） | | |

### B8 · 本轮总评（必填）

| 问 | 答 |
|----|-----|
| 本轮最有价值的一步 | 获取：YouTube + Bilibili 均成功沉淀 |
| 本轮最烦人的一步 | 长 YouTube 无字幕 ASR 等待久 + 进度停在 35% |
| 若只能改一件事（仍不解冻 H4 / 不扩 SETV） | （可选）ASR/下载阶段进度细分，减少误判卡住 |
| 还愿不愿继续用 Archive 答下一题？ ☑ 愿（获取段） ☐ 暂缓 · 原因： Owner：「其他都正常，很好」 |

---

## Gap 汇总（会话结束时填 · 轨 A）

| Metric | Value |
|--------|-------|
| 已答题数 | |
| usable | |
| A | |
| B | |
| C | |
| D | |

### Tickets（仅有 gap 或阻塞反馈时）

| 来源 | Class / 级 | 摘要 | Owner | Action |
|------|------------|------|-------|--------|
| 轨 A gap | A/B/C/D | | | |
| 轨 B 阻塞 | UX/Ops | | KF | 观察；不自动扩架构 |

### 本轮签收（结束时）

```text
Status:      OPEN → …
轨 A:        usable / A/B/C/D 计数见上
轨 B:        分功能表已填 ☐ · 总评已填 ☐
Archive 判定: （按题累计，不因 Ops ISSUE / 摩擦反馈翻盘）
Ops 备注:    Twitter / TTS 已知 ISSUE 仍有效
Signed:
Next:
Forbidden:   Matrix expand · THAW H4 · SETV scope expand · KF→SETV 提需求
```

---

## 指针

- **入口（先读）** [`UAT_ENTRY_V0.md`](UAT_ENTRY_V0.md)
- 章程 [`UAT_USER_CONSUME_V0.md`](UAT_USER_CONSUME_V0.md)
- SOP [`../ops/CONSUME_USER_HANDBOOK_V0.md`](../ops/CONSUME_USER_HANDBOOK_V0.md)
- Skill 消费 [`../interop/DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md) · phase-out [`../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md)
- UI 五段 [`../ui/WEB_UI_v0.md`](../ui/WEB_UI_v0.md)
- 首轮结案 [`UAT_SESSION_LOG_20260828.md`](UAT_SESSION_LOG_20260828.md) · [`OWNER_INTERPRET_UAT_SPLIT_20260828.md`](OWNER_INTERPRET_UAT_SPLIT_20260828.md)
