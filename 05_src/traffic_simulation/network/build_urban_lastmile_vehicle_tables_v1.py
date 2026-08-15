"""Build deterministic vehicle-population envelopes, CSV and Markdown tables."""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path
from typing import Any

import yaml

from traffic_simulation.paths import REPOSITORY_ROOT


CONFIG = REPOSITORY_ROOT / "reproducibility/config/traffic_simulation"
RECORDS_PATH = CONFIG / "datasets/urban_lastmile_vehicle_records_v1.yml"
CSV_PATH = CONFIG / "datasets/urban_lastmile_vehicle_records_v1.csv"
STRATA_PATH = CONFIG / "vehicle_populations/urban_lastmile_vehicle_strata_v1.yml"
UNIVERSE_PATH = CONFIG / "vehicle_populations/urban_lastmile_vehicle_universe_v1.yml"
DEPLOYMENT_PATH = CONFIG / "evidence/lastmile_delivery_deployment_evidence_v1.yml"
MARKDOWN_PATH = (
    REPOSITORY_ROOT
    / "05_src/traffic_simulation/specifications/urban_lastmile_vehicle_population_evidence_v1.md"
)

ENVELOPE_FIELDS = (
    ("length_m", "physical"), ("width_m", "physical"),
    ("height_m", "physical"), ("gross_vehicle_mass_kg", "physical"),
    ("maximum_payload_kg", "physical"),
    ("battery_capacity_kwh", "energy"), ("range_km", "energy"),
)
CSV_FIELDS = (
    "record_id", "record_type", "platform_family_id", "manufacturer", "model",
    "variant", "model_year", "vehicle_stratum_id", "legal_vehicle_class_jp",
    "body_type", "upfit_type", "powertrain", "length_m", "width_m", "height_m",
    "wheelbase_m", "curb_mass_kg", "gross_vehicle_mass_kg", "maximum_payload_kg",
    "battery_capacity_kwh", "range_km", "range_test_cycle",
    "energy_consumption_wh_km", "ac_max_kw", "dc_max_kw",
    "deployment_evidence_ids", "evidence_status",
)


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return value


def _display(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "—"
    return str(value)


def build_strata(records_doc: dict[str, Any], strata_doc: dict[str, Any]) -> dict[str, Any]:
    output = {key: value for key, value in strata_doc.items() if key != "strata"}
    output["strata"] = {}
    for stratum_id, original in strata_doc["strata"].items():
        definition = {
            key: value for key, value in original.items()
            if key not in {
                "independent_platform_family_count",
                "source_record_count",
                "contributing_record_count",
                "source_record_ids",
                "empirical_envelope",
                "range_interpretation",
                "sampling_policy",
            }
        }
        records = [item for item in records_doc["records"] if item["vehicle_stratum_id"] == stratum_id]
        envelope: dict[str, Any] = {}
        for field, section in ENVELOPE_FIELDS:
            eligible = (
                records
                if section != "energy"
                else [item for item in records if item["powertrain"] == "battery_electric"]
            )
            contributions = [
                (item["record_id"], item[section][field])
                for item in eligible
                if item[section][field] is not None
            ]
            values = [value for _record_id, value in contributions]
            envelope[field] = {
                "observed_min": min(values) if values else None,
                "observed_max": max(values) if values else None,
                "contributing_record_count": len(values),
                "source_record_ids": [record_id for record_id, _value in contributions],
            }
        definition.update({
            "independent_platform_family_count": len({item["platform_family_id"] for item in records}),
            "contributing_record_count": len(records),
            "source_record_ids": [item["record_id"] for item in records],
            "empirical_envelope": envelope,
            "range_interpretation": "observed_empirical_envelope",
            "sampling_policy": "source_record_only",
        })
        output["strata"][stratum_id] = definition
    return output


def render_csv(records_doc: dict[str, Any]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in sorted(records_doc["records"], key=lambda value: value["record_id"]):
        row = {key: item.get(key) for key in CSV_FIELDS}
        row.update(item["physical"])
        row.update(item["energy"])
        row.update(item["charging"])
        row["deployment_evidence_ids"] = ";".join(item["deployment_evidence_ids"])
        writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in CSV_FIELDS})
    return stream.getvalue()


