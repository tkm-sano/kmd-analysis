#!/usr/bin/env python3
"""Build the canonical Tokyo synthetic EVRP constraint-gap notebook."""

from __future__ import annotations

from pathlib import Path
import sys

import nbformat as nbf

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT / "constraint_evaluation"))

from validation_utils import find_repository_root


def section_card(
    number: int,
    title: str,
    *,
    purpose: str,
    question: str,
    inputs: str,
    method: str,
    output: str,
    assumptions: str,
    can_show: str,
    cannot_show: str,
) -> str:
    """Create the required eight-field section preamble."""

    return f"""## {number}. {title}

**Purpose**  
{purpose}

**Research question**  
{question}

**Input**  
{inputs}

**Method**  
{method}

**Output**  
{output}

**Assumptions**  
{assumptions}

**What this step can show**  
{can_show}

**What this step cannot show**  
{cannot_show}
"""


def main() -> None:
    """Write a clean, deterministic notebook source file."""

    root = find_repository_root(Path(__file__).resolve())
    output = root / "04_notebooks/500_20260711_tokyo_synthetic_evrp_constraint_gap_analysis.ipynb"
    notebook = nbf.v4.new_notebook()
    notebook.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    }
    cells: list[nbf.NotebookNode] = []

    cells.append(
        nbf.v4.new_markdown_cell(
            """# Tokyo Synthetic EVRP Scenario and Constraint-Gap Analysis

> 東京都の公開地理データとsynthetic customer configurationsを用いて、EV配送における各制約が、顧客の空間配置および分析条件の変化に対してどの程度拘束的になるかを探索的に評価する。

```text
公開データ
↓
synthetic scenario
↓
route proxy
↓
制約評価
↓
顧客配置・パラメータ感度
↓
量子VRP研究とのギャップ
↓
今後の研究優先課題
```

本分析は東京都の実配送失敗率、EVRP最適解、実際の充電行動、充電需要、充電器利用率、電力需要を推定しない。充電関連の評価は、候補地点への地理的アクセス、単純化した航続距離補完可能性、および一定出力による充電時間上限のproxyに限定する。
"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                0,
                "Research Question and Scope",
                purpose="研究上の位置づけ、対象、非対象、および成果の論理を固定する。",
                question="Which EV-delivery constraints become binding across synthetic customer configurations and analytical conditions?",
                inputs="東京都公開データのprocessed proxies、synthetic assumptions、local quantum-VRP extraction notes。",
                method="探索的なscenario/route-proxy/constraint-gap分析として研究境界を明示する。",
                output="研究質問、分析フロー、valid/invalid interpretationの境界。",
                assumptions="顧客はsynthetic、routeはproxy、結果はモデル条件付き。",
                can_show="どの制約・仮定・evidence gapを次に研究すべきか。",
                cannot_show="東京都の実配送失敗率、最適ルート、実際の充電・電力需要。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """from IPython.display import Markdown, display

display(Markdown(
    "**Primary research question:** Under explicit synthetic assumptions, which constraints are binding, "
    "which vary with customer configurations, and which remain insufficiently covered in the reviewed quantum-VRP evidence?"
))"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                1,
                "Environment and Configuration",
                purpose="repository root、依存環境、再現モード、ログ保存、実行状態を一元管理する。",
                question="Can the analysis be executed without a machine-specific path or stale notebook state?",
                inputs="Current kernel, `.git` marker, `00_project_management/001_20260712_requirements.txt`, environment variable `TOKYO_EVRP_REPRODUCE`。",
                method="`.git`からrootを探索し、package versionsを収集し、subprocess stdout/stderrを保存する。",
                output="Environment table、execution configuration、step status。",
                assumptions="Full regeneration is destructive/time-consuming and therefore opt-in。",
                can_show="実行環境と、どのモードで成果物が作られたか。",
                cannot_show="異なるOS/package combinationでの完全同一性能。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """from __future__ import annotations

import importlib.metadata as metadata
import os
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore", message="Pandas requires version.*numexpr")
warnings.filterwarnings("ignore", message="Pandas requires version.*bottleneck")

_start = Path.cwd().resolve()
_bootstrap_root = next(
    (candidate for candidate in (_start, *_start.parents) if (candidate / ".git").exists()),
    None,
)
if _bootstrap_root is None:
    raise RuntimeError(f"Repository root could not be found from {_start}.")
SCRIPTS_HINT = _bootstrap_root / "scripts"
if str(SCRIPTS_HINT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_HINT))

from validation_utils import (
    find_repository_root,
    generate_output_manifest,
    read_csv_checked,
    validate_output_manifest,
    write_csv_atomic,
)

ROOT = find_repository_root(Path.cwd())
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

REPRODUCE_ALL = os.environ.get("TOKYO_EVRP_REPRODUCE", "0") == "1"
RUN_SCRIPTS = REPRODUCE_ALL  # default False; explicit reproduction mode enables all stages
BOOTSTRAP_ITERATIONS = 1000
SEED_COUNT = 100
BOOTSTRAP_RANDOM_SEED = 20260711
LOG_DIR = ROOT / "outputs/logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STEP_STATUS: list[dict[str, object]] = []

def run_step(step_name: str, command: list[str], timeout_seconds: int = 1200) -> None:
    'Run one command, persist stdout/stderr, and fail loudly on a non-zero return code.'
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    safe_name = step_name.lower().replace(" ", "_").replace("/", "_")
    stdout_path = LOG_DIR / f"{safe_name}.stdout.log"
    stderr_path = LOG_DIR / f"{safe_name}.stderr.log"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    status = {
        "step_name": step_name,
        "status": "success" if completed.returncode == 0 else "failed",
        "return_code": completed.returncode,
        "duration_seconds": time.perf_counter() - started,
        "stdout_log": str(stdout_path.relative_to(ROOT)),
        "stderr_log": str(stderr_path.relative_to(ROOT)),
        "warning": completed.stderr[-2000:] if completed.returncode == 0 else "",
        "error": completed.stderr[-2000:] if completed.returncode else "",
    }
    STEP_STATUS.append(status)
    print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"Step {step_name!r} failed with return code {completed.returncode}.")

