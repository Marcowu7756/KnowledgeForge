"""Unit test for collect_from_index priority before limit (A3)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from app.reconstruct import load as load_mod


def test_a3_collect_from_index_prefers_richer_before_limit(tmp_path: Path, two_kos):
    rich_ko, poor_ko = two_kos[0], two_kos[1]
    poor = tmp_path / "poor.md"
    rich = tmp_path / "rich.md"
    poor.write_text("# poor\n", encoding="utf-8")
    rich.write_text("# rich\n", encoding="utf-8")

    # Poorer metadata listed first in jsonl — limit=1 must still pick richer
    index = [
        {
            "path": str(poor),
            "tags": [],
            "concepts": [],
            "summary": "",
        },
        {
            "path": str(rich),
            "tags": ["金融"],
            "concepts": ["美债", "美元", "信用"],
            "summary": "yes",
        },
    ]

    def fake_load(path: Path):
        if path.name == "rich.md":
            return rich_ko
        return poor_ko

    with (
        patch.object(load_mod, "load_jsonl", return_value=index),
        patch.object(load_mod, "global_jsonl_path", return_value=tmp_path / "index.jsonl"),
        patch.object(load_mod, "load_knowledge_object", side_effect=fake_load),
    ):
        objs = load_mod.collect_from_index(limit=1)

    assert len(objs) == 1
    assert objs[0].id == rich_ko.id
