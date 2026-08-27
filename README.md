# KnowledgeForge

Local engine for **PAILE** — Personal AI Learning Engine.

## One-line definition (v0.2)

> Use AI to **decompose, abstract, reconstruct, and re-express** knowledge — turning existing materials into a personal system optimized for understanding, learning, and creation.

Not an AI notes app. Not a summarizer. Not a search-only RAG store.

$$
\boxed{\textbf{AI Knowledge Reconstruction Engine}}
$$

---

## Core shift

Traditional path:

```
资料 → 阅读 → 理解 → 记忆
```

PAILE adds:

$$
\boxed{拆解 + 抽象 + 重组 + 重新表达}
$$

```
Knowledge → Representation Space → New Knowledge Form
```

| Traditional RAG | PAILE |
| --- | --- |
| Store knowledge | Reconstruct knowledge |
| Search answers | Generate understanding paths |
| Text-first | Multi-modal expression |
| Fixed author structure | Dynamic learner structure |
| Answer questions | Augment cognition |

---

## Reconstruction loop

```
教材 / 视频 / 图片 / 课堂 / 论文
        ↓
Knowledge Extraction
        ↓
Knowledge Abstraction
        ↓
Knowledge Reconstruction   ← core
        ↓
Multi-modal Expression
        ↓
Human Understanding
        ↓
Feedback / Creation
```

Math view:

- Compress: \(K_s \rightarrow K_d\) (source → dense units)
- Expand: \(K_d \rightarrow K_p\) (notes / audio / animation / derivation)
- Transfer: \(K_p \rightarrow K_c\) (new understanding / application / creation)

---

## Five layers (product)

| Layer | Role | Now |
| --- | --- | --- |
| 1 Input | OCR / ASR / parsers / YouTube / Bilibili / Twitter | YouTube + Bilibili + Twitter + MD/TXT/PDF + image OCR + folder search |
| 2 Distill | Atomic Knowledge Units | LLM compress → Markdown/JSON |
| 3 Reconstruct | Reorganize by concept / stage / question | 🔜 next after asset density |
| 4 Express | Notes, TTS, Manim, interactive | animate GIF + express GIF+TTS MVP |
| 5 Feedback | Mastery / gaps / next path | later |

---

## Phase 1 engineering goal (redefined)

MVP is **not** “upload → summarize”.

MVP is:

```
输入知识
  ↓
AI 拆解
  ↓
形成知识单元（Atomic KU）
  ↓
保存为个人知识资产（+ 可选索引）
```

Reconstruction (作者结构 → 学习者结构) and multi-modal expression come **after** enough atomic units exist.

Still protect this foundation:

$$
\boxed{Capture \rightarrow Decompose/Compress \rightarrow Knowledge Assets}
$$

---

## What works now

| Capability | Status |
| --- | --- |
| YouTube → captions/ASR → atomic Knowledge Unit | ✅ |
| Bilibili → subtitles/ASR → atomic Knowledge Unit | ✅ |
| Twitter/X → tweet or timeline signal digest | ✅ |
| Local MD/TXT/PDF/DOCX ingest | ✅ |
| **Derive**: English / Physics / Finance expansion | ✅ |
| **Express**: state GIF + clone TTS (your voice sample) | ✅ MVP |
| Voice bank: record / import → F5-TTS clone speak | ✅ |
| Fixed-folder keyword search (read-only external roots) | ✅ |
| Optional index (`INDEX.md` / jsonl / concept glance) | ✅ |
| Multi-provider LLM (`ollama` / `openai` / `gemini` / `deepseek`) | ✅ |
| Image OCR (`image` CLI, local PaddleOCR) | ✅ |
| **Harness** `compile` → KnowledgeObject package + evidence | ✅ P0 |
| `--rerun-step` animation / expression / manifest | ✅ P0 |
| **Expression** KO → Visual/Audio Expression → artifacts | ✅ P1 |
| **Reconstruct** Multiple KO → ConceptGraph → views | ✅ P2 v0.2 |
| **Retrieve** KO + Embedding (+ Graph) → KO hits | 🟡 P3 |
| Independent audio ingest (`audio` CLI) | ✅ |
| **Compose** retrieve → LLM → paper/lecture | 🟡 |
| Cross-unit reconstruction views | 🔜 |
| Embedding RAG | later |
| TTS / Manim / teaching feedback | later |
| Windows `.exe` UI | later |

---

