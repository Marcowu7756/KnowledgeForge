# KF · Skill Consume Phase-Out Map v0

```yaml
doc_id: KF-DS-SKILL-PHASEOUT-V0
as_of: 2026-09-01
status: ACTIVE · GRADUAL
posture: KF = Skill consumer only · legacy kept · phase out by replacement
```

$$
\boxed{\text{KF = Brain / Knowledge}}
\qquad
\boxed{\text{Digital Self = Senses + Body + Skills}}
\qquad
\boxed{\text{KF calls Skills; KF does not become Skill Runtime}}
$$

## 冻结口径

| 钉 | 含义 |
|----|------|
| **消费端** | KF 只调用 Digital Self 目录 / `skills/invoke.py` |
| **不抄实现** | 不把 Skill 执行体搬进 KF；不改成第二个 Runtime |
| **旧程序暂留** | 现有 `voice` / `express` / UI narrate 等 **先不动** |
| **逐步 phase out** | 文档与 SOP **先**改成「legacy → skill」；代码按门替换，不一次砍光 |

```text
今天:   KF native path 仍可用（legacy）
同时:   KF 已能 ds invoke 调 DS Skills（consume）
以后:   同类能力优先写 Skill 调用；native 入口标 legacy → 再删
禁止:   为「对齐 Skill」在 KF 里重写一套 DS Runtime
```

## Legacy → Skill 对照（文档先换）

| 能力意图 | Legacy（暂留） | Skill 消费（目标） | Phase |
|----------|----------------|--------------------|-------|
| 注意力 / 是否打断 Owner | （无独立门 · 或人工） | **S00** `AttentionGate` | **优先写进 SOP** |
| 同语言朗读（嘴） | `voice speak` · UI ▶ 听讲解 · `express` TTS | **S02** `ReadAloud`（DS Identity） | 旁路并存 → 后迁口 |
| 浏览观察计划 | （无 / 手工） | **S06** Browser（plan only · 禁 `--live`） | 仅 Skill |
| 研究计划 / SETV cite 场景 | `retrieve` / compose 草稿 | **S15** ResearchOp（禁 L4） | 并存；L4 永不进 KF |
| 草稿标注 / 不发布 | `compose` lecture/paper | **S16** Compose（禁 `--publish`） | 并存；发布仍 Owner |

**KF 仍永久拥有（不 phase out）：** Capture 沉淀 · KO / Admission · Index · Retrieve · Taxonomy · Access · Archive 判定。  
Skills **只传候选**；不在 DS 内 compile 知识。

## SOP / 文档替换顺序

| 顺序 | 文档 | 改法 |
|------|------|------|
| 1 | [`DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md) | 消费协议 SoT（已有） |
| 2 | **本页** | phase-out 地图 |
| 3 | [`OPS_RUNBOOK_V0.md`](OPS_RUNBOOK_V0.md) | 操作清单加 `ds list` / `ds invoke`；标 legacy |
| 4 | [`CONSUME_USER_HANDBOOK_V0.md`](CONSUME_USER_HANDBOOK_V0.md) | 消费主线旁挂 S00 / 可选 S02 |
| 5 | [`LANGUAGE_EXPRESSION_V0.md`](LANGUAGE_EXPRESSION_V0.md) · [`VOICE_IDENTITY_V0.md`](VOICE_IDENTITY_V0.md) | 钉：KF derive = Meaning→Script；S02 = 嘴 Skill |
| 6 | [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) · README | 入口指针；不强制砍 UI narrate |

**代码替换规则（以后做，不是现在）：** 仅当 Skill 门禁 + 测试绿 + Owner 签收后，才把某 native 入口标 `DEPRECATED` 或改薄壳为 `ds invoke`。

## 硬停

```text
KF ↛ 抄 Digital Self Skill 实现
KF ↛ Playwright / live browser 消费门
KF ↛ MT5 / 下单 / 资金 L4
KF ↛ 因 Compose JSON 自动发布
KF ↛ 一次删光 voice/express「为了看起来像 Skill」
文档 ↛ 写「KF 已是数字人 Runtime」
```

## CLI 速查

```powershell
.\.venv\Scripts\python.exe main.py ds list
.\.venv\Scripts\python.exe main.py ds invoke S00 --text "…"
.\.venv\Scripts\python.exe main.py ds invoke S02 --text "…" --language zh -o data\expression\_out.wav
# legacy 仍可用（暂不删）:
.\.venv\Scripts\python.exe main.py voice speak "…" --voice me
```

Producer SoT：`D:\DigitalSelf` · 证据：[`DS_SKILL_CONSUME_20260901.md`](../audit/DS_SKILL_CONSUME_20260901.md)

> **Brain 调 Skill；Body 不进 KF；旧路先留，文档先换，代码后迁。**
