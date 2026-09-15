#!/usr/bin/env python3
"""Build the R24 Planning Horizon semantic decision; no scientific data generation."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
START_SHA = "5bb6829ced63195dcbd3ce5785c8e66331994b6b"


def rel(path):
    return str(path.relative_to(ROOT))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(name, content):
    (OUT / name).write_text(content.strip() + "\n", encoding="utf-8")


def write_csv(name, fieldnames, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == START_SHA
    assert subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).strip() == ""

    inspected_paths = [
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/R24_GATE_A_REQUEST_EVENT_TEMPORAL_EVIDENCE.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/PLANNING_HORIZON_OPTIONS.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/GATE_A_ACCEPTANCE_CRITERIA.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/GATE_A_STOP_REASSESSMENT.csv",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/LEGACY_DISPATCH_CONFLICTS.csv",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/REQUEST_SCHEMA_PROPOSAL.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/ELIGIBLE_STOP_PREREQUISITES.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/EVIDENCE_STATISTICS.json",
        ROOT / "reproducibility/outputs/traffic_simulation/end_to_end_workflow_feasibility_audit/20260914_v2/END_TO_END_WORKFLOW_AUTHORITY.md",
        ROOT / "reproducibility/outputs/traffic_simulation/end_to_end_workflow_feasibility_audit/20260914_v2/END_TO_END_WORKFLOW_FEASIBILITY_AUDIT.md",
        ROOT / "reproducibility/outputs/traffic_simulation/end_to_end_workflow_feasibility_audit/20260914_v2/INSTANCE_GENERATION_POLICY.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_data_gate_execution_pipeline/20260914_v1/R24_DATA_GATE_EXECUTION_PIPELINE.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_data_gate_execution_pipeline/20260914_v1/GATE_A_SERVICE_EVENT_BATCH.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/R24_PROBLEM_DATA_SPEC_FREEZE_REVIEW.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/DISPATCH_BATCH_SPEC.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/CUSTOMER_SERVICE_STOP_SPEC.md",
        ROOT / "reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/R24_DATA_SPECIFICATION_DRAFT.md",
        ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv",
        ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/request_building_mapping.csv",
        ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv",
        ROOT / "reproducibility/outputs/traffic_simulation/demand/candidate_validation/20260909_r03_edge_mapping/candidate_validation_manifest.json",
        ROOT / "reproducibility/outputs/traffic_simulation/demand/candidate_validation/20260909_r03_edge_mapping/candidate_delivery_edge_connections.csv",
    ]
    inspected = []
    for path in inspected_paths:
        assert path.is_file(), path
        inspected.append({"file": rel(path), "sha256": sha256(path), "bytes": path.stat().st_size, "inspection": "FULL_TEXT_OR_FULL_BYTE_HASH"})
    prior_hashes = {
        row["file"]: row["sha256"]
        for row in csv.DictReader(
            (ROOT / "reproducibility/outputs/traffic_simulation/r24_gate_a_request_event_temporal_evidence/20260915_v1/INSPECTED_FILES.csv").open(encoding="utf-8")
        )
    }
    assert all(prior_hashes.get(row["file"], row["sha256"]) == row["sha256"] for row in inspected)
    write_csv("INSPECTED_FILES.csv", ["file", "sha256", "bytes", "inspection"], inspected)

    daily_path = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv"
    with daily_path.open(newline="", encoding="utf-8") as stream:
        daily = list(csv.DictReader(stream))
    assert len(daily) == 73547
    assert {row["evaluation_date"] for row in daily} == {"2026-01-01"}
    assert sum(int(row["parcel_equivalent"]) for row in daily) == 82246
    assert len({row["request_id"] for row in daily}) == len(daily)

    mapping_path = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/request_building_mapping.csv"
    with mapping_path.open(newline="", encoding="utf-8") as stream:
        mapping = list(csv.DictReader(stream))
    assert len(mapping) == 73547
    assigned = [row for row in mapping if row["assignment_status"] == "assigned"]
    exceptions = [row for row in mapping if row["assignment_status"] != "assigned"]
    assert (len(assigned), sum(int(row["parcel_equivalent"]) for row in assigned)) == (73200, 81859)
    assert (len(exceptions), sum(int(row["parcel_equivalent"]) for row in exceptions)) == (347, 387)

    stops_path = ROOT / "03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv"
    with stops_path.open(newline="", encoding="utf-8") as stream:
        stops = list(csv.DictReader(stream))
    assert len(stops) == 39956
    assert len({row["stop_id"] for row in stops}) == len(stops)

    options = [
        {
            "option": "A_ONE_SYNTHETIC_DAY_AS_SOURCE_HORIZON",
            "decision": "ADOPT_AS_SOURCE_HORIZON",
            "data_support": "DATA_SUPPORTED",
            "reproducibility": "HIGH; exact evaluation_date filter on immutable saved snapshot",
            "arbitrariness": "LOW for source boundary; no invented sub-day membership",
            "operational_validity": "NONE CLAIMED; synthetic day is not carrier day/dispatch/shift",
            "instance_generation": "HIGH; defines C_source before eligibility and sampling; does not force all 39956 into one instance",
            "future_models": "COMPATIBLE as lineage boundary; VRPTW/EVRP need separate time/energy evidence",
            "reason": "Only request-linked temporal evidence is 2026-01-01 at day resolution",
        },
        {
            "option": "B_ABSTRACT_PLANNING_HORIZON_PLUS_DAY_ELIGIBLE_POPULATION",
            "decision": "ADOPT_AS_OPTIMIZATION_SEMANTIC",
            "data_support": "DATA_SUPPORTED_WITH_LIMITATIONS",
            "reproducibility": "HIGH when source snapshot/date and future eligible manifest hashes are bound",
            "arbitrariness": "LOW; keeps n/seed/structure in Instance Generation",
            "operational_validity": "CONTROLLED BENCHMARK ONLY",
            "instance_generation": "HIGH; C_(n,r) is a benchmark subset of C_eligible",
            "future_models": "HIGH; dispatch/wave/shift can be later typed specializations without changing source lineage",
            "reason": "Separates source temporal boundary from a finite computational instance",
        },
        {
            "option": "C_SYNTHETIC_DAY_EQUALS_R24_OPERATIONAL_HORIZON",
            "decision": "REJECT",
            "data_support": "MODEL_ASSUMPTION_REQUIRED",
            "reproducibility": "Date membership reproducible; operational interpretation is not",
            "arbitrariness": "HIGH; silently treats 39956 proxies as one operating horizon",
            "operational_validity": "UNSUPPORTED",
            "instance_generation": "LOW; conflates source population with instance and fleet/load/tour semantics",
            "future_models": "LOW; no clocks, shifts, windows, fleet or reload evidence",
            "reason": "Would imply unsupported carrier-day, one-tour-per-vehicle and capacity meanings",
        },
        {
            "option": "D_ONE_DISPATCH",
            "decision": "REJECT_CURRENT_BASELINE_RETAIN_FUTURE_OPTION",
            "data_support": "UNSUPPORTED",
            "reproducibility": "NONE; no membership rule or IDs",
            "arbitrariness": "HIGH if invented",
            "operational_validity": "UNSUPPORTED",
            "instance_generation": "NOT CURRENTLY COMPATIBLE",
            "future_models": "POSSIBLE only with new operational evidence/version",
            "reason": "No dispatch/operator/departure evidence",
        },
        {
            "option": "D_ONE_WAVE",
            "decision": "REJECT_CURRENT_BASELINE_RETAIN_FUTURE_OPTION",
            "data_support": "UNSUPPORTED",
            "reproducibility": "NONE; no request-linked bucket",
            "arbitrariness": "HIGH if day is split",
            "operational_validity": "UNSUPPORTED",
            "instance_generation": "NOT CURRENTLY COMPATIBLE",
            "future_models": "POSSIBLE only with new timing evidence/version",
            "reason": "No wave/time-bucket membership",
        },
        {
            "option": "D_ONE_SHIFT",
            "decision": "REJECT_CURRENT_BASELINE_RETAIN_FUTURE_OPTION",
            "data_support": "UNSUPPORTED",
            "reproducibility": "NONE; no shift boundary",
            "arbitrariness": "HIGH if duration is invented",
            "operational_validity": "UNSUPPORTED",
            "instance_generation": "NOT CURRENTLY COMPATIBLE",
            "future_models": "POSSIBLE only with working-time evidence/version",
            "reason": "No worker/vehicle shift evidence",
        },
    ]
    write_csv("PLANNING_HORIZON_OPTION_COMPARISON.csv", list(options[0]), options)

    four_axis = [
        {"option": row[0], "arbitrariness": row[1], "validity": row[2], "compatibility": row[3], "grounding_representativeness": row[4]}
        for row in [
            ("A synthetic day source horizon", "LOW: observed saved date filter; snapshot selection inherited", "HIGH synthetic construct validity; NO operational-day validity claim", "HIGH with saved demand, eligibility, all three instance suites; future VRPTW/EVRP require new fields", "Ota/statistical/geographic synthetic grounding; not observed or representative operations"),
            ("B abstract optimization horizon", "LOW/MEDIUM: later instance policy choices remain explicit downstream", "HIGH for controlled benchmark finite-set semantics", "HIGH with R24 and extensible typed horizons", "Benchmark representativeness only; no carrier claim"),
            ("C day equals operational horizon", "HIGH hidden fleet/tour/load assumptions", "LOW operational and construct validity", "LOW at 39956 proxy scale without m/Q/events; conflicts with stage separation", "Synthetic Ota grounding cannot establish an operating day"),
            ("D one dispatch", "HIGH without manifests", "UNSUPPORTED", "BLOCKED for current baseline", "No operator/depot dispatch observation"),
            ("D one wave", "HIGH without request times", "UNSUPPORTED", "BLOCKED for current baseline/VRPTW", "Aggregate survey hours are not request membership"),
            ("D one shift", "HIGH without workforce evidence", "UNSUPPORTED", "BLOCKED for current baseline", "No observed worker/vehicle shift"),
        ]
    ]
    write_csv("FOUR_AXIS_PLANNING_HORIZON_AUDIT.csv", list(four_axis[0]), four_axis)

    migration = [
        ("reproducibility/outputs/traffic_simulation/r24_data_gate_execution_pipeline/20260914_v1/R24_DATA_GATE_EXECUTION_PIPELINE.md", "15,49", "REWRITE", "batch service events and stale NEXT", "finite required benchmark customer nodes within planning_horizon_id; NEXT points to completed horizon decision then routing-proxy remediation"),
        ("reproducibility/outputs/traffic_simulation/r24_data_gate_execution_pipeline/20260914_v1/GATE_A_SERVICE_EVENT_BATCH.md", "A3,A5,A6", "REWRITE", "mandatory dispatch-batch membership", "source-horizon membership plus optional typed dispatch_id; preserve event/access and conservation gates"),
        ("reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/R24_PROBLEM_DATA_SPEC_FREEZE_REVIEW.md", "sections 2-4", "REWRITE", "one dispatch batch / within batch", "source horizon plus separate optimization instance; preserve one tour per used vehicle and no reload within each instance"),
        ("reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/DISPATCH_BATCH_SPEC.md", "whole document", "REWRITE", "dispatch as mandatory horizon", "retain as conditional dispatch specialization; introduce general Planning Horizon contract in a new version"),
        ("reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/R24_DATA_SPECIFICATION_DRAFT.md", "batches/events/demands/instance_manifest", "REWRITE", "required batch_id/horizon_semantics=one_dispatch_batch", "planning_horizon_id required; dispatch_id nullable/conditional; source horizon and instance manifest separated"),
        ("reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/CUSTOMER_SERVICE_STOP_SPEC.md", "event cardinalities", "REWRITE", "within one batch", "within one optimization instance/planning-horizon specialization; no building/event/access equality"),
        ("reproducibility/outputs/traffic_simulation/pipeline_authority_and_r24_capacity_plan/20260914_v1/R24_CAPACITY_PIPELINE.md", "9-10", "REWRITE", "proposed one-dispatch horizon and within-batch load", "controlled optimization instance; no operational dispatch claim"),
        ("reproducibility/outputs/traffic_simulation/pipeline_authority_and_r24_capacity_plan/20260914_v1/CUSTOMER_TERMINOLOGY.md", "16", "REWRITE", "dispatch_batch_id mandatory-looking contract field", "planning_horizon_id required; dispatch_id conditional"),
        ("reproducibility/outputs/traffic_simulation/r24_demand_capacity_authority/20260914_v2/representative_instance_schema.md", "horizon_days=1", "MARK_SUPERSEDED", "day scalar tied to legacy assumed-load instance", "not reusable as current R24 horizon schema"),
        ("reproducibility/outputs/traffic_simulation/r24_demand_capacity_authority/20260914_v2/build_review.py and validate_review.py", "horizon_days assertions", "MARK_SUPERSEDED", "legacy generated/validated one-day assumption", "do not reuse for R24; preserve files unchanged"),
        ("R05/R07/R15-R23 archived demand/time-window/route fixtures", "historical scope", "KEEP_HISTORICAL", "old selections, fixture times and route contexts", "retain for original evidence/regression only; never infer current horizon membership"),
    ]
    write_csv(
        "LEGACY_DISPATCH_MIGRATION.csv",
        ["file_or_scope", "location", "classification", "current_issue", "minimal_migration"],
        [dict(zip(["file_or_scope", "location", "classification", "current_issue", "minimal_migration"], row)) for row in migration],
    )

    write_text("R24_PLANNING_HORIZON_DECISION.md", """
