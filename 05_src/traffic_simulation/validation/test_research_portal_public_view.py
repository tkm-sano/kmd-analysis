"""Check the Portal's public/technical information boundary."""

from __future__ import annotations

import importlib.util
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INDEX_HTML = ROOT / "research_portal/index.html"


def portal_state() -> dict:
    spec = importlib.util.spec_from_file_location("research_portal_serve", ROOT / "research_portal/serve.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.summary()


class ElementBoundaryParser(HTMLParser):
    VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, str | None]] = []
        self.ancestors_by_id: dict[str, set[str]] = {}
        self.attributes_by_id: dict[str, dict[str, str | None]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ancestors_by_id[element_id] = {item_id for _, item_id in self.stack if item_id}
            self.attributes_by_id[element_id] = attributes
        if tag not in self.VOID_ELEMENTS:
            self.stack.append((tag, element_id))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return


def test_public_view_is_default_and_technical_content_is_collapsed() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    parser = ElementBoundaryParser()
    parser.feed(html)

    assert "open" not in parser.attributes_by_id["technical-details"]
    for element_id in ("question", "public-pipeline", "public-current-stage", "public-network-scale", "public-validation"):
        assert "technical-details" not in parser.ancestors_by_id[element_id]
    for element_id in ("implementation-map", "network-summary", "validation-table", "unresolved-grid", "artifact-browser", "command-list", "timeline-list"):
        assert "technical-details" in parser.ancestors_by_id[element_id]

    public_markup = html[: html.index('<details id="technical-details"')]
    assert "SHA256" not in public_markup
    assert "./research " not in public_markup
    assert "Research Commands" not in public_markup
    assert "Technical Details" in html
    assert "Explore Network / Instances" in html


def test_public_state_is_grounded_in_current_state() -> None:
    state = portal_state()
    public = state["public_view"]

    assert public["role"] == "Research communication layer"
    assert state["current_position"]["current_stage"] == "Routing Baseline"
    assert public["network_validation"] == "Passed"
    assert public["mapped_delivery_stops"] == state["accepted_network"]["mapping"]["mapped"]
    assert public["interpretation_assessment"] == state["interpretation_evidence"]["overall_assessment"]
    assert [item["status"] for item in public["pipeline"]] == [
        "DONE", "DONE", "DONE", "NEXT", "PLANNED", "FUTURE", "FUTURE", "FUTURE",
    ]
    assert state["network_scale"]["network_node_count"] > 0
    assert state["network_scale"]["network_edge_count"] > 0
    assert state["network_scale"]["network_lane_count"] > 0
    assert any("sample-based" in limitation for limitation in public["limitations"])
    assert any("投資行動を予測しません" in limitation for limitation in public["limitations"])
