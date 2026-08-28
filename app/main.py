from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app import config
from app.compose import compose_from_query
from app.derive import derive_from_card
from app.expression import animate_from_card, express_from_card
from app.expression.render_tts import TtsError
from app.harness import HarnessError, compile_knowledge, rerun_step
from app.reconstruct import ReconstructLoadError, run_reconstruct
from app.retrieve import EmbedderError, run_index, run_query
from app.local_models import pull as pull_local_model
from app.local_models import status_rows, verify_local_assets, write_lock_manifest
from app.voice import (
    CloneTtsError,
    VoiceRecordError,
    default_voice_name,
    import_profile,
    list_profiles,
    record_profile,
    set_default_voice,
    speak_with_voice,
)
from app.ingest.ecosystem import run_ecosystem_ingest
from app.ingest.setv_artifact import run_artifact_ingest, run_manifest_ingest
from app.pipeline import (
    AudioIngestError,
    BilibiliIngestError,
    FileIngestError,
    ImageIngestError,
    TwitterIngestError,
    YouTubeIngestError,
    run_audio,
    run_bilibili,
    run_file,
    run_image,
    run_search,
    run_twitter,
    run_twitter_timeline,
    run_youtube,
)
from app.storage.index import rebuild_index

USAGE = """KnowledgeForge — PAILE knowledge reconstruction engine

  python main.py youtube <URL>
  python main.py bilibili <URL>
  python main.py twitter <TWEET_URL>
  python main.py twitter <@USER> --timeline [--limit N]
  python main.py file <FILE>
  python main.py image <IMAGE>
  python main.py audio <WAV|MP3|...>
  python main.py pdf <FILE>
  python main.py search <ROOT> ... --keyword <WORD>
  python main.py ecosystem ingest setv|factorlib|asharelib <ROOT> ... [--dry-run] [--limit N]
  python main.py setv snapshot|evolution|family|measurement|experiment|uncertainty <path|dir> ...
  python main.py setv ingest --setv-root DIR [--manifest PATH] [--class CLASS] [--dry-run] [--limit N]
  python main.py derive <KNOWLEDGE.md> [--mode auto|english|physics|generic]
  python main.py express <KNOWLEDGE.md> [--voice NAME] [--no-animation] [--no-narration]
  python main.py animate <KNOWLEDGE.md> [--fast]
  python main.py compile <SOURCE|CARD.md> [--animate] [--narrate] [--fast]
  python main.py compile --rerun-step animation|expression|manifest --package DIR
  python main.py reconstruct --from-index [--view theme|concept|learning_path|taxonomy|contrast] [--seed X]
  python main.py reconstruct --from-index --min-confidence 0.5
  python main.py reconstruct --evolve data\\reconstruct\\<id> --add CARD.md
  python main.py reconstruct --from-packages [--view theme]
  python main.py reconstruct CARD1.md CARD2.md ... --view concept --seed 美债
  python main.py retrieve index --from-index
  python main.py retrieve query "美债信用风险" [--graph DIR] [--top 5]
  python main.py compose paper|lecture "主题" [--top 5] [--graph DIR]
  python main.py voice record --name me [--seconds 12]
  python main.py voice import <WAV> --name me
  python main.py voice list
  python main.py voice use <NAME>
  python main.py voice speak "文本" [--voice NAME] [-o out.wav]
  python main.py index rebuild [--subdir NAME]
  python main.py models status
  python main.py models pull [--only whisper,embed,ollama,tts,vocos,ocr,pix2tex]
  python main.py ui [--port 8765] [--desktop]
  python main.py export encrypted <PATH> [-o OUT.kfexport]
  python main.py status
"""


