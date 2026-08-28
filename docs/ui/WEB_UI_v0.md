# Web UI v0 — KnowledgeForge / PAILE

```yaml
ui_id: KF-UI-WEB-v0
status: ACTIVE (product of record)
stack: FastAPI (local) + static shell · optional pywebview · optional portable .exe
rule: UI 只编排现有管线；不发明新 ontology；KO ≠ Expression ≠ Artifact
bind: 127.0.0.1 (local-first; no LAN/cloud)
```

## Goal

本机 **浏览器优先** 的车间界面：把 CLI 能力变成可点的五段剧本，而不是第二个 RAG 聊天窗。

$$
\boxed{Capture \rightarrow Distill \rightarrow Reconstruct \rightarrow Retrieve \rightarrow Compose/Express}
$$

## Product principles

1. **Brand first**：首屏是 KnowledgeForge / PAILE，不是功能仪表盘。
2. **One job per stage**：导航按知识剧本五段，每段一个主任务。
3. **Local-first**：只打本机 `127.0.0.1`；模型 / 数据仍走现有 `data/`、`models/`。
4. **Browser-first**：`python main.py ui` 默认打开系统浏览器；`--desktop` 可选 pywebview。
5. **Thin shell**：UI 调用 `app.*` Python API，不重写 harness / retrieve / compose。
6. **HOLD 部分解冻**：一源多卡 H1 · Manim H2 · GNN H3 已落地；chunk-RAG 仍 HOLD。  
   排期：[`HOLD_THAW_SCHEDULE_V0.md`](../audit/HOLD_THAW_SCHEDULE_V0.md)。
7. **维护只删**：垃圾 / 不重要知识只提供 delete；新增与更新 = 重新获取。

## Launch

```powershell
.\.venv\Scripts\python.exe main.py ui
# → http://127.0.0.1:8765 （系统浏览器）

.\.venv\Scripts\python.exe -m pip install pywebview
.\.venv\Scripts\python.exe main.py ui --desktop   # 可选桌面窗
```

Health: `ui_version` ≥ `0.6.0` · `features.web_ui: true`.

## Information architecture

| Stage | 中文 | Primary action | Backend |
| --- | --- | --- | --- |
| Capture | 获取 | 文件 / YouTube / Bilibili / **Twitter·X 单条** / 音频 / 图 | `pipeline.run_*` |
| Distill | 沉淀 | `compile` → KO package · 维护删除 | `harness` / `knowledge.maintain` |
| Reconstruct | 重组 | 建图 / 出 view | `reconstruct.run_reconstruct` |
| Retrieve | 检索 | KO 级 query · 一源多卡 family | `retrieve` / `family_view` |
| Compose / Express | 表达 | paper·lecture · GIF/WAV | `compose` / `expression` |

Secondary (settings): bind URL · browser-first note · `models status` · paths.

## Screen map (v0)

```
┌─────────────────────────────────────────────┐
│  KnowledgeForge          [车间] [任务] [设置] │
├─────────────────────────────────────────────┤
│  获取 · 沉淀 · 重组 · 检索 · 表达            │  ← stage rail
├─────────────────────────────────────────────┤
│   (one composition: title + one CTA block)  │
│   results / artifact links                  │
└─────────────────────────────────────────────┘
```

No multi-stat dashboard on home. Home = brand + enter 车间.

## Tech path

| Phase | Deliverable |
| --- | --- |
| **v0** (now) | Browser-first `main.py ui` → `http://127.0.0.1:8765` |
| **Optional** | `pywebview` via `--desktop` |
| **Legacy** | PyInstaller portable shell (`scripts/build_windows_ui.ps1`) |

Deps: FastAPI, uvicorn. Desktop wrapper optional: `pywebview`.

## Non-goals (v0)

- React / Next / separate frontend package
- Binding `0.0.0.0` / auth / remote deploy
- Cloud sync / accounts
- Chunk-RAG chat UI (H4 HOLD)
- Editing KO JSON by hand in forms（**delete + re-acquire** instead）
- Soft-delete / recycle bin

## Maintain · delete only (SOP)

UI path: **沉淀** →「维护 · 删除」→ confirm.

Full SOP: [`../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md).

CLI: `python main.py knowledge delete <path|id> [--dry-run] [--yes]`

## Features already in shell

- Async jobs + 任务列表 · artifact / compose preview
- H1 multi-card family + layout persist (`data/ui`)
- Capture: Twitter/X single-status URL (align CLI `twitter`)
- Settings: bind URL + browser-first + `--desktop` hint

## Acceptance

- [x] Design doc (this file = product of record)
- [x] `main.py ui` opens system browser by default
- [x] `--desktop` optional pywebview
- [x] Five stages + tasks + settings
- [x] Capture includes Twitter/X
- [x] Health reports `web_ui` + `ui_version` 0.6.x
- [x] Local bind only; no cloud upload

## Legacy pointer

Former Windows-desktop framing: [`WINDOWS_UI_v0.md`](WINDOWS_UI_v0.md) (superseded; kept as pointer).
