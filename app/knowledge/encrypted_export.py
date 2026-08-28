"""Encrypted export envelope — controlled off-machine channel for proprietary KOs.

Format: kf_encrypted_export_v0 (.kfexport)
  - JSON header (classification watermark · metadata) + Fernet ciphertext of file bytes
  - Key: KF_EXPORT_KEY (Fernet url-safe base64) or derived from KF_EXPORT_PASSPHRASE

Does not change SETV. Secret remains deny. Plaintext external still blocked for local_only.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

SCHEMA = "kf_encrypted_export_v0"
ENVELOPE_SUFFIX = ".kfexport"


class EncryptedExportError(RuntimeError):
    pass


class EncryptedEnvelope(BaseModel):
    schema_id: str = Field(default=SCHEMA, alias="schema")
    classification: str
    source_project: str = ""
    original_name: str
    content_type: str = "application/octet-stream"
    exported_at: str
    watermark: str
    kdf: str = "fernet"
    ciphertext_b64: str
    sha256_plain: str = ""

    model_config = {"populate_by_name": True}


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:  # pragma: no cover
        raise EncryptedExportError(
            "cryptography package required for encrypted export — "
            "pip install cryptography"
        ) from exc
    return Fernet


def generate_export_key() -> str:
    Fernet = _fernet()
    return Fernet.generate_key().decode("ascii")


def resolve_export_key(*, passphrase: str | None = None) -> bytes:
    """Resolve Fernet key bytes from env or passphrase."""
    Fernet = _fernet()
    raw = (os.getenv("KF_EXPORT_KEY") or "").strip()
    if raw:
        try:
            key = raw.encode("ascii")
            Fernet(key)  # validate
            return key
        except Exception as exc:
            raise EncryptedExportError(
                "KF_EXPORT_KEY is not a valid Fernet key "
                "(url-safe base64 32-byte key)"
            ) from exc
    phrase = (passphrase or os.getenv("KF_EXPORT_PASSPHRASE") or "").strip()
    if phrase:
        # Deterministic Fernet key from passphrase (PBKDF2-ish via sha256 stretch)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            phrase.encode("utf-8"),
            b"knowledgeforge-export-v0",
            390000,
            dklen=32,
        )
        return base64.urlsafe_b64encode(digest)
    raise EncryptedExportError(
        "set KF_EXPORT_KEY (Fernet) or KF_EXPORT_PASSPHRASE before encrypted export"
    )


def watermark_line(*, classification: str, source_project: str) -> str:
    proj = f" · {source_project}" if source_project else ""
    return (
        f"KnowledgeForge encrypted export · classification={classification}{proj} "
        f"· do not redistribute in plaintext"
    )


def encrypt_file(
    path: Path,
    *,
    classification: str,
    source_project: str = "",
    content_type: str | None = None,
    passphrase: str | None = None,
) -> bytes:
    """Return .kfexport JSON bytes (UTF-8)."""
    Fernet = _fernet()
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    plain = path.read_bytes()
    key = resolve_export_key(passphrase=passphrase)
    token = Fernet(key).encrypt(plain)
    ctype = content_type or "application/octet-stream"
    if path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}:
        ctype = "text/plain; charset=utf-8"
    env = EncryptedEnvelope(
        classification=classification,
        source_project=source_project or "",
        original_name=path.name,
        content_type=ctype,
        exported_at=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        watermark=watermark_line(
            classification=classification, source_project=source_project or ""
        ),
        ciphertext_b64=token.decode("ascii"),
        sha256_plain=hashlib.sha256(plain).hexdigest(),
    )
    return json.dumps(
        env.model_dump(by_alias=True),
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def decrypt_envelope(
    data: bytes | str | Path,
    *,
    passphrase: str | None = None,
) -> tuple[EncryptedEnvelope, bytes]:
    """Decrypt .kfexport → (metadata, plaintext bytes)."""
    Fernet = _fernet()
    if isinstance(data, Path):
        raw = data.read_bytes()
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = data
    payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
    env = EncryptedEnvelope.model_validate(payload)
    if env.schema_id != SCHEMA and payload.get("schema") != SCHEMA:
        raise EncryptedExportError(f"unsupported schema {env.schema_id!r}")
    key = resolve_export_key(passphrase=passphrase)
    plain = Fernet(key).decrypt(env.ciphertext_b64.encode("ascii"))
    if env.sha256_plain:
        digest = hashlib.sha256(plain).hexdigest()
        if digest != env.sha256_plain:
            raise EncryptedExportError("plaintext sha256 mismatch after decrypt")
    return env, plain


def write_encrypted_export(
    path: Path,
    dest: Path,
    *,
    classification: str,
    source_project: str = "",
    passphrase: str | None = None,
) -> Path:
    blob = encrypt_file(
        path,
        classification=classification,
        source_project=source_project,
        passphrase=passphrase,
    )
    dest = dest.expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    return dest