# R24 Planning Horizon decision
Decision ID: R24-PLANNING-HORIZON-20260915-v1. Date: 2026-09-15 JST.
Scope: PLANNING HORIZON DECISION / SEMANTIC FREEZE ONLY.

Verdict: **PLANNING_HORIZON_FROZEN_WITH_LIMITATIONS**.

`PLANNING_HORIZON = designated synthetic day (2026-01-01) as source horizon; optimization instances are separately generated controlled benchmark subsets of a later accepted eligible routing-proxy-stop population.`

`NEXT_EXECUTABLE_TASK = finalize routing-proxy stop policy`

## Frozen meaning

Planning Horizon defines the source temporal and demand-universe boundary for one downstream instance-construction program. The immutable source boundary is all 73,547 saved synthetic household-day demand records dated 2026-01-01 (82,246 parcel-equivalents), with 73,200 mapped records / 81,859 units and 347 records / 387 units retained as explicit mapping exceptions. The 39,956 positive mapped building-day aggregates are a candidate routing-proxy population, not the horizon itself and not yet eligible customer nodes.

The horizon is not an actual carrier operating day, dispatch, wave, shift, route or observed operational period. It creates no clock time. It does not require all 39,956 candidate locations to enter one CVRP. `C_eligible` is established after the routing-proxy/event/exception remediation; Instance Generation later selects finite `C_(n,r) subset C_eligible` under repeated-random, controlled-structural or fixed-anchor policies. n, seeds, replicates and spatial structure are not Planning Horizon decisions.

