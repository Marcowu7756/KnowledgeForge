from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXCLUDES = (
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    "legacy",
    "_legacy",
    ".cursor",
)

DEFAULT_EXTENSIONS = (".md", ".txt", ".markdown", ".pdf", ".docx")


@dataclass(frozen=True)
class SearchHit:
    path: Path
    root: Path
    keyword: str

    @property
    def relative(self) -> str:
        try:
            return self.path.relative_to(self.root).as_posix()
        except ValueError:
            return self.path.as_posix()


def _should_skip_dir(name: str, excludes: tuple[str, ...]) -> bool:
    lowered = name.lower()
    return lowered in {item.lower() for item in excludes}


def search_files(
    roots: list[str | Path],
    *,
    keyword: str,
    extensions: tuple[str, ...] = DEFAULT_EXTENSIONS,
    excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
    match_path: bool = False,
) -> list[SearchHit]:
    """Find files under fixed roots whose names contain keyword (case-insensitive).

    Read-only discovery. Does not open or modify file contents.
    """
    needle = keyword.strip().lower()
    if not needle:
        raise ValueError("keyword must not be empty")

    ext_set = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
    hits: list[SearchHit] = []
    seen: set[Path] = set()

    for root_arg in roots:
        root = Path(root_arg).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"search root does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"search root is not a directory: {root}")

        for dirpath, dirnames, filenames in root.walk():
            dirnames[:] = [d for d in dirnames if not _should_skip_dir(d, excludes)]
            for name in filenames:
                path = dirpath / name
                if path.suffix.lower() not in ext_set:
                    continue
                haystack = path.name.lower()
                if match_path:
                    try:
                        haystack = path.relative_to(root).as_posix().lower()
                    except ValueError:
                        haystack = str(path).lower()
                if needle not in haystack:
                    continue
                resolved = path.resolve()
                if resolved in seen:
                    continue
                if resolved.stat().st_size <= 0:
                    continue
                seen.add(resolved)
                hits.append(SearchHit(path=resolved, root=root, keyword=keyword))

    hits.sort(key=lambda h: str(h.path).lower())
    return hits