def _add_index_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip writing knowledge indexes for this run",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knowledgeforge",
        description="Compress unstructured input into Knowledge Units.",
    )
    sub = parser.add_subparsers(dest="command")

    yt = sub.add_parser("youtube", help="Ingest a YouTube URL → Knowledge Unit")
    yt.add_argument("url")
    _add_index_flag(yt)

    bili = sub.add_parser("bilibili", help="Ingest a Bilibili URL → Knowledge Unit")
    bili.add_argument("url")
    _add_index_flag(bili)

    tw = sub.add_parser("twitter", help="Ingest Twitter/X tweets or a user timeline")
    tw.add_argument(
        "target",
        help="Tweet URL, or @handle when using --timeline",
    )
    tw.add_argument(
        "--timeline",
        action="store_true",
        help="Fetch recent tweets from @handle (needs TWITTER_BEARER_TOKEN)",
    )
    tw.add_argument("--limit", type=int, default=10, help="Max tweets for --timeline")
    _add_index_flag(tw)

    pdf = sub.add_parser("pdf", help="Ingest a local PDF → Knowledge Unit")
    pdf.add_argument("file")
    pdf.add_argument(
        "--dest-subdir",
        default=None,
        help="Optional subfolder under data/knowledge/",
    )
    _add_index_flag(pdf)

    file_cmd = sub.add_parser(
        "file",
        help="Ingest a local MD / TXT / DOCX / PDF file",
    )
    file_cmd.add_argument("file")
    file_cmd.add_argument(
        "--dest-subdir",
        default=None,
        help="Optional subfolder under data/knowledge/",
    )
    _add_index_flag(file_cmd)

    image_cmd = sub.add_parser("image", help="OCR a local image → Knowledge Unit")
    image_cmd.add_argument("file")
    image_cmd.add_argument(
        "--dest-subdir",
        default=None,
        help="Optional subfolder under data/knowledge/",
    )
    _add_index_flag(image_cmd)

    audio_cmd = sub.add_parser(
        "audio",
        help="Ingest local audio (WAV/MP3/…) via Whisper → Knowledge Unit",
    )
    audio_cmd.add_argument("file", help="Path to audio file")
    audio_cmd.add_argument(
        "--dest-subdir",
        default=None,
        help="Optional subfolder under data/knowledge/",
    )
    _add_index_flag(audio_cmd)

    search = sub.add_parser(
        "search",
        help="Search fixed folders by keyword and compress matches",
    )
    search.add_argument(
        "roots",
        nargs="+",
        help="One or more directories to search (read-only)",
    )
    search.add_argument(
        "--keyword",
        required=True,
        help="Case-insensitive filename keyword, e.g. methodology",
    )
    search.add_argument(
        "--dest-subdir",
        default=None,
        help="Write cards under data/knowledge/<subdir>/",
    )
    search.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N matched files",
    )
    search.add_argument(
        "--dry-run",
        action="store_true",
        help="List matches only; do not call the LLM",
    )
    search.add_argument(
        "--no-synthesis",
        action="store_true",
        help="Skip the final integrated atlas card",
    )
    search.add_argument(
        "--synthesis-title",
        default=None,
        help="Title for the integrated synthesis card",
    )
    _add_index_flag(search)

    ecosystem = sub.add_parser(
        "ecosystem",
        help="Ingest SETV / FactorLib / AShareLib design docs → hierarchical KOs",
    )
    eco_sub = ecosystem.add_subparsers(dest="ecosystem_command")
    eco_ingest = eco_sub.add_parser(
        "ingest",
        help="Compile external design docs (conclusions only, no raw data)",
    )
    eco_ingest.add_argument(
        "project",
        choices=["setv", "factorlib", "asharelib"],
        help="Source ecosystem project",
    )
    eco_ingest.add_argument(
        "roots",
        nargs="+",
        help="Read-only doc roots to scan (.md/.txt)",
    )
    eco_ingest.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N matched files",
    )
    eco_ingest.add_argument(
        "--dry-run",
        action="store_true",
        help="List matches only; do not call the LLM",
    )
    _add_index_flag(eco_ingest)

    setv = sub.add_parser(
        "setv",
        help="SETV Artifact cite-only ingest (AE-2 snapshot / evolution / family)",
    )
    setv_sub = setv.add_subparsers(dest="setv_command")

    def _add_setv_paths(parser: argparse.ArgumentParser, *, path_help: str) -> None:
        parser.add_argument("paths", nargs="+", help=path_help)
        parser.add_argument(
            "--setv-root",
            default=None,
            help="SETV / fxtrading root for relative evidence_pointer resolution",
        )
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--dry-run", action="store_true")
        _add_index_flag(parser)

    setv_snap = setv_sub.add_parser(
        "snapshot",
        help="Instance CARD.md → State Snapshot KO (no LLM)",
    )
    _add_setv_paths(
        setv_snap,
        path_help="CARD.md file(s) and/or instances directory roots",
    )
    setv_evo = setv_sub.add_parser(
        "evolution",
        help="L-SA/KP/KR edges + kernel Evidence → State Evolution KO (no LLM)",
    )
    _add_setv_paths(
        setv_evo,
        path_help="Edge/Evidence .md file(s) and/or SETV research|evidence roots",
    )
    setv_fam = setv_sub.add_parser(
        "family",
        help="SETV-FAM / L-XS / L-SF → State Family KO (no LLM)",
    )
    _add_setv_paths(
        setv_fam,
        path_help="Family/edge .md file(s) and/or families|links roots",
    )
    setv_meas = setv_sub.add_parser(
        "measurement",
        help="State Contract / fascicle → Measurement Knowledge KO (no LLM)",
    )
    _add_setv_paths(
        setv_meas,
        path_help="Contract .md file(s) and/or methodology roots",
    )
    setv_exp = setv_sub.add_parser(
        "experiment",
        help="SETV-EXP packs → Experiment Evidence KO (no LLM)",
    )
    _add_setv_paths(
        setv_exp,
        path_help="SETV_EXP_*.md and/or evidence/families roots",
    )
    setv_unc = setv_sub.add_parser(
        "uncertainty",
        help="Uncertainty Language / fence docs → Uncertainty KO (no LLM)",
    )
    _add_setv_paths(
        setv_unc,
        path_help="DESIGN_*UNCERTAINTY* / OWNER_CONFIRM_*UNCERTAINTY* roots",
    )
    setv_ingest = setv_sub.add_parser(
        "ingest",
        help="OPEN KF INGEST · prefer manifest_v0.jsonl → export sidecars (no LLM)",
    )
    setv_ingest.add_argument(
        "--setv-root",
        required=True,
        help="SETV / fxtrading root (required for manifest relative paths)",
    )
    setv_ingest.add_argument(
        "--manifest",
        default=None,
        help="Path to manifest_v0.jsonl (default: <setv-root>/methodology/SETV/export/manifest_v0.jsonl)",
    )
    setv_ingest.add_argument(
        "--class",
        dest="ingest_class",
        choices=[
            "snapshot",
            "evolution",
            "family",
            "measurement",
            "experiment",
            "uncertainty",
        ],
        default=None,
        help="Optional filter by asset_class",
    )
    setv_ingest.add_argument("--limit", type=int, default=None)
    setv_ingest.add_argument("--dry-run", action="store_true")
    _add_index_flag(setv_ingest)

    index = sub.add_parser("index", help="Manage knowledge indexes (optional feature)")
    index_sub = index.add_subparsers(dest="index_command")
    rebuild = index_sub.add_parser(
        "rebuild",
        help="Rebuild INDEX.md / index.json from existing knowledge cards",
    )
    rebuild.add_argument(
        "--subdir",
        default=None,
        help="Only rebuild one folder under data/knowledge/, e.g. methodology",
    )

    derive = sub.add_parser(
        "derive",
        help="Expand a Knowledge Unit into examples (EN) or vivid process (physics)",
    )
    derive.add_argument("card", help="Path to an existing knowledge markdown card")
    derive.add_argument(
        "--mode",
        choices=["auto", "english", "physics", "finance", "generic"],
        default="auto",
        help="Derivation mode (default: auto-detect from tags/title)",
    )

    express = sub.add_parser(
        "express",
        help="Present a Knowledge Unit as animation + narration (Layer 3)",
    )
    express.add_argument("card", help="Path to knowledge markdown card")
    express.add_argument("--voice", default=None, help="Voice profile name for clone TTS")
    express.add_argument("--no-animation", action="store_true")
    express.add_argument("--no-narration", action="store_true")

    animate = sub.add_parser(
        "animate",
        help="Present a Knowledge Unit as animation GIF only (Layer 3, no TTS)",
    )
    animate.add_argument("card", help="Path to knowledge markdown card")
    animate.add_argument(
        "--fast",
        action="store_true",
        help="Rule-based compile from Mechanisms/Timeline/Key Points (no LLM)",
    )

    compile_cmd = sub.add_parser(
        "compile",
        help="Harness: Source/Card → KnowledgeObject package",
    )
    compile_cmd.add_argument(
        "source",
        nargs="?",
        default=None,
        help="URL, local file/image, or existing knowledge card .md",
    )
    compile_cmd.add_argument(
        "--from-card",
        action="store_true",
        help="Treat source as an existing Knowledge Unit card",
    )
    compile_cmd.add_argument(
        "--animate",
        action="store_true",
        help="Also compile animation GIF",
    )
    compile_cmd.add_argument(
        "--narrate",
        action="store_true",
        help="Also compile narration (includes animation via express)",
    )
    compile_cmd.add_argument(
        "--fast",
        action="store_true",
        help="Use rule-based animation when --animate (no LLM)",
    )
    compile_cmd.add_argument("--voice", default=None, help="Voice profile for --narrate")
    compile_cmd.add_argument(
        "--rerun-step",
        choices=["animation", "expression", "manifest"],
        default=None,
        help="Re-run one step on an existing package",
    )
    compile_cmd.add_argument(
        "--package",
        default=None,
        help="Package directory for --rerun-step",
    )
    _add_index_flag(compile_cmd)

    reconstruct = sub.add_parser(
        "reconstruct",
        help="P2: Multiple KO → Concept Graph → Reconstructed View",
    )
    reconstruct.add_argument(
        "sources",
        nargs="*",
        help="KnowledgeObject JSON and/or knowledge card .md paths",
    )
    reconstruct.add_argument(
        "--from-index",
        action="store_true",
        help="Load KOs from data/knowledge/index/units.jsonl",
    )
    reconstruct.add_argument(
        "--from-packages",
        action="store_true",
        help="Load KOs from data/packages/*/knowledge_object.json",
    )
    reconstruct.add_argument(
        "--subdir",
        default=None,
        help="Filter index by knowledge subfolder",
    )
    reconstruct.add_argument("--tag", default=None, help="Filter index by tag")
    reconstruct.add_argument(
        "--concept",
        default=None,
        help="Filter index by concept",
    )
    reconstruct.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max KOs when using --from-index",
    )
    reconstruct.add_argument(
        "--taxonomy-prefix",
        default=None,
        help="Filter index by taxonomy path prefix, e.g. 专有知识/SETV",
    )
    reconstruct.add_argument(
        "--view",
        choices=["theme", "concept", "learning_path", "taxonomy", "contrast", "none"],
        default="theme",
        help="Reconstructed view type (default: theme)",
    )
    reconstruct.add_argument(
        "--seed",
        default="",
        help="Seed concept/theme for concept or filtered theme views",
    )
    reconstruct.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Drop graph edges below this confidence (relation quality filter)",
    )
    reconstruct.add_argument(
        "--evolve",
        default=None,
        metavar="DIR",
        help="Evolve an existing reconstruct dir (incremental graph generation)",
    )
    reconstruct.add_argument(
        "--add",
        nargs="*",
        default=None,
        help="Extra KO/card paths to add when using --evolve",
    )
    reconstruct.add_argument(
        "--remove",
        nargs="*",
        default=None,
        help="KO ids to drop when using --evolve",
    )

    retrieve = sub.add_parser(
        "retrieve",
        help="P3: KO + Graph + Embedding → KnowledgeObject retrieval",
    )
    retrieve_sub = retrieve.add_subparsers(dest="retrieve_command")
    r_index = retrieve_sub.add_parser(
        "index",
        help="Build KO embedding index (whole objects, no chunking)",
    )
    r_index.add_argument("sources", nargs="*", help="Optional KO/card paths")
    r_index.add_argument("--from-index", action="store_true")
    r_index.add_argument("--from-packages", action="store_true")
    r_index.add_argument("--subdir", default=None)
    r_index.add_argument("--tag", default=None)
    r_index.add_argument(
        "--taxonomy-prefix",
        default=None,
        help="Filter index by taxonomy path prefix",
    )
    r_index.add_argument("--limit", type=int, default=None)
    r_index.add_argument(
        "--no-write-back-packages",
        action="store_true",
        help="Skip writing EmbeddingRef back to data/packages/*/knowledge_object.json",
    )
    r_index.add_argument(
        "--write-back-dry-run",
        action="store_true",
        help="Report package write-back targets without modifying files",
    )
    r_query = retrieve_sub.add_parser(
        "query",
        help="Query KnowledgeObjects (optional ConceptGraph boost)",
    )
    r_query.add_argument("query", help="Natural language query")
    r_query.add_argument("--top", type=int, default=5, help="Top-K KOs")
    r_query.add_argument(
        "--graph",
        default=None,
        help="ConceptGraph JSON or reconstruct dir for graph-aware mode",
    )
    r_query.add_argument(
        "--graph-weight",
        type=float,
        default=0.35,
        help="Blend weight for graph boost (default 0.35)",
    )

    compose = sub.add_parser(
        "compose",
        help="Application: retrieve KOs → LLM → paper/lecture draft",
    )
    compose.add_argument(
        "kind",
        choices=["paper", "lecture"],
        help="Draft type",
    )
    compose.add_argument("query", help="Topic / question to retrieve and compose")
    compose.add_argument("--top", type=int, default=5, help="Top-K KnowledgeObjects")
    compose.add_argument(
        "--graph",
        default=None,
        help="Optional reconstruct dir / concept_graph.json for graph-aware retrieve",
    )
    compose.add_argument(
        "--graph-weight",
        type=float,
        default=0.35,
        help="Graph boost weight when --graph is set",
    )

    voice = sub.add_parser("voice", help="Record/import voice sample and clone-speak")
    voice_sub = voice.add_subparsers(dest="voice_command")
    v_rec = voice_sub.add_parser("record", help="Record microphone sample as voice profile")
    v_rec.add_argument("--name", required=True, help="Profile name, e.g. me")
    v_rec.add_argument("--seconds", type=float, default=12.0)
    v_rec.add_argument(
        "--transcript",
        default=None,
        help="Exact words you will say (default: built-in 10s Chinese script)",
    )
    v_rec.add_argument(
        "--auto-transcribe",
        action="store_true",
        help="Use Whisper to caption recording instead of fixed script",
    )
    v_imp = voice_sub.add_parser("import", help="Import an existing WAV/MP3 as voice sample")
    v_imp.add_argument("file", help="Path to audio sample (5–15s recommended)")
    v_imp.add_argument("--name", required=True)
    v_imp.add_argument("--transcript", default=None)
    voice_sub.add_parser("list", help="List voice profiles")
    v_use = voice_sub.add_parser("use", help="Set default voice profile")
    v_use.add_argument("name")
    v_spk = voice_sub.add_parser("speak", help="Speak text with cloned voice")
    v_spk.add_argument("text")
    v_spk.add_argument("--voice", default=None)
    v_spk.add_argument("-o", "--output", default=None, help="Output wav path")

    sub.add_parser("status", help="Show environment and phase status")

    models = sub.add_parser("models", help="Local model weights (offline-first)")
    models_sub = models.add_subparsers(dest="models_command")
    models_status = models_sub.add_parser("status", help="Show local model readiness")
    models_verify = models_sub.add_parser("verify", help="Verify all local assets are locked")
    models_pull = models_sub.add_parser("pull", help="Download models into models/")
    models_pull.add_argument(
        "--only",
        default="whisper,embed,ollama,tts,vocos,ocr,pix2tex",
        help="whisper,embed,ollama,tts,vocos,ocr,pix2tex or 'all'",
    )
    models_pull.add_argument("--force", action="store_true")

    ui = sub.add_parser("ui", help="Launch local Windows workshop UI (FastAPI)")
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument(
        "--browser",
        action="store_true",
        help="Open system browser instead of pywebview desktop window (default: desktop)",
    )

    export = sub.add_parser(
        "export",
        help="Controlled export (encrypted .kfexport for proprietary / local_only)",
    )
    export_sub = export.add_subparsers(dest="export_command")
    exp_enc = export_sub.add_parser(
        "encrypted",
        help="Write Fernet envelope (.kfexport); needs KF_EXPORT_KEY or KF_EXPORT_PASSPHRASE",
    )
    exp_enc.add_argument("path", help="Knowledge card / file under data/")
    exp_enc.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output .kfexport path (default: data/exports/<stem>.kfexport)",
    )
    exp_dec = export_sub.add_parser(
        "decrypt",
        help="Decrypt a .kfexport envelope (local verify)",
    )
    exp_dec.add_argument("path", help="Path to .kfexport")
    exp_dec.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write plaintext here (default: stdout text / sibling file)",
    )

    return parser


