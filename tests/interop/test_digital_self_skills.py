"""KF consumes Digital Self catalog. Neighbor must be on disk; no live Playwright/MT5."""
from __future__ import annotations

from app.interop.digital_self import digital_self_root, invoke, invoke_path, list_skills
from app.main import main


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


def test_s06_plan_and_live_denied():
    plan = invoke("S06", "--intent", "open YouTube", "--url", "https://www.youtube.com")
    assert plan["ok"] is True
    assert plan["live"] is False
    denied = invoke("S06", "--intent", "open YouTube", "--live")
    assert denied["ok"] is False
    assert denied["error"] == "LIVE_BROWSER_NOT_AUTHORIZED"


def test_s15_setv_plan_and_l4_denied():
    plan = invoke("S14", "--scene", "setv", "--task", "cite artifact_id=demo")
    assert plan["ok"] is True
    assert plan["skill"] == "S15_ResearchOp"
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


def test_s16_w0_and_publish_denied():
    draft = invoke("S08", "--text", "a local W0 draft", "--depth", "W0")
    assert draft["ok"] is True
    assert draft["skill"] == "S16_Compose"
    assert draft["llm"] is False
    denied = invoke("S16", "--text", "publish this", "--publish")
    assert denied["ok"] is False
    assert denied["error"] == "CAN_WRITE_NEQ_CAN_PUBLISH"


def test_kf_cli_ds_list():
    assert main(["ds", "list"]) == 0
