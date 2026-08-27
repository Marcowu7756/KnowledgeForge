from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

ModelKind = Literal["whisper", "embed", "ollama", "tts", "vocos", "ocr", "pix2tex"]

ALL_MODEL_KINDS: tuple[ModelKind, ...] = (
    "whisper",
    "embed",
    "ollama",
    "tts",
    "vocos",
    "ocr",
    "pix2tex",
)

LOCK_FILE = "LOCK.json"


@dataclass(frozen=True)
class LocalModelSpec:
    kind: ModelKind
    label: str
    env_var: str
    default_rel_path: str | None = None
    hub_id: str | None = None
    modelscope_id: str | None = None
    ollama_tag: str | None = None
    required_files: tuple[str, ...] = ()
    hub_files: tuple[str, ...] = ()


CATALOG: dict[ModelKind, LocalModelSpec] = {
    "whisper": LocalModelSpec(
        kind="whisper",
        label="Whisper ASR (faster-whisper medium)",
        env_var="WHISPER_MODEL",
        default_rel_path="models/faster-whisper-medium",
        hub_id="Systran/faster-whisper-medium",
        modelscope_id="AI-ModelScope/faster-whisper-medium",
        required_files=("model.bin", "config.json"),
    ),
    "embed": LocalModelSpec(
        kind="embed",
        label="Embedding (BGE small zh)",
        env_var="EMBED_MODEL_PATH",
        default_rel_path="models/bge-small-zh-v1.5",
        hub_id="BAAI/bge-small-zh-v1.5",
        modelscope_id="AI-ModelScope/bge-small-zh-v1.5",
        required_files=("config.json", "model.safetensors"),
    ),
    "ollama": LocalModelSpec(
        kind="ollama",
        label="LLM (Ollama)",
        env_var="OLLAMA_MODEL",
        ollama_tag="qwen2.5:14b",
    ),
    "tts": LocalModelSpec(
        kind="tts",
        label="TTS clone (F5-TTS)",
        env_var="TTS_MODEL_PATH",
        default_rel_path="models/F5-TTS",
        hub_id="SWivid/F5-TTS",
        modelscope_id="AI-ModelScope/F5-TTS",
        required_files=(
            "F5TTS_v1_Base/model_1250000.safetensors",
            "F5TTS_v1_Base/vocab.txt",
        ),
        hub_files=(
            "F5TTS_v1_Base/model_1250000.safetensors",
            "F5TTS_v1_Base/vocab.txt",
        ),
    ),
    "vocos": LocalModelSpec(
        kind="vocos",
        label="Vocoder (F5-TTS dependency)",
        env_var="VOCOS_MODEL_PATH",
        default_rel_path="models/vocos-mel-24khz",
        hub_id="charactr/vocos-mel-24khz",
        modelscope_id=None,
        required_files=("config.yaml", "pytorch_model.bin"),
        hub_files=("config.yaml", "pytorch_model.bin"),
    ),
    "ocr": LocalModelSpec(
        kind="ocr",
        label="PaddleOCR (PP-OCRv6 zh det+rec)",
        env_var="PADDLEX_CACHE_HOME",
        default_rel_path="models/paddlex",
        required_files=(
            "official_models/PP-OCRv6_medium_det/inference.json",
            "official_models/PP-OCRv6_medium_rec/inference.json",
        ),
    ),
    "pix2tex": LocalModelSpec(
        kind="pix2tex",
        label="pix2tex / LaTeX-OCR weights",
        env_var="PIX2TEX_MODEL_PATH",
        default_rel_path="models/pix2tex",
        required_files=("weights.pth", "image_resizer.pth"),
    ),
}


def _cfg():
    from app import config

    return config


def spec(kind: ModelKind) -> LocalModelSpec:
    return CATALOG[kind]


def default_path(kind: ModelKind) -> Path | None:
    item = CATALOG[kind]
    if not item.default_rel_path:
        return None
    return _cfg().ROOT / item.default_rel_path


