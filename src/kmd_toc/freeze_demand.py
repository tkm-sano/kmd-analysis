"""Explicit, one-off audited demand freeze. Never called by A/B/C/D loaders."""

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import csv
import io
import json
from pathlib import Path
import re

from .frozen_demand import (ROOT, SCENARIOS, COLUMNS, FrozenDemandError,
                             read_csv, sha256, stop_set_sha256, _verify_bundle)

AUDIT_REL = "review_outputs/toc_stops_full_audit_20261108/run_20261108T091121Z_attempt02"
SOURCE_REL = ("03_data/processed/traffic_simulation/demand/household_parcel_v1/"
              "pipelines_v1/building_delivery_stops_scoped.csv")
BUNDLE_REL = "03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1"
CONFIG_REL = "configs/toc_delivery/frozen_demand_v1.json"
RANK_PREFIX = b"toc-stop-rank-v1\x00"
AUDIT_FILES = ("ALL_STOPS_AUDIT.csv", "REGIONAL_COVERAGE.csv", "AUDIT_SUMMARY.json",
               "REPRODUCE.md", "STRATIFIED_QUOTA_CHECK.csv", "INPUT_MANIFEST.json",
               "OUTPUT_HASHES.json", "AUDIT_PROTOCOL.json")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def csv_bytes(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def rank_key(stop_id):
    identifier = stop_id.encode("utf-8")
    from hashlib import sha256 as digest
    return digest(RANK_PREFIX + identifier).digest(), identifier


def allocate(original_counts, N):
    if len(original_counts) != 182 or sum(original_counts.values()) != 39956:
        raise FrozenDemandError("Expected 182 regions / 39,956 original stops")
    if any(not re.fullmatch(r"[0-9]{6}", g) or type(m) is not int or m <= 0
           for g, m in original_counts.items()):
        raise FrozenDemandError("Invalid original region counts")
    if type(N) is not int or N < 0:
        raise FrozenDemandError("Invalid N")
    result = {g: N * m // 39956 for g, m in original_counts.items()}
    order = sorted(original_counts, key=lambda g: (-(N * original_counts[g] % 39956),
                                                   g.encode("utf-8")))
    for g in order[:N - sum(result.values())]:
        result[g] += 1
    if sum(result.values()) != N:
        raise FrozenDemandError("Allocation total mismatch")
    return result


def load_inputs():
    base = ROOT / AUDIT_REL
    raw = {f"{AUDIT_REL}/{name}": (base / name).read_bytes() for name in AUDIT_FILES}
    inventory = json.loads(raw[f"{AUDIT_REL}/OUTPUT_HASHES.json"])
    # Validate the complete existing audit inventory, not only the selected rows.
    for name, expected in inventory.items():
        if Path(name).name != name:
            raise FrozenDemandError("Unsafe audit inventory name")
        content = (base / name).read_bytes()
        if len(content) != expected["bytes"] or sha256(content) != expected["sha256"]:
            raise FrozenDemandError(f"Audit artifact changed: {name}")
    raw[SOURCE_REL] = (ROOT / SOURCE_REL).read_bytes()
    source_records = json.loads(raw[f"{AUDIT_REL}/INPUT_MANIFEST.json"])
    source_entry = [e for e in source_records if Path(e["path"]).name == Path(SOURCE_REL).name]
    if len(source_entry) != 1 or sha256(raw[SOURCE_REL]) != source_entry[0]["sha256"]:
        raise FrozenDemandError("Original stop source differs from the audited source")
    summary = json.loads(raw[f"{AUDIT_REL}/AUDIT_SUMMARY.json"])
    if summary["target_count"] != 39956 or summary["status_counts"].get("PASS") != 34912:
        raise FrozenDemandError("Audit count definition changed")
    protocol = json.loads(raw[f"{AUDIT_REL}/AUDIT_PROTOCOL.json"])
    if protocol["version"] != "toc-stops-audit-v1" or not protocol["coordinate_crs"].startswith("EPSG:4326"):
        raise FrozenDemandError("Unverified coordinate CRS")
    provenance = {path: {"bytes": len(data), "sha256": sha256(data)} for path, data in raw.items()}
    for name in ("freeze_demand.py", "frozen_demand.py"):
        relative = f"src/kmd_toc/{name}"
        data = (ROOT / relative).read_bytes()
        provenance[relative] = {"bytes": len(data), "sha256": sha256(data)}
    return (read_csv(raw[f"{AUDIT_REL}/ALL_STOPS_AUDIT.csv"]), read_csv(raw[SOURCE_REL]),
            read_csv(raw[f"{AUDIT_REL}/REGIONAL_COVERAGE.csv"]),
            read_csv(raw[f"{AUDIT_REL}/STRATIFIED_QUOTA_CHECK.csv"]), summary, provenance)


def _index(rows, field):
    result = {}
    for row in rows:
        if field not in row or not row[field] or row[field] in result:
            raise FrozenDemandError(f"Missing/duplicate {field}")
        result[row[field]] = row
    return result


def build_bundle(audit, source, regional, historical_quotas, summary, provenance):
    """Pure deterministic bytes: usable for independent regeneration checks."""
    if len(audit) != 39956 or len(source) != 39956:
        raise FrozenDemandError("Wrong full input count")
    ai, si = _index(audit, "stop_id"), _index(source, "stop_id")
    _index(audit, "building_id")
    _index(source, "building_id")
    if set(ai) != set(si):
        raise FrozenDemandError("Source/audit stop reference mismatch")
    original = Counter(r["chocho_code"] for r in audit)
    status_counts = Counter(r["overall_status"] for r in audit)
    regional_status = Counter((r["chocho_code"], r["overall_status"]) for r in audit)
    expected_status = {k: v for k, v in summary["status_counts"].items() if v}
    if dict(status_counts) != expected_status or status_counts["PASS"] != 34912:
        raise FrozenDemandError("Audit row status counts differ from summary")
    by_region = defaultdict(list)
    for sid, row in ai.items():
        master = si[sid]
        required = ("stop_id", "building_id", "chocho_code", "longitude", "latitude",
                    "overall_status", "coordinate_crs", "source_master_sha256")
        if any(not row.get(key) for key in required):
            raise FrozenDemandError("Missing required audit value")
        if not re.fullmatch(r"[0-9]{6}", row["chocho_code"]):
            raise FrozenDemandError("Region code is not six ASCII digits")
        if (row["building_id"], row["chocho_code"]) != (master["building_id"], master["chocho_code"]):
            raise FrozenDemandError("Audit/source identity mismatch")
        point = re.fullmatch(r"POINT \(([^ ]+) ([^ ]+)\)", master["building_representative_point"])
        if not point or point.groups() != (row["longitude"], row["latitude"]):
            raise FrozenDemandError("Coordinates differ from original WKT tokens")
        lon, lat = Decimal(row["longitude"]), Decimal(row["latitude"])
        if not (lon.is_finite() and lat.is_finite() and -180 <= lon <= 180 and -90 <= lat <= 90):
            raise FrozenDemandError("Invalid original coordinates")
        if row["coordinate_crs"] != "EPSG:4326" or row["source_master_sha256"] != provenance[SOURCE_REL]["sha256"]:
            raise FrozenDemandError("Coordinate/source lineage mismatch")
        if row["overall_status"] == "PASS":
            by_region[row["chocho_code"]].append(row)
    ri = _index(regional, "chocho_code")
    if set(ri) != set(original):
        raise FrozenDemandError("Regional inventory mismatch")
    for g, row in ri.items():
        if int(row["original_count"]) != original[g] or int(row["PASS"]) != len(by_region[g]):
            raise FrozenDemandError("Regional counts differ from all-stop audit")
        for status in ("PASS", "CONDITIONAL", "HOLD", "FAIL"):
            if int(row[status]) != regional_status[g, status]:
                raise FrozenDemandError("Regional status mismatch")
    for candidates in by_region.values():
        candidates.sort(key=lambda r: rank_key(r["stop_id"]))
    quotas = {s: allocate(original, n) for s, (n, _, _) in SCENARIOS.items()}
    if any(not quotas["S1"][g] <= quotas["S2"][g] <= quotas["S3"][g] for g in original):
        raise FrozenDemandError("HOLD: Hamilton allocation is not monotone; no automatic replacement")
    expected_old = {}
    for row in historical_quotas:
        if row["policy"] == "PASS_ONLY":
            key = (int(row["N"]), row["chocho_code"])
            if key in expected_old:
                raise FrozenDemandError("Duplicate historical quota")
            expected_old[key] = row
    if len(expected_old) != 3 * 182:
        raise FrozenDemandError("Historical quota coverage incomplete")
    payload, metadata, allocated_rows, selected_sets = {}, {}, [], {}
    for scenario_id, (n, vehicles, berths) in SCENARIOS.items():
        selected = []
        for g in sorted(original, key=lambda s: s.encode("utf-8")):
            q = quotas[scenario_id][g]
            old = expected_old[(n, g)]
            if (int(old["quota_preserving_original_share"]), int(old["available_count"]), int(old["shortage"])) != (
                    q, len(by_region[g]), 0):
                raise FrozenDemandError("Historical quota evidence mismatch")
            if q > len(by_region[g]):
                raise FrozenDemandError("HOLD: insufficient PASS candidates; no redistribution")
            selected.extend(by_region[g][:q])
            allocated_rows.append(dict(scenario_id=scenario_id, chocho_code=g,
                original_count=original[g], pass_count=len(by_region[g]),
                quota_numerator=n * original[g], quota_denominator=39956,
                floor_count=n * original[g] // 39956, remainder=n * original[g] % 39956,
                allocated_count=q, selected_count=q))
        selected.sort(key=lambda r: r["stop_id"].encode("utf-8"))
        rows = [dict(scenario_id=scenario_id, stop_id=r["stop_id"], building_id=r["building_id"],
                     chocho_code=r["chocho_code"], longitude=r["longitude"], latitude=r["latitude"],
                     parcel_count=1) for r in selected]
        selected_sets[scenario_id] = {r["stop_id"] for r in rows}
        if len(rows) != n or len(selected_sets[scenario_id]) != n:
            raise FrozenDemandError("Selected total mismatch")
        payload[scenario_id + ".csv"] = csv_bytes(COLUMNS, rows)
        metadata[scenario_id] = dict(N=n, vehicles=vehicles, berths=berths, total_parcels=n,
                                    stop_set_sha256=stop_set_sha256(selected_sets[scenario_id]))
    if not selected_sets["S1"] < selected_sets["S2"] < selected_sets["S3"]:
        raise FrozenDemandError("HOLD: strict nesting not satisfied")
    payload["REGIONAL_ALLOCATION.csv"] = csv_bytes(tuple(allocated_rows[0]), allocated_rows)
    payload["VALIDATION.json"] = json_bytes(dict(status="PASS", original_stops=39956,
        pass_stops=34912, regions=182, full_input_identity_coordinate_checks=39956,
        scenarios=metadata, checks={key: True for key in (
            "source_audit_identity", "all_ids_unique", "all_buildings_unique",
            "source_coordinate_tokens_unchanged", "regional_counts_match_audit",
            "historical_quota_match", "integer_allocation_totals", "capacity_of_candidate_pools",
            "monotone_regional_quotas", "strict_nested_stop_sets", "pass_only", "one_parcel_per_stop")},
        vrp_feasibility="NOT_ASSESSED", road_od_adoption="HOLD"))
    payload["READING_CONTRACT.md"] = reading_contract().encode("utf-8")
    manifest = dict(schema_version=1, dataset_id="ota-toc-frozen-demand-v1", frozen=True,
        scope="synthetic_controlled_ToC_stops_Ota_single_Keihin_depot",
        original_stop_count=39956, eligible_stop_count=34912, region_count=182,
        coordinate_crs="EPSG:4326", coordinate_serialization="original_WKT_tokens_unchanged",
        allocation="original_stop_share_integer_largest_remainder",
        allocation_tie_break="six_ASCII_digit_chocho_code_UTF8_bytes_ascending",
        rank_algorithm="SHA256", rank_prefix_utf8="toc-stop-rank-v1", rank_separator_hex="00",
        rank_id_encoding="UTF-8; verbatim; no trimming/numeric conversion/Unicode normalization",
        rank_comparison="32 unsigned digest bytes ascending, then stop_id UTF8 bytes ascending",
        row_order="stop_id_UTF8_bytes_ascending", sampling="stratified_without_replacement_common_rank",
        nesting="S1 strict_subset S2 strict_subset S3",
        parcel_rule="exactly_one_parcel_per_stop_controlled_assumption_not_observed_demand",
        stop_set_hash="SHA256(UTF8(toc-stop-set-v1)||00||concat(uint32be(byte_length(id))||UTF8(id))); IDs UTF8-byte sorted",
        scenarios=metadata, inputs=provenance,
        files={name: dict(bytes=len(data), sha256=sha256(data)) for name, data in payload.items()},
        reproducibility="no timestamp/environment/consumer method in generated bytes; dependencies are Python stdlib",
        overwrite_policy="existing identical bytes: verify_only; any difference/extra/missing file: stop",
        trust_root="external source pin freezes MANIFEST/config/SHA256SUMS; manifest is not its own trust anchor",
        road_od_adoption="HOLD", vehicle_capacity="HOLD", vrp_feasibility="NOT_ASSESSED")
    payload["MANIFEST.json"] = json_bytes(manifest)
    payload["SHA256SUMS"] = b"".join(f"{sha256(payload[name])}  {name}\n".encode("utf-8")
        for name in sorted(payload, key=lambda s: s.encode("utf-8")))
    return payload


def reading_contract():
    return """# A〜D共通：固定需要v1の読込契約

この8ファイルを一体で凍結する。S1=1,000地点/10台/2バース、S2=2,000/20/4、
S3=4,000/40/8である。全地点1個は制御仮定であり、実配送の推計ではない。

読込は `from kmd_toc.frozen_demand import load_frozen_demand`、
`demand = load_frozen_demand('S1', method_id='A')` とする。B/C/Dもmethod_idだけを変える。
実行例はリポジトリルートで `PYTHONPATH=src python -B -c "from kmd_toc.frozen_demand import load_frozen_demand; d=load_frozen_demand('S1', method_id='A'); print(d.N, len(d.stops))"` である。

読込前にソース側の固定pin、設定、manifest、全payload、SHA256SUMS、件数、地域配分、
包含関係を検証する。不一致・欠損はFrozenDemandErrorで停止し、生成や自動修復をしない。
bundle_dirは完全同一の保存コピーの検証にだけ使用でき、別hashの指定はできない。
戻り値はfrozen dataclassとtupleである。経緯度は元の十進文字列を保持し、IDと地域コードも
文字列のままである。必要な数値演算は別の作業用配列で行い、元値を丸めて保存し直さない。

CSVはUTF-8・BOMなし・LF、列順はscenario_id,stop_id,building_id,chocho_code,
longitude,latitude,parcel_countである。行はstop_idのUTF-8バイト列昇順である。
同じ地点の属性は系列間で同じである。配分は元39,956地点の182町丁目構成比、
整数最大剰余法、同率は6桁コードUTF-8昇順である。各層は
SHA256(UTF8('toc-stop-rank-v1') || 0x00 || UTF8(stop_id))の32バイト昇順、
同値は地点IDのUTF-8昇順とし、共通順位先頭を非復元抽出する。需要seedは使用しない。

地点集合hashは、UTF8('toc-stop-set-v1') || 0x00 に続けて、UTF-8バイト昇順の各IDについて
4バイト符号なしbig-endian長とIDのUTF-8バイト列を連結した列のSHA-256である。
ファイルhashはファイルの全バイトを対象とする。SHA256SUMSは自身以外の7ファイルを記録する。
SHA256SUMS自身とmanifestと設定のhashは、別のfrozen_demand_pin.pyで固定する。

Aは事業者方式を参考にした規則ベース、BはVeRyPy並列Clarke–Wright、CはOR-Tools、
Dは量子研究に基づく手法である。いずれも需要の再生成・再抽出・地点削除・座標変更・
荷量変更・需要seed追加を禁止する。可能なのは訪問順・車両/便割当・時刻等の計画決定である。
容量超過や到達不能は計画側・道路側の未解決事項として記録し、需要を減らして解消しない。
車両容量や道路端点は本CSVに含まない。道路採用・全必要OD・運行条件・VRP可行性はHOLDである。
不足ODは固定stop_idの有向組合せを別工程で記録し、今回道路計算を行わない。
需要抽出と共通道路整備はA〜Dの手法固有Tの外に分け、共通準備時間として別に記録する。

旧study.json/contracts.pyの人口配分・旧単位・input_seeds・固定担当はこの需要の読込には使わない。
通常実行からfreeze_demandを呼ばない。既存v1と異なる出力は上書きせず停止する。
仕様変更はv1を残した別版の提案とし、明示的承認なく比較入力を切り替えない。
SHA-256は誤変更検知でありOSによる絶対的な書込禁止ではない。pinも含むソースの変更は
研究仕様変更としてレビューする。固定原本を書き換えるテストは行わない。

監査担当者の再現確認はリポジトリルートから
`PYTHONPATH=src python -B -m kmd_toc.freeze_demand --verify-only` とする。
元入力からメモリ内で再構築して全8ファイルのバイト一致を検査し、原本へ一切書き込まない。
初回固定専用の--freeze-v1はA〜Dから呼ばない。既存の同一v1なら照合のみで書込なし、
相違があれば停止する。出力に実行日時を含めず、実行環境・共通準備秒は別の検証報告へ保存する。
"""


def write_bundle(destination, payload):
    """Exclusive first publish; repeat invocation never overwrites any file."""
    destination = Path(destination)
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir() or {p.name for p in destination.iterdir()} != set(payload):
            raise FrozenDemandError("Existing destination differs; refusing overwrite")
        if any(p.is_symlink() or not p.is_file() or p.read_bytes() != payload[p.name]
               for p in destination.iterdir()):
            raise FrozenDemandError("Existing v1 content differs; refusing overwrite")
        return "VERIFIED_EXISTING_NO_WRITE"
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in payload.items():
        with (destination / name).open("xb") as stream:
            stream.write(data)
    _verify_bundle(destination, sha256(payload["MANIFEST.json"]))
    return "CREATED"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-v1", action="store_true", help="explicit one-off publish only")
    parser.add_argument("--verify-only", action="store_true", help="regenerate in memory and compare; no writes")
    args = parser.parse_args()
    if args.freeze_v1 == args.verify_only:
        parser.error("Specify exactly one of --freeze-v1 or --verify-only")
    inputs = load_inputs()
    payload = build_bundle(*inputs)
    if payload != build_bundle(*inputs):
        raise FrozenDemandError("Regeneration differs")
    shuffled = [list(reversed(x)) if isinstance(x, list) else x for x in inputs]
    if payload != build_bundle(*shuffled):
        raise FrozenDemandError("Input row-order dependence")
    config_data = json_bytes(dict(dataset_id="ota-toc-frozen-demand-v1", bundle_relative_path=BUNDLE_REL,
        manifest_sha256=sha256(payload["MANIFEST.json"]), methods=["A", "B", "C", "D"],
        loader="kmd_toc.frozen_demand.load_frozen_demand", runtime_generation=False))
    pin_data = ("\"\"\"Approved v1 trust root; changes require explicit research approval.\"\"\"\n"
        f"MANIFEST_SHA256 = {sha256(payload['MANIFEST.json'])!r}\n"
        f"CHECKSUMS_SHA256 = {sha256(payload['SHA256SUMS'])!r}\n"
        f"CONFIG_SHA256 = {sha256(config_data)!r}\n"
        f"CONFIG_RELATIVE_PATH = {CONFIG_REL!r}\n").encode("utf-8")
    external = {ROOT / CONFIG_REL: config_data, ROOT / "src/kmd_toc/frozen_demand_pin.py": pin_data}
    for path, data in external.items():
        if path.exists() and (path.is_symlink() or path.read_bytes() != data):
            raise FrozenDemandError(f"Existing pin/config differs: {path}")
        if args.verify_only and not path.is_file():
            raise FrozenDemandError("Missing published pin/config")
    if args.verify_only:
        directory = ROOT / BUNDLE_REL
        _verify_bundle(directory, sha256(payload["MANIFEST.json"]))
        if any((directory / n).read_bytes() != v for n, v in payload.items()):
            raise FrozenDemandError("Frozen bundle differs from regeneration")
        status = "VERIFIED_NO_WRITE"
    else:
        status = write_bundle(ROOT / BUNDLE_REL, payload)
        for path, data in external.items():
            if not path.exists():
                with path.open("xb") as stream:
                    stream.write(data)
    print(json.dumps(dict(status=status, manifest_sha256=sha256(payload["MANIFEST.json"]),
                         regeneration_identical=True, reversed_input_identical=True)))


if __name__ == "__main__":
    main()
