"""Build the current 66-section Road Census-to-SUMO baseline snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = (
    REPOSITORY_ROOT
    / "03_data/processed/traffic_simulation/calibration/road_census_sumo_mapping_20260826"
)
DEFAULT_JSON = (
    REPOSITORY_ROOT
    / "reproducibility/config/traffic_simulation/road_census_sumo_baseline_20260827.json"
)
DEFAULT_MARKDOWN = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/road_census_sumo_current_baseline.md"
)

TARGETS = {
    "lane": "LANE_DIRECTION_ALLOCATION",
    "speed": "SPEED_VALUE_SELECTION",
    "traffic": "TRAFFIC_COMPARISON_CROSS_SECTION",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(REPOSITORY_ROOT))


def _base_statuses(inventory: list[dict[str, str]], target: str) -> dict[str, str]:
    statuses = {
        row["section_id"]: row["classification"]
        for row in inventory
        if row["target"] == target
    }
    if len(statuses) != 66:
        raise ValueError(f"{target}: expected 66 unique sections, got {len(statuses)}")
    return statuses


def _counts(statuses: dict[str, str]) -> dict[str, int]:
    return dict(sorted(Counter(statuses.values()).items()))


def build_snapshot(data_dir: Path) -> dict[str, Any]:
    source_names = [
        "assumption_inventory.csv",
        "census_final_mapping_summary.json",
        "road_census_section_attributes_normalized_qa_summary.json",
        "osm_sumo_edge_attributes_normalized_qa_summary.json",
        "lane_direction_assumption_refinement.csv",
        "lane_direction_assumption_final_review.csv",
        "speed_assumption_refinement.csv",
        "traffic_comparison_cross_section_final_review.csv",
        "traffic_comparison_data_availability_review.csv",
        "external_observation_mapping_candidate_summary.json",
        "external_observation_final_mapping.csv",
        "external_observation_mapping_final_edge_evidence.csv",
        "external_observation_final_inventory.csv",
        "external_observation_network_extension_before_after.csv",
        "ota66_network_extension_regression.csv",
        "external_observation_final_mapping_qa_summary.json",
        "external_observation_final_mapping_manifest.json",
    ]
    paths = {name: data_dir / name for name in source_names}
    missing = [relative(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"baseline inputs missing: {missing}")

    inventory = read_csv(paths["assumption_inventory.csv"])

    lane = _base_statuses(inventory, TARGETS["lane"])
    lane_refinement = read_csv(paths["lane_direction_assumption_refinement.csv"])
    for row in lane_refinement:
        if lane[row["section_id"]] != row["original_classification"]:
            raise ValueError(f"lane refinement predecessor mismatch: {row['section_id']}")
        lane[row["section_id"]] = row["refined_classification"]
    lane_review = read_csv(paths["lane_direction_assumption_final_review.csv"])
    for row in lane_review:
        if lane[row["section_id"]] != row["previous_classification"]:
            raise ValueError(f"lane final-review predecessor mismatch: {row['section_id']}")
        lane[row["section_id"]] = row["final_classification"]

    speed = _base_statuses(inventory, TARGETS["speed"])
    speed_refinement = read_csv(paths["speed_assumption_refinement.csv"])
    for row in speed_refinement:
        if speed[row["section_id"]] != row["original_classification"]:
            raise ValueError(f"speed refinement predecessor mismatch: {row['section_id']}")
        status = row["refined_classification"]
        if status == "UNRESOLVED" and row["primary_cause_code"] == "SOURCE_CONFLICT":
            status = "DATA_CONFLICT"
        speed[row["section_id"]] = status

    traffic = _base_statuses(inventory, TARGETS["traffic"])
    traffic_review = read_csv(paths["traffic_comparison_cross_section_final_review.csv"])
    for row in traffic_review:
        if traffic[row["section_id"]] != row["original_classification"]:
            raise ValueError(f"traffic final-review predecessor mismatch: {row['section_id']}")
        traffic[row["section_id"]] = row["final_classification"]
    availability = read_csv(paths["traffic_comparison_data_availability_review.csv"])
    for row in availability:
        traffic[row["section_id"]] = row["final_status"]

    mapping = read_json(paths["census_final_mapping_summary.json"])
    census = read_json(paths["road_census_section_attributes_normalized_qa_summary.json"])
    edge = read_json(paths["osm_sumo_edge_attributes_normalized_qa_summary.json"])
    external = read_json(paths["external_observation_mapping_candidate_summary.json"])
    external_qa = read_json(paths["external_observation_final_mapping_qa_summary.json"])
    external_inventory = read_csv(paths["external_observation_final_inventory.csv"])
    omissions = [row for row in availability if row["primary_availability_cause"] == "PROCESSING_OMISSION"]
    omission_codes = Counter(row["r3_observation_section_municipality_code"] for row in omissions)

    final_names = [
        "census_section_final_mapping.csv",
        "final_sumo_road_attributes.csv",
        "final_traffic_observations.csv",
    ]
    artifacts = {
        name: {
            "exists": (data_dir / name).is_file(),
            "formal_contract_complete": False,
        }
        for name in final_names
    }
    artifacts["census_section_final_mapping.csv"]["note"] = (
        "Existing 9-column intermediate mapping; formal provenance schema is not complete."
    )
    artifacts["external_observation_final_mapping.csv"] = {
        "exists": True, "formal_contract_complete": True,
        "record_count": external_qa["counts"]["formal_mapping_rows"],
    }
    artifacts["external_observation_final_inventory.csv"] = {
        "exists": True, "formal_contract_complete": True,
        "record_count": external_qa["counts"]["inventory_rows"],
    }

    snapshot = {
        "schema_version": 1,
        "baseline_id": "road_census_sumo_ota_20260827",
        "as_of_date": "2026-08-27",
        "scope": {
            "road_census_sections": 66,
            "municipality_code": "13111",
            "unique_final_mapping_edges": edge["scope"]["unique_final_mapping_edges"],
        },
        "mapping": {
            "unique_final_mapping_sections": mapping["section_count"],
            "usable_sections": mapping["final_usable_mapping_section_count"],
            "not_usable_sections": mapping["not_usable_section_ids"],
            "confidence_counts": mapping["final_confidence_counts"],
            "connection_violation_count": mapping["selected_corridor_sumo_connection_violation_count"],
        },
        "road_census_normalization": {
            "status_counts": census["normalization_status_counts"],
            "unresolved_section_count": census["unresolved_section_count"],
            "qa_issue_count": census["qa_issue_count"],
        },
        "edge_provenance": {
            "edge_count": edge["scope"]["unique_final_mapping_edges"],
            "lane_count": edge["sumo_value_provenance"]["lane_count"],
            "speed": edge["sumo_value_provenance"]["speed"],
            "reverse_edge_resolution": edge["reverse_edge_resolution"],
        },
        "section_statuses": {
            "lane": {
                "section_count": len(lane),
                "counts": _counts(lane),
                "stage_note": "Initial 66-section inventory overlaid by 59-section refinement and 21-section final review.",
            },
            "speed": {
                "section_count": len(speed),
                "counts": _counts(speed),
                "stage_note": "Initial 66-section inventory overlaid by 41-section refinement; SOURCE_CONFLICT is reported as DATA_CONFLICT.",
            },
            "traffic": {
                "section_count": len(traffic),
                "counts": _counts(traffic),
                "stage_note": "Initial 66-section inventory overlaid by 32-section final review and 26-section availability audit.",
            },
        },
        "external_observation_mapping": {
            "processing_omission_sections": len(omissions),
            "municipality_counts": {
                "13109_shinagawa": omission_codes["13109"],
                "13112_setagaya": omission_codes["13112"],
            },
            "mapping_status": "FORMALIZED_10_OF_10",
            "classification_counts": external["classification_counts"],
            "formal_mapping_status_counts": dict(Counter(row["mapping_status"] for row in external_inventory)),
            "direction_status_counts": dict(Counter(row["direction_status"] for row in external_inventory)),
            "traffic_assignment_status_counts": dict(Counter(row["traffic_assignment_usability"] for row in external_inventory)),
            "final_acceptance_status_counts": dict(Counter(row["final_acceptance_status"] for row in external_inventory)),
            "limited_network_extension": {
                "section_id": "13300010260",
                "mapping_status": external_qa["network_extension"]["mapping_status"],
                "coverage_ratio": external_qa["network_extension"]["coverage_ratio"],
                "uncovered_length_m": external_qa["network_extension"]["uncovered_length_m"],
                "connection_violation_count": external_qa["network_extension"]["connection_violation_count"],
                "bbox_auto_expanded": external_qa["guardrails"]["bbox_auto_expanded"],
            },
            "requested_haneda_direction_finalized": any(
                row["official_observation_section_id"] == "13200100070" and row["direction_status"] == "RESOLVED"
                for row in external_inventory
            ),
            "all_external_directions_finalized": all(row["direction_status"] == "RESOLVED" for row in external_inventory),
        },
        "formalization_gaps": {
            "canonical_route_identity": "NOT_COMPLETE",
            "census_to_sumo_direction": "EXTERNAL_1_RESOLVED_9_MODEL_ASSUMPTION_REQUIRED_OTA66_NOT_COMPLETE",
            "external_observation_mapping": "COMPLETE_10_OF_10_LAYERED_FINAL_STATUS",
            "traffic_66_final_taxonomy": "NOT_COMPLETE",
            "final_inventory_330_cells": "NOT_GENERATED",
            "formal_export_runner": "NOT_IMPLEMENTED",
        },
        "formal_artifacts": artifacts,
        "source_manifest": [
            {"path": relative(path), "sha256": sha256_file(path)}
            for path in paths.values()
        ],
        "guardrails": {
            "source_values_modified": False,
            "mapping_thresholds_modified": False,
            "missing_values_imputed": False,
            "partial_stage_counts_reported_as_66_section_counts": False,
        },
    }

    expected = {
        "lane": {"NO_ASSUMPTION_NEEDED": 40, "MODEL_ASSUMPTION_REQUIRED": 19, "DATA_CONFLICT": 2, "UNRESOLVED": 5},
        "speed": {"NO_ASSUMPTION_NEEDED": 55, "DATA_CONFLICT": 10, "UNRESOLVED": 1},
        "traffic": {"NO_ASSUMPTION_NEEDED": 34, "MODEL_ASSUMPTION_REQUIRED": 1, "DATA_NOT_AVAILABLE": 11, "UNRESOLVED": 20},
    }
    for target, counts in expected.items():
        if snapshot["section_statuses"][target]["counts"] != dict(sorted(counts.items())):
            raise ValueError(f"unexpected {target} baseline: {snapshot['section_statuses'][target]['counts']}")
    return snapshot


def render_markdown(snapshot: dict[str, Any], json_path: Path) -> str:
    lane = snapshot["section_statuses"]["lane"]["counts"]
    speed = snapshot["section_statuses"]["speed"]["counts"]
    traffic = snapshot["section_statuses"]["traffic"]["counts"]
    mapping = snapshot["mapping"]
    external = snapshot["external_observation_mapping"]
    return f"""# 大田区 Road Census→SUMO 現状ベースライン

