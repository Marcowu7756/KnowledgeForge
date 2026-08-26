# KnowledgeForge

Local **Personal Knowledge Compression Engine (PKCE)**.

Not a chatbot. Pipeline:

```
Input → Ingest → Process → Compress → Knowledge Store
```

Any unstructured source (YouTube, PDF, Markdown, DOCX, later web/audio) becomes a dense, retrievable, maintainable Knowledge Unit.

## Phase 0 status

Done:

- Independent git repo at `D:\KnowledgeForge` (`main` only)
- Python 3.12 virtualenv
- `requirements.txt`
- First directory layout
- Knowledge Unit schema + Markdown renderer
- Provider-agnostic `compress(text)` interface

Not in this phase: YouTube fetch, PDF parse, LLM calls, vector search, UI.

## Setup

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\Activate.ps1
copy .env.example .env
# fill API keys in .env if you will use cloud models
```

## CLI (Phase 1+)

```powershell
python main.py youtube https://youtube.com/watch?v=xxxx
python main.py pdf path\to\file.pdf
python main.py file path\to\notes.md
```

Phase 0 will print the planned pipeline and exit. Phase 1 implements YouTube → subtitle → LLM → Markdown.

## Layout

```
KnowledgeForge/
├── app/
│   ├── main.py              # CLI dispatch
│   ├── config.py            # paths + LLM settings
│   ├── models.py            # Knowledge Unit schema
│   ├── ingest/              # YouTube / PDF / DOCX / MD / TXT
│   ├── process/             # clean + split
│   ├── compression/         # LLM providers + prompt
│   └── storage/             # Markdown writer + index
├── data/
│   ├── inbox/               # Phase 4 watch folder
│   ├── raw/                 # unmodified extracts
│   └── knowledge/           # compressed units
│       ├── concepts/
│       ├── summaries/
│       ├── sources/
│       └── index/
├── main.py
├── requirements.txt
└── .env.example
```

## Knowledge Unit

Output is not a generic summary. Each unit carries:

`id`, `title`, `source`, `type`, `url`, `created`, `summary`, `concepts`, `key_points`, `relationships`, `formulas`, `examples`, `unknowns`, `tags`

See `app/models.py` and `app/storage/markdown.py`.

## Roadmap

| Phase | Scope |
| ----- | ----- |
| 0 | Environment + skeleton (this) |
| 1 | YouTube URL → Knowledge Unit Markdown |
| 2 | Local files: PDF / DOCX / MD / TXT |
| 3 | Embedding + local search |
| 4 | `data/inbox/` auto-ingest |

Out of scope until the core loop is stable: agents, multi-agent, RAG UI, auto-reasoning.

## Hardware

Cloud models: 16GB RAM is enough. Local 7B/14B quantized models: 32GB RAM + 12GB+ VRAM recommended. RX 6800 XT is sufficient as a local auxiliary.
