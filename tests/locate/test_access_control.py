"""KO access classification — retrieve / compose / ingest gates (§8)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from app.compose.engine import compose_from_query
from app.knowledge.access import (
    AccessBlock,
    access_from_meta,
    default_access_for_ingest,
    infer_source_project,
    is_compose_eligible,
)
from app.knowledge.parse import load_unit_from_markdown
from app.knowledge.yaml_meta import parse_card_yaml
from app.retrieve.models import IndexRecord, RetrieveHit, RetrieveResult
from app.retrieve.query import retrieve_kos
from app.retrieve.store import save_index
from app.storage.markdown import render_markdown
from app.models import KnowledgeUnit
from app import config


SECRET_CARD = """# Secret Strategy

```yaml
id: seck001
title: Secret Strategy
source: unit-test
type: notes
tags: ["secret"]
access:
  classification: secret
  export_policy: local_only
```

## Core Idea

Never leave this machine.
"""


RESTRICTED_SETV_CARD = """# SETV Method

```yaml
id: setv001
title: SETV Method
source: D:/fxtrading/setv/docs/method.md
type: md
tags: ["methodology"]
access:
  classification: restricted
  source_project: setv
  export_policy: local_only
```

## Core Idea

State-first discipline.
"""


def test_access_infer_source_project():
    assert infer_source_project(r"D:\fxtrading\setv\doc.md") == "setv"
    assert infer_source_project("/repos/factorlib/README.md") == "factorlib"
    assert infer_source_project("data/asharelib/notes.txt") == "asharelib"
    assert infer_source_project("public/blog.md") == ""


def test_access_default_for_proprietary_paths():
    block = default_access_for_ingest(
        source_path=r"D:\factorlib\alpha.md",
        dest_path="data/knowledge/methodology",
        tags=["folder-search"],
    )
    assert block.classification == "restricted"
    assert block.source_project == "factorlib"
    assert block.export_policy == "local_only"


def test_access_default_public_for_generic_ingest():
    block = default_access_for_ingest(source_path="notes.txt", dest_path="data/knowledge/physics")
    assert block.classification == "public"
    assert block.export_policy == "export_ok"


def test_access_yaml_roundtrip(tmp_path: Path):
    unit = KnowledgeUnit(
        title="Tagged",
        source="unit-test",
        type="notes",
        summary="x",
        access=AccessBlock(classification="internal", source_project="setv"),
    )
    md = render_markdown(unit)
    path = tmp_path / "card.md"
    path.write_text(md, encoding="utf-8")
    loaded = load_unit_from_markdown(path)
    assert loaded.access.classification == "internal"
    assert loaded.access.source_project == "setv"


def test_access_parse_nested_yaml_block():
    meta = parse_card_yaml(
        "id: a\naccess:\n  classification: restricted\n  source_project: setv\n"
    )
    block = access_from_meta(meta)
    assert block.classification == "restricted"
    assert block.source_project == "setv"


def test_access_compose_eligibility():
    assert is_compose_eligible("public", llm_provider="openai")
    assert not is_compose_eligible("restricted", llm_provider="openai")
    assert is_compose_eligible("restricted", llm_provider="ollama")
    assert not is_compose_eligible("secret", llm_provider="ollama")


def test_access_retrieve_filters_secret_by_default(tmp_path: Path):
    records = [
        IndexRecord(
            ko_id="ko_pub",
            vector_id="emb_1",
            title="Public",
            path="a.md",
            classification="public",
        ),
        IndexRecord(
            ko_id="ko_sec",
            vector_id="emb_2",
            title="Secret",
            path="b.md",
            classification="secret",
        ),
    ]
    vectors = np.array([[1.0, 0.0], [0.9, 0.1]], dtype=np.float32)
    save_index(records=records, vectors=vectors, model="mock", root=tmp_path)

    with patch("app.retrieve.query.embed_query", return_value=np.array([1.0, 0.0], dtype=np.float32)):
        result = retrieve_kos("query", top_k=5, index_dir=tmp_path)

    ids = {h.ko_id for h in result.hits}
    assert "ko_pub" in ids
    assert "ko_sec" not in ids


def test_access_compose_blocks_cloud_restricted(monkeypatch):
    fake_result = RetrieveResult(
        query="q",
        hits=[
            RetrieveHit(
                ko_id="ko_r",
                title="Restricted",
                score=0.9,
                path="r.md",
                classification="restricted",
            )
        ],
    )

    class FakeQuery:
        result = fake_result
        result_path = None

    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    with (
        patch("app.compose.engine.run_query", return_value=FakeQuery()),
        pytest.raises(RuntimeError, match="compose-eligible"),
    ):
        compose_from_query("q", kind="paper", top_k=1)


def test_preview_blocks_secret_card(tmp_path: Path, monkeypatch):
    from app.ui.preview import resolve_data_path

    data = tmp_path / "data"
    data.mkdir()
    secret = data / "secret.md"
    secret.write_text(SECRET_CARD, encoding="utf-8")
    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "ROOT", tmp_path)

    with pytest.raises(PermissionError, match="secret"):
        resolve_data_path(str(secret))
