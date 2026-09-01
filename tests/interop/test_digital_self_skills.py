"""KF consumes Digital Self Skills — one suite per exported skill.

Neighbor Digital Self must be on disk. No live Playwright / MT5 / publish.
S02 live TTS is opt-in via KF_RUN_SLOW=1 (uses KF venv F5 + DS Identity).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.interop.digital_self import digital_self_root, invoke, invoke_path, list_skills
from app.main import main

ROOT = Path(__file__).resolve().parents[2]
EXPR = ROOT / "data" / "expression"


# --- catalog surface ---


def test_digital_self_on_disk():
    root = digital_self_root()
    assert (root / "skills" / "CATALOG.yaml").is_file()
    assert invoke_path().is_file()


def test_list_catalog_from_kf():
    payload = list_skills()
    assert payload.get("ok") is True
    ids = {s["id"] for s in payload["skills"]}
    assert {
        "S00_AttentionGate",
        "S02_ReadAloud",
        "S06_Browser",
        "S15_ResearchOp",
        "S16_Compose",
    } <= ids


def test_kf_cli_ds_list():
    assert main(["ds", "list"]) == 0


# --- S00 AttentionGate ---


def test_s00_triage_useful():
    payload = invoke("S00", "--text", "NAS100 H1 backtest MAR improved")
    assert payload["ok"] is True
    assert payload["skill"] == "S00_AttentionGate"
    assert payload["class"] == "useful"
    assert payload["pass_kf"] is True
    assert payload["interrupt"] is False
    assert payload["compile_in_ds"] is False


def test_s00_important_interrupt():
    payload = invoke("S00", "--text", "发现重大风险，可能改变已有判断")
    assert payload["ok"] is True
    assert payload["class"] == "important"
    assert payload["interrupt"] is True


def test_s00_garbage_empty_or_low_relevance():
    empty = invoke("S00", "--text", "")
    assert empty["ok"] is True
    assert empty["class"] == "garbage"
    assert empty["pass_kf"] is False
    low = invoke("S00", "--text", "noise", "--relevance", "0.1")
    assert low["ok"] is True
    assert low["class"] == "garbage"


def test_s00_alias_attention_gate():
    payload = invoke("AttentionGate", "--text", "useful observation for archive")
    assert payload["ok"] is True
    assert payload["skill"] == "S00_AttentionGate"


# --- S06 Browser (YouTube / web = plan only) ---


def test_s06_youtube_plan_no_live():
    plan = invoke(
        "S06",
        "--intent",
        "打开 YouTube 搜 NVIDIA earnings",
        "--url",
        "https://www.youtube.com",
    )
    assert plan["ok"] is True
    assert plan["skill"] == "S06_Browser"
    assert plan["live"] is False
    assert isinstance(plan.get("actions"), list)
    assert plan.get("actions")  # non-empty plan


def test_s06_browser_generic_intent():
    plan = invoke("Browser", "--intent", "open docs.python.org and note title")
    assert plan["ok"] is True
    assert plan["live"] is False


def test_s06_live_denied():
    denied = invoke("S06", "--intent", "open YouTube", "--live")
    assert denied["ok"] is False
    assert denied["error"] == "LIVE_BROWSER_NOT_AUTHORIZED"


def test_s06_missing_intent_fails():
    bad = invoke("S06")
    assert bad["ok"] is False
    assert bad["error"] == "DS_INVOKE_USAGE"
    assert "intent" in bad.get("message", "").lower()


# --- S15 ResearchOp ---


def test_s15_setv_plan_and_l4_denied():
    plan = invoke("S14", "--scene", "setv", "--task", "cite artifact_id=demo")
    assert plan["ok"] is True
    assert plan["skill"] == "S15_ResearchOp"
    assert plan.get("live") is False
    denied = invoke(
        "S15",
        "--scene",
        "mt5_backtest",
        "--task",
        "NAS100",
        "--action",
        "place_order",
    )
    assert denied["ok"] is False
    assert denied["error"] == "L4_NO_AUTHORIZABLE_PATH"


@pytest.mark.parametrize(
    "scene,task",
    [
        ("setv", "list AAPL H4 snapshots"),
        ("mt5_backtest", "summarize NAS100 H1 backtest candidate"),
        ("ashare", "cite ashare methodology note"),
    ],
)
def test_s15_scenes_plan_only(scene: str, task: str):
    plan = invoke("S15", "--scene", scene, "--task", task)
    assert plan["ok"] is True
    assert plan["skill"] == "S15_ResearchOp"
    assert plan.get("live") is False
    assert plan.get("danger_class") == "L1"


def test_s15_live_compute_denied():
    denied = invoke(
        "S15",
        "--scene",
        "mt5_backtest",
        "--task",
        "run backtest",
        "--live",
    )
    assert denied["ok"] is False
    assert denied["error"] == "LIVE_COMPUTE_NOT_AUTHORIZED"


@pytest.mark.parametrize(
    "action",
    [
        "place_order",
        "cancel_order",
        "modify_order",
        "withdraw",
        "transfer_money",
        "transfer",
        "deposit",
        "live_trade",
    ],
)
def test_s15_l4_verbs_denied(action: str):
    denied = invoke(
        "S15",
        "--scene",
        "mt5_backtest",
        "--task",
        "x",
        "--action",
        action,
    )
    assert denied["ok"] is False
    assert denied["error"] == "L4_NO_AUTHORIZABLE_PATH"



# --- S16 Compose ---


def test_s16_w0_and_publish_denied():
    draft = invoke("S08", "--text", "a local W0 draft", "--depth", "W0")
    assert draft["ok"] is True
    assert draft["skill"] == "S16_Compose"
    assert draft["llm"] is False
    denied = invoke("S16", "--text", "publish this", "--publish")
    assert denied["ok"] is False
    assert denied["error"] == "CAN_WRITE_NEQ_CAN_PUBLISH"


def test_s16_w4_depth_denied():
    denied = invoke("S16", "--text", "ready to ship", "--depth", "W4")
    assert denied["ok"] is False
    assert denied["error"] == "CAN_WRITE_NEQ_CAN_PUBLISH"


def test_s16_fact_without_evidence_unmarked():
    claims = json.dumps([{"tag": "FACT"}])
    denied = invoke("S16", "--text", "claim without ref", "--claims-json", claims)
    assert denied["ok"] is False
    assert denied["error"] == "UNMARKED_ERROR"


def test_s16_fact_with_evidence_ok():
    claims = json.dumps([{"tag": "FACT", "evidence_ref": "SETV-INST-DEMO"}])
    payload = invoke("S16", "--text", "marked claim", "--claims-json", claims)
    assert payload["ok"] is True
    assert payload["skill"] == "S16_Compose"


def test_s16_alias_explain():
    payload = invoke("S09", "--text", "explain GARCH briefly", "--depth", "W0")
    assert payload["ok"] is True
    assert payload["skill"] == "S16_Compose"


# --- S02 ReadAloud (live · opt-in) ---


@pytest.mark.skipif(
    os.environ.get("KF_RUN_SLOW", "").strip() not in {"1", "true", "yes"},
    reason="S02 live TTS — set KF_RUN_SLOW=1",
)
def test_s02_zh_live_read_aloud(tmp_path: Path):
    out = tmp_path / "s02_zh.wav"
    payload = invoke(
        "S02",
        "--text",
        "核心观点先读出来。",
        "--language",
        "zh",
        "-o",
        str(out),
        timeout=180.0,
    )
    assert payload["ok"] is True
    assert payload["skill"] == "S02_ReadAloud"
    assert payload["language"] == "zh"
    assert payload["voice"] == "me"
    assert Path(payload["audio"]).is_file() or out.is_file()


@pytest.mark.skipif(
    os.environ.get("KF_RUN_SLOW", "").strip() not in {"1", "true", "yes"},
    reason="S02 live TTS — set KF_RUN_SLOW=1",
)
def test_s02_en_live_read_aloud(tmp_path: Path):
    out = tmp_path / "s02_en.wav"
    payload = invoke(
        "S02",
        "--text",
        "The core idea comes first.",
        "--language",
        "en",
        "-o",
        str(out),
        timeout=180.0,
    )
    assert payload["ok"] is True
    assert payload["language"] == "en"
    assert payload["voice"] == "me_en"


def test_s02_missing_output_fails():
    bad = invoke("S02", "--text", "no output path", "--language", "zh")
    assert bad["ok"] is False
    assert bad["error"] == "DS_INVOKE_USAGE"
    assert "output" in bad.get("message", "").lower()
