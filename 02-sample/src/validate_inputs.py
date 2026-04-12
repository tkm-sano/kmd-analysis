#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import pandas as pd


REQUIRED_FILES = {
    "benchmark_evidence": ["benchmark_evidence.csv", "benchmark_evidence_model_input.csv", "benchmark_evidence_demo.csv"],
    "od_flow": ["od_flow.csv", "od_flow_demo.csv"],
    "translation_parameters": ["translation_parameters.csv", "translation_parameters_demo.csv"],
    "model_controls": ["model_controls.csv"],
}

REQUIRED_COLUMNS = {
    "benchmark_evidence": {
        "source_key", "industry_group", "problem_class", "compute_condition",
        "quality_metric", "quality_threshold", "cost_index", "time_hours",
        "quality_value", "valid_candidates", "quantum_algorithm_availability",
        "evidence_weight", "note"
    },
    "od_flow": {
        "origin_region", "city", "industry_group", "distance_km", "car_dependency",
        "time_cost", "non_energy_cost", "base_energy_cost_per_km", "flow_count"
    },
    "translation_parameters": {
        "industry_group", "max_lightweighting_rate", "response_curvature",
        "efficiency_translation", "low_multiplier", "base_multiplier",
        "high_multiplier", "note"
    },
    "model_controls": {"key", "value", "description"},
}


def resolve_path(input_dir: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        p = input_dir / name
        if p.exists():
            return p
    return None


def validate_table(path: Path, table_key: str) -> list[str]:
    errors: list[str] = []
    df = pd.read_csv(path)
    missing_cols = REQUIRED_COLUMNS[table_key] - set(df.columns)
    if missing_cols:
        errors.append(f"{table_key}: 欠落列 {sorted(missing_cols)}")
    if df.empty:
        errors.append(f"{table_key}: 行数が0である")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="統合分析環境の入力検証")
    parser.add_argument("--input_dir", required=True, help="入力ディレクトリ")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists():
        print(f"入力ディレクトリが存在しない: {input_dir}")
        raise SystemExit(1)

    all_errors: list[str] = []
    resolved = {}
    for key, candidates in REQUIRED_FILES.items():
        path = resolve_path(input_dir, candidates)
        if path is None:
            all_errors.append(f"{key}: 必要ファイルが見つからない（候補: {candidates}）")
        else:
            resolved[key] = path

    for key, path in resolved.items():
        all_errors.extend(validate_table(path, key))

    if all_errors:
        print("入力検証で問題を検出した。")
        for err in all_errors:
            print(f"- {err}")
        raise SystemExit(1)

    print("入力検証は正常終了した。")
    for key, path in resolved.items():
        print(f"- {key}: {path.name}")


if __name__ == "__main__":
    main()