基準日: **{snapshot['as_of_date']}**  
baseline ID: `{snapshot['baseline_id']}`  
機械可読正本: `{relative(json_path)}`

## 判定

本資料は既存成果物を再実行・変更せず、section ID単位で段階的レビュー結果を重ねて再集計したスナップショットである。部分工程の件数を66区間全体の件数として扱わない。

## 現状値

| 項目 | 66区間全体の現状 |
|---|---:|
| final mapping一意 | {mapping['unique_final_mapping_sections']}/66 |
| 後段利用可能mapping | {mapping['usable_sections']}/66 |
| 後段利用不可mapping | {len(mapping['not_usable_sections'])}/66（`{';'.join(mapping['not_usable_sections'])}`） |
| Road Census属性正規化 | RESOLVED 65 / UNRESOLVED 1 |
| final mapping対象edge | {snapshot['scope']['unique_final_mapping_edges']} unique edge |
| lane | NO_ASSUMPTION_NEEDED {lane['NO_ASSUMPTION_NEEDED']} / MODEL_ASSUMPTION_REQUIRED {lane['MODEL_ASSUMPTION_REQUIRED']} / DATA_CONFLICT {lane['DATA_CONFLICT']} / UNRESOLVED {lane['UNRESOLVED']} |
| speed | NO_ASSUMPTION_NEEDED {speed['NO_ASSUMPTION_NEEDED']} / DATA_CONFLICT {speed['DATA_CONFLICT']} / UNRESOLVED {speed['UNRESOLVED']} |
| traffic comparison | NO_ASSUMPTION_NEEDED {traffic['NO_ASSUMPTION_NEEDED']} / MODEL_ASSUMPTION_REQUIRED {traffic['MODEL_ASSUMPTION_REQUIRED']} / DATA_NOT_AVAILABLE {traffic['DATA_NOT_AVAILABLE']} / UNRESOLVED {traffic['UNRESOLVED']} |
| 外部観測mapping処理漏れ | 10/10を正式status化済み（品川区7 / 世田谷区3）。mapping RESOLVED {external['formal_mapping_status_counts']['RESOLVED']}、direction RESOLVED {external['direction_status_counts']['RESOLVED']} / MODEL_ASSUMPTION_REQUIRED {external['direction_status_counts']['MODEL_ASSUMPTION_REQUIRED']}、traffic assignment USABLE {external['traffic_assignment_status_counts']['USABLE']} / PENDING {external['traffic_assignment_status_counts']['PENDING_DIRECTION_ASSIGNMENT']} |
| final inventory | 330セル未生成 |

