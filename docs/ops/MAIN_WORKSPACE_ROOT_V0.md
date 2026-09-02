# GitHub · 统一根 `Marcowu7756/main`

```yaml
doc_id: KF-MAIN-WORKSPACE-ROOT-V0
as_of: 2026-09-02
status: ACTIVE
github: https://github.com/Marcowu7756/main
branch: main
sot: https://github.com/Marcowu7756/main/blob/main/README.md
```

**GitHub 上的统一入口**是伞形仓：

```text
https://github.com/Marcowu7756/main
```

子项目以 **git submodule** 挂在该根下（各仓仍独立 SoT · 默认分支 `main`）：

| 子目录 | Remote |
|--------|--------|
| KnowledgeForge | `Marcowu7756/KnowledgeForge` |
| DigitalSelf | `Marcowu7756/DigitalSelf` |
| fxtrading | `Marcowu7756/FXTrading` |
| NTW_Shanghai_OP | `Marcowu7756/NTW_Shanghai_OP` |

```bash
git clone --recurse-submodules git@github.com:Marcowu7756/main.git
```

本机 Cursor 可打开 `D:\main`（junction 对齐同一批 remote）。  
**不是 monorepo：** 提交 / push / status 仍按子仓分别处理。

Producer / S15 seal 仍在 DigitalSelf；伞形根不改变治理边界。
