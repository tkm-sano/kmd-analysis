#!/usr/bin/env python3
"""Independent validation of R24-INSTANCE-GEN-20260915-v1 outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pyproj import Transformer
from sumolib.net import readNet


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r24_benchmark_instance_suite/20260915_v1"
SOURCE = ROOT / "reproducibility/outputs/traffic_simulation/r24_routing_compatibility_revalidation/20260915_v1/C_ELIGIBLE_MANIFEST.csv"
NETWORK = ROOT / "reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml"
SOURCE_HASH = "245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c"
NETWORK_HASH = "460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2"
PROTOCOL = "R24-INSTANCE-GEN-20260915-v1"
RANDOM_NS = (2, 3, 4, 5, 8, 10, 15, 20)
STRUCTURAL_NS = (4, 10, 20)
STRUCTURES = ("CLUSTERED", "DISPERSED", "MIXED")
Q = 14


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def canonical_hash(value: Any) -> str:
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def assert_close(actual: float, expected: float, tolerance: float = 2e-8) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-11, abs_tol=tolerance):
        raise AssertionError(f"cost mismatch: {actual} != {expected}")


def main() -> None:
    checks: dict[str, Any] = {}
    assert sha_file(SOURCE) == SOURCE_HASH
    assert sha_file(NETWORK) == NETWORK_HASH
    checks["fixed_input_hashes"] = "PASS"

    source = [row for row in read_csv(SOURCE) if row["eligibility_status"] == "ELIGIBLE"]
    assert len(source) == 39930 and sum(int(row["q_i"]) for row in source) == 81793
    source.sort(key=lambda row: row["benchmark_customer_id"].encode())
    source_by_id = {row["benchmark_customer_id"]: row for row in source}
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6677", always_xy=True)
    coordinates = {row["benchmark_customer_id"]: transformer.transform(float(row["source_longitude"]), float(row["source_latitude"])) for row in source}
    checks["source_population"] = "PASS"

    base_rows = read_csv(OUT / "BASE_INSTANCE_MANIFEST.csv")
    condition_rows = read_csv(OUT / "CAPACITY_CONDITION_MANIFEST.csv")
    od_rows = read_csv(OUT / "OD_MANIFEST.csv")
    seed_rows = read_csv(OUT / "SEED_MANIFEST.csv")
    assert len(base_rows) == 110 and len(condition_rows) == 330 and len(od_rows) == 14600 and len(seed_rows) == 107
    expected_random = {f"R24-RND-N{n:03d}-R{rep:02d}" for n in RANDOM_NS for rep in range(1, 11)}
    expected_structural = {f"R24-STR-{structure}-N{n:03d}-R{rep:02d}" for structure in STRUCTURES for n in STRUCTURAL_NS for rep in range(1, 4)}
    expected_anchor = {f"R24-ANCHOR-N{n:03d}" for n in STRUCTURAL_NS}
    actual_ids = {row["instance_id"] for row in base_rows}
    assert actual_ids == expected_random | expected_structural | expected_anchor
    assert {row["instance_id"] for row in seed_rows} == expected_random | expected_structural
    checks["planned_id_completeness"] = "PASS"

    base_json: dict[str, dict[str, Any]] = {}
    for instance_id in sorted(actual_ids):
        record = json.loads((OUT / "instances" / instance_id / "base_instance.json").read_text(encoding="utf-8"))
        claimed = record.pop("output_sha256")
        assert canonical_hash(record) == claimed
        record["output_sha256"] = claimed
        assert record["instance_id"] == instance_id
        assert record["base_status"] == "VALID" and record["hard_rejection_reasons"] == []
        assert len(record["customer_ids"]) == record["n"] == len(set(record["customer_ids"]))
        assert all(customer_id in source_by_id for customer_id in record["customer_ids"])
        assert record["customer_ids_sha256"] == canonical_hash(record["customer_ids"])
        assert record["q_i_vector_sha256"] == canonical_hash(record["q_i_by_customer"])
        assert sum(item["q_i"] for item in record["q_i_by_customer"]) == record["total_demand_D"]
        assert all(1 <= item["q_i"] <= Q for item in record["q_i_by_customer"])
        base_json[instance_id] = record
    checks["base_content_hash_membership_q"] = "PASS"

    # Independently derive all seed digests and primary hash-ranked samples.
    for seed in seed_rows:
        if seed["suite"] == "RND":
            material = f"{PROTOCOL}|suite=RND|n={int(seed['n'])}|rep={int(seed['repetition']):02d}"
        else:
            material = f"{PROTOCOL}|suite=STR|structure={seed['structure']}|n={int(seed['n'])}|rep={int(seed['repetition']):02d}"
        seed_digest = digest(material)
        assert seed["seed_material"] == material and seed["seed_digest_sha256"] == seed_digest
        assert int(seed["seed_uint64"]) == int.from_bytes(bytes.fromhex(seed_digest)[:8], "big")
        if seed["suite"] == "RND":
            n = int(seed["n"])
            selected = sorted(source, key=lambda row: (digest(f"{seed_digest}|customer={row['benchmark_customer_id']}"), row["benchmark_customer_id"].encode()))[:n]
            expected = sorted((row["benchmark_customer_id"] for row in selected), key=lambda value: value.encode())
            assert base_json[seed["instance_id"]]["customer_ids"] == expected
    checks["seed_and_random_selection_rederivation"] = "PASS"

    # Independently derive structural subsets from the frozen metric/rules.
    def d(a: str, b: str) -> float:
        ax, ay = coordinates[a]
        bx, by = coordinates[b]
        return math.hypot(ax - bx, ay - by)

    all_ids = [row["benchmark_customer_id"] for row in source]
    for seed in (row for row in seed_rows if row["suite"] == "STR"):
        score = {customer_id: digest(f"{seed['seed_digest_sha256']}|customer={customer_id}") for customer_id in all_ids}
        first = min(all_ids, key=lambda customer_id: (score[customer_id], customer_id.encode()))
        n = int(seed["n"])
        structure = seed["structure"]
        if structure == "CLUSTERED":
            selected = sorted(all_ids, key=lambda customer_id: (d(first, customer_id), score[customer_id], customer_id.encode()))[:n]
        elif structure == "DISPERSED":
            selected = [first]
            selected_set = {first}
            while len(selected) < n:
                chosen = min((customer_id for customer_id in all_ids if customer_id not in selected_set), key=lambda customer_id: (-min(d(customer_id, existing) for existing in selected), score[customer_id], customer_id.encode()))
                selected.append(chosen)
                selected_set.add(chosen)
        else:
            second = min((customer_id for customer_id in all_ids if customer_id != first), key=lambda customer_id: (-d(first, customer_id), score[customer_id], customer_id.encode()))
            groups = [[first], [second]]
            quotas = ((n + 1) // 2, n // 2)
            selected_set = {first, second}
            index = 0
            while len(selected_set) < n:
                if len(groups[index]) < quotas[index]:
                    anchor = first if index == 0 else second
                    chosen = min((customer_id for customer_id in all_ids if customer_id not in selected_set), key=lambda customer_id: (d(anchor, customer_id), score[customer_id], customer_id.encode()))
                    groups[index].append(chosen)
                    selected_set.add(chosen)
                index = 1 - index
            selected = groups[0] + groups[1]
        assert base_json[seed["instance_id"]]["customer_ids"] == sorted(selected, key=lambda value: value.encode())
    checks["structural_selection_rederivation"] = "PASS"

    # Anchors must be exact aliases for customer, q and OD semantic hashes.
    for n in STRUCTURAL_NS:
        anchor = base_json[f"R24-ANCHOR-N{n:03d}"]
        source_record = base_json[f"R24-RND-N{n:03d}-R01"]
        assert anchor["anchor_source_base_instance_id"] == source_record["instance_id"]
        for field in ("customer_ids_sha256", "q_i_vector_sha256", "od_matrix_sha256", "total_demand_D"):
            assert anchor[field] == source_record[field]
    checks["anchor_aliases"] = "PASS"

    # Recompute every stored path cost and connection validity from run_3.
    net = readNet(str(NETWORK), withInternal=False, withPrograms=False)
    edges = {edge.getID(): edge for edge in net.getEdges() if edge.allows("delivery")}
    adjacency: dict[str, set[str]] = {}
    for edge_id, edge in edges.items():
        adjacency[edge_id] = {
            target.getID() for target, connections in edge.getOutgoing().items()
            if target.getID() in edges and any(connection.getFromLane().allows("delivery") and connection.getToLane().allows("delivery") for connection in connections)
        }
    od_by_instance: dict[str, list[dict[str, str]]] = defaultdict(list)
    zero_distance = zero_time = 0
    for row in od_rows:
        od_by_instance[row["instance_id"]].append(row)
        sequence = json.loads(row["edge_sequence"])
        assert sequence[0] == row["origin_edge_id"] and sequence[-1] == row["destination_edge_id"]
        assert all(b in adjacency[a] for a, b in zip(sequence, sequence[1:]))
        origin_offset = float(row["origin_offset_m"])
        destination_offset = float(row["destination_offset_m"])
        if len(sequence) == 1:
            expected_distance = destination_offset - origin_offset
            expected_time = expected_distance / float(edges[sequence[0]].getSpeed())
        else:
            expected_distance = float(edges[sequence[0]].getLength()) - origin_offset + sum(float(edges[e].getLength()) for e in sequence[1:-1]) + destination_offset
            expected_time = (float(edges[sequence[0]].getLength()) - origin_offset) / float(edges[sequence[0]].getSpeed()) + sum(float(edges[e].getLength()) / float(edges[e].getSpeed()) for e in sequence[1:-1]) + destination_offset / float(edges[sequence[-1]].getSpeed())
        assert_close(float(row["distance_m"]), expected_distance)
        assert_close(float(row["travel_time_s"]), expected_time)
        assert row["reachable"] == "True" and row["connection_validation_status"] == "PASS" and row["validation_status"] == "PASS"
        if row["zero_distance_flag"] == "True":
            zero_distance += 1
            assert row["duplicate_proxy_arc_flag"] == "True" and float(row["distance_m"]) == 0
        if row["zero_travel_time_flag"] == "True":
            zero_time += 1
            assert row["duplicate_proxy_arc_flag"] == "True" and float(row["travel_time_s"]) == 0
    for instance_id, rows in od_by_instance.items():
        n = base_json[instance_id]["n"]
        assert len(rows) == (n + 1) * n == len({(row["origin_id"], row["destination_id"]) for row in rows})
    checks["run3_path_connection_cost_and_od_completeness"] = "PASS"
    checks["zero_distance_ordered_arcs_including_anchors"] = zero_distance
    checks["zero_time_ordered_arcs_including_anchors"] = zero_time

    # Validate every m/rho result and every feasible packing certificate.
    conditions_by_base: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in condition_rows:
        conditions_by_base[row["base_instance_id"]].append(row)
        base = base_json[row["base_instance_id"]]
        expected_m = math.ceil(base["total_demand_D"] / (float(row["target_rho"]) * Q))
        assert int(row["Q"]) == Q and int(row["m"]) == expected_m
        assert_close(float(row["actual_rho"]), base["total_demand_D"] / (expected_m * Q))
        assert row["packing_feasibility"] == "PACKING_FEASIBLE"
        individual = json.loads((OUT / "instances" / row["base_instance_id"] / "capacity_conditions.json").read_text(encoding="utf-8"))
        full = next(item for item in individual if item["condition_id"] == row["condition_id"])
        certificate = full["packing_certificate"]
        flattened = [customer_id for bin_members in certificate for customer_id in bin_members]
        assert sorted(flattened) == sorted(base["customer_ids"]) and len(certificate) <= expected_m
        demands = {item["customer_id"]: item["q_i"] for item in base["q_i_by_customer"]}
        assert all(sum(demands[customer_id] for customer_id in bin_members) <= Q for bin_members in certificate)
        assert canonical_hash(certificate) == row["packing_certificate_sha256"]
    for instance_id, rows in conditions_by_base.items():
        assert len(rows) == 3
        m_groups = Counter(int(row["m"]) for row in rows)
        for row in rows:
            expected_degenerate = m_groups[int(row["m"])] > 1
            assert (row["degenerate_regime_flag"] == "True") == expected_degenerate
            assert row["condition_status"] == ("DEGENERATE_REGIME_SAME_M" if expected_degenerate else "READY")
    checks["capacity_formula_packing_certificates_and_degeneracy"] = "PASS"

    assert len(read_csv(OUT / "INSTANCE_REJECTION_LOG.csv")) == 0
    checks["hard_rejections"] = 0
    checks["packing_infeasible"] = 0
    checks["status"] = "PASS"
    report = {"validator": Path(__file__).name, "validator_sha256": sha_file(Path(__file__)), "checks": checks}
    (OUT / "VALIDATION_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    checksum_path = OUT / "SHA256SUMS.txt"
    checksum_lines = []
    for path in sorted((path for path in OUT.rglob("*") if path.is_file() and path != checksum_path), key=lambda path: str(path.relative_to(OUT))):
        checksum_lines.append(f"{sha_file(path)}  {path.relative_to(OUT)}")
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
