"""Encrypted export (.kfexport) — Fernet envelope for proprietary leave path."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge.access import check_export_gate, check_expression_gate, default_policy_for
from app.knowledge.encrypted_export import (
    EncryptedExportError,
    decrypt_envelope,
    encrypt_file,
    generate_export_key,
)
from app.knowledge.path_access import build_encrypted_export, gate_export


def test_plaintext_still_blocks_local_only():
    pol = default_policy_for("restricted")
    g = check_export_gate("restricted", policy=pol, external=True, channel="plaintext")
    assert not g.allowed
    assert g.reason == "local_only_blocks_external"


def test_encrypted_channel_allows_restricted():
    pol = default_policy_for("restricted")
    g = check_export_gate("restricted", policy=pol, external=True, channel="encrypted")
    assert g.allowed
    assert g.mode == "encrypted"
    expr = check_expression_gate(
        "restricted", policy=pol, external=True, channel="encrypted"
    )
    assert expr.allowed


def test_encrypted_mode_requires_channel():
    pol = default_policy_for("restricted").model_copy(update={"export": "encrypted"})
    plain = check_export_gate("restricted", policy=pol, external=True, channel="plaintext")
    assert not plain.allowed
    assert plain.reason == "requires_encrypted_channel"
    enc = check_export_gate("restricted", policy=pol, external=True, channel="encrypted")
    assert enc.allowed


def test_secret_never_exports_encrypted():
    pol = default_policy_for("secret")
    g = check_export_gate("secret", policy=pol, external=True, channel="encrypted")
    assert not g.allowed


def test_encrypt_decrypt_roundtrip(tmp_path: Path, monkeypatch):
    pytest.importorskip("cryptography")
    key = generate_export_key()
    monkeypatch.setenv("KF_EXPORT_KEY", key)
    monkeypatch.delenv("KF_EXPORT_PASSPHRASE", raising=False)
    src = tmp_path / "card.md"
    src.write_text("# SETV cite\n\nobserved only\n", encoding="utf-8")
    blob = encrypt_file(
        src, classification="restricted", source_project="setv"
    )
    env, plain = decrypt_envelope(blob)
    assert env.classification == "restricted"
    assert env.source_project == "setv"
    assert "watermark" in env.watermark.lower() or "KnowledgeForge" in env.watermark
    assert plain == src.read_bytes()


def test_build_encrypted_export_writes(tmp_path: Path, monkeypatch):
    pytest.importorskip("cryptography")
    from app import config

    monkeypatch.setenv("KF_EXPORT_KEY", generate_export_key())
    monkeypatch.setattr(config, "AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    card = tmp_path / "knowledge" / "restricted" / "setv" / "x.md"
    card.parent.mkdir(parents=True)
    card.write_text("# x\n", encoding="utf-8")
    access, dest, blob = build_encrypted_export(card)
    assert access.classification == "restricted"
    assert dest.suffix == ".kfexport"
    assert dest.is_file()
    assert b"kf_encrypted_export_v0" in blob
    _, expr, exp = gate_export(card, external=True, channel="encrypted")
    assert expr.allowed and exp.allowed


def test_missing_key_raises(tmp_path: Path, monkeypatch):
    pytest.importorskip("cryptography")
    monkeypatch.delenv("KF_EXPORT_KEY", raising=False)
    monkeypatch.delenv("KF_EXPORT_PASSPHRASE", raising=False)
    src = tmp_path / "a.md"
    src.write_text("hi", encoding="utf-8")
    with pytest.raises(EncryptedExportError):
        encrypt_file(src, classification="restricted")
