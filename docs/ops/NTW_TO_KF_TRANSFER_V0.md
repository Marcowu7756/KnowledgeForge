# NTW → KnowledgeForge 可平移项

```yaml
doc_id: KF-NTW-TRANSFER-V0
as_of: 2026-09-01
status: ACTIVE
source: D:\NTW_Shanghai_OP\docs\VISION.md
```

Napoleon 是 **Dubbing 实验场**。KF 是 **知识保存 / 检索 / 表达**。Identity 可以跨项目；管线、引擎、成片不要搬。

```text
平移概念与 Gate
不平移 Runtime / 视频 / 云端 TTS / 方言对照
```

---

## 已经在 KF 的（加固，不要重写）

| NTW 结论 | KF 落点 |
|---|---|
| Voice Identity ⟂ Language ⟂ Script | `docs/ops/VOICE_IDENTITY_V0.md` |
| 英语素材用英语 seed | `voice_for_language("en")` → `me_en`；`.cursor/rules/voice-language-seed.mdc` |
| Seed 是身份，不是成品声轨 | `me` / `me_en` 各 10–12s；zh 长源仍在 NTW；**en 长源** = Owner 授权儿子样本（见 [`VOICE_IDENTITY_V0.md`](VOICE_IDENTITY_V0.md)） |
| 引擎合同不同 | NTW 可用长 seed + Qwen-VC；KF/F5 要短样本 + transcript |
| 授权音色 | 槽位只 `me` / `me_en`；`me`=Owner zh · `me_en`=授权英语（现为儿子样本）；其它亲属另 profile |

这些已经对。不要为了「对齐 NTW」再做一套配音流水线。

---

## 应该平移的概念（进 KF 表达层，不是配音层）

### 1. KO = Canonical Meaning

NTW 商务场景要的：

```text
中文 → Canonical Meaning → 日文
```

KF 已经有这层：**KnowledgeObject 是语义 SoT**，GIF / 旁白只是 Expression。

因此 KF 的正确路径是：

```text
KO
 ↓
中文旁白 / 英语旁白 / （以后）其他语言旁白
```

禁止：

```text
中文旁白稿 → 再翻成英语再 TTS
```

那是语义升级和二次失真。翻译发生在 **KO → 目标语表达**，不发生在「已经写成的中文讲解稿」上。

### 2. 知识场景的 Accuracy First

Napoleon 可以 `Naturalness > Accuracy`（娱乐听对照）。KF 是知识讲解：

```text
Accuracy ≥ Naturalness
Semantic Fidelity > 音色像不像
```

旁白好听但不能讲错机制、数字、关系。TTS 失败可以记 Ops ISSUE；**语义错了不能出 express**。

映射到现有门：classification / export gate 管「能不能表达」；还缺的是「这段旁白有没有把 KO 讲对」。先当人工听感/校对门，不要做成自动评分器。

### 3. 语言可以扩张，Gate 不能扩张

KF 现在只稳中/英。NTW 证明：能合成 ≠ 可当教材。

若以后 `express` 出日语/意大利语旁白：

- 有对应 seed 就用（`me_ja` 这类）；没有就跨语种，并标 LISTEN_ONLY
- 字准未验证 → 不得当教学交付
- 不要把 NTW 的日/意/德听感外推成 KF 旁白能力

### 4. Voice Identity ≠ 目标台词

不要把「要朗读的知识稿」录进 seed 再生成同一段。那是复读，不是 Identity。

`me_en` 的 F5 短样本只当 **注册参考**（当前 transcript：作业句片段），不要循环拿 seed 正文当英语知识旁白来源。证据：[`../audit/ME_EN_SON_SEED_20260901.md`](../audit/ME_EN_SON_SEED_20260901.md)。

### 5. Visual Identity 继续正交

KF 的 GIF / Manim 是 **知识可视化**，不是换脸数字人。NTW Visual Identity 不并进 KF。

---

## 可做的小代码修正（仍属 KF，不是搬 NTW）

~~`derive_audio_from_ko` 无论 KO 语言都套中文模板~~ → **已修**（2026-09-01）

旁白跟 KO **同语言**：中文 → `me` · 英文 → `me_en` · 其他 → HOLD。  
SoT：[`LANGUAGE_EXPRESSION_V0.md`](LANGUAGE_EXPRESSION_V0.md)

`voice_hint` 目前只有 `zh | en`。在 KF 真正要讲第三种语言之前，不要加 `me_it` / `me_de`。

---

## 不要平移

| NTW 项 | 为什么留下 |
|---|---|
| 视频、时间窗、BGM、HEVC、字幕烧录 | KF 不配视频 |
| Qwen-VC / DashScope / CosyVoice | KF 本地 F5；云端密钥不进本仓库 |
| 沪语 A/B、谐音字 | 方言实验，不是知识旁白 |
| Napoleon 8 句 Language Benchmark | 对照集属于 NTW 实例 |
| `--it-only` / `--de-only` / mix render | 配音 Runtime |
| 实时 ASR ↔ TTS 对话 | 不是 KF 产品 |
| Shadowing 学习教练 | 独立产品；KF 最多提供「正确的 KO 旁白」当示范素材 |
| 把 NTW 长 seed 直接塞给 F5 | 引擎合同已禁止 |

---

## 分工（钉死）

```text
NTW     Identity × Language × Rendering 实验场（视频配音 · 听感）
KF      Knowledge First — KO → Expression → Renderer（Text / Audio / Visual / …）
DS      S15 只读 Research Producer（SEALED）；S03 = 配音合同 only · invoke DENY
共享    授权 Voice Identity 槽（me / me_en）+ 正交规则 · SoT [`VOICE_IDENTITY_V0.md`](VOICE_IDENTITY_V0.md)
```

NTW 验证「同一 Identity 在不同 Language 下听感如何」；KF 只消费 **已允许进入表达层** 的能力，不因 NTW 某语言「好听」就自动获得教学/知识表达资格。

**Digital Human 未来接入 KF = 新 Renderer，不是把数字人变成 KF 核心。**

KF 不因为日/意/德好听，就声明「知识可以用你的声音讲任何语言」。那要在 **KO 语义正确 + 目标语旁白字准** 之后才能说。