def configured_path(kind: ModelKind) -> Path | None:
    item = CATALOG[kind]
    raw = os.getenv(item.env_var, "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = _cfg().ROOT / path
        return path
    return default_path(kind)


def is_path_ready(path: Path | None, *, required_files: tuple[str, ...]) -> bool:
    if path is None or not path.exists():
        return False
    if path.is_file():
        return True
    if not required_files:
        return True
    return all((path / name).exists() for name in required_files)


def _package_vocab_exists() -> bool:
    try:
        from importlib.resources import files

        return files("f5_tts").joinpath("infer/examples/vocab.txt").is_file()
    except Exception:  # noqa: BLE001
        return False


def f5_vocab_path() -> Path | None:
    base = configured_path("tts")
    if base is not None:
        candidate = base / "F5TTS_v1_Base" / "vocab.txt"
        if candidate.is_file():
            return candidate
    return None


def whisper_ready() -> bool:
    item = CATALOG["whisper"]
    path = configured_path("whisper")
    if path is None:
        return False
    if path.is_file():
        return True
    return is_path_ready(path, required_files=item.required_files)


def embed_ready() -> bool:
    item = CATALOG["embed"]
    path = configured_path("embed")
    if path is None:
        return False
    if (path / "model.safetensors").is_file():
        return is_path_ready(path, required_files=item.required_files)
    # Accept legacy pytorch_model.bin layout.
    return is_path_ready(path, required_files=("config.json", "pytorch_model.bin"))


def ollama_ready() -> bool:
    tag = os.getenv("OLLAMA_MODEL", CATALOG["ollama"].ollama_tag or "").strip()
    if not tag:
        return False
    try:
        proc = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0:
        return False
    base = tag.split(":", 1)[0]
    return any(line.split()[0].startswith(base) for line in proc.stdout.splitlines()[1:] if line.strip())


def vocos_ready() -> bool:
    item = CATALOG["vocos"]
    return is_path_ready(configured_path("vocos"), required_files=item.required_files)


def tts_ready() -> bool:
    try:
        import f5_tts  # noqa: F401
    except ImportError:
        return False
    item = CATALOG["tts"]
    path = configured_path("tts")
    if path is None:
        return False
    ckpt = path / "F5TTS_v1_Base" / "model_1250000.safetensors"
    if not ckpt.is_file():
        return False
    vocab_local = path / "F5TTS_v1_Base" / "vocab.txt"
    if not vocab_local.is_file() and not _package_vocab_exists():
        return False
    return vocos_ready()


def apply_paddle_env(*, for_pull: bool = False) -> None:
    """Pin PaddleX/PaddleOCR caches under models/paddlex."""
    cache = configured_path("ocr") or default_path("ocr")
    if cache is not None:
        os.environ["PADDLE_PDX_CACHE_HOME"] = str(cache)
    os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", _cfg().PADDLE_PDX_MODEL_SOURCE)
    if _cfg().HF_ENDPOINT:
        os.environ.setdefault("PADDLE_PDX_HUGGING_FACE_ENDPOINT", _cfg().HF_ENDPOINT)
    # Avoid oneDNN / PIR attribute crashes on some Windows CPU builds.
    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")
    if for_pull:
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    elif ocr_ready():
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")


def ocr_ready() -> bool:
    item = CATALOG["ocr"]
    return is_path_ready(configured_path("ocr"), required_files=item.required_files)


def pix2tex_ready() -> bool:
    item = CATALOG["pix2tex"]
    return is_path_ready(configured_path("pix2tex"), required_files=item.required_files)


def apply_offline_env() -> None:
    """Pin caches under models/ and block surprise Hub downloads when local-first."""
    cfg = _cfg()
    models_dir = cfg.MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)
    hf_home = cfg.HF_HOME
    hf_home.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("HF_HOME", str(hf_home))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(hf_home / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(hf_home / "transformers"))
    os.environ.setdefault("TORCH_HOME", str(models_dir / "torch"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(models_dir))

    embed_path = configured_path("embed")
    if embed_path is not None:
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(embed_path.parent))

    if not cfg.LOCAL_FIRST:
        apply_paddle_env()
        return

    if whisper_ready() and embed_ready() and vocos_ready():
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    elif cfg.HF_HUB_OFFLINE:
        os.environ.setdefault("HF_HUB_OFFLINE", cfg.HF_HUB_OFFLINE)
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    apply_paddle_env()


@contextmanager
def online_pull() -> Iterator[None]:
    """Temporarily allow Hub downloads during `models pull`."""
    saved = {
        key: os.environ.get(key)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")
    }
    for key in saved:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _cleanup_incomplete(root: Path) -> None:
    if not root.exists():
        return
    for path in root.rglob("*.incomplete"):
        try:
            path.unlink()
        except OSError:
            pass