packages = [
    "pandas", "numpy", "scipy", "scikit-learn", "matplotlib", "geopandas",
    "shapely", "networkx", "jupyter", "jupyterlab", "notebook", "nbformat",
    "nbclient", "seaborn", "numexpr", "bottleneck",
]
environment = [{"component": "Python", "version": sys.version.split()[0]}]
environment += [{"component": "OS", "version": platform.platform()}]
for package in packages:
    try:
        version = metadata.version(package)
    except metadata.PackageNotFoundError:
        version = "Not installed"
    environment.append({"component": package, "version": version})
environment_df = __import__("pandas").DataFrame(environment)
display(environment_df)
print(f"Repository root: {ROOT}")
print(f"REPRODUCE_ALL={REPRODUCE_ALL}; RUN_SCRIPTS={RUN_SCRIPTS}")"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                2,
                "Input Data Inventory and Validation",
                purpose="存在だけでなく、bytes・header・schema・rows・numeric types・keysを検証する。",
                question="Are canonical processed inputs readable and structurally valid?",
                inputs="Population mesh、OCM connections、depot/vehicle snapshots、parameter/evidence registries。",
                method="共通`read_csv_checked`とSHA-256 provenance registryで検証する。",
                output="Input preview; full inventory is written by the analysis pipeline。",
                assumptions="Raw archives may be macOS dataless placeholders; validated processed fallback is permitted and recorded。",
                can_show="missing/zero-byte/header-only/bad schema/type/keyを区別できる。",
                cannot_show="raw public-data archivesからの再download・再前処理が常に可能であること。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """input_specs = {
    "population_mesh": (ROOT / "03_data/processed/413_20260705_estat_tokyo_mesh_population_cells.csv", ["mesh_code", "total_population"]),
    "charger_connections": (ROOT / "03_data/processed/428_20260705_open_charge_map_tokyo_boundary_clipped_connections.csv", ["connection_id", "latitude", "longitude"]),
    "depot_candidates": (ROOT / "03_data/processed/evrp_constraint_gap_inputs/419_20260711_depot_candidates_public_proxy_snapshot.csv", ["scenario_depot_id", "latitude", "longitude"]),
    "vehicle_specs": (ROOT / "03_data/processed/evrp_constraint_gap_inputs/423_20260711_vehicle_specs_public_source_snapshot.csv", ["scenario_vehicle_id", "battery_kwh", "catalog_range_km"]),
    "quantum_evidence": (ROOT / "03_data/processed/evrp_constraint_gap_inputs/421_20260711_quantum_vrp_evidence_registry.csv", ["reference_id", "paper_title", "page_or_section"]),
}
input_preview = []
for name, (path, required) in input_specs.items():
    frame = read_csv_checked(path, required_columns=required, require_nonempty=True)
    input_preview.append({
        "input": name,
        "path": str(path.relative_to(ROOT)),
        "rows": len(frame),
        "columns": len(frame.columns),
        "csv_state": frame.attrs["csv_state"],
        "max_missing_rate": float(frame.isna().mean().max()),
        "duplicate_rows": int(frame.duplicated().sum()),
    })