def cmd_export(args: argparse.Namespace) -> int:
    from pathlib import Path

    from app.knowledge.encrypted_export import (
        EncryptedExportError,
        decrypt_envelope,
        generate_export_key,
    )
    from app.knowledge.path_access import build_encrypted_export

    if args.export_command == "encrypted":
        path = Path(args.path).expanduser().resolve()
        if not path.is_file():
            print(f"not a file: {path}", file=sys.stderr)
            return 1
        dest = Path(args.output).expanduser() if args.output else None
        try:
            access, out, _blob = build_encrypted_export(path, dest=dest)
        except PermissionError as exc:
            print(f"export blocked: {exc}", file=sys.stderr)
            return 1
        except EncryptedExportError as exc:
            print(f"encrypted export failed: {exc}", file=sys.stderr)
            print(
                f"hint: set KF_EXPORT_KEY={generate_export_key()!r} once, or KF_EXPORT_PASSPHRASE",
                file=sys.stderr,
            )
            return 1
        print(f"[ok] encrypted export: {out}")
        print(f"  classification: {access.classification}")
        print(f"  source_project: {access.source_project or '-'}")
        return 0

    if args.export_command == "decrypt":
        path = Path(args.path).expanduser().resolve()
        if not path.is_file():
            print(f"not a file: {path}", file=sys.stderr)
            return 1
        try:
            env, plain = decrypt_envelope(path)
        except EncryptedExportError as exc:
            print(f"decrypt failed: {exc}", file=sys.stderr)
            return 1
        print(f"[ok] schema={env.schema_id} original={env.original_name}")
        print(f"  classification: {env.classification}")
        print(f"  watermark: {env.watermark}")
        if args.output:
            out = Path(args.output).expanduser()
            out.write_bytes(plain)
            print(f"  wrote: {out}")
        else:
            try:
                text = plain.decode("utf-8")
                print("--- plaintext ---")
                print(text[:4000])
            except UnicodeDecodeError:
                print(f"  binary {len(plain)} bytes (pass -o to write)")
        return 0

    print("Usage: python main.py export encrypted|decrypt ...", file=sys.stderr)
    return 2


