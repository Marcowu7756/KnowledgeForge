# Voice Identity v0 — 跨项目复用边界

```yaml
doc_id: KF-VOICE-IDENTITY-V0
as_of: 2026-09-01
status: ACTIVE
posture: user-owned / explicitly authorized only
```

## 正交钉

```text
Voice Identity  ⟂  Script / Language / 项目 / 引擎合同
```

| 轴 | 含义 |
|----|------|
| **Identity** | 谁的音色（你 / 亲属…）· 须本人授权 |
| **Script / Language** | 读知识卡 · 沪语 OP · 别的剧本 |
| **引擎合同** | NTW 可用整段种子；KF/F5-TTS 宜 10–12s + transcript |

同一份 Identity **可以**跨 NTW 与 KnowledgeForge；**不要**把某一引擎的最优输入格式当成「一份 WAV 到处无脑塞」。

**目标语言对齐采样语言。** 英语素材用英语 seed（`me_en`），不要用普通话 `me` 去克隆英语。

## KnowledgeForge 落地（本机）

| 项 | 值 |
|----|-----|
| 默认 Profile | `me`（普通话；`data/voices/DEFAULT` 必须保持 `me`） |
| 英语 Profile | `me_en`（英语素材自动选用；**不要**设成 DEFAULT） |
| 普通话源 | `D:\NTW_Shanghai_OP\voice\my_voice.wav`（产品说明书朗读 · ~147s · 48k） |
| 英语源 | `D:\NTW_Shanghai_OP\voice\my_voice_en.wav`（原英文字幕朗读 · ~50s · 48k） |
| KF 普通话样本 | 自源片 **t≈2.0s** 起截取 **12s mono 24 kHz** → `data/voices/me/sample.wav` |
| KF 英语样本 | 自源片 **首句起 t≈0.95s** 截取 **10s mono 24 kHz** → `data/voices/me_en/sample.wav`（完整两句，避免拦腰切断） |
| 普通话 Transcript | Whisper 对截取段转写 |
| 英语 Transcript | 与截取段对齐的原英文字幕正写（非整段 50s） |
| 亲属预留 | 另建 profile（如 `family_<name>`）；**禁止**未授权克隆 |

```powershell
# 普通话（默认）
python main.py voice import data/voices/_staging/me_ref_12s.wav --name me

# 英语（旁路默认；不要让 DEFAULT 变成 me_en）
python main.py voice import data/voices/_staging/me_en_ref_12s.wav --name me_en --no-default --transcript "My enemies are many. My equals are none. In the shade of olive trees they said Italy could never be conquered."
python main.py voice list
```

自动选用：`voice_for_language("en")` → `me_en`（若已导入）；中文与未指定语言仍走 `me`。  
**Language ≠ Translation：** [`LANGUAGE_EXPRESSION_V0.md`](LANGUAGE_EXPRESSION_V0.md)  
`express --voice me` 会强制普通话 seed，英语卡不要这样写。

### Skill 消费（目标口 · legacy 暂留）

朗读能力逐步改为 Digital Self **S02**（KF 只 `ds invoke`，Identity 在 DS）：

```powershell
python main.py ds invoke S02 --text "核心观点先读出来。" --language zh -o data\expression\_out.wav
```

KF 本地 `data/voices/me` · `me_en` 与 `voice speak` **暂不删**。对照：[`KF_SKILL_CONSUME_PHASEOUT_V0.md`](KF_SKILL_CONSUME_PHASEOUT_V0.md)。

## 禁止

- 克隆非授权他人音色
- 因「Identity 可复用」把 NTW 整段种子当作 F5 最优参考而不截取
- 把亲属样本与 `me` / `me_en` 混成同一 profile
- 用普通话 `me` 去克隆英语（或反过来）
- 导入 `me_en` 时把它设成 DEFAULT

> Identity 可跨项目；引擎合同按模型各备样本；语言对语言采样。

NTW 实验结论里，哪些概念可以进 KF、哪些必须留在配音实例：见 [`NTW_TO_KF_TRANSFER_V0.md`](NTW_TO_KF_TRANSFER_V0.md)。
