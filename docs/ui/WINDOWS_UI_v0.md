# Windows UI v0 — superseded

> **Superseded.** Product of record is [`WEB_UI_v0.md`](WEB_UI_v0.md) (browser-first local Web UI).

This file remains only as a historical pointer. Do not treat “Windows console / desktop-default” as current framing.

| Topic | Where |
| --- | --- |
| Launch (browser default) | `python main.py ui` → `http://127.0.0.1:8765` |
| Optional desktop window | `python main.py ui --desktop` (pywebview) |
| Portable `.exe` shell | `scripts/build_windows_ui.ps1` — **legacy / optional**; full pipeline still prefers venv + `main.py ui` |
| Maintain delete | [`../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md) |

Stack unchanged under the rename of intent: FastAPI + static shell under `app/ui/`. No React SPA; no LAN/cloud bind.
