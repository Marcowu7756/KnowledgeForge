"""Package EmbeddingRef write-back after retrieve index (F-P2-02 deep)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.knowledge.object import EmbeddingRef, EvidenceBlock, from_knowledge_unit
from app.knowledge.parse import load_knowledge_object, write_knowledge_object
from app.models import KnowledgeUnit
from app.retrieve.embed_writeback import (
    build_package_ko_index,
    resolve_package_ko_path,
    write_embedding_ref_to_package,
    write_embedding_refs_to_packages,
)
from app.retrieve.index_build import build_ko_index


def _package_ko(tmp_path: Path, *, ko_id: str = "ko_pkg001abc") -> Path:
    packages = tmp_path / "packages" / "run001"
    packages.mkdir(parents=True)
    unit = KnowledgeUnit(
        id=ko_id.removeprefix("ko_"),
        title="Package KO",
        source="unit-test",
        type="notes",
        summary="summary",
        concepts=["alpha"],
        tags=["t"],
    )
    obj = from_knowledge_unit(unit, knowledge_md=(packages / "knowledge.md").as_posix())
    obj.id = ko_id
    obj.evidence = EvidenceBlock(package_id="run001")
    obj.embedding = EmbeddingRef(model="mock-embed", status="pending")
    dest = packages / "knowledge_object.json"
    write_knowledge_object(obj, dest)
    return dest


def test_embed_writeback_resolves_by_ko_id(tmp_path: Path):
    ko_path = _package_ko(tmp_path)
    obj = load_knowledge_object(ko_path)
    index = build_package_ko_index(tmp_path / "packages")
    resolved = resolve_package_ko_path(obj, packages_root=tmp_path / "packages", ko_index=index)
    assert resolved == ko_path


def test_embed_writeback_resolves_by_package_id(tmp_path: Path):
    ko_path = _package_ko(tmp_path)
    obj = load_knowledge_object(ko_path)
    resolved = resolve_package_ko_path(obj, packages_root=tmp_path / "packages")
    assert resolved == ko_path


def test_embed_writeback_updates_pending_embedding(tmp_path: Path):
    ko_path = _package_ko(tmp_path)
    obj = load_knowledge_object(ko_path)
    obj.embedding = EmbeddingRef(model="mock-embed", vector_id="vec_abc", status="ready")

    assert write_embedding_ref_to_package(obj, ko_path) is True
    saved = load_knowledge_object(ko_path)
    assert saved.embedding.status == "ready"
    assert saved.embedding.vector_id == "vec_abc"
    assert saved.embedding.model == "mock-embed"
    assert saved.lifecycle.version == 2


def test_embed_writeback_skips_when_already_ready(tmp_path: Path):
    ko_path = _package_ko(tmp_path)
    obj = load_knowledge_object(ko_path)
    obj.embedding = EmbeddingRef(model="mock-embed", vector_id="vec_abc", status="ready")
    write_embedding_ref_to_package(obj, ko_path)

    again = load_knowledge_object(ko_path)
    again.embedding = EmbeddingRef(model="mock-embed", vector_id="vec_abc", status="ready")
    assert write_embedding_ref_to_package(again, ko_path) is False


def test_build_ko_index_writeback_from_packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ko_path = _package_ko(tmp_path)
    packages_root = tmp_path / "packages"
    index_dir = tmp_path / "retrieve"

    monkeypatch.setattr("app.config.PACKAGES_DIR", packages_root)

    def fake_embed(texts, *, normalize=True):
        return np.array([[1.0, 0.0]] * len(texts), dtype=np.float32)

    with patch("app.retrieve.index_build.embed_texts", side_effect=fake_embed):
        with patch("app.retrieve.index_build.model_path_str", return_value="mock-embed"):
            manifest, kos, report = build_ko_index(
                from_packages=True,
                dest=index_dir,
                write_back_packages=True,
            )

    assert manifest.count == 1
    assert report is not None
    assert report.updated == 1
    saved = load_knowledge_object(ko_path)
    assert saved.embedding.status == "ready"
    assert saved.embedding.vector_id
    assert saved.embedding.model == "mock-embed"


def test_build_ko_index_skips_writeback_when_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _package_ko(tmp_path)
    packages_root = tmp_path / "packages"
    index_dir = tmp_path / "retrieve"
    ko_path = packages_root / "run001" / "knowledge_object.json"
    before = ko_path.read_text(encoding="utf-8")

    monkeypatch.setattr("app.config.PACKAGES_DIR", packages_root)

    with patch("app.retrieve.index_build.embed_texts", return_value=np.array([[1.0, 0.0]], dtype=np.float32)):
        with patch("app.retrieve.index_build.model_path_str", return_value="mock-embed"):
            _manifest, _kos, report = build_ko_index(
                from_packages=True,
                dest=index_dir,
                write_back_packages=False,
            )

    assert report is None
    assert ko_path.read_text(encoding="utf-8") == before


def test_build_ko_index_writeback_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ko_path = _package_ko(tmp_path)
    before = ko_path.read_text(encoding="utf-8")
    packages_root = tmp_path / "packages"
    index_dir = tmp_path / "retrieve"

    monkeypatch.setattr("app.config.PACKAGES_DIR", packages_root)

    with patch("app.retrieve.index_build.embed_texts", return_value=np.array([[1.0, 0.0]], dtype=np.float32)):
        with patch("app.retrieve.index_build.model_path_str", return_value="mock-embed"):
            _manifest, _kos, report = build_ko_index(
                from_packages=True,
                dest=index_dir,
                write_back_dry_run=True,
            )

    assert report is not None
    assert report.updated == 1
    assert ko_path.read_text(encoding="utf-8") == before
    payload = json.loads(before)
    assert payload["embedding"]["status"] == "pending"