This combines Option A for the source boundary with Option B for optimization semantics. Option C is rejected: treating the whole synthetic day as an operational R24 horizon would add unsupported fleet, capacity, one-tour and service-event meanings at 39,956-stop scale. Option D dispatch/wave/shift forms remain future typed specializations and are unsupported for the current baseline.

## Benchmark claims

R24 remains an **Ota-grounded controlled benchmark**. Permitted claims: Ota geographic grounding, saved synthetic-demand grounding, conditional Routing Baseline grounding and controlled computational comparison. Prohibited claims: one real dispatch, observed route, actual carrier day, or statistical representation of Ota delivery operations. Snapshot continuity does not repair the original generator provenance.

## Dependencies and Gate A effect

Planning Horizon/source-membership remediation is closed by this decision. It can freeze before service-event or routing-proxy adoption because it selects source records by an existing date and makes no claim about visit identity. Physical-stop evidence is likewise not needed to define this source universe. Gate A remains `GATE_A_REQUIRES_TARGETED_REMEDIATION`: the next dependency is explicit adoption/rejection of the `ROUTING_PROXY_STOP` policy, followed by the compatible benchmark service-event/customer-node abstraction, conservation/exception contract and formal Gate A sign-off. Their policies may narrow `C_eligible` but cannot rewrite the frozen date/source universe silently.

