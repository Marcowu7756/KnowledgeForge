# SETV Audit — KnowledgeForge Foundation + P0–P3

```yaml
audit_id: KF-SETV-20260827
method: SETV (State → Invalidation → Transition → Reconfirmation → Risk)
scope: KnowledgeForge after unit-test campaign (acquire/distill/locate/reorganize)
date: 2026-08-27
pytest: 38 passed (tests/)
```

## 0. SETV 审计框架（本项目映射）

参照知识库中 SETV 方法论：

| SETV 环节 | 本仓库含义 |
| --- | --- |
| **State（状态）** | 当前架构声称成立的能力边界（什么已 CLOSED / ACTIVE） |
| **Invalidation（失效）** | 何种证据会使该声称失效 |
| **Transition（过渡）** | 状态不确定时禁止“立刻扩方向”，只降风险、记问题 |
| **Reconfirmation（再确认）** | 用可复现测试 / 证据链重新证明 |
| **Risk（风险控制）** | 未证明能力不进主链路；不把草稿当真理 |

核心纪律：

> 状态失效 ≠ 新方向成立。禁止未验证的反手扩 scope。

---

## 1. State — 当前宣称状态

### 1.1 Foundation（CLOSED）

| 声称 | 状态锚 |
| --- | --- |
| 多源获取 → Harness → KnowledgeObject | 架构主链路成立 |
| Knowledge ≠ Expression ≠ Artifact | 对象分离成立 |
| Local models 可锁定 | `models verify` / LOCK 路径存在 |

### 1.2 P0–P3

| 层 | 宣称 | 状态标签 |
| --- | --- | --- |
| P0 KO + Harness | CLOSED | `knowledge_object.json` + `manifest` + `--rerun-step` |
| P1 Expression | CLOSED (scope) | Visual/Audio Expression + evidence；Manim DEFER |
| P2 Reconstruct | CLOSED v0.2 | Relation quality / evolve / view stability |
| P3 Retrieve + Compose | ACTIVE | KO embedding index + compose paper/lecture |
| Audio ingest | LANDED | `python main.py audio` |

### 1.3 测试再确认样本（Reconfirmation evidence）

```text
pytest tests → 38 passed
分类：
  acquire/     获取知识
  distill/     沉淀知识
  locate/      搜索定位
  reorganize/  重组知识
```

单元测试默认不加载 Whisper/BGE/Ollama 权重（mock / 纯逻辑）。

---

## 2. Invalidation — 会使状态失效的条件

下列任一发生，对应声称进入 **失效 → 过渡**，不得继续宣称 CLOSED：

| ID | 失效条件 | 影响声称 |
| --- | --- | --- |
| INV-01 | `load_unit_from_markdown` 在真实语料上大量空 section（回归 CRLF/DOTALL） | KO 沉淀 |
| INV-02 | `build_graph` 同一 KO 集合产生不同 `graph_id` / view fingerprint | P2 可复现性 |
| INV-03 | retrieve 以 chunk 文本而非 KO 整对象为索引单元 | P3 架构原则 |
| INV-04 | Expression 回写污染 `KnowledgeObject.content` | KO≠Expression |
| INV-05 | compose 在无 retrieve hit 时仍生成“像样论文”且不标 unknowns | 应用层诚实性 |
| INV-06 | audio ingest 在 whisper 未就绪时静默成功 | 获取层门禁 |
| INV-07 | 单元测试依赖外网或本地大模型权重才能绿 | 测试再确认失效 |

---

## 3. Findings — 问题记录（按风险）

### P0 — 必须处理（状态不确定，降风险）

#### F-P0-01 运行产物与密钥目录未完全纳入 git 纪律

- **现象**：工作区出现 `data/compose/`、`data/retrieve/`、`data/reconstruct/`、`.venv/` 等未忽略/未规范项；远程尚未配置。
- **风险**：误提交密钥、大体积向量、虚拟环境；或无法 push。
- **SETV**：过渡态 — 先补 `.gitignore` 与 gitkeep，再允许发布。
- **建议**：忽略 runtime 输出，仅保留目录占位；永不提交 `.env` / `.venv` / `models/`。

#### F-P0-02 无 Git remote / 无 `gh` CLI

- **现象**：审计时 `git remote -v` 为空，`gh` 不在 PATH。
- **风险**：无法完成“推 GitHub”闭环。
- **建议**：创建 GitHub 空仓库并 `git remote add origin …`；或安装 GitHub CLI 后 `gh repo create`。

### P1 — 高优先级（已知缺陷，不阻塞当前 CLOSED 叙述但需排队）

#### F-P1-01 Graph-aware retrieve 在弱语义时仍可能被 graph_boost 扰动

- **现象**：早期冒烟中，与 query 弱相关的 KO 可因 `shared_concept` 高置信度抬升名次；虽已加 soft-gate（`sem < 0.15` 降权），阈值与门限仍拍脑袋。
- **失效条件**：金融 query 稳定打出方法论噪音卡。
- **建议**：boost 仅限 semantic pool 内；或要求 `shared_concept` 与 query token 重叠。

#### F-P1-02 Compose 依赖 LLM JSON 强制，长文质量无契约测试

