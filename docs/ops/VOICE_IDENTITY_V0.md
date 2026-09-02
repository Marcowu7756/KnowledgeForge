# Voice Identity v0 — 跨项目复用边界

```yaml
doc_id: KF-VOICE-IDENTITY-V0
as_of: 2026-09-01
status: ACTIVE
posture: user-owned / explicitly authorized only
refreshed: 2026-09-02
```

## 正交钉

```text
Voice Identity  ⟂  Script / Language / 项目 / 引擎合同
```

| 轴 | 含义 |
|----|------|
| **Identity** | 谁的音色（Owner / 亲属…）· 须本人或监护授权 |
| **Script / Language** | 读知识卡 · 沪语 OP · 别的剧本 |
| **引擎合同** | NTW 可用整段种子；KF/F5-TTS 宜 10–12s + transcript |

同一 **语言槽** 可以跨 NTW / KF / DS；**不要**把某一引擎的最优输入格式当成「一份 WAV 到处无脑塞」。

**目标语言对齐采样语言。** 英语素材用英语 seed（`me_en`），不要用普通话 `me` 去克隆英语。

---

## 授权实例（本机）

| Profile | Language | Identity | 说明 |
|---------|----------|----------|------|
| `me` | zh | **Owner** | 默认；`data/voices/DEFAULT` **必须**保持 `me` |
| `me_en` | en | **Owner-authorized son**（2026-09-01） | 英语槽；**禁止**设成 DEFAULT |

`me_en` 是 **英语语言槽名**，不是「Owner 本人英语声」的承诺。  
2026-09-01 Owner 授权用儿子英语录音替换该槽；普通话槽 `me` 仍是 Owner。

亲属其它语言 / 其它人 → **另建** profile（如 `family_<name>`）；禁止混进 `me`。

---

## KnowledgeForge 落地（本机）

| 项 | 值 |
|----|-----|
| 默认 Profile | `me` → `data/voices/DEFAULT` = `me` |
| 英语 Profile | `me_en`（`voice_for_language("en")`；**不要** DEFAULT） |
| 普通话源 | `D:\NTW_Shanghai_OP\voice\my_voice.wav`（~147s · 48k） |
| 英语源 | `C:\Users\Panzer\Downloads\9月1日.m4a`（Owner 授权 · 儿子 · 2026-09-01 · ~283s） |
| KF 普通话样本 | t≈2.0s 起 · **12s** mono 24 kHz → `data/voices/me/sample.wav` |
| KF 英语样本 | 首句 t≈0.89s 起 · **12s** mono 24 kHz → `data/voices/me_en/sample.wav` |
| 英语 Transcript | `A writing assignment, the English teacher gave the class a` |
| DS Identity pack（S02 SoT） | `D:\DigitalSelf\data\identity\voice/` · `MANIFEST.yaml` 路由 zh→`me` · en→`me_en` |
| 证据 | [`../audit/ME_EN_SON_SEED_20260901.md`](../audit/ME_EN_SON_SEED_20260901.md) |

```powershell
# 普通话（默认）
python main.py voice import data/voices/_staging/me_ref_12s.wav --name me

# 英语（旁路默认；不要让 DEFAULT 变成 me_en）
python main.py voice import data/voices/_staging/son_en_f5_12s.wav --name me_en --no-default --transcript "A writing assignment, the English teacher gave the class a"
python main.py voice list
# 确认 DEFAULT 仍是 me
Get-Content data\voices\DEFAULT
```

自动选用：`voice_for_language("en")` → `me_en`（若已导入）；中文与未指定语言仍走 `me`。  
**Language ≠ Translation：** [`LANGUAGE_EXPRESSION_V0.md`](LANGUAGE_EXPRESSION_V0.md)  
`express --voice me` 会强制普通话 seed，英语卡不要这样写。  
Cursor 规则：`.cursor/rules/voice-language-seed.mdc`。

### Skill 消费（目标口 · legacy 暂留）

朗读走 Digital Self **S02**（KF 只 `ds invoke`，Identity 在 DS pack）：

```powershell
python main.py ds invoke S02 --text "核心观点先读出来。" --language zh -o data\expression\_out.wav
python main.py ds invoke S02 --text "A short English card." --language en -o data\expression\_out_en.wav
```

KF 本地 `data/voices/me` · `me_en` 与 `voice speak` **暂不删**（legacy / F5 镜像）。  
对照：[`KF_SKILL_CONSUME_PHASEOUT_V0.md`](KF_SKILL_CONSUME_PHASEOUT_V0.md) · [`../interop/DIGITAL_SELF_SKILLS_V0.md`](../interop/DIGITAL_SELF_SKILLS_V0.md)。

S03 配音 = DS **合同 only**（invoke DENY）；KF **不**配视频。见 DS `docs/skills/S03_Dubbing.md`。

---

## 禁止

- 克隆非授权他人音色
- 把长源片整段塞给 F5（须 10–12s + transcript）
- 把儿子英语样本混进普通话 `me`
- 用普通话 `me` 去克隆英语（或反过来）
- 导入 `me_en` 时把它设成 DEFAULT
- 因 `me_en` 好听就外推日/意/德教学资格（仍 HOLD）

> Identity 槽可跨项目；引擎合同按模型各备样本；语言对语言采样；DEFAULT 永不改成 `me_en`。

NTW 哪些概念可进 KF：[`NTW_TO_KF_TRANSFER_V0.md`](NTW_TO_KF_TRANSFER_V0.md)。
