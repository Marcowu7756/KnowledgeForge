from app.ingest.audio import AudioIngestError, ingest_audio
from app.ingest.bilibili import BilibiliIngestError, ingest_bilibili
from app.ingest.docs import ingest_file
from app.ingest.errors import FileIngestError
from app.ingest.pdf import ingest_pdf
from app.ingest.search import SearchHit, search_files
from app.ingest.twitter import TwitterIngestError, ingest_twitter, ingest_twitter_timeline
from app.ingest.youtube import YouTubeIngestError, ingest_youtube
from app.models import IngestedSource


def ingest(kind: str, target: str) -> IngestedSource:
    if kind == "youtube":
        return ingest_youtube(target)
    if kind == "bilibili":
        return ingest_bilibili(target)
    if kind == "twitter":
        return ingest_twitter(target)
    if kind == "pdf":
        return ingest_pdf(target)
    if kind == "file":
        return ingest_file(target)
    if kind == "audio":
        return ingest_audio(target)
    raise ValueError(f"unsupported ingest kind: {kind}")


__all__ = [
    "AudioIngestError",
    "BilibiliIngestError",
    "FileIngestError",
    "SearchHit",
    "TwitterIngestError",
    "YouTubeIngestError",
    "ingest",
    "ingest_audio",
    "ingest_bilibili",
    "ingest_file",
    "ingest_pdf",
    "ingest_twitter",
    "ingest_twitter_timeline",
    "ingest_youtube",
    "search_files",
]