input_preview_df = __import__("pandas").DataFrame(input_preview)
display(input_preview_df)"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                3,
                "Open-data Preprocessing",
                purpose="processed fallbackを明示し、全CSV分析を一度だけ実行する。",
                question="Can the requested analysis be regenerated from validated local inputs without using stale outputs?",
                inputs="Section 2のvalidated inputs。",
                method="明示的再現モードではCSV-only analysis scriptを一回実行し、旧canonical CSV dirsを先に削除する。",
                output="`03_data/processed/**`、`06_outputs/tables/csv/**`、analysis manifest、step statuses。",
                assumptions="Raw-to-processed regeneration and road-network improved mode are unavailable; baseline fallback is explicit。",
                can_show="新しいrun IDに属する完全なCSV分析成果物。",
                cannot_show="raw source hydrationやOSM shortest pathの成功。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """analysis_manifest_path = ROOT / "06_outputs/reports/validation/analysis_output_902_20260711_v04_manifest.csv"
if RUN_SCRIPTS:
    run_step(
        "analysis_csv_generation",
        [
            sys.executable,
            str(ROOT / "05_src/constraint_evaluation/run_tokyo_synthetic_evrp_analysis.py"),
            "--reproduce",
            "--seed-count", str(SEED_COUNT),
            "--bootstrap-iterations", str(BOOTSTRAP_ITERATIONS),
            "--bootstrap-random-seed", str(BOOTSTRAP_RANDOM_SEED),
        ],
    )
else:
    if not analysis_manifest_path.exists():
        raise RuntimeError(
            "Canonical outputs are absent. Re-run with TOKYO_EVRP_REPRODUCE=1 for explicit full regeneration."
        )
    STEP_STATUS.append({"step_name": "analysis_csv_generation", "status": "validated_existing", "return_code": 0, "duration_seconds": 0.0, "stdout_log": "Not run", "stderr_log": "Not run", "warning": "", "error": ""})