def cmd_status() -> int:
    from app.knowledge.access import (
        CLOUD_LLM_PROVIDERS,
        LOCAL_LLM_PROVIDERS,
        is_local_llm_provider,
        max_retrieve_classification,
    )

    print("KnowledgeForge Phase 1+")
    print(f"  root:        {config.ROOT}")
    print(f"  python:      {sys.version.split()[0]}")
    print(f"  local_first: {'on' if config.LOCAL_FIRST else 'off'}")
    track = "local" if is_local_llm_provider(config.LLM_PROVIDER) else "cloud"
    print(f"  llm_track:   {track} (choose local or cloud via LLM_PROVIDER)")
    print(f"  provider:    {config.LLM_PROVIDER}")
    print(f"  providers:   local={','.join(sorted(LOCAL_LLM_PROVIDERS))} | cloud={','.join(sorted(CLOUD_LLM_PROVIDERS))}")
    print(f"  ollama:      {config.OLLAMA_MODEL} @ {config.OLLAMA_HOST}")
    print(f"  access_max:  {max_retrieve_classification()}")
    print(f"  whisper:     {config.WHISPER_MODEL}")
    print(f"  embed:       {config.EMBED_MODEL_PATH}")
    print(f"  vocos:       {config.VOCOS_MODEL_PATH}")
    print(f"  hf_home:     {config.HF_HOME}")
    print(f"  hf_offline:  {config.HF_HUB_OFFLINE or '(unset)'}")
    print(f"  tts_engine:  {config.TTS_ENGINE}")
    print(f"  voice:       {default_voice_name() or '(none — voice record)'}")
    print(f"  voices_dir:  {config.VOICES_DIR}")
    print(f"  index:       {'on' if config.INDEX_ENABLED else 'off'}")
    print(f"  knowledge:   {config.KNOWLEDGE_DIR}")
    print()
    print("Local models:")
    for name, path, state in status_rows():
        mark = "ok" if state == "ready" else state
        print(f"  {name:12} {mark:14} {path}")
    print()
    print("Ready: youtube | bilibili | twitter | pdf | file | image | search | derive | express | animate | compile | voice | models")
    print("Loop: 获取信号源 → 沉淀知识 → 展示知识  (Harness: compile)")
    return 0