- **现象**：`complete_json` 全提供商强制 JSON；有冒烟无 schema 契约单测（渲染有测，生成无测）。
- **风险**：模型偶发缺字段 → 半残草稿进入 `data/compose/`。
- **建议**：对 payload 做最小字段校验；失败进入 transition（写 `FAILED.md` + unknowns），禁止静默成功。

#### F-P1-03 知识索引 `limit` 截断顺序非语义

- **现象**：`collect_from_index(limit=N)` 按 jsonl 顺序截断，易漏主题相关卡。
- **建议**：limit 前按 tag/concept 过滤；或显式 `--seed` 优先。

#### F-P1-04 Inter-KO 边类型仍偏软

- **现象**：跨卡边主要靠 `shared_concept` / `shared_tag`；`vs` 对比句、前置知识解析仍粗。
- **风险**：Graph 看起来密、解释力不足。
- **建议**：P2 后续只做 relation quality，不引入 GNN。

### P2 — 中优先级（技术债 / 范围债务）

#### F-P2-01 测试未覆盖 CLI / Harness 端到端

- **现象**：38 单测覆盖对象逻辑；`compile` / `retrieve index`（真 BGE）/ `audio`（真 Whisper）无 CI 级集成测。
- **SETV**：单元再确认 ≠ 生产状态再确认。
- **建议**：另开 `tests/integration/`（标记 slow），默认 CI 不跑。

#### F-P2-02 `EmbeddingRef` 未写回 package KO

- **现象**：retrieve index 只更新内存对象 / 独立 `data/retrieve`；package 内 `knowledge_object.json` 的 embedding 常为 `pending`。
- **建议**：index 后可选写回或生成 sidecar `embedding.json`。

#### F-P2-03 derive → animate（manim_beats）仍 DEFER 但文档易误读为已通

- **现象**：README 已标 DEFER；derive 输出仍含 Manim beats 文案。
- **建议**：在 derive 输出抬头标注 `not wired to expression`。

#### F-P2-04 Harness 对 audio 的 evidence.models.asr 路径依赖配置

- **现象**：ASR 失败模式依赖 `whisper_ready()`；配置路径漂移时错误信息依赖调用链。
- **建议**：audio / compile 统一走 `app.ingest.asr.transcribe_file`。

### P3 — 低优先级 / 观察项

#### F-P3-01 中文 Windows 控制台乱码

- **现象**：CLI 打印中文标题在部分终端显示为 `??`；文件内容本身 UTF-8 正常。
- **建议**：文档注明 `chcp 65001` 或使用 Windows Terminal。

#### F-P3-02 一源多卡 / UI / 多 renderer

- **状态**：明确 HOLD/DEFER，**不是缺陷**。
- **纪律**：在 P3 retrieve 再确认稳定前，不启动这些方向。

---

## 4. Transition — 当前过渡策略

对 F-P0-01/02：进入发布过渡态：

1. 补齐 ignore 与审计文档  
2. 提交可复现代码 + 测试  
3. 配置 remote 后 push  
4. **不**在本轮引入 Manim / UI / GNN / 一源多卡  

对 F-P1-*：记入 backlog，降低“graph_boost / compose 成功率”宣传权重，直到有契约测试。

---

## 5. Reconfirmation — 本轮已做

| 证据 | 结果 |
| --- | --- |
| `pytest tests` | 38 passed |
| 剧本分类存在 | acquire / distill / locate / reorganize |
| Compose 冒烟（人工） | lecture 草稿生成成功 |
| Audio 冒烟（人工） | wav → knowledge card 成功 |
| SETV 审计文档 | 本文件 |

未再确认（明确降风险）：

- 全量真模型 CI  
- 远程仓库可达性（审计时 remote 缺失）

---

## 6. Risk register（摘要）

| 风险 | 等级 | 控制 |
| --- | --- | --- |
| 误提交 secrets / venv | 高 | gitignore + 审查 status |
| 把单元测试绿当作生产可用 | 中 | 区分 unit vs integration |
| Graph boost 噪音检索 | 中 | soft-gate；后续收紧 |
| Compose 幻觉论文 | 中 | unknowns 字段；缺字段失败 |
| Scope 反手扩张（UI/Manim） | 中 | HOLD/DEFER 冻结 |

---

## 7. Verdict

```text
State: Foundation + P0/P1/P2 = CLOSED (with known P1 debts)
       P3 Retrieve/Compose + Audio = LANDED / ACTIVE
Invalidation watch: INV-01..07
Transition: publishing hygiene (gitignore, remote) before claim "shipped"
Reconfirmation: unit tests 38/38 PASS
Risk: do not expand renderer/UI until P1 retrieve/compose debts shrink
```

**总体**：架构状态可维持；发布前必须先关闭 F-P0-01/02。问题已登记，不把未证明能力写成已完成。

---

## 9. Publish note (2026-08-27)

- Commit landed locally with scenario tests + this audit.
- F-P0-01 addressed via `.gitignore` for compose/retrieve/reconstruct + `.venv`.
- F-P0-02: GitHub remote created at publish time (`Marcowu7756/KnowledgeForge`).