preprocessing_status = read_csv_checked(
    ROOT / "03_data/processed/scenario/444_20260711_open_data_preprocessing_status.csv",
    required_columns=["step", "mode", "raw_source_status", "result", "limitation"],
    require_nonempty=True,
)
display(preprocessing_status)"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                4,
                "Scenario Definition",
                purpose="scenarioを未来物語ではなく分析条件の組合せとして定義する。",
                question="What customer, vehicle, charger, time, speed, and route-proxy conditions were compared?",
                inputs="Validated charger candidates、one coherent vehicle row、factor levels。",
                method="3 customer counts × 3 vehicle counts × 3 charger conditionsのfactorial design。",
                output="27 unique scenario configurations with explicit policies and IDs。",
                assumptions="All operating parameters are evidence-labelled assumptions, not forecasts。",
                can_show="customer count、vehicle count、customers/vehicle、およびcharger conditionの効果を分けて比較できる。",
                cannot_show="東京都の将来配送需要やfleet composition。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """scenario_configurations = read_csv_checked(
    ROOT / "03_data/processed/scenario/446_20260711_scenario_configurations.csv",
    required_columns=["scenario_id", "customer_count", "vehicle_count", "charger_condition", "usable_range_km"],
    unique_keys=["scenario_id"],
    require_nonempty=True,
)
display(scenario_configurations[[
    "scenario_id", "customer_count", "vehicle_count", "customers_per_vehicle",
    "charger_condition", "eligible_charger_candidate_count", "usable_range_km",
    "payload_capacity_kg", "operating_time_limit_min", "assumed_speed_kmh",
]].head(12))
print(f"Scenario configurations: {len(scenario_configurations)} (expected 27)")"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                5,
                "Synthetic Customer Generation",
                purpose="何がsyntheticで、何をseedごとに変化させたかを保存する。",
                question="How do results vary when population-weighted customer locations, demand, and service time change?",
                inputs="e-Stat mesh population weights、explicit synthetic distributions、100 seed identifiers。",
                method="locationsはpopulation-weighted sample、demand/serviceはdiscrete-uniform synthetic draws。",
                output="17,500 customer rows、300 customer-count-specific configurations、randomization registry。",
                assumptions="Customer locations are not observed orders; demand and service time are not operational measurements。",
                can_show="特定配置依存とseedを変えて共通する傾向。",
                cannot_show="実顧客、実貨物重量、実サービス時間、独立な2,700試行。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """customers = read_csv_checked(
    ROOT / "03_data/processed/scenario/447_20260711_synthetic_customers.csv",
    required_columns=["customer_configuration_id", "seed", "customer_id", "latitude", "longitude", "demand_kg", "service_time_min", "evidence_status"],
    unique_keys=["customer_configuration_id", "customer_id"],
    require_nonempty=True,
)
randomization = read_csv_checked(
    ROOT / "03_data/processed/scenario/443_20260711_monte_carlo_randomization_registry.csv",
    required_columns=["seed", "customer_locations_randomized", "customer_demands_randomized", "charger_availability_randomized", "speed_randomized"],
    require_nonempty=True,
)
display(customers.head())
display(randomization.head())
print(f"Unique seed identifiers: {customers['seed'].nunique()}")
print(f"Customer-count-specific configurations: {customers['customer_configuration_id'].nunique()}")"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                6,
                "Route Proxy Construction",
                purpose="customer assignment、visit order、distance definitionを追跡可能にする。",
                question="What does the route proxy represent, and how does its distance vary?",
                inputs="Synthetic customers、public logistics-facility depot candidates、customer/vehicle factors。",
                method="KMeansで車両別割当てを近似し、nearest neighborで訪問順を近似する。",
                output="Base routes、route members、proxy edges、haversine/road-adjusted/network fields。",
                assumptions="Road multiplier=1.25 baseline; network distance is Data unavailable。",
                can_show="仮訪問順序、顧客数/route、proxy distance distribution。",
                cannot_show="EVRP最適解、時間窓/SOC最適化、道路上の実経路。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """routes = read_csv_checked(
    ROOT / "03_data/processed/route_proxy/440_20260711_route_proxy_results.csv",
    required_columns=["scenario_route_proxy_id", "base_route_proxy_id", "haversine_distance_km", "road_adjusted_distance_km", "network_distance_km", "route_proxy_distance_km", "route_proxy_limitation"],
    unique_keys=["scenario_route_proxy_id"],
    require_nonempty=True,
)
distance_summary = read_csv_checked(
    ROOT / "03_data/processed/route_proxy/437_20260711_route_distance_summary.csv",
    required_columns=["mean", "median", "standard_deviation", "percentile_5", "percentile_95", "maximum", "distance_unmet_rate"],
    require_nonempty=True,
)
display(routes[["scenario_route_proxy_id", "customer_count_on_route", "route_proxy_distance_km", "route_total_demand_kg", "route_proxy_limitation"]].head())
display(distance_summary)"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                7,
                "Constraint Evaluation",
                purpose="各未充足率のnumerator/denominatorと未評価項目を分離する。",
                question="Which constraints became binding under the current synthetic assumptions?",
                inputs="Condition-route proxy results。",
                method="payload、operating time、range、candidate accessを全routeで評価し、assisted range/durationは適格routeだけを分母にする。",
                output="Long constraint evaluations、case rates、route-weighted summary、payload/time diagnostics。",
                assumptions="SOC trajectory、visit-level time windows、waiting/detour are not evaluated。",
                can_show="モデル内の制約拘束性と定義別分母。",
                cannot_show="実配送の失敗率、SOC feasibility、driver-hours compliance。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """constraint_summary = read_csv_checked(
    ROOT / "03_data/processed/constraints/407_20260711_constraint_summary.csv",
    required_columns=["constraint_name", "route_weighted_unmet_rate", "case_weighted_unmet_rate", "evaluated_route_count", "numerator_definition", "denominator_definition", "evidence_status"],
    require_nonempty=True,
)
display(constraint_summary[[
    "constraint_name", "route_weighted_unmet_rate", "case_weighted_unmet_rate",
    "confidence_interval_lower", "confidence_interval_upper", "evaluated_route_count",
    "spatial_sensitivity", "evidence_status",
]])
display(read_csv_checked(ROOT / "03_data/processed/constraints/409_20260711_payload_diagnostics.csv", require_nonempty=True))
display(read_csv_checked(ROOT / "03_data/processed/constraints/412_20260711_time_constraint_diagnostics.csv", require_nonempty=True))"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                8,
                "Monte Carlo and Sensitivity Analysis",
                purpose="配置依存性、paired design、仮定感度を統計的に分離する。",
                question="Which findings persist across seeds, and which are driven by analytical assumptions?",
                inputs="100 paired seed clusters、2,700 conditional cases、13 requested sensitivity levers。",
                method="seed-cluster bootstrap 1,000回とthree-level OAT sensitivity。",
                output="Route/case-weighted rates、95% CI、seed variability、sensitivity response。",
                assumptions="Bootstrap unit is seed; all conditions within a sampled seed are retained。",
                can_show="配置変動とパラメータ応答の相対的重要性。",
                cannot_show="2,700独立試行、causal effect、calibrated operational elasticities。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """statistics = read_csv_checked(
    ROOT / "06_outputs/reports/validation/687_20260711_statistical_validation.csv", require_nonempty=True
)
sensitivity = read_csv_checked(
    ROOT / "03_data/processed/constraints/411_20260711_sensitivity_summary.csv",
    required_columns=["parameter", "level", "constraint_name", "route_weighted_unmet_rate", "unmet_rate_change_from_base"],
    require_nonempty=True,
)
display(statistics)
display(
    sensitivity.assign(abs_change=sensitivity["unmet_rate_change_from_base"].abs())
    .sort_values("abs_change", ascending=False)
    .head(15)
)"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                9,
                "Charger-access and Charging-assisted Feasibility",
                purpose="充電関連評価を候補アクセス・単純化したrange support・duration proxyに限定する。",
                question="Is a screened charger candidate geographically near, and can a simplified support assumption cover range exceedance?",
                inputs="OCM candidate records、route-proxy nodes、condition-specific thresholds、reported power。",
                method="nearest candidate distance、two-usable-range rule、constant reported-power duration。",
                output="Candidate counts、nearest distance、geographic access、assisted-range/duration feasibility。",
                assumptions="Actual public access、availability、queue、failure、operating hours、arrival SOC、stop choice are unknown/not evaluated。",
                can_show="設定した地理閾値と単純化条件で候補支援が可能か。",
                cannot_show="実際の充電時刻・地点選択・量・需要・利用率・電力負荷。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """charger_definitions = read_csv_checked(
    ROOT / "03_data/processed/charger_access/402_20260711_charger_condition_definitions.csv",
    required_columns=["charger_condition", "eligible_charger_candidate_count", "maximum_access_distance_km", "condition_definition"],
    require_nonempty=True,
)
charger_results = read_csv_checked(
    ROOT / "03_data/processed/charger_access/404_20260711_route_charger_access_results.csv",
    required_columns=["charger_geographically_accessible", "charger_arrival_soc_feasible", "charging_assisted_range_feasible", "charging_duration_feasible"],
    require_nonempty=True,
)
display(charger_definitions)
display(charger_results.head())
display(Markdown(
    "**Boundary:** this section does not infer an actual charging event, time series, station choice, demand, utilization, or grid load."
))"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                10,
                "Quantum VRP Evidence Comparison",
                purpose="operational requirementsとreviewed quantum-VRP evidenceを報告粒度を保って比較する。",
                question="Which operationally important requirements remain insufficiently covered in the reviewed quantum-VRP evidence?",
                inputs="Seven local extraction notes and normalized conservative registry。",
                method="reported facts only; missing resource/performance values are `Not reported`; route count/qubit width/hardware execution are not equated。",
                output="Paper-row evidence CSV and requirement gap table。",
                assumptions="This is a bounded evidence set, not a systematic review of all literature。",
                can_show="reviewed evidence内のcoverageとreporting gap。",
                cannot_show="未報告項目の推定、全量子VRP研究における不存在、量子優位性。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """quantum_evidence = read_csv_checked(
    ROOT / "03_data/processed/quantum_gap/434_20260711_quantum_vrp_evidence.csv",
    required_columns=["reference_id", "paper_title", "authors", "year", "doi", "url", "page_or_section", "execution_type"],
    require_nonempty=True,
)
quantum_gap = read_csv_checked(
    ROOT / "06_outputs/tables/csv/690_20260711_table_03_quantum_vrp_gap.csv",
    required_columns=["evaluation_item", "quantum_vrp_coverage", "evidence_gap", "gap_basis", "reference_id"],
    require_nonempty=True,
)
display(quantum_evidence[["reference_id", "paper_title", "problem_type", "customer_count", "vehicle_count", "execution_type", "classical_baseline"]])
display(quantum_gap[["evaluation_item", "analysis_importance", "quantum_vrp_coverage", "evidence_gap", "gap_basis"]])"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                11,
                "Research Presentation Summary Tables",
                purpose="分析CSVから研究発表用5表と17図を再現する。",
                question="Can presentation claims be traced to unrounded analysis CSVs?",
                inputs="Canonical analysis CSVs only。",
                method="Rendererを一度だけ実行し、CSVの値は未丸め、PNG/SVGでのみ表示整形する。",
                output="6 table CSV/PNG/SVG (Table 5 full/slide) and 17 figure PNG/SVG/source-data CSV。",
                assumptions="Japanese font is selected from installed fonts; all figures are explanatory, not operational predictions。",
                can_show="研究質問に対応する表・図とそのsource-data traceability。",
                cannot_show="source CSVに存在しない固定数値や実運用の確定的結論。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """render_manifest_path = ROOT / "06_outputs/reports/validation/render_output_902_20260711_v04_manifest.csv"
