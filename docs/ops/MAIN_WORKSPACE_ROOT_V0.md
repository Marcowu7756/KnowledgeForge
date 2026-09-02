# Cursor / Agent · 统一根 `D:\main`

```yaml
doc_id: KF-MAIN-WORKSPACE-ROOT-V0
as_of: 2026-09-02
status: ACTIVE
sot: D:\main\README.md
```

Agent 与人工打开工作区时，**唯一根**为：

```text
D:\main
```

子项目以 junction 挂在该根下（各仓仍独立 `git` · 默认分支 `main`）：

| 子目录 | 真实路径 |
|--------|----------|
| KnowledgeForge | `D:\KnowledgeForge` |
| DigitalSelf | `D:\DigitalSelf` |
| fxtrading | `D:\fxtrading` |
| NTW_Shanghai_OP | `D:\NTW_Shanghai_OP` |
| AI / dify | `D:\AI` / `D:\dify` |

打开：`D:\main` 或 `D:\main\main.code-workspace`。

不把各仓合并成 monorepo。Producer seal 仍在 DigitalSelf。