## Setup

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\Activate.ps1
copy .env.example .env
python main.py models pull
python main.py models status
```

### Local-first policy (frozen)

Runtime intelligence should not depend on cloud APIs or HuggingFace downloads:

| Asset | Local path | Pull |
| --- | --- | --- |
| LLM | Ollama `qwen2.5:14b` | `ollama pull qwen2.5:14b` |
| ASR | `models/faster-whisper-medium` | `models pull --only whisper` |
| Embeddings (RAG) | `models/bge-small-zh-v1.5` | `models pull --only embed` |
| TTS clone | `models/F5-TTS` + `models/vocos-mel-24khz` | `models pull --only tts,vocos` |
| OCR | `models/paddlex` (PP-OCRv6) | `models pull --only ocr` |
| Formula OCR | `models/pix2tex` | `models pull --only pix2tex` |
| Voice sample | `data/voices/<name>/` | `voice record --name me` |

One-shot pull everything:

```powershell
python main.py models pull              # all local intelligence assets
python main.py models verify            # check + write models/LOCK.json
python main.py image path\to\scan.png   # OCR → Knowledge Unit (offline)
```

Set `HF_HUB_OFFLINE=1` and `HF_HOME=models/.hf` in `.env` after pulls. Cloud LLM keys remain optional fallback.

### 声音克隆（你的音色朗读）

```powershell
# 1) 拉 F5-TTS 模型（约 1.3GB，只需一次）
python main.py models pull --only tts

# 2) 录制 10–12 秒样本（按提示朗读固定句子，或自己 --transcript）
python main.py voice record --name me --seconds 12

# 3) 用你的声音读任意文本
python main.py voice speak "这是知识讲解测试。" --voice me

# 4) 展示层 express 也会优先用你的样本
python main.py express data\knowledge\某卡片.md --voice me
```

### 动图（纯动画，无需 TTS）

从知识卡片生成因果链 / 时间线 / 要点网络的 **GIF 动图**，不调用配音：

```powershell
# 规则编译（读 Mechanisms / Timeline / Key Points，秒出）
python main.py animate data\knowledge\某卡片.md --fast

# LLM 编译（更贴合全文，需 Ollama）
python main.py animate data\knowledge\某卡片.md
```

输出在 `data/expression/<卡片名>/`：`animation.gif`、`animation.json`、`ANIMATE.md`。

`express` = 动图 + 旁白；`animate` = 仅动图。

### Harness（编排层）

确定性流水线，不是自主 Agent。把摄入 / 知识 / 动图 / 旁白收成可审计包；包内以 **KnowledgeObject** + `manifest.json` 为事实来源：

```powershell
# 已有知识卡 → KnowledgeObject package（含动图）
python main.py compile data\knowledge\某卡片.md --from-card --animate --fast

# 本地文件 / 图片 / URL → KnowledgeObject + 可选表达
python main.py compile path\to\notes.md --animate --fast
python main.py compile path\to\scan.png