if RUN_SCRIPTS:
    run_step(
        "csv_driven_rendering",
        [sys.executable, str(ROOT / "05_src/visualization/render_tokyo_synthetic_evrp_outputs.py"), "--reproduce"],
    )
else:
    if not render_manifest_path.exists():
        raise RuntimeError(
            "Rendered outputs are absent. Re-run with TOKYO_EVRP_REPRODUCE=1 for explicit full regeneration."
        )
    STEP_STATUS.append({"step_name": "csv_driven_rendering", "status": "validated_existing", "return_code": 0, "duration_seconds": 0.0, "stdout_log": "Not run", "stderr_log": "Not run", "warning": "", "error": ""})

table_files = sorted((ROOT / "06_outputs/tables/csv").glob("table_*.csv"))
figure_files = sorted((ROOT / "06_outputs/06_outputs/figures/active/active/png").glob("figure_*.png"))
display(__import__("pandas").DataFrame({"table_csv": [str(path.relative_to(ROOT)) for path in table_files]}))
print(f"Table CSVs: {len(table_files)}; PNG figures: {len(figure_files)}")
display(read_csv_checked(ROOT / "06_outputs/tables/csv/691_20260711_table_04_integrated_research_summary.csv", require_nonempty=True))"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                12,
                "Interpretation and Limitations",
                purpose="各数値のvalid interpretation、invalid interpretation、未評価項目を明示する。",
                question="What can and cannot be claimed from each model-conditional result?",
                inputs="Table 5、assumptions/limitations registry、constraint evidence statuses。",
                method="Observed value、definition、assumption、evidence qualityを一体で表示する。",
                output="Full/slide interpretation tables and limitations registry。",
                assumptions="Low unmet rate is not evidence that a constraint is absent operationally。",
                can_show="発表で言えることと言えないこと。",
                cannot_show="synthetic/proxy evidenceをreal-world observationへ一般化すること。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """interpretation_table = read_csv_checked(
    ROOT / "06_outputs/tables/csv/692_20260711_table_05_constraint_interpretation_full.csv",
    required_columns=["constraint_name", "observed_value", "valid_interpretation", "invalid_interpretation", "evidence_status"],
    require_nonempty=True,
)
limitations = read_csv_checked(
    ROOT / "03_data/processed/scenario/442_20260711_assumptions_and_limitations.csv",
    required_columns=["topic", "limitation", "status"],
    require_nonempty=True,
)
display(interpretation_table[["constraint_name", "observed_value", "evidence_status", "valid_interpretation", "invalid_interpretation"]])
display(limitations)"""
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            section_card(
                13,
                "Validation and Export Summary",
                purpose="全工程、統計、出力、research integrityを最終検証する。",
                question="Did every required stage and artifact complete in the current run without forbidden output classes?",
                inputs="Execution statuses、analysis/render manifests、canonical output directories、integrity checks。",
                method="hash/size/mtime/CSV shape検証、count assertions、forbidden filename scan、explicit false flags。",
                output="Final manifest、notebook status、validation summary。",
                assumptions="Deprecated outputs are excluded from active validation。",
                can_show="Run All success/failure、current artifact completeness、research-scope integrity。",
                cannot_show="deprecated historical artifactsが正しいこと、外部data hydration。",
            )
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """analysis_manifest = read_csv_checked(
    analysis_manifest_path,
    required_columns=["analysis_run_id", "path", "size_bytes", "sha256", "row_count", "column_count", "status"],
    require_nonempty=True,
)
render_manifest = read_csv_checked(
    render_manifest_path,
    required_columns=["path", "size_bytes", "sha256", "status"],
    require_nonempty=True,
)
validate_output_manifest(analysis_manifest.drop(columns=["analysis_run_id"]), root=ROOT)
validate_output_manifest(render_manifest, root=ROOT)