def _hub_mirror_base() -> str:
    endpoint = (_cfg().HF_ENDPOINT or "https://huggingface.co").rstrip("/")
    return endpoint


def _download_url_resumable(url: str, dest: Path, *, retries: int = 5) -> None:
    import requests

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        return
    partial = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        try:
            with requests.get(url, headers=headers, stream=True, timeout=120) as resp:
                if resp.status_code == 416:
                    # Partial already complete — promote it.
                    if partial.exists() and partial.stat().st_size > 0:
                        partial.replace(dest)
                        return
                    partial.unlink(missing_ok=True)
                    offset = 0
                    continue
                if resp.status_code not in (200, 206):
                    resp.raise_for_status()
                mode = "ab" if offset and resp.status_code == 206 else "wb"
                if mode == "wb" and offset:
                    partial.unlink(missing_ok=True)
                    offset = 0
                with partial.open(mode) as handle:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            partial.replace(dest)
            return
        except Exception as exc:  # noqa: BLE001
            if attempt >= retries:
                raise RuntimeError(f"download failed for {url}: {exc}") from exc


def _download_hub_files(repo_id: str, dest: Path, filenames: tuple[str, ...]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    for name in filenames:
        target = dest / name
        if target.is_file() and target.stat().st_size > 0:
            continue
        try:
            from huggingface_hub import hf_hub_download

            fetched = hf_hub_download(repo_id=repo_id, filename=name, local_dir=str(dest))
            if Path(fetched).is_file():
                continue
        except Exception as exc:  # noqa: BLE001
            errors.append(f"hub:{name}:{exc}")

        mirror_url = f"{_hub_mirror_base()}/{repo_id}/resolve/main/{name}"
        try:
            _download_url_resumable(mirror_url, target)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"mirror:{name}:{exc}")

    missing = [name for name in filenames if not (dest / name).is_file()]
    if missing:
        raise RuntimeError(
            f"failed to fetch {repo_id} files {missing}: " + "; ".join(errors)
        )


def _ensure_f5_vocab(dest: Path) -> Path:
    vocab = dest / "F5TTS_v1_Base" / "vocab.txt"
    if vocab.is_file():
        return vocab
    try:
        from importlib.resources import as_file, files

        ref = files("f5_tts").joinpath("infer/examples/vocab.txt")
        with as_file(ref) as packaged:
            if not packaged.is_file():
                raise RuntimeError("F5-TTS packaged vocab.txt not found")
            vocab.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(packaged, vocab)
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("F5-TTS vocab.txt not found locally or in f5-tts package") from exc
    return vocab


def _download_via_modelscope(repo_id: str, dest: Path) -> None:
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "modelscope is not installed. Run: pip install modelscope"
        ) from exc
    dest.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id, local_dir=str(dest))


def _download_via_hub(
    repo_id: str,
    dest: Path,
    *,
    allow_patterns: tuple[str, ...] | None = None,
) -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "huggingface_hub is not installed. Run: pip install huggingface_hub"
        ) from exc
    dest.mkdir(parents=True, exist_ok=True)
    kwargs: dict = {"local_dir": str(dest)}
    if allow_patterns:
        kwargs["allow_patterns"] = list(allow_patterns)
    snapshot_download(repo_id, **kwargs)