# 单步骤重跑（不整包重编）
python main.py compile --rerun-step animation --package data\packages\<id> --fast
python main.py compile --rerun-step expression --package data\packages\<id>
python main.py compile --rerun-step manifest --package data\packages\<id>
```

输出在 `data/packages/<id>/`：

| 文件 | 角色 |
| --- | --- |
| `knowledge_object.json` | 系统级知识对象（identity / source / content / relation / visual / audio / embedding / evidence） |
| `visual_expression.json` | P1：KO 派生的动图 IR（storyboard + intent + evidence） |
| `audio_expression.json` | P1：KO 派生的旁白 IR（script + voice + evidence） |
| `manifest.json` | 包级 SoT：步骤、模型版本冻结、artifact checksum、expression evidence |
| `knowledge.md` | 兼容 distill 时代的 Markdown 卡 |
| `animation.gif` / `narration.wav` | 由 Expression 渲染的产物（KO 不直接绑定文件） |

也可导入已有 WAV：`python main.py voice import sample.wav --name me --transcript "..."`

---

## CLI

```powershell
python main.py models status
python main.py models verify
python main.py models pull
python main.py youtube https://www.youtube.com/watch?v=xxxx
python main.py bilibili https://www.bilibili.com/video/BVxxxx
python main.py twitter https://x.com/user/status/1234567890
python main.py twitter @someaccount --timeline --limit 10
python main.py file path\to\notes.md --dest-subdir physics
python main.py image path\to\scan.png --dest-subdir physics
python main.py search D:\folder --keyword methodology --dest-subdir methodology
python main.py derive path\to\card.md --mode auto   # english|physics|finance|generic
python main.py voice record --name me --seconds 12
python main.py voice speak "用我的声音读这段话"
python main.py animate path\to\card.md --fast
python main.py compile path\to\card.md --from-card --animate --fast
python main.py compile --rerun-step animation --package data\packages\<id> --fast
python main.py reconstruct --from-index --view theme
python main.py reconstruct --from-index --view concept --seed 美债
python main.py reconstruct --from-index --min-confidence 0.5
python main.py reconstruct --evolve data\reconstruct\<id> --add path\to\card.md
python main.py reconstruct --from-index --view learning_path --tag 金融
python main.py retrieve index --from-index
python main.py retrieve query "美债信用风险" --graph data\reconstruct\<id> --top 5
python main.py compose paper "美债信用风险与美元地位" --top 5 --graph data\reconstruct\<id>
python main.py compose lecture "美债信用风险" --top 5
python main.py audio path\to\lecture.wav --dest-subdir notes
python main.py express path\to\card.md --voice me
python main.py index rebuild [--subdir NAME]
```

`derive` expands \(K_d \rightarrow K_p\):

| Subject | Mode | Output under `derived/` |
| --- | --- | --- |
| English (定语从句等) | `english` | examples, patterns, contrast, drills |
| Physics | `physics` | vivid process steps + Manim storyboard beats |

- External trees are **read-only sources**
- Outputs only under `data/`
- `--no-index` or `INDEX_ENABLED=false` disables indexing

---

## Knowledge Unit → KnowledgeObject (P0)

Distill 时代仍产出 Markdown 卡（兼容）：

`id`, `title`, `source`, `type`, `url`, `created`, `summary`, `concepts`, `definitions`, `key_points`, `mechanisms`, `relationships`, `timeline`, `claims`, `evidence`, `formulas`, `examples`, `prerequisites`, `unknowns`, `tags`

Harness `compile` 将其升级为 **KnowledgeObject**（`schema_version: 0.1`）：

```
identity · source · content · relations · visual · audio · embedding · evidence · lifecycle
```

`manifest.json` 冻结模型版本（llm / embed / asr / tts / ocr / harness）与步骤证据，支持 `--rerun-step`。

Aligned toward PAILE distill targets (additive later):

`subject`, `chapter`, `mistakes`, mastery metadata

---

## Roadmap

| Phase | Focus | Status |
| --- | --- | --- |
| **P0** | KU → KnowledgeObject + manifest / evidence / step re-run | ✅ CLOSED |
| **P1** | KO → ExpressionObject → Artifact（Pillow GIF + TTS；evidence） | ✅ CLOSED |
| **P2** | Multiple KO → Concept Graph → Reconstruction views | ✅ CLOSED (v0.2) |
| **P3 (active)** | KO + Graph + Embedding → KO Retrieval + Compose (paper/lecture) | 🟡 ACTIVE |
| deferred | derive → animate（manim_beats）；extra renderers（Manim/SVG/WebGL） | ⏸ DEFER |
| later | Windows desktop UI → `.exe` | 🔜 |

**Frozen boundary:** Expression Layer proves KO can drive multimodal consumers without polluting the knowledge ontology. Renderer expansion ≠ Expression Layer work. P2 reorganizes **structure across KOs**, not text rewrite. Original KO remains immutable; Reconstruct outputs live under `data/reconstruct/`.

**P2 CLOSED (v0.2):** Relation Quality · Graph Evolution · View Stability.

**P3 ACTIVE:** Retrieve **KnowledgeObjects** (not document chunks) via local BGE embeddings + optional ConceptGraph boost (`data/retrieve/`).

Long-term:

$$
\boxed{Personal\ Cognitive\ Engine}
$$

Amplifies learning speed, depth, cross-domain links, and creation — it does not replace thinking.

---

## Tests（按知识剧本分类）

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
# 分类跑：
.\.venv\Scripts\python.exe -m pytest tests/acquire -q    # 获取知识
.\.venv\Scripts\python.exe -m pytest tests/distill -q    # 沉淀知识
.\.venv\Scripts\python.exe -m pytest tests/locate -q     # 搜索定位
.\.venv\Scripts\python.exe -m pytest tests/reorganize -q # 重组知识
```

| 目录 | 剧本 |
| --- | --- |
| `tests/acquire/` | 文本/音频入口、清洗切分（mock ASR） |
| `tests/distill/` | KU↔KO、Expression 派生、Harness artifact |
| `tests/locate/` | KO 嵌入文本、向量索引、Compose 渲染 |
| `tests/reorganize/` | Relation 规则、Graph、Evolution、Views |

单元测试默认不打外网、不加载 Whisper/BGE/Ollama 权重。

---

## Layout

```
KnowledgeForge/
├── app/           # ingest → process → compression → storage/index
├── data/
│   ├── inbox/
│   ├── raw/
│   └── knowledge/ # atomic units + INDEX.md
├── main.py
├── requirements.txt
└── .env.example
```