canonical_dirs = [
    ROOT / "outputs/data",
    ROOT / "outputs/tables",
    ROOT / "outputs/figures",
    ROOT / "outputs/logs",
    ROOT / "outputs/validation",
]
final_manifest_path = ROOT / "06_outputs/reports/validation/final_output_902_20260711_v04_manifest.csv"
final_manifest = generate_output_manifest(
    canonical_dirs,
    manifest_path=final_manifest_path,
    root=ROOT,
    include_csv_shape=True,
)

counts = {
    "table_csv_count": len(list((ROOT / "06_outputs/tables/csv").glob("table_*.csv"))),
    "table_png_count": len(list((ROOT / "06_outputs/tables/png").glob("table_*.png"))),
    "table_svg_count": len(list((ROOT / "06_outputs/tables/svg").glob("table_*.svg"))),
    "figure_png_count": len(list((ROOT / "06_outputs/06_outputs/figures/active/active/png").glob("figure_*.png"))),
    "figure_svg_count": len(list((ROOT / "06_outputs/06_outputs/figures/active/active/svg").glob("figure_*.svg"))),
    "figure_source_csv_count": len(list((ROOT / "06_outputs/06_outputs/figures/active/active/source_data").glob("figure_*.csv"))),
}
assert counts == {
    "table_csv_count": 6,
    "table_png_count": 6,
    "table_svg_count": 6,
    "figure_png_count": 17,
    "figure_svg_count": 17,
    "figure_source_csv_count": 17,
}, counts

