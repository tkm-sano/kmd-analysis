from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/use_case_scenario"


def write_probability_scale() -> Path:
    rows = [
        {
            "score": 1,
            "probability": 0.2,
            "meaning_ja": "起こり得るが、直接根拠が弱い",
            "meaning_en": "Possible, but direct evidence is weak.",
        },
        {
            "score": 2,
            "probability": 0.5,
            "meaning_ja": "条件付きで起こり得る、または複数のproxyがある",
            "meaning_en": "Conditionally plausible, or supported by multiple proxy indicators.",
        },
        {
            "score": 3,
            "probability": 0.8,
            "meaning_ja": "データ・文献・benchmarkの複数根拠がある",
            "meaning_en": "Supported by multiple sources such as data, literature, and benchmarks.",
        },
    ]
    path = OUT / "future_wheels_probability_scale.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_impact_scale() -> Path:
    rows = [
        {
            "score": 1,
            "impact_value": 1,
            "meaning_ja": "研究上の補助的示唆にとどまる",
            "meaning_en": "Supplementary implication for the research.",
        },
        {
            "score": 2,
            "impact_value": 2,
            "meaning_ja": "一部の問題設定に影響",
            "meaning_en": "Affects some problem settings.",
        },
        {
            "score": 3,
            "impact_value": 3,
            "meaning_ja": "EV routing設計に明確な影響",
            "meaning_en": "Clearly affects EV routing design.",
        },
        {
            "score": 4,
            "impact_value": 4,
            "meaning_ja": "Tokyo use caseの主要要件に影響",
            "meaning_en": "Affects major requirements of the Tokyo use case.",
        },
        {
            "score": 5,
            "impact_value": 5,
            "meaning_ja": "研究主張の中心になる影響",
            "meaning_en": "Central implication for the research claim.",
        },
    ]
    path = OUT / "future_wheels_impact_scale.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_evidence_strength_scale() -> Path:
    rows = [
        {
            "score": 1,
            "meaning_ja": "概念的・推論ベース",
            "meaning_en": "Conceptual or inference-based.",
        },
        {
            "score": 2,
            "meaning_ja": "proxy data または benchmark で支持",
            "meaning_en": "Supported by proxy data or benchmark evidence.",
        },
        {
            "score": 3,
            "meaning_ja": "複数の一次情報・実データ・benchmarkで支持",
            "meaning_en": "Supported by multiple primary sources, empirical data, or benchmarks.",
        },
    ]
    path = OUT / "future_wheels_evidence_strength_scale.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_rulebook() -> Path:
    rows = [
        {
            "rule_id": "probability",
            "item": "conditional_probability",
            "recommended_design": "Three-level probability: 0.2 / 0.5 / 0.8",
            "scoring_rule_ja": "各枝の条件付き確率を1-3点で採点し、1=0.2、2=0.5、3=0.8へ変換する。",
            "scoring_rule_en": "Score each branch probability from 1 to 3 and convert 1=0.2, 2=0.5, 3=0.8.",
            "calculation_rule": "conditional_probability is looked up from future_wheels_probability_scale.csv.",
        },
        {
            "rule_id": "impact",
            "item": "impact_value",
            "recommended_design": "Five-level impact value: 1-5",
            "scoring_rule_ja": "終端ノードまたは評価対象ノードの影響を1-5点で採点する。",
            "scoring_rule_en": "Score node impact from 1 to 5.",
            "calculation_rule": "impact_value equals impact_score unless a later sensitivity analysis changes the mapping.",
        },
        {
            "rule_id": "evidence_strength",
            "item": "evidence_strength_score",
            "recommended_design": "Three-level evidence strength: 1-3",
            "scoring_rule_ja": "根拠の強さを1-3点で採点し、概念・proxy/benchmark・複数根拠を区別する。",
            "scoring_rule_en": "Score evidence strength from 1 to 3, distinguishing conceptual evidence, proxy/benchmark support, and multiple-source support.",
            "calculation_rule": "Evidence strength is recorded for auditability and uncertainty assignment; it is not multiplied into expected impact by default.",
        },
        {
            "rule_id": "cumulative_probability",
            "item": "cumulative_probability",
            "recommended_design": "Product of conditional probabilities from the root node",
            "scoring_rule_ja": "rootから対象ノードまでの条件付き確率を掛け合わせる。",
            "scoring_rule_en": "Multiply conditional probabilities along the path from the root to the target node.",
            "calculation_rule": "root cumulative_probability = 1.0; child cumulative_probability = parent cumulative_probability * conditional_probability.",
        },
        {
            "rule_id": "expected_impact",
            "item": "expected_impact",
            "recommended_design": "cumulative_probability x impact_value",
            "scoring_rule_ja": "累積確率とimpact valueを掛け合わせる。",
            "scoring_rule_en": "Multiply cumulative probability by impact value.",
            "calculation_rule": "expected_impact = cumulative_probability * impact_value.",
        },
        {
            "rule_id": "uncertainty_flag",
            "item": "uncertainty_flag",
            "recommended_design": "high / medium / low",
            "scoring_rule_ja": "採点根拠の弱さやproxy依存度に応じて不確実性をhigh / medium / lowで記録する。",
            "scoring_rule_en": "Record uncertainty as high, medium, or low depending on evidence weakness and proxy dependence.",
            "calculation_rule": "Default guide: evidence_strength_score 1=high, 2=medium, 3=low; adjust manually when the rationale requires it.",
        },
    ]
    path = OUT / "future_wheels_scoring_rulebook.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_node_scoring_template() -> Path:
    columns = [
        "node_id",
        "parent_node_id",
        "node_label",
        "node_layer",
        "STEEP_tag",
        "desirability",
        "time_horizon",
        "conditional_probability_score",
        "conditional_probability",
        "impact_axis",
        "impact_score",
        "impact_value",
        "evidence_strength_score",
        "evidence_sources",
        "scoring_rationale",
        "uncertainty_flag",
        "cumulative_probability",
        "expected_impact",
    ]
    rows = [
        {
            "node_id": "FW0",
            "parent_node_id": "",
            "node_label": "Charging-aware EV last-mile routing in Tokyo",
            "node_layer": "root",
            "STEEP_tag": "technology",
            "desirability": "mixed",
            "time_horizon": "medium",
            "conditional_probability_score": "",
            "conditional_probability": 1.0,
            "impact_axis": "",
            "impact_score": "",
            "impact_value": "",
            "evidence_strength_score": "",
            "evidence_sources": "selected_use_case_scope; Tokyo public data; EVRP benchmark; quantum VRP Figure 1",
            "scoring_rationale": "Root node fixed by the selected use case; not scored as an uncertain branch.",
            "uncertainty_flag": "",
            "cumulative_probability": 1.0,
            "expected_impact": "",
        }
    ]
    path = OUT / "future_wheels_node_scoring_template.csv"
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    return path


def write_summary() -> Path:
    rows = [
        {
            "output_file": "future_wheels_scoring_rulebook.csv",
            "role": "Defines the scoring design and calculation rules.",
        },
        {
            "output_file": "future_wheels_probability_scale.csv",
            "role": "Maps probability scores 1-3 to 0.2 / 0.5 / 0.8.",
        },
        {
            "output_file": "future_wheels_impact_scale.csv",
            "role": "Maps impact scores 1-5 to impact values 1-5.",
        },
        {
            "output_file": "future_wheels_evidence_strength_scale.csv",
            "role": "Defines evidence strength scores 1-3.",
        },
        {
            "output_file": "future_wheels_node_scoring_template.csv",
            "role": "Template for scoring Future Wheels nodes and calculating expected impact.",
        },
    ]
    path = OUT / "future_wheels_scoring_outputs_902_20260711_v04_manifest.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [
        write_rulebook(),
        write_probability_scale(),
        write_impact_scale(),
        write_evidence_strength_scale(),
        write_node_scoring_template(),
        write_summary(),
    ]
    for path in paths:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
