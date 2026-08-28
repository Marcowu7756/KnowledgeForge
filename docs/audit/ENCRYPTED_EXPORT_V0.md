# Encrypted Export v0 (`.kfexport`)

**Status:** LANDED (replaces `encrypted_export_unimplemented` stub)  
**Module:** `app/knowledge/encrypted_export.py`

## Model

```text
plaintext external          → blocked for local_only / policy.export=encrypted
encrypted channel (.kfexport) → allowed for restricted / local_only / encrypted
secret / deny               → always blocked
```

Envelope schema `kf_encrypted_export_v0`:

- plaintext metadata watermark (classification · source_project · original_name)
- Fernet ciphertext of file bytes
- `sha256_plain` integrity check on decrypt

## Key material

```text
KF_EXPORT_KEY          # Fernet url-safe base64 (preferred)
# or
KF_EXPORT_PASSPHRASE   # PBKDF2 → Fernet key
```

Generate once:

```powershell
.\.venv\Scripts\python.exe -c "from app.knowledge.encrypted_export import generate_export_key; print(generate_export_key())"
```

## CLI / API

```powershell
.\.venv\Scripts\python.exe main.py export encrypted data\knowledge\restricted\setv\...\x.md
.\.venv\Scripts\python.exe main.py export decrypt data\exports\x.kfexport -o out.md
# UI / HTTP
# GET /api/export/encrypted?path=...
```

Default write path: `data/exports/<stem>.kfexport` (gitignored).

## Access audit

Successful encrypted exports append `action=export mode=encrypted` under `data/audit/access/`.