forbidden_name_tokens = [
    "charging_pathway", "charging_event_pathway", "charging_demand", "grid_load",
    "potential_charging_event", "route_to_charging_pathway",
]
active_relative_paths = [str(path.relative_to(ROOT)).lower() for path in ROOT.glob("outputs/**/*") if path.is_file()]
for token in forbidden_name_tokens:
    matches = [path for path in active_relative_paths if token in path]
    if matches:
        raise RuntimeError(f"Forbidden active output token {token!r}: {matches}")

integrity = read_csv_checked(
    ROOT / "06_outputs/reports/validation/686_20260711_research_integrity_checks.csv",
    required_columns=["check", "status", "observed"],
    require_nonempty=True,
)
assert integrity["status"].eq("pass").all()
step_status_df = __import__("pandas").DataFrame(STEP_STATUS)
assert step_status_df["status"].isin(["success", "validated_existing"]).all()
write_csv_atomic(step_status_df, ROOT / "06_outputs/reports/validation/notebook_679_20260711_execution_status.csv")

validation_summary = __import__("pandas").DataFrame([
    {
        "validation_status": "success",
        "analysis_run_id": analysis_manifest["analysis_run_id"].iloc[0],
        "python_version": sys.version.split()[0],
        "independent_seed_count": int(statistics["independent_seed_count"].iloc[0]),
        "conditional_evaluation_count": int(statistics["conditional_evaluation_count"].iloc[0]),
        "condition_route_evaluation_count": int(statistics["condition_route_evaluation_count"].iloc[0]),
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        **counts,
        "charging_pathway_generated": False,
        "charging_demand_estimation_generated": False,
        "charging_event_timeline_generated": False,
        "grid_load_estimation_generated": False,
    }
])
write_csv_atomic(validation_summary, ROOT / "06_outputs/reports/validation/681_20260711_final_validation_summary.csv")
final_manifest = generate_output_manifest(
    canonical_dirs,
    manifest_path=final_manifest_path,
    root=ROOT,
    include_csv_shape=True,
)

display(Markdown("## ✅ Validation passed"))
display(step_status_df)
display(validation_summary)
print("Charging pathway generated: False")
print("Charging-demand estimation generated: False")
print("Charging-event timeline generated: False")
print("Grid-load estimation generated: False")"""
        )
    )

    notebook.cells = cells
    nbf.write(notebook, output)
    print(output)


if __name__ == "__main__":
    main()
