# Windows UI v0 — KnowledgeForge / PAILE

```yaml
ui_id: KF-UI-WIN-v0
status: ACTIVE (scaffold)
stack: FastAPI (local) + static shell → optional pywebview → later .exe
rule: UI 只编排现有管线；不发明新 ontology；KO ≠ Expression ≠ Artifact
```

## Goal

Windows 本地控制台：把 CLI 能力变成可点的车间界面，而不是第二个 RAG 聊天窗。

$$
\boxed{Capture \rightarrow Distill \rightarrow Reconstruct \rightarrow Retrieve \rightarrow Compose/Express}
$$

## Product principles

1. **Brand first**：首屏是 KnowledgeForge / PAILE，不是功能仪表盘。
2. **One job per stage**：导航按知识剧本五段，每段一个主任务。
3. **Local-first**：只打本机 `127.0.0.1`；模型 / 数据仍走现有 `data/`、`models/`。
4. **Thin shell**：UI 调用 `app.*` Python API，不重写 harness / retrieve / compose。
5. **HOLD 仍有效的部分**：一源多卡布局、Manim 多 renderer、GNN — 本版不做。

## Information architecture

| Stage | 中文 | Primary action | Backend |
| --- | --- | --- | --- |
| Capture | 获取 | URL / 文件 / 音频入库 | `pipeline.run_*` |
| Distill | 沉淀 | `compile` → KO package | `harness.compile_knowledge` |
| Reconstruct | 重组 | 建图 / 出 view | `reconstruct.run_reconstruct` |
| Retrieve | 检索 | KO 级 query | `retrieve.run_query` |
| Compose / Express | 表达 | paper·lecture · GIF/WAV | `compose` / `expression` |

Secondary (footer / settings): `models status`, `voice`, paths.

## Screen map (v0)

```
┌─────────────────────────────────────────────┐
│  KnowledgeForge          [车间] [设置]       │
├─────────────────────────────────────────────┤
│  获取 · 沉淀 · 重组 · 检索 · 表达            │  ← stage rail
├─────────────────────────────────────────────┤
│                                             │
│   (one composition: title + one CTA block)  │
│                                             │
│   results / artifact links                  │
│                                             │
└─────────────────────────────────────────────┘
```

No multi-stat dashboard on home. Home = brand + enter 车间.

## Tech path (Windows)

| Phase | Deliverable |
| --- | --- |
| **v0** (now) | `python main.py ui` → browser at `http://127.0.0.1:8765` |
| **v0.1** | Optional `pywebview` desktop window (`--desktop`) |
| **v1** | PyInstaller / briefcase → `KnowledgeForge.exe` |

Deps already present: FastAPI, uvicorn. Desktop wrapper optional: `pywebview`.

## Non-goals (v0)

- Cloud sync / accounts
- Chunk-RAG chat UI
- Editing KO JSON by hand in forms
- Manim scene editor
- Multi-card “一源多卡” canvas

## v0.2 additions

1. **Async jobs** — long actions return `job_id`; UI polls `/api/jobs/{id}` with progress bar.
2. **Artifact preview** — MD/GIF/WAV under `data/` via `/api/preview` (path sandbox).
3. **Windows .exe shell** — `scripts/build_windows_ui.ps1` → `dist/KnowledgeForgeUI/` (ML runtimes excluded; set `KF_ROOT` for full pipeline).

## Acceptance

- [x] Design doc
- [x] `main.py ui` starts local server
- [x] Five stages reachable; status endpoint works
- [x] Capture / Distill / Reconstruct / Retrieve / Compose forms call real APIs
- [x] README documents how to launch on Windows
- [x] Async progress for long jobs
- [x] Artifact preview modal
- [x] PyInstaller onedir build script
