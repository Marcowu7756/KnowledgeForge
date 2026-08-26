from __future__ import annotations


def split_text(text: str, max_chars: int = 8000) -> list[str]:
    """Chunk long extracts so a later compressor can stay within context.

    Phase 0: paragraph-aware character windows. No embeddings.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    buf = ""
    for para in text.split("\n\n"):
        candidate = para if not buf else f"{buf}\n\n{para}"
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
            buf = ""
        if len(para) <= max_chars:
            buf = para
            continue
        for i in range(0, len(para), max_chars):
            piece = para[i : i + max_chars]
            if i + max_chars < len(para):
                chunks.append(piece)
            else:
                buf = piece
    if buf:
        chunks.append(buf)
    return chunks
