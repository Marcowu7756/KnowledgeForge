"""Optional native Windows window via pywebview."""

from __future__ import annotations

import threading


def open_desktop(*, host: str = "127.0.0.1", port: int = 8765) -> None:
    try:
        import webview
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "pywebview not installed. Run:\n"
            "  .\\.venv\\Scripts\\python.exe -m pip install pywebview\n"
            "Or use default browser: python main.py ui"
        ) from exc

    import uvicorn

    url = f"http://{host}:{port}"

    def _run() -> None:
        uvicorn.run(
            "app.ui.server:create_app",
            factory=True,
            host=host,
            port=port,
            log_level="warning",
        )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    webview.create_window(
        "KnowledgeForge Web UI",
        url,
        width=1180,
        height=780,
        min_size=(880, 600),
    )
    webview.start()
