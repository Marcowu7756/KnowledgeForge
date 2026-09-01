# Language Expression v0 — 同语言旁白，不翻译

```yaml
doc_id: KF-LANGUAGE-EXPRESSION-V0
as_of: 2026-09-01
status: FROZEN
posture: Language ≠ Translation · KO = Meaning
```

## 冻结钉

```text
Language ≠ Translation

ZH input  →  ZH expression  →  me
EN input  →  EN expression  →  me_en
```

**禁止隐式路径：**

```text
ZH → EN → TTS    ✗
EN → ZH → TTS    ✗
```

KF **不负责**把一种语言变成另一种语言；KF **只负责**把已有语言的 KnowledgeObject **准确表达**出来。

## KF 当前口径

| 输入语言 | 表达语言 | Voice | 状态 |
|----------|----------|-------|------|
| 中文 | 中文 | `me` | **允许**（默认母语通道） |
| 英文 | 英文 | `me_en` | **允许** |
| 中文 → 英文 | 翻译 | — | **暂不做** |
| 英文 → 中文 | 翻译 | — | **暂不做** |
| 其他（`ja` / `de` / …） | 任意 | — | **HOLD** |

## 正交

```text
Identity  ⟂  Language  ⟂  Meaning (KO)
```

| 轴 | 职责 |
|----|------|
| **Meaning** | KnowledgeObject canonical content |
| **Language** | 旁白与 KO **同语言** |
| **Identity** | 授权音色 `me` / `me_en` / … |
| **Script** | 由 KO 派生的 Expression（非 seed 复读） |

优先级：

$$
\boxed{\text{Accuracy} \rightarrow \text{Comprehension} \rightarrow \text{Naturalness}}
$$

## `derive_audio_from_ko` 职责（已实现）

```text
KO
 ↓
检查 language（canonical content，非翻译）
 ↓
选择对应 expression template（zh | en）
 ↓
选择对应 authorized voice（me | me_en）
 ↓
TTS → audio.wav
```

| KO 语言 | 表达 | Voice |
|---------|------|-------|
| `zh` | 中文旁白 | `me` |
| `en` | English narration | `me_en` |
| `ja` / 其他 | — | **HOLD** (`AudioLanguageNotSupportedError`) |

实现：`app/expression/derive.py` · 测试：`tests/express/test_derive_audio_from_ko.py`

## Expression Layer · Renderer 栈（钉死）

```text
KnowledgeForge
      │
KnowledgeObject（Canonical Meaning — 不变）
      │
Expression Layer（Script / IR — 由 KO 派生，同语言）
      │
      ├── Text
      ├── Audio          ← V0（▶ 听讲解）
      ├── Visual         ← GIF / 动图（已有）
      └── Digital Human  ← future · 能力接入，非 KF 核心
```

**现在：**

```text
KO → 同语言旁白 → Voice Identity（me / me_en）→ Audio
```

**未来（成熟后）：**

```text
KO → 同语言旁白 → Voice Identity → Digital Human Renderer → 视频讲解
```

数字人可同步：说话 · 表情 · 手势 · 屏幕上的卡 / 公式 / 图表 —— 但都属于 **Presentation / Rendering**，不是 Knowledge Layer。

$$
\boxed{\text{Digital Human} \subset \text{Expression Renderer}}
\qquad
\boxed{\text{Digital Human} \not\subset \text{Knowledge Layer}}
$$

数字人 **不能改变 KO 的知识内容**；只是另一种表达载体。

扩展路径（无需改 KO 基础架构）：

| 阶段 | KO → |
|------|------|
| 现在 | Text · Audio |
| 以后 | Slides · Animation · **Digital Human** |
| 更后 | Interactive Tutor（听问 → 调 KO → 分身回答）— **独立阶段，非当前** |

**今天把 `KO → Expression → Audio` 做干净，未来数字人只是多一个 Renderer。**

## V0 产品：看 + 听

```text
KnowledgeObject
      │
      │ Canonical Meaning
      ↓
Expression Layer（同语言）
      │
      ├── zh → 中文讲解 → me
      └── en → English narration → me_en
      ↓
Audio（车间预览 · ▶ 听讲解）
```

**V0 范围：** KO → Narration Script → TTS → 可播放 `audio.wav`  
**V0 不做：** 翻译 · 多语言数字人 · 视频 · BGM · lip-sync · 公式高亮同步

Gate（先验证再扩展）：

1. 内容有没有讲错  
2. 语言是否自然  
3. 声音是否适合长期听  

## 与 Digital Self Skill 的分工（phase-out）

| 层 | 谁做 | 说明 |
|----|------|------|
| **Meaning → Script** | KF `derive_audio_from_ko` | 同语言旁白稿 · Language ≠ Translation |
| **嘴 / TTS（Skill）** | DS **S02** via `ds invoke` | 目标口；Identity 在 DS pack |
| **嘴 / TTS（legacy）** | KF `voice speak` · UI ▶ 听讲解 · `express` | **暂留** · 逐步迁到 S02 |

地图：[`KF_SKILL_CONSUME_PHASEOUT_V0.md`](KF_SKILL_CONSUME_PHASEOUT_V0.md)。  
**不要**为迁 Skill 在 KF 内再造一套 TTS Runtime。

## NTW 分工

NTW = Identity × Language **听感实验场**（视频配音 · 沪语等）  
KF = Identity × Knowledge **表达层**（卡 → 同语言旁白 / 动图）

NTW 的日语 / 意大利语实验 **不自动** 成为 KF 产品能力。

## 相关

- Voice Identity：[`VOICE_IDENTITY_V0.md`](VOICE_IDENTITY_V0.md)
- NTW 平移边界：[`NTW_TO_KF_TRANSFER_V0.md`](NTW_TO_KF_TRANSFER_V0.md)
- Taxonomy / Access：[`../audit/TAXONOMY_VS_ACCESS_V0.md`](../audit/TAXONOMY_VS_ACCESS_V0.md)
- Digital Self 导出 Skill（KF **调用**，不改 DS Runtime）：[`../interop/DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md)

> **KO = Meaning · 同语言 Expression · 授权 Voice · Renderer 可扩展 · 不翻译 · Knowledge First。**
