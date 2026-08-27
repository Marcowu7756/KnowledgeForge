from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app import config
from app.retrieve.models import IndexManifest, IndexRecord


def retrieve_dir() -> Path:
    path = getattr(config, "RETRIEVE_DIR", None) or (config.DATA_DIR / "retrieve")
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path(root: Path | None = None) -> Path:
    return (root or retrieve_dir()) / "manifest.json"


def records_path(root: Path | None = None) -> Path:
    return (root or retrieve_dir()) / "records.jsonl"


def vectors_path(root: Path | None = None) -> Path:
    return (root or retrieve_dir()) / "vectors.npy"


def save_index(
    *,
    records: list[IndexRecord],
    vectors: np.ndarray,
    model: str,
    evidence: dict | None = None,
    root: Path | None = None,
) -> IndexManifest:
    root = root or retrieve_dir()
    root.mkdir(parents=True, exist_ok=True)
    if len(records) != len(vectors):
        raise ValueError("records/vectors length mismatch")

    # Stable order by ko_id
    order = sorted(range(len(records)), key=lambda i: records[i].ko_id)
    records = [records[i] for i in order]
    vectors = vectors[order] if len(vectors) else vectors

    dim = int(vectors.shape[1]) if vectors.ndim == 2 and len(vectors) else 0
    now = datetime.now(timezone.utc)
    manifest = IndexManifest(
        model=model,
        dim=dim,
        count=len(records),
        ko_ids=[r.ko_id for r in records],
        created=now,
        updated=now,
        evidence=evidence or {},
    )
    manifest_path(root).write_text(
        manifest.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    with records_path(root).open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(rec.model_dump_json() + "\n")
    np.save(vectors_path(root), vectors.astype(np.float32))
    return manifest


def load_manifest(root: Path | None = None) -> IndexManifest:
    path = manifest_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"retrieve index missing: {path}")
    return IndexManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_records(root: Path | None = None) -> list[IndexRecord]:
    path = records_path(root)
    if not path.is_file():
        return []
    out: list[IndexRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(IndexRecord.model_validate(json.loads(line)))
    return out


def load_vectors(root: Path | None = None) -> np.ndarray:
    path = vectors_path(root)
    if not path.is_file():
        return np.zeros((0, 0), dtype=np.float32)
    return np.load(path)


def cosine_top_k(
    query: np.ndarray,
    matrix: np.ndarray,
    *,
    top_k: int,
) -> list[tuple[int, float]]:
    if matrix.size == 0 or query.size == 0:
        return []
    # vectors assumed L2-normalized → cosine = dot
    scores = matrix @ query.astype(np.float32)
    k = min(top_k, len(scores))
    if k <= 0:
        return []
    idx = np.argpartition(-scores, kth=k - 1)[:k]
    ranked = sorted(((int(i), float(scores[i])) for i in idx), key=lambda x: -x[1])
    return ranked