## 旧計画値からの訂正

- 後段利用可能mappingは64/66ではなく、現行summaryに基づき **65/66** とする。
- laneの38/17/4は59区間だけを対象としたrefinement中間値である。66区間へ初期inventoryとfinal reviewを統合した現状値は **40/19/2/5** である。
- speedの31/0/10は41区間だけを対象としたrefinement値である。66区間全体では **55 NO_ASSUMPTION_NEEDED / 10 DATA_CONFLICT / 1 UNRESOLVED** である。
- trafficの11 DATA_NOT_AVAILABLE / 15 UNRESOLVEDは追加調査26区間だけの値である。66区間全体の現行分類は上表のとおりであり、最終traffic taxonomyではない。

## 未完了ゲート

- canonical route identityの全66区間・対象edgeへの確定
- Census上下方向とSUMO directed edge列の正式対応
- 外部観測10件のmapping層は完了。残る9件の上下方向は`MODEL_ASSUMPTION_REQUIRED`であり、方向別traffic assignmentには公式証拠または明示的研究仮定が必要
- traffic 66区間の目的別最終taxonomy
- lane、speed、route、direction、trafficの330セルinventory
- 3正式CSVのschema、export runner、QA、再生成manifest

既存の`census_section_final_mapping.csv`は中間mappingとして存在するが、計画が要求するraw・normalized・adopted・provenanceを備えた正式契約は未完成である。`final_sumo_road_attributes.csv`と`final_traffic_observations.csv`は未生成である。

