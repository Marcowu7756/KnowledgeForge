"""Taxonomy outline builder + UI API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.ui.server import create_app
from app.ui.taxonomy_outline import build_taxonomy_outline, cards_under_prefix


def test_build_taxonomy_outline_groups_and_lane_filter():
    records = [
        {
            "id": "a",
            "title": "YT card",
            "path": "data/knowledge/a.md",
            "access": {"classification": "public"},
            "taxonomy": {"path": ["公开媒体", "捕获", "YouTube", "YT card"]},
        },
        {
            "id": "b",
            "title": "SETV snap",
            "path": "data/knowledge/restricted/setv/b.md",
            "access": {"classification": "restricted", "source_project": "setv"},
            "taxonomy": {"path": ["专有知识", "SETV", "State Snapshot", "AAPL"]},
        },
        {
            "id": "c",
            "title": "No tax",
            "path": "data/knowledge/c.md",
            "access": {"classification": "public"},
            "taxonomy": {"path": []},
        },
    ]
    general = build_taxonomy_outline(access_lane="general", records=records)
    assert general["included"] == 2
    assert general["denied"] == 1
    labels = {r["label"] for r in general["roots"]}
    assert "公开媒体" in labels
    assert "(未分类)" in labels
    assert "专有知识" not in labels

    prop = build_taxonomy_outline(access_lane="proprietary", records=records)
    assert prop["included"] == 3
    prop_labels = {r["label"] for r in prop["roots"]}
    assert "专有知识" in prop_labels
    assert "公开媒体" in prop_labels

    cards = cards_under_prefix(prop, "专有知识/SETV")
    assert any(c["title"] == "SETV snap" for c in cards)


def test_ui_taxonomy_tree_endpoint_and_shell_markers():
    client = TestClient(create_app())
    h = client.get("/api/health")
    assert h.status_code == 200
    body = h.json()
    assert body["ui_version"] == "0.6.4"
    assert body["features"]["taxonomy_outline"] is True
    assert body["features"]["taxonomy_open_card"] is True

    tree = client.get("/api/taxonomy/tree", params={"lane": "general"})
    assert tree.status_code == 200
    data = tree.json()
    assert data["ok"] is True
    assert data["access_lane"] == "general"
    assert "roots" in data

    page = client.get("/")
    assert page.status_code == 200
    assert b"tax-tree-reconstruct" in page.content
    assert b"tax-tree-retrieve" in page.content
    assert b"taxonomy_prefix" in page.content
    assert b"tax-group-cards-reconstruct" in page.content
    assert b"tax-hint" in page.content
    assert b"tax-doc" in page.content


def test_ui_shell_version_bump():
    client = TestClient(create_app())
    h = client.get("/api/health")
    assert h.json()["ui_version"] == "0.6.4"