Observed entrances are not required merely to freeze this controlled source horizon. A future routing-proxy decision may accept modeled access with limitations; this decision does not do so. Parcel mass, capacity and vehicle class are later gates. Generator STOP remains `BLOCKS_REGENERATION_ONLY`.

No demand, timestamp, membership, event, access, eligible population or instance was generated. Historical artifacts were not edited. The migration CSV is a versioned amendment proposal only.
""")

    write_text("SOURCE_HORIZON_VS_INSTANCE.md", """
# Source Horizon versus Optimization Instance

`Source Horizon != Optimization Instance` and `Synthetic Day != Observed Carrier Day`.

| Object | Frozen meaning | Identity/membership | Not implied |
|---|---|---|---|
| Source Horizon | saved synthetic demand universe dated 2026-01-01 | exact `evaluation_date` filter plus snapshot hashes and explicit unmapped exceptions | dispatch, shift, route, fleet feasibility, all-day CVRP |
| Candidate proxy population | 39,956 positive mapped building-day aggregates with saved road relations | existing stable source IDs; still candidate-only | physical entrances or service events |
| Eligible population `C_eligible` | later accepted routing-proxy/customer-node frame inside the source horizon | future versioned manifest/hash after Gate A remediation | sample size, seed or selected instance |
| Optimization Instance `C_(n,r)` | finite controlled benchmark subset of `C_eligible` | selected IDs and future instance manifest | one carrier day/dispatch or Ota-representative operation |

