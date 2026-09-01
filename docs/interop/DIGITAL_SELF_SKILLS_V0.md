# KnowledgeForge · consume Digital Self Skills

```yaml
doc_id: KF-DS-SKILLS-CONSUME-V0
as_of: 2026-09-01
status: LANDED · CONSUME ONLY
owner_gate: DS G4_NARROW_SKILL_PACKAGES
kf_rewrite_of_ds: FORBIDDEN
ds_rewrite_of_kf: FORBIDDEN
```

$$
\boxed{\text{KF = Brain}}
\qquad
\boxed{\text{DS = Senses + Body + Skills}}
\qquad
\boxed{\text{KF calls catalog; KF does not become the Skill Runtime}}
$$

**Phase-out：** 旧 native 程序（`voice` / `express` / UI narrate 等）**暂时保留**；能力逐步改为 **Skill 调用**。文档与 SOP 先换，代码后迁。地图：[`../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md)。

Machine flags: [`digital_self_catalog_v0.yaml`](digital_self_catalog_v0.yaml)  
Producer SoT: `D:\DigitalSelf\skills\CATALOG.yaml` · `D:\DigitalSelf\docs\SKILL_EXPORT.md`

---

## CLI (this repo)

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe main.py ds list
.\.venv\Scripts\python.exe main.py ds invoke S00 --text "NAS100 H1 回测值得沉淀"
.\.venv\Scripts\python.exe main.py ds invoke S06 --intent "打开 YouTube 搜 NVIDIA"
.\.venv\Scripts\python.exe main.py ds invoke S15 --scene setv --task "cite artifact_id=demo"
.\.venv\Scripts\python.exe main.py ds invoke S16 --text "一段草稿" --depth W0
.\.venv\Scripts\python.exe main.py ds invoke S02 --text "核心观点先读出来。" --language zh -o data\expression\_ds_s02.wav
```

Stdout is **one JSON object**. Use KF venv: S02 TTS runs neighbor F5 inside that interpreter.

---

## What KF may do

| Skill | KF role | Live here? |
|---|---|---|
| S00 AttentionGate | Filter before Owner interrupt / `submit_candidate` | rules |
| S02 ReadAloud | Optional mouth using DS Identity pack | F5 via this venv |
| S06 Browser | Observation **plan** only | no |
| S15 ResearchOp | Research **plan**; SETV cite scene | no |
| S16 Compose | W0 local marks; not KF Reader / not LLM Writer | no |

KF still owns: classify / index / Admission / KO.  
DS Skills **pass candidates**. They do not compile knowledge inside Digital Self.

Native `python main.py voice speak` / UI ▶ 听讲解 / `express` TTS remain as **legacy** until phased out.  
S02 is the **exported Skill call** for mouth; prefer documenting `ds invoke S02` for new SOP steps. See phase-out map.

---

## Parameters (complete)

### S00 AttentionGate

| Flag | Type | Required | Meaning |
|---|---|---|---|
| `--text` | string | no (empty → garbage) | observation / abstract |
| `--relevance` | float | no | &lt; 0.2 → garbage |
| `--importance` | float | no | ≥ 0.8 → important |
| `--utility` | float | no | reserved |

OK JSON: `class` ∈ {garbage, useful, important}; `interrupt` only if important; `pass_kf` if useful.

Aliases: `S00` · `Attention` · `AttentionGate`.

### S02 ReadAloud

| Flag | Type | Required | Meaning |
|---|---|---|---|
| `--text` | string | one of text/file | script in **same language** as seed |
| `--file` | path | one of text/file | utf-8 text file |
| `--language` | zh \| en | no | default detect; mismatch → error |
| `-o` / `--output` | path | **yes** | wav |

Routing: zh → Identity `me`; en → `me_en`. Samples live under `D:\DigitalSelf\data\identity\voice\`, not KF `data/voices/`.

Forbidden: ZH→EN TTS, EN→ZH TTS, 沪语, writing KO from this Skill.

### S06 Browser

| Flag | Type | Required | Meaning |
|---|---|---|---|
| `--intent` | string | yes | what the Hand should do |
| `--url` | string | no | optional start URL |
| `--live` | flag | no | **denied** `LIVE_BROWSER_NOT_AUTHORIZED` |

Sites are scenes. Do not add YouTube/Gmail Skills in KF.

### S15 ResearchOp

| Flag | Type | Required | Meaning |
|---|---|---|---|
| `--scene` | mt5_backtest \| ashare \| setv | yes | neighbor system |
| `--task` | string | yes | research intent |
| `--action` | string | no, default `research` | L4 verbs denied |
| `--live` | flag | no | **denied** `LIVE_COMPUTE_NOT_AUTHORIZED` |

L4 (`place_order`, `cancel_order`, `modify_order`, `withdraw`, `deposit`, `transfer`) → `L4_NO_AUTHORIZABLE_PATH`. No order API.

Aliases: `S14` / `SetvQuery` → this Skill, `--scene setv`.

### S16 Compose

| Flag | Type | Required | Meaning |
|---|---|---|---|
| `--text` | string | yes | draft intent |
| `--depth` | W0–W4 | no, default W0 | W4 = publish path |
| `--publish` | flag | no | **denied** |
| `--claims-json` | JSON list | no | `{tag, evidence_ref?}` |

`--publish` or `W4` → `CAN_WRITE_NEQ_CAN_PUBLISH`.  
`FACT` without `evidence_ref` → `UNMARKED_ERROR`.

Aliases: `S08` Summarize · `S09` Explain.

---

## Hard stops

```text
KF ↛ rewrite Digital Self Skills
KF ↛ Playwright / live browser from this consume door
KF ↛ MT5 / AShareLib executor from this consume door
KF ↛ order / money movement   (no authorizable path)
KF ↛ auto-publish because Compose returned JSON
S02 ↛ replace Language ≠ Translation
```

---

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/interop/test_digital_self_skills.py -v
```

*KF · consume DS Skills · 2026-09-01*