def _range(item: dict[str, Any], field: str) -> str:
    value = item["empirical_envelope"][field]
    count = value["contributing_record_count"]
    if count == 0:
        return "—"
    if value["observed_min"] == value["observed_max"]:
        return f"{value['observed_min']} (n={count})"
    return f"{value['observed_min']}–{value['observed_max']} (n={count})"


def render_markdown(records_doc: dict[str, Any], strata_doc: dict[str, Any]) -> str:
    universe = _load(UNIVERSE_PATH)
    deployment = _load(DEPLOYMENT_PATH)
    deployment_ids = {item["evidence_id"] for item in deployment["evidence"]}
    lines = [
        "# Urban last-mile vehicle population evidence v1", "",
        "> この文書はcanonical YAMLから自動生成する。表の手動編集は禁止する。", "",
        "本研究は、大田区および近郊の配送拠点から、大田区内を中心とする最終需要地点への都市内ラストマイル配送を対象とする。vehicle populationは実験用scalar vehicle profileではない。現行`managed_urban_ev_delivery_v1`は変更しない。", "",
        "## Table A — Last-mile vehicle universe", "",
        "| ID | Modality | Universe | SUMO four-wheel |", "|---|---|---:|---:|",
    ]
    for key, item in universe["modalities"].items():
        lines.append(f"| {key} | {item['name']} | {item['included_in_universe']} | {item['included_in_sumo_fourwheel_population']} |")
    lines += ["", "## Table B — Four-wheel vehicle strata", "", "| ID | Definition | Treatment | Included | Evidence | Exclusion reason |", "|---|---|---|---:|---|---|"]
    for key, item in strata_doc["strata"].items():
        lines.append(f"| {key} | {item['meaning']} | {item['research_treatment']} | {item['included']} | {item['evidence_status']} / BEV {item['bev_energy_parameter_status']} | {_display(item['exclusion_reason'])} |")
    lines += ["", "## Table C — Real vehicle evidence records", "", "| ID | Stratum | Manufacturer | Model | Body | Powertrain | L | W | H | GVW | Payload | Battery | Range | Sources | Deployment evidence |", "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for item in sorted(records_doc["records"], key=lambda value: value["record_id"]):
        p, e = item["physical"], item["energy"]
        evidence = [value for value in item["deployment_evidence_ids"] if value in deployment_ids]
        sources = sorted(set(item["field_provenance"].values()))
        lines.append(f"| {item['record_id']} | {item['vehicle_stratum_id']} | {item['manufacturer']} | {item['model']} | {item['body_type']} | {item['powertrain']} | {_display(p['length_m'])} | {_display(p['width_m'])} | {_display(p['height_m'])} | {_display(p['gross_vehicle_mass_kg'])} | {_display(p['maximum_payload_kg'])} | {_display(e['battery_capacity_kwh'])} | {_display(e['range_km'])} | {_display(sources)} | {_display(evidence)} |")
    lines += ["", "## Table D — Empirical envelopes", "", "| Stratum | Independent families | Evidence | Length | Width | Height | GVW | Payload | Battery | Range |", "|---|---:|---:|---|---|---|---|---|---|---|"]
    for key, item in strata_doc["strata"].items():
        lines.append(f"| {key} | {item['independent_platform_family_count']} | {item['contributing_record_count']} records | {_range(item, 'length_m')} | {_range(item, 'width_m')} | {_range(item, 'height_m')} | {_range(item, 'gross_vehicle_mass_kg')} | {_range(item, 'maximum_payload_kg')} | {_range(item, 'battery_capacity_kwh')} | {_range(item, 'range_km')} |")
    lines += ["", "`observed_empirical_envelope`は観測recordの範囲であり、確率分布、日本全体のP95、または独立一様分布ではない。F2/F3の欠損は推定で補完しない。", ""]
    return "\n".join(lines)


def generated_content() -> dict[Path, str]:
    records = _load(RECORDS_PATH)
    strata = build_strata(records, _load(STRATA_PATH))
    return {
        STRATA_PATH: yaml.safe_dump(strata, allow_unicode=True, sort_keys=False),
        CSV_PATH: render_csv(records),
        MARKDOWN_PATH: render_markdown(records, strata),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = []
    for path, content in generated_content().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(str(path.relative_to(REPOSITORY_ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if mismatches:
        raise SystemExit("generated artifacts differ: " + ", ".join(mismatches))
    print("urban_lastmile_vehicle_tables=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