def _pull_f5_tts(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    _cleanup_incomplete(dest)
    ckpt = dest / "F5TTS_v1_Base" / "model_1250000.safetensors"
    vocab = dest / "F5TTS_v1_Base" / "vocab.txt"
    errors: list[str] = []

    if ckpt.is_file() and vocab.is_file():
        return dest

    if ckpt.is_file() and not vocab.is_file():
        try:
            _ensure_f5_vocab(dest)
            return dest
        except Exception as exc:  # noqa: BLE001
            errors.append(f"vocab: {exc}")

    patterns = list(CATALOG["tts"].hub_files)

    item = CATALOG["tts"]
    if item.modelscope_id:
        try:
            _download_via_modelscope(item.modelscope_id, dest)
            if ckpt.is_file() and vocab.is_file():
                return dest
        except Exception as exc:  # noqa: BLE001
            errors.append(f"modelscope: {exc}")

    if item.hub_id:
        try:
            _download_via_hub(item.hub_id, dest, allow_patterns=tuple(patterns))
            if ckpt.is_file() and vocab.is_file():
                return dest
        except Exception as exc:  # noqa: BLE001
            errors.append(f"huggingface: {exc}")

    if ckpt.is_file() and not vocab.is_file():
        packaged = f5_vocab_path()
        if packaged and packaged.is_file():
            vocab.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(packaged, vocab)

    if ckpt.is_file() and vocab.is_file():
        return dest

    raise RuntimeError("failed to pull F5-TTS: " + "; ".join(errors or ["incomplete files"]))


def _pull_vocos(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    _cleanup_incomplete(dest)
    item = CATALOG["vocos"]
    if is_path_ready(dest, required_files=item.required_files):
        return dest

    errors: list[str] = []
    if item.hub_id:
        try:
            _download_hub_files(item.hub_id, dest, item.hub_files)
            if is_path_ready(dest, required_files=item.required_files):
                return dest
        except Exception as exc:  # noqa: BLE001
            errors.append(f"huggingface: {exc}")

    raise RuntimeError("failed to pull vocos: " + "; ".join(errors or ["incomplete files"]))


def _pull_ocr(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    apply_paddle_env(for_pull=True)
    if ocr_ready():
        return dest
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("paddleocr not installed. Run: pip install paddleocr") from exc

    print("[ocr] downloading PP-OCRv6 models via Paddle BOS …", flush=True)
    PaddleOCR(
        lang=_cfg().PADDLE_OCR_LANG,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    if not ocr_ready():
        raise RuntimeError("PaddleOCR pull incomplete")
    return dest


def _pull_pix2tex(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    item = CATALOG["pix2tex"]
    if is_path_ready(dest, required_files=item.required_files):
        return dest

    tag = "v0.0.1"
    files = {
        "weights.pth": f"https://github.com/lukas-blecher/LaTeX-OCR/releases/download/{tag}/weights.pth",
        "image_resizer.pth": f"https://github.com/lukas-blecher/LaTeX-OCR/releases/download/{tag}/image_resizer.pth",
    }
    for name, url in files.items():
        target = dest / name
        if target.is_file() and target.stat().st_size > 0:
            continue
        print(f"[pix2tex] downloading {name} …", flush=True)
        _download_url_resumable(url, target)
    if not pix2tex_ready():
        raise RuntimeError("pix2tex pull incomplete")
    return dest


def pull(kind: ModelKind, *, force: bool = False) -> Path | str:
    item = CATALOG[kind]
    with online_pull():
        if kind == "ollama":
            tag = os.getenv("OLLAMA_MODEL", item.ollama_tag or "").strip()
            if not tag:
                raise RuntimeError("OLLAMA_MODEL is empty")
            subprocess.run(["ollama", "pull", tag], check=True)
            return tag

        if kind == "tts":
            dest = configured_path(kind) or default_path(kind)
            if dest is None:
                raise RuntimeError("tts has no local path configured")
            ckpt = dest / "F5TTS_v1_Base" / "model_1250000.safetensors"
            vocab = dest / "F5TTS_v1_Base" / "vocab.txt"
            if not force and ckpt.is_file():
                if not vocab.is_file():
                    packaged = f5_vocab_path()
                    if packaged and packaged.is_file():
                        vocab.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(packaged, vocab)
                if vocab.is_file():
                    return dest
            if dest.exists() and force:
                shutil.rmtree(dest)
            return _pull_f5_tts(dest)

        if kind == "vocos":
            dest = configured_path(kind) or default_path(kind)
            if dest is None:
                raise RuntimeError("vocos has no local path configured")
            if not force and is_path_ready(dest, required_files=item.required_files):
                return dest
            if dest.exists() and force:
                shutil.rmtree(dest)
            return _pull_vocos(dest)

        if kind == "ocr":
            dest = configured_path(kind) or default_path(kind)
            if dest is None:
                raise RuntimeError("ocr has no local path configured")
            if force and (dest / "official_models").exists():
                shutil.rmtree(dest / "official_models")
            if not force and ocr_ready():
                return dest
            return _pull_ocr(dest)

        if kind == "pix2tex":
            dest = configured_path(kind) or default_path(kind)
            if dest is None:
                raise RuntimeError("pix2tex has no local path configured")
            if not force and pix2tex_ready():
                return dest
            if dest.exists() and force:
                shutil.rmtree(dest)
            return _pull_pix2tex(dest)

        dest = configured_path(kind) or default_path(kind)
        if dest is None:
            raise RuntimeError(f"{kind} has no local path configured")

        if not force and is_path_ready(dest, required_files=item.required_files):
            return dest

        if dest.exists() and force:
            shutil.rmtree(dest)

        errors: list[str] = []
        if item.modelscope_id:
            try:
                _download_via_modelscope(item.modelscope_id, dest)
                if is_path_ready(dest, required_files=item.required_files):
                    return dest
            except Exception as exc:  # noqa: BLE001
                errors.append(f"modelscope: {exc}")
        if item.hub_id:
            try:
                _download_via_hub(item.hub_id, dest)
                if is_path_ready(dest, required_files=item.required_files):
                    return dest
            except Exception as exc:  # noqa: BLE001
                errors.append(f"huggingface: {exc}")

        raise RuntimeError(f"failed to pull {kind}: " + "; ".join(errors))


def pull_all(*, force: bool = False) -> list[tuple[ModelKind, Path | str]]:
    results: list[tuple[ModelKind, Path | str]] = []
    for kind in ALL_MODEL_KINDS:
        results.append((kind, pull(kind, force=force)))
    return results


def readiness() -> dict[str, tuple[str, str, bool]]:
    rows: dict[str, tuple[str, str, bool]] = {}
    rows["whisper"] = (
        str(configured_path("whisper") or "-"),
        CATALOG["whisper"].label,
        whisper_ready(),
    )
    rows["embed"] = (
        str(configured_path("embed") or "-"),
        CATALOG["embed"].label,
        embed_ready(),
    )
    rows["ollama"] = (
        os.getenv("OLLAMA_MODEL", CATALOG["ollama"].ollama_tag or "-"),
        CATALOG["ollama"].label,
        ollama_ready(),
    )
    rows["tts"] = (
        str(configured_path("tts") or "-"),
        CATALOG["tts"].label,
        tts_ready(),
    )
    rows["vocos"] = (
        str(configured_path("vocos") or "-"),
        CATALOG["vocos"].label,
        vocos_ready(),
    )
    rows["ocr"] = (
        str(configured_path("ocr") or "-"),
        CATALOG["ocr"].label,
        ocr_ready(),
    )
    rows["pix2tex"] = (
        str(configured_path("pix2tex") or "-"),
        CATALOG["pix2tex"].label,
        pix2tex_ready(),
    )
    return rows


def status_rows() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for name, (path, _label, ready) in readiness().items():
        rows.append((name, path, "ready" if ready else "missing"))
    rows.append(
        (
            "llm_provider",
            _cfg().LLM_PROVIDER,
            "local" if _cfg().LLM_PROVIDER == "ollama" else "cloud",
        )
    )
    offline = os.getenv("HF_HUB_OFFLINE", "")
    rows.append(("hf_offline", offline or "(unset)", "on" if offline == "1" else "off"))
    rows.append(("local_first", str(_cfg().LOCAL_FIRST).lower(), "on" if _cfg().LOCAL_FIRST else "off"))
    return rows


def verify_local_assets() -> list[str]:
    """Return human-readable issues for missing runtime intelligence assets."""
    issues: list[str] = []
    for name, (path, label, ready) in readiness().items():
        if not ready:
            issues.append(f"{name} missing ({label}) @ {path}")
    cfg = _cfg()
    if cfg.LOCAL_FIRST and cfg.LLM_PROVIDER != "ollama":
        issues.append(
            f"LOCAL_FIRST=true but LLM_PROVIDER={cfg.LLM_PROVIDER} (set ollama for offline LLM)"
        )
    if cfg.LOCAL_FIRST and not os.getenv("HF_HUB_OFFLINE"):
        issues.append("HF_HUB_OFFLINE not set — runtime may still reach HuggingFace Hub")
    return issues


def write_lock_manifest() -> Path:
    """Write models/LOCK.json describing pinned local asset paths."""
    cfg = _cfg()
    cfg.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 1,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local_first": cfg.LOCAL_FIRST,
        "llm_provider": cfg.LLM_PROVIDER,
        "hf_home": str(cfg.HF_HOME),
        "assets": {},
    }
    for name, (path, label, ready) in readiness().items():
        manifest["assets"][name] = {
            "label": label,
            "path": path,
            "ready": ready,
            "env": CATALOG[name].env_var if name in CATALOG else "",
        }
    manifest["assets"]["f5_vocab"] = {
        "path": str(f5_vocab_path() or ""),
        "ready": f5_vocab_path() is not None,
    }
    dest = cfg.MODELS_DIR / LOCK_FILE
    dest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest
