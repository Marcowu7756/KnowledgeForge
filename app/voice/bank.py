from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app import config


@dataclass
class VoiceProfile:
    name: str
    sample_path: str
    transcript: str = ""
    created: str = ""
    duration_sec: float | None = None
    source: str = "record"  # record | import


def voices_dir() -> Path:
    path = config.VOICES_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def profile_dir(name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip())[:40]
    if not safe:
        raise ValueError("voice name is empty")
    return voices_dir() / safe


def meta_path(name: str) -> Path:
    return profile_dir(name) / "meta.json"


def sample_path(name: str) -> Path:
    return profile_dir(name) / "sample.wav"


def load_profile(name: str) -> VoiceProfile:
    path = meta_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"voice profile not found: {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return VoiceProfile(
        name=str(data.get("name") or name),
        sample_path=str(data.get("sample_path") or sample_path(name)),
        transcript=str(data.get("transcript") or ""),
        created=str(data.get("created") or ""),
        duration_sec=data.get("duration_sec"),
        source=str(data.get("source") or "record"),
    )


def save_profile(profile: VoiceProfile) -> Path:
    dest = profile_dir(profile.name)
    dest.mkdir(parents=True, exist_ok=True)
    path = meta_path(profile.name)
    path.write_text(
        json.dumps(asdict(profile), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def list_profiles() -> list[VoiceProfile]:
    items: list[VoiceProfile] = []
    for child in sorted(voices_dir().iterdir()):
        if child.is_dir() and (child / "meta.json").is_file():
            try:
                items.append(load_profile(child.name))
            except Exception:  # noqa: BLE001
                continue
    return items


def default_voice_name() -> str | None:
    name = (config.TTS_VOICE_NAME or "").strip()
    if name:
        return name
    marker = voices_dir() / "DEFAULT"
    if marker.is_file():
        return marker.read_text(encoding="utf-8").strip() or None
    profiles = list_profiles()
    return profiles[0].name if profiles else None


def set_default_voice(name: str) -> None:
    load_profile(name)  # validate
    (voices_dir() / "DEFAULT").write_text(name, encoding="utf-8")


def resolve_voice(name: str | None = None) -> VoiceProfile | None:
    chosen = (name or "").strip() or default_voice_name()
    if not chosen:
        return None
    return load_profile(chosen)


def write_profile_from_wav(
    name: str,
    wav_path: Path,
    *,
    transcript: str = "",
    source: str = "import",
    duration_sec: float | None = None,
) -> VoiceProfile:
    dest_dir = profile_dir(name)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_wav = sample_path(name)
    if Path(wav_path).resolve() != dest_wav.resolve():
        dest_wav.write_bytes(Path(wav_path).read_bytes())
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    profile = VoiceProfile(
        name=dest_dir.name,
        sample_path=dest_wav.as_posix(),
        transcript=transcript.strip(),
        created=stamp,
        duration_sec=duration_sec,
        source=source,
    )
    save_profile(profile)
    return profile
