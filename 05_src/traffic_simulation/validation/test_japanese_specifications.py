"""Keep translated specifications aligned with stable normative identifiers."""

from __future__ import annotations

import re

from traffic_simulation.paths import REPOSITORY_ROOT


SPECIFICATIONS = REPOSITORY_ROOT / "05_src/traffic_simulation/specifications"


def tokens(path: str, pattern: str) -> set[str]:
    content = (SPECIFICATIONS / path).read_text(encoding="utf-8")
    return set(re.findall(pattern, content))


def test_resolver_translation_contains_every_normative_identifier() -> None:
    english = "02_resolver_specification.md"
    japanese = "ja/02_resolver_specification_ja.md"

    for pattern in (
        r"RS-REQ-\d{3}",
        r"RS-TST-\d{3}",
        r"RS\d{3}",
    ):
        assert tokens(japanese, pattern) == tokens(english, pattern)


def test_criticality_translation_contains_every_rule_level_and_action() -> None:
    english = "attribute_criticality_and_evidence_specification.md"
    japanese = "ja/attribute_criticality_and_evidence_specification_ja.md"

    for pattern in (
        r"LANE-CRIT-\d{3}",
        r"SPEED-CRIT-\d{3}",
        r"`[LS][0-3]`",
        r"`(?:adopt_explicit|derive_osm_rule|adopt_external_evidence|"
        r"apply_governed_rule|apply_structural_placeholder|"
        r"require_human_review|stop_unresolved|exclude)`",
    ):
        assert tokens(japanese, pattern) == tokens(english, pattern)


def test_criticality_translation_contains_every_failure_identifier() -> None:
    english = "attribute_criticality_and_evidence_specification.md"
    japanese = "ja/attribute_criticality_and_evidence_specification_ja.md"

    for pattern in (
        r"AC-REQ-\d{3}",
        r"AC-TST-\d{3}",
        r"AC\d{3}",
    ):
        assert tokens(japanese, pattern) == tokens(english, pattern)


def test_classification_and_resolution_are_separate_in_both_languages() -> None:
    for path in (
        "attribute_criticality_and_evidence_specification.md",
        "ja/attribute_criticality_and_evidence_specification_ja.md",
    ):
        content = (SPECIFICATIONS / path).read_text(encoding="utf-8")
        assert "attribute_criticality_classification.json" in content
        assert "attribute_resolution_decisions.json" in content
        assert "`evidence_candidates`" in content
        assert "`selected_evidence_id`" in content