Flow: Designated Synthetic Day -> `C_eligible` -> Instance Generation (repeated random / controlled structural / fixed anchor) -> Optimization Instance.

The horizon owns temporal source inclusion. Eligibility owns admissible proxy/customer records and exceptions. Instance Generation owns n, RNG/seed/replicate, clustering/dispersion rules, anchors and selected IDs. Later vehicle/load/cost gates complete a concrete CVRP instance; this decision supplies none of them.
""")

    write_text("PLANNING_HORIZON_STAGE_CONTRACT.md", """
# Planning Horizon stage contract

## Inputs

Immutable daily-demand snapshot and hashes; `evaluation_date`; request-unit dictionary; saved mapping exception ledger; parent authority and decision IDs.

## Frozen output

`planning_horizon_id=R24-SOURCE-DAY-2026-01-01-v1`; `horizon_type=DESIGNATED_SYNTHETIC_DAY_SOURCE`; date 2026-01-01; day-level resolution; source snapshot references; included-record rule; mapped/unmapped accounting; classification `MODEL_BASED_SYNTHETIC`; observation status `SYNTHETIC`; operational interpretation `NONE`; decision version/hash.

The ID above names the semantic decision, not a newly materialized membership file. Saved source records remain authoritative bytes.

## Invariants

- Include every saved demand record whose `evaluation_date` equals 2026-01-01; do not invent sub-day membership.
- Preserve 73,547 records / 82,246 content units and explicitly carry 347 unmapped records / 387 units into the exception boundary.
- Do not equate source horizon membership with eligibility or instance membership.
- Any future temporal source change requires a new horizon version and dependent-frame review.
- Dispatch/wave/shift IDs are nullable and absent for this baseline.

## Out of scope / handoff

Planning Horizon does not choose n, seeds, replicates, sampling algorithm parameters, clustered/dispersed cases, anchors, event IDs, access points, vehicle, q/Q/m or OD matrices. Eligibility and Instance Generation own those decisions after their gates. An optimization instance may contain only a subset of the source-horizon eligible frame and must preserve parent IDs/hashes.
""")

    write_text("ELIGIBLE_POPULATION_DEPENDENCIES.md", """
# Eligible population dependencies after horizon freeze

## Required to define the candidate/eligible frame

1. Membership in `R24-SOURCE-DAY-2026-01-01-v1`.
2. Positive realized synthetic demand with stable request/building lineage.
3. Stable destination/building and routing-proxy identifiers.
4. Valid coordinate/CRS and an existing road-mapping relation with method/network hash.
5. An accepted `ROUTING_PROXY_STOP` interpretation, including limitations and missing-access reason.
6. Versioned inclusion/exclusion and row/content conservation rules.
7. Depot reachability status for routing eligibility; unresolved/unreachable records retained as exceptions, not silently dropped.

Vehicle-class-specific legality and final OD compatibility remain downstream B/D validation dependencies. If they remove records, version the eligible frame and review the effect; do not reopen the synthetic-date source horizon unless its records/date change.

## Not required for source-horizon freeze

Observed entrance, actual service-event identity, parcel mass/volume, vehicle class/capacity and q/Q/m. These may be necessary for stronger operational claims or concrete instances, but making them prerequisites for the temporal source boundary would conflate stages.

The current 39,956 mapped positive-demand buildings are reconstructable candidates only. No eligible manifest is frozen here.
""")

    write_text("GATE_A_REMAINING_REMEDIATION.md", """
# Gate A remaining remediation after Planning Horizon freeze

Gate A remains **GATE_A_REQUIRES_TARGETED_REMEDIATION**. General Planning Horizon membership is no longer an active blocker.