def cmd_voice(args: argparse.Namespace) -> int:
    if args.voice_command == "record":
        try:
            profile = record_profile(
                args.name,
                seconds=args.seconds,
                transcript=args.transcript,
                auto_transcribe=args.auto_transcribe,
            )
        except VoiceRecordError as exc:
            print(f"Record failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Record failed: {exc}", file=sys.stderr)
            return 1
        set_default_voice(profile.name)
        print(f"[ok] voice:      {profile.name}")
        print(f"[ok] sample:     {profile.sample_path}")
        print(f"[ok] transcript: {profile.transcript}")
        print(f"[ok] default:    {profile.name}")
        return 0

    if args.voice_command == "import":
        try:
            profile = import_profile(
                args.name,
                args.file,
                transcript=args.transcript,
            )
        except (VoiceRecordError, FileNotFoundError) as exc:
            print(f"Import failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Import failed: {exc}", file=sys.stderr)
            return 1
        set_default_voice(profile.name)
        print(f"[ok] voice:      {profile.name}")
        print(f"[ok] sample:     {profile.sample_path}")
        print(f"[ok] transcript: {profile.transcript}")
        return 0

    if args.voice_command == "list":
        profiles = list_profiles()
        default = default_voice_name()
        if not profiles:
            print("No voice profiles. Record one:")
            print('  python main.py voice record --name me --seconds 12')
            return 0
        for profile in profiles:
            mark = "*" if profile.name == default else " "
            print(
                f"{mark} {profile.name:16} {profile.duration_sec or '?'}s  "
                f"{profile.source}  {profile.transcript[:40]}"
            )
        return 0

    if args.voice_command == "use":
        try:
            set_default_voice(args.name)
        except FileNotFoundError as exc:
            print(f"Use failed: {exc}", file=sys.stderr)
            return 1
        print(f"[ok] default voice: {args.name}")
        return 0

    if args.voice_command == "speak":
        out = Path(args.output) if args.output else (
            config.EXPRESSION_DIR / "_voice_test" / "speak.wav"
        )
        print(f"[voice] speak → {out}")
        try:
            path = speak_with_voice(args.text, out, voice_name=args.voice)
        except CloneTtsError as exc:
            print(f"Speak failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Speak failed: {exc}", file=sys.stderr)
            return 1
        print(f"[ok] audio: {path}")
        return 0

    print(
        "Usage: python main.py voice record|import|list|use|speak ...",
        file=sys.stderr,
    )
    return 2


def cmd_models_status() -> int:
    print("Local model readiness (offline-first):")
    missing = 0
    for name, path, state in status_rows():
        print(f"  {name:12} {state:14} {path}")
        if state == "missing":
            missing += 1
    if missing:
        print(f"\n{missing} required local asset(s) missing. Run: python main.py models pull")
        return 1
    return 0