## 集計規則

1. `assumption_inventory.csv`の66区間を初期母集団とする。
2. laneは59区間refinement、続いて21区間final reviewをsection IDで上書きする。
3. speedは41区間refinementを上書きし、`SOURCE_CONFLICT`を`DATA_CONFLICT`として表示する。
4. trafficは32区間final review、続いて26区間availability auditを上書きする。
5. 入力値、mapping閾値、欠測値は変更しない。

入力ファイルとSHA-256は機械可読正本の`source_manifest`に記録する。

## 外部観測mapping正式化（2026-08-27）

- 既存`AUTO_ACCEPT` 8/8を、edge列とcoverageを変更せず正式mappingへ昇格した。
- `13200100070`は上りを`45554540#0;45554540#1`、下りを`4854104#1;4854104#2`として確定した。
- `13300010260`は指定bboxだけを使う版付き別networkで再評価し、coverage {external['limited_network_extension']['coverage_ratio']:.4%}、未被覆{external['limited_network_extension']['uncovered_length_m']:.3f}m、connection violation {external['limited_network_extension']['connection_violation_count']}で`{external['limited_network_extension']['mapping_status']}`とした。
- `13403160320`系3件のcoverageは58.0542%のまま保持し、未被覆336.185mを記録した。
- 既存66区間はedge ID、edge分割/topology、lane、speed、route identityの変更0、後段利用可能mappingは65/66のままである。
- 作業後回帰は既存57件と新規11件の計68件が成功した。

正式成果物の正本は`external_observation_final_mapping_manifest.json`である。
"""


def write_outputs(snapshot: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(snapshot, json_path), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    snapshot = build_snapshot(args.data_dir.resolve())
    write_outputs(snapshot, args.json_output.resolve(), args.markdown_output.resolve())
    print(json.dumps({"baseline_id": snapshot["baseline_id"], "json": str(args.json_output), "markdown": str(args.markdown_output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