| Item | Status after this decision | Required resolution |
|---|---|---|
| Source horizon / source-use boundary | CLOSED_WITH_LIMITATIONS | immutable 2026-01-01 snapshot; synthetic benchmark claims only |
| Generator provenance | BLOCKS_REGENERATION_ONLY | no historical regeneration claim; not a saved-snapshot Gate A blocker |
| Routing proxy / access | ACTIVE_GATE_A_STOP | decide whether saved building-to-road mappings are admissible modeled stops and specify identifiers/network/missing access limits |
| Service-event abstraction | ACTIVE_GATE_A_STOP_AFTER_PROXY | decide whether one routing proxy may be one benchmark customer node, without claiming observed one-visit events |
| Conservation / exceptions | OPEN | bind 73,547/82,246 source totals, 347/387 mapping exceptions, child records and later eligibility exclusions |
| Formal Gate A sign-off | OPEN | version interface amendments, verify A1-A6, record limitations and permit/deny Gate B |

Routing-proxy policy is next because a modeled visit-location identity is needed before a benchmark customer-node/event abstraction can be finalized. The horizon is independent: proxy remediation may narrow eligibility but cannot fabricate dispatch/wave/shift membership or change the frozen day silently.

`NEXT_EXECUTABLE_TASK = finalize routing-proxy stop policy`
""")

    write_text("PROVENANCE.md", f"""
# Provenance and reproducibility boundary

Branch `main`; start SHA `{START_SHA}`. End SHA is recorded in GIT_STATUS.json and equals the start SHA unless an external commit occurs. INSPECTED_FILES.csv records full byte hashes for {len(inspected)} parent authorities, prior Gate A registers, source tables and road-mapping evidence. No historical artifact was edited.

The decision reuses verified saved facts: 73,547 records / 82,246 parcel-equivalents on 2026-01-01; 73,200 mapped records / 81,859 units; 347 records / 387 units unmapped; 39,956 positive mapped building aggregates. No generator or mapper was executed. The decision does not materialize a horizon-membership table, eligible frame, service event, stop, dispatch, wave, shift or instance.

Scientific mutation = NONE. Experiment execution = NONE. Demand generation = NONE. Request timestamp generation = NONE. Instance generation = NONE. Optimization = NONE. R23 rerun = NONE. Vehicle/capacity/q/Q/m decisions = NONE.

All outputs are documentation/semantic-decision artifacts under an existing ignored output path. SHA256SUMS.txt covers all flat outputs except itself to avoid self-reference. Verify with `sha256sum -c SHA256SUMS.txt` from this directory.
""")

    git_status = {
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "start_sha": START_SHA,
        "end_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "tracked_changes": subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines(),
        "output_tracking": "IGNORED_BY_EXISTING_GITIGNORE; not staged or committed",
        "scientific_mutation": "NONE; semantic decision artifacts only",
        "experiment_execution": "NONE",
        "demand_generation": "NONE",
        "instance_generation": "NONE",
        "optimization": "NONE",
        "python": sys.version,
    }
    assert not git_status["tracked_changes"]
    (OUT / "GIT_STATUS.json").write_text(json.dumps(git_status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    validation = {
        "verdict": "PLANNING_HORIZON_FROZEN_WITH_LIMITATIONS",
        "planning_horizon": "designated synthetic day as source horizon; optimization instances separately generated benchmark subsets",
        "source_date": "2026-01-01",
        "source_horizon_separated_from_instance": True,
        "dispatch_wave_shift_adopted": False,
        "saved_source_hashes_equal_prior_gate_a_inventory": True,
        "saved_source_counts_reverified": True,
        "daily_request_records": len(daily),
        "daily_content_units": sum(int(row["parcel_equivalent"]) for row in daily),
        "mapped_records": len(assigned),
        "mapping_exception_records": len(exceptions),
        "positive_mapped_building_aggregates": len(stops),
        "eligible_population_generated": False,
        "instance_generated": False,
        "historical_files_modified": False,
        "tracked_changes": False,
        "next_executable_task": "finalize routing-proxy stop policy",
    }
    (OUT / "VALIDATION.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    required = {
        "R24_PLANNING_HORIZON_DECISION.md",
        "PLANNING_HORIZON_OPTION_COMPARISON.csv",
        "SOURCE_HORIZON_VS_INSTANCE.md",
        "PLANNING_HORIZON_STAGE_CONTRACT.md",
        "ELIGIBLE_POPULATION_DEPENDENCIES.md",
        "GATE_A_REMAINING_REMEDIATION.md",
        "LEGACY_DISPATCH_MIGRATION.csv",
        "FOUR_AXIS_PLANNING_HORIZON_AUDIT.csv",
        "PROVENANCE.md",
    }
    assert all((OUT / name).is_file() for name in required)
    files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt")
    (OUT / "SHA256SUMS.txt").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in files), encoding="utf-8")
    print(json.dumps(validation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