def cmd_models_verify() -> int:
    issues = verify_local_assets()
    if issues:
        print("Local asset verification failed:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        print("\nRun: python main.py models pull", file=sys.stderr)
        return 1
    lock = write_lock_manifest()
    print("All local intelligence assets are ready.")
    print(f"[ok] lock: {lock}")
    return 0


def cmd_models_pull(only: str, *, force: bool) -> int:
    kinds = [k.strip() for k in only.split(",") if k.strip()]
    if len(kinds) == 1 and kinds[0].lower() == "all":
        kinds = ["whisper", "embed", "ollama", "tts", "vocos", "ocr", "pix2tex"]
    for kind in kinds:
        print(f"[pull] {kind} ...", flush=True)
        try:
            result = pull_local_model(kind, force=force)  # type: ignore[arg-type]
            print(f"[ok] {kind}: {result}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] {kind}: {exc}", file=sys.stderr)
            return 1
    lock = write_lock_manifest()
    print(f"\n[ok] lock manifest: {lock}")
    print("Set HF_HUB_OFFLINE=1 in .env after pulls complete.")
    return 0


def cmd_bilibili(url: str, *, no_index: bool) -> int:
    print(f"[bilibili] {url}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = run_bilibili(url, index=False if no_index else None)
    except BilibiliIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    _print_result(result)
    return 0


def cmd_twitter_url(url: str, *, no_index: bool) -> int:
    print(f"[twitter] {url}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = run_twitter(url, index=False if no_index else None)
    except TwitterIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    _print_result(result)
    return 0


def cmd_twitter_timeline(username: str, limit: int, *, no_index: bool) -> int:
    print(f"[twitter] timeline @{username.lstrip('@')}")
    print(f"[twitter] limit={limit}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = run_twitter_timeline(
            username,
            limit=limit,
            index=False if no_index else None,
        )
    except TwitterIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    _print_result(result)
    return 0


def cmd_youtube(url: str, *, no_index: bool) -> int:
    print(f"[youtube] {url}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = run_youtube(url, index=False if no_index else None)
    except YouTubeIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    _print_result(result)
    return 0


def cmd_image(path: str, dest_subdir: str | None, *, no_index: bool) -> int:
    print(f"[image] {path}")
    print(f"[ocr] lang={config.PADDLE_OCR_LANG} cache={config.PADDLEX_CACHE_HOME}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    dest = (config.KNOWLEDGE_DIR / dest_subdir) if dest_subdir else None
    if dest is not None:
        dest.mkdir(parents=True, exist_ok=True)
    try:
        result = run_image(path, dest_dir=dest, index=False if no_index else None)
    except ImageIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1
    _print_result(result)
    return 0


def cmd_audio(path: str, dest_subdir: str | None, *, no_index: bool) -> int:
    print(f"[audio] {path}")
    print(f"[asr] whisper={config.WHISPER_MODEL}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    dest = (config.KNOWLEDGE_DIR / dest_subdir) if dest_subdir else None
    if dest is not None:
        dest.mkdir(parents=True, exist_ok=True)
    try:
        result = run_audio(path, dest_dir=dest, index=False if no_index else None)
    except AudioIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1
    _print_result(result)
    return 0


def cmd_file(path: str, dest_subdir: str | None, *, no_index: bool) -> int:
    print(f"[file] {path}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    dest = (config.KNOWLEDGE_DIR / dest_subdir) if dest_subdir else None
    if dest is not None:
        dest.mkdir(parents=True, exist_ok=True)
    try:
        result = run_file(
            path,
            dest_dir=dest,
            extra_tags=["file"],
            index=False if no_index else None,
        )
    except FileIngestError as exc:
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1
    _print_result(result)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    print(f"[search] keyword={args.keyword!r}")
    for root in args.roots:
        print(f"[search] root={root}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        batch = run_search(
            args.roots,
            keyword=args.keyword,
            dest_subdir=args.dest_subdir,
            synthesize=not args.no_synthesis,
            synthesis_title=args.synthesis_title,
            limit=args.limit,
            dry_run=args.dry_run,
            index=False if args.no_index else None,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"Search failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    print(f"[search] matched={len(batch.hits)}")
    for hit in batch.hits:
        print(f"  - {hit.path}")

    if args.dry_run:
        print("[dry-run] no LLM calls; external sources untouched")
        return 0

    for result in batch.results:
        _print_result(result)
    for path, reason in batch.skipped:
        print(f"[skip] {path}: {reason}", file=sys.stderr)
    if batch.synthesis is not None:
        print("[synthesis]")
        _print_result(batch.synthesis)

    print(
        f"[done] compressed={len(batch.results)} skipped={len(batch.skipped)} "
        f"synthesis={'yes' if batch.synthesis else 'no'}"
    )
    return 0


def cmd_ecosystem(args: argparse.Namespace) -> int:
    if args.ecosystem_command != "ingest":
        print(
            "Usage: python main.py ecosystem ingest setv|factorlib|asharelib <ROOT> ...",
            file=sys.stderr,
        )
        return 2
    print(f"[ecosystem] project={args.project}")
    for root in args.roots:
        print(f"[ecosystem] root={root}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        batch = run_ecosystem_ingest(
            args.project,
            args.roots,
            limit=args.limit,
            dry_run=args.dry_run,
            index=False if args.no_index else None,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"Ecosystem ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Ecosystem ingest failed: {exc}", file=sys.stderr)
        return 1

    print(f"[ecosystem] matched={len(batch.hits)}")
    for hit in batch.hits:
        print(f"  - {hit.path}")

    if args.dry_run:
        print("[dry-run] no LLM calls; external sources untouched")
        return 0

    for result in batch.results:
        _print_result(result)
        print(f"  taxonomy: {result.unit.taxonomy.canonical}")
    for path, reason in batch.skipped:
        print(f"[skip] {path}: {reason}", file=sys.stderr)
    print(
        f"[done] compressed={len(batch.results)} skipped={len(batch.skipped)}"
    )
    return 0


def cmd_setv(args: argparse.Namespace) -> int:
    asset_class = args.setv_command
    if asset_class == "ingest":
        print("[setv] ingest via OPEN KF INGEST (manifest → sidecars · no LLM)")
        print(f"[setv] setv_root={args.setv_root}")
        if args.manifest:
            print(f"[setv] manifest={args.manifest}")
        if args.ingest_class:
            print(f"[setv] class_filter={args.ingest_class}")
        try:
            batch = run_manifest_ingest(
                setv_root=args.setv_root,
                manifest=args.manifest,
                asset_class=args.ingest_class,
                limit=args.limit,
                dry_run=args.dry_run,
                index=False if args.no_index else None,
            )
        except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
            print(f"SETV ingest failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"SETV ingest failed: {exc}", file=sys.stderr)
            return 1
        print(f"[setv] matched={len(batch.hits)}")
        for hit in batch.hits:
            print(f"  - {hit}")
        if args.dry_run:
            print("[dry-run] no writes; SETV sources untouched")
            return 0
        for result in batch.results:
            _print_result(result)
            ref = result.unit.setv_artifact
            if ref:
                print(
                    f"  cite: {ref.asset_class}/{ref.artifact_id} → {ref.evidence_pointer}"
                )
            print(f"  memory_kind: {result.unit.memory_kind}")
        for path, reason in batch.skipped:
            print(f"[skip] {path}: {reason}", file=sys.stderr)
        print(
            f"[done] ingested={len(batch.results)} skipped={len(batch.skipped)}"
        )
        return 0 if not batch.skipped or batch.results else 1

    if asset_class not in {
        "snapshot",
        "evolution",
        "family",
        "measurement",
        "experiment",
        "uncertainty",
    }:
        print(
            "Usage: python main.py setv snapshot|evolution|family|measurement|"
            "experiment|uncertainty|ingest ...",
            file=sys.stderr,
        )
        return 2
    done_label = {
        "snapshot": "snapshots",
        "evolution": "evolutions",
        "family": "families",
        "measurement": "measurements",
        "experiment": "experiments",
        "uncertainty": "uncertainties",
    }[asset_class]
    print(
        f"[setv] {asset_class} adapter (cite-only · no LLM · memory_kind=state)"
    )
    for p in args.paths:
        print(f"[setv] path={p}")
    if args.setv_root:
        print(f"[setv] setv_root={args.setv_root}")
    try:
        batch = run_artifact_ingest(
            args.paths,
            asset_class=asset_class,
            setv_root=args.setv_root,
            limit=args.limit,
            dry_run=args.dry_run,
            index=False if args.no_index else None,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"SETV {asset_class} ingest failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"SETV {asset_class} ingest failed: {exc}", file=sys.stderr)
        return 1

    print(f"[setv] matched={len(batch.hits)}")
    for hit in batch.hits:
        print(f"  - {hit}")

    if args.dry_run:
        print("[dry-run] no writes; SETV sources untouched")
        return 0

    for result in batch.results:
        _print_result(result)
        ref = result.unit.setv_artifact
        if ref:
            print(
                f"  cite: {ref.asset_class}/{ref.artifact_id} → {ref.evidence_pointer}"
            )
        print(f"  memory_kind: {result.unit.memory_kind}")
        print(f"  taxonomy: {result.unit.taxonomy.canonical}")
    for path, reason in batch.skipped:
        print(f"[skip] {path}: {reason}", file=sys.stderr)
    print(f"[done] {done_label}={len(batch.results)} skipped={len(batch.skipped)}")
    return 0 if not batch.skipped or batch.results else 1


def cmd_express(
    card: str,
    *,
    animation: bool,
    narration: bool,
    voice_name: str | None,
) -> int:
    print(f"[express] card={card}")
    print(f"[express] animation={'on' if animation else 'off'} narration={'on' if narration else 'off'}")
    if voice_name:
        print(f"[express] voice={voice_name}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = express_from_card(
            card,
            animation=animation,
            narration=narration,
            voice_name=voice_name,
        )
    except FileNotFoundError as exc:
        print(f"Express failed: {exc}", file=sys.stderr)
        return 1
    except TtsError as exc:
        print(f"TTS failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Express failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] parent:   {result.parent_path}")
    print(f"[ok] output:   {result.output_dir}")
    print(f"[ok] schema:   {result.schema_path}")
    if result.gif_path:
        print(f"[ok] animation: {result.gif_path}")
    if result.audio_path:
        print(f"[ok] narration: {result.audio_path}")
    elif narration:
        print("[warn] narration script saved; audio skipped (install pyttsx3)", file=sys.stderr)
    print(f"[ok] manifest: {result.manifest_path}")
    return 0


def cmd_reconstruct(args: argparse.Namespace) -> int:
    view = None if args.view == "none" else args.view
    print("[reconstruct] Multiple KO → Relation → Graph → View")
    print(
        f"[reconstruct] from_index={args.from_index} from_packages={args.from_packages} "
        f"paths={len(args.sources)} view={view} seed={args.seed!r} "
        f"min_confidence={args.min_confidence} evolve={args.evolve}"
    )
    try:
        result = run_reconstruct(
            paths=list(args.sources) or None,
            from_index=args.from_index,
            from_packages=args.from_packages,
            subdir=args.subdir,
            tag=args.tag,
            concept=args.concept,
            taxonomy_prefix=args.taxonomy_prefix,
            limit=args.limit,
            view=view,
            seed=args.seed,
            min_confidence=args.min_confidence,
            evolve_dir=args.evolve,
            add_paths=args.add,
            remove_ko_ids=args.remove,
        )
    except ReconstructLoadError as exc:
        print(f"Reconstruct failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Reconstruct failed: {exc}", file=sys.stderr)
        return 1

    print(f"[ok] output:  {result.output_dir}")
    print(f"[ok] graph:   {result.graph_path}")
    print(f"[ok] graph_id:{result.graph.id} gen={result.graph.generation}")
    print(f"[ok] kos:     {len(result.kos)}")
    print(f"[ok] nodes:   {result.graph.relations.stats.get('nodes')}")
    print(f"[ok] edges:   {result.graph.relations.stats.get('edges')}")
    buckets = result.graph.relations.stats.get("confidence_buckets")
    if buckets:
        print(f"[ok] conf:    {buckets}")
    if result.evolved and result.delta:
        print(
            f"[ok] evolved: +{len(result.delta.get('added_ko_ids') or [])} "
            f"-{len(result.delta.get('removed_ko_ids') or [])}"
        )
    if result.view_path and result.view:
        print(f"[ok] view:    {result.view_path}")
        print(f"[ok] type:    {result.view.view_type}")
        print(f"[ok] sections:{len(result.view.sections)}")
        fp = result.view.stability.get("fingerprint")
        if fp:
            print(f"[ok] stable:  {fp}")
    print(f"[ok] report:  {result.report_path}")
    return 0


def cmd_compose(args: argparse.Namespace) -> int:
    print(f"[compose] kind={args.kind} query={args.query!r} top={args.top}")
    if args.graph:
        print(f"[compose] graph={args.graph}")
    try:
        result = compose_from_query(
            args.query,
            kind=args.kind,
            top_k=args.top,
            graph_path=args.graph,
            graph_weight=args.graph_weight,
        )
    except (EmbedderError, FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Compose failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Compose failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] draft:   {result.draft_path}")
    print(f"[ok] output:  {result.output_dir}")
    print(f"[ok] sources: {len(result.meta.sources)}")
    print(f"[ok] mode:    {result.meta.retrieve_mode}")
    if result.retrieve_path:
        print(f"[ok] retrieve:{result.retrieve_path}")
    return 0


def cmd_retrieve(args: argparse.Namespace) -> int:
    if args.retrieve_command == "index":
        print("[retrieve] index KnowledgeObjects (no chunking)")
        try:
            built = run_index(
                paths=list(args.sources) or None,
                from_index=args.from_index,
                from_packages=args.from_packages,
                subdir=args.subdir,
                tag=args.tag,
                taxonomy_prefix=args.taxonomy_prefix,
                limit=args.limit,
                write_back_packages=not args.no_write_back_packages,
                write_back_dry_run=args.write_back_dry_run,
            )
        except (ReconstructLoadError, EmbedderError, FileNotFoundError) as exc:
            print(f"Retrieve index failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Retrieve index failed: {exc}", file=sys.stderr)
            return 1
        print(f"[ok] index_dir: {built.index_dir}")
        print(f"[ok] count:     {built.count}")
        print(f"[ok] dim:       {built.manifest.dim}")
        print(f"[ok] model:     {built.manifest.model}")
        if built.writeback is not None:
            wb = built.writeback
            print(
                f"[ok] writeback: updated={wb.updated} "
                f"missing={wb.missing} skipped={wb.skipped}"
            )
            if wb.errors:
                print(f"[warn] writeback errors: {len(wb.errors)}", file=sys.stderr)
        return 0

    if args.retrieve_command == "query":
        print(
            f"[retrieve] query={args.query!r} top={args.top} graph={args.graph}"
        )
        try:
            run = run_query(
                args.query,
                top_k=args.top,
                graph_path=args.graph,
                graph_weight=args.graph_weight,
            )
        except (EmbedderError, FileNotFoundError, ValueError) as exc:
            print(f"Retrieve failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Retrieve failed: {exc}", file=sys.stderr)
            return 1

        result = run.result
        print(f"[ok] mode:  {result.mode}")
        print(f"[ok] hits:  {len(result.hits)}")
        for i, hit in enumerate(result.hits, start=1):
            print(
                f"  {i}. {hit.score:.4f}  {hit.title}  "
                f"[sem={hit.semantic_score:.3f} graph={hit.graph_score:.3f}]"
            )
            for w in hit.why[:2]:
                print(f"      - {w}")
        if run.result_path:
            print(f"[ok] saved: {run.result_path}")
        return 0

    print(
        "Usage:\n"
        "  python main.py retrieve index --from-index\n"
        "  python main.py retrieve query \"美债信用风险\" [--graph DIR] [--top 5]",
        file=sys.stderr,
    )
    return 2


def cmd_compile(args: argparse.Namespace) -> int:
    if args.rerun_step:
        if not args.package:
            print("Compile --rerun-step requires --package DIR", file=sys.stderr)
            return 2
        print(f"[compile] rerun_step={args.rerun_step} package={args.package}")
        try:
            result = rerun_step(
                args.package,
                args.rerun_step,
                fast=args.fast,
                voice_name=args.voice,
            )
        except HarnessError as exc:
            print(f"Compile failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Compile failed: {exc}", file=sys.stderr)
            return 1
    else:
        if not args.source:
            print("Compile requires SOURCE or --rerun-step/--package", file=sys.stderr)
            return 2
        print(f"[compile] source={args.source}")
        print(
            f"[compile] from_card={args.from_card} animate={args.animate} "
            f"narrate={args.narrate} fast={args.fast}"
        )
        if args.voice:
            print(f"[compile] voice={args.voice}")
        try:
            result = compile_knowledge(
                args.source,
                from_card=args.from_card,
                animate=args.animate,
                narrate=args.narrate,
                fast=args.fast,
                voice_name=args.voice,
                index=False if args.no_index else None,
            )
        except HarnessError as exc:
            print(f"Compile failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Compile failed: {exc}", file=sys.stderr)
            return 1

    print(f"[ok] package:  {result.package_dir}")
    print(f"[ok] status:   {result.run.status}")
    print(f"[ok] manifest: {result.manifest_path}")
    if result.knowledge_object_path:
        print(f"[ok] object:   {result.knowledge_object_path}")
    if result.knowledge_md:
        print(f"[ok] knowledge:{result.knowledge_md}")
    if result.animation_gif:
        print(f"[ok] animation:{result.animation_gif}")
    if result.narration_wav:
        print(f"[ok] narration:{result.narration_wav}")
    for step in result.run.steps[-8:]:
        print(f"  - {step.name:16} {step.status}")
    return 0


def cmd_animate(card: str, *, fast: bool) -> int:
    print(f"[animate] card={card}")
    print(f"[animate] fast={'on' if fast else 'off'}")
    if not fast:
        print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = animate_from_card(card, fast=fast)
    except FileNotFoundError as exc:
        print(f"Animate failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Animate failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] parent:   {result.parent_path}")
    print(f"[ok] output:   {result.output_dir}")
    print(f"[ok] source:   {result.source}")
    print(f"[ok] type:     {result.schema.animation.type}")
    print(f"[ok] schema:   {result.schema_path}")
    print(f"[ok] gif:      {result.gif_path}")
    print(f"[ok] manifest: {result.output_dir / 'ANIMATE.md'}")
    return 0


def cmd_derive(card: str, mode: str) -> int:
    print(f"[derive] card={card}")
    print(f"[derive] mode={mode}")
    print(f"[llm] provider={config.LLM_PROVIDER}")
    try:
        result = derive_from_card(card, mode=mode)  # type: ignore[arg-type]
    except FileNotFoundError as exc:
        print(f"Derive failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Derive failed: {exc}", file=sys.stderr)
        return 1
    print(f"[ok] mode:   {result.mode}")
    print(f"[ok] parent: {result.parent_path}")
    print(f"[ok] output: {result.output_path}")
    return 0


def cmd_index_rebuild(subdir: str | None) -> int:
    if not config.INDEX_ENABLED:
        print("INDEX_ENABLED=false; nothing to rebuild", file=sys.stderr)
        return 2
    written = rebuild_index(subdir=subdir)
    print(f"[index] rebuilt={len(written)}")
    for key, path in written.items():
        print(f"[index] {key}: {path}")
    return 0


def _print_result(result) -> None:
    print(f"[ok] title:     {result.unit.title}")
    print(f"[ok] concepts:  {len(result.unit.concepts)}")
    print(f"[ok] source:    {result.source.path or result.source.url or ''}")
    print(f"[ok] raw:       {result.raw_path}")
    print(f"[ok] knowledge: {result.markdown_path}")
    if result.truncated:
        print("[warn] source truncated to fit model context")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command or args.command == "status":
        return cmd_status()
    if args.command == "youtube":
        return cmd_youtube(args.url, no_index=args.no_index)
    if args.command == "bilibili":
        return cmd_bilibili(args.url, no_index=args.no_index)
    if args.command == "twitter":
        if args.timeline:
            return cmd_twitter_timeline(
                args.target,
                args.limit,
                no_index=args.no_index,
            )
        return cmd_twitter_url(args.target, no_index=args.no_index)
    if args.command in {"file", "pdf"}:
        return cmd_file(args.file, args.dest_subdir, no_index=args.no_index)
    if args.command == "image":
        return cmd_image(args.file, args.dest_subdir, no_index=args.no_index)
    if args.command == "audio":
        return cmd_audio(args.file, args.dest_subdir, no_index=args.no_index)
    if args.command == "search":
        return cmd_search(args)
    if args.command == "ecosystem":
        return cmd_ecosystem(args)
    if args.command == "setv":
        return cmd_setv(args)
    if args.command == "index":
        if args.index_command == "rebuild":
            return cmd_index_rebuild(args.subdir)
        print("Usage: python main.py index rebuild [--subdir NAME]", file=sys.stderr)
        return 2
    if args.command == "derive":
        return cmd_derive(args.card, args.mode)
    if args.command == "express":
        return cmd_express(
            args.card,
            animation=not args.no_animation,
            narration=not args.no_narration,
            voice_name=args.voice,
        )
    if args.command == "animate":
        return cmd_animate(args.card, fast=args.fast)
    if args.command == "compile":
        return cmd_compile(args)
    if args.command == "reconstruct":
        return cmd_reconstruct(args)
    if args.command == "retrieve":
        return cmd_retrieve(args)
    if args.command == "compose":
        return cmd_compose(args)
    if args.command == "voice":
        return cmd_voice(args)
    if args.command == "models":
        if args.models_command == "pull":
            return cmd_models_pull(args.only, force=args.force)
        if args.models_command == "verify":
            return cmd_models_verify()
        return cmd_models_status()
    if args.command == "ui":
        return cmd_ui(args)
    if args.command == "export":
        return cmd_export(args)
    parser.print_help()
    return 2


def cmd_ui(args: argparse.Namespace) -> int:
    from app.ui.server import serve

    serve(host=args.host, port=args.port, desktop=not args.browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
