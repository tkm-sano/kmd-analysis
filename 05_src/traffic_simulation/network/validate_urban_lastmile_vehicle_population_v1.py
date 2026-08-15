"""Validate the v1 urban last-mile vehicle evidence population."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from traffic_simulation.network.build_urban_lastmile_vehicle_tables_v1 import (
    CONFIG, DEPLOYMENT_PATH, RECORDS_PATH, STRATA_PATH, UNIVERSE_PATH, generated_content,
)
from traffic_simulation.paths import REPOSITORY_ROOT


class VehiclePopulationError(ValueError):
    pass


AUTHORITATIVE_SOURCES = {
    "SOURCE-MLIT-LAST-MILE": "https://wwwtb.mlit.go.jp/shikoku/00001_02677.html",
    "SOURCE-JAPAN-POST-EV": "https://www.post.japanpost.jp/about/csr/nature/",
    "SOURCE-MITSUBISHI-MINICAB-EV": "https://www.mitsubishi-motors.co.jp/lineup/minicab_ev/spec/spe_02.html",
    "SOURCE-HONDA-NVAN-E-TYPE": "https://www.honda.co.jp/N-VAN-e/webcatalog/type/compare/",
    "SOURCE-HONDA-NVAN-E-PAYLOAD": "https://www.honda.co.jp/ownersmanual/webom/jpn/n-van-e/2025/details/136249090-15246.html",
    "SOURCE-SUZUKI-E-EVERY": "https://www.suzuki.co.jp/release/a/2026/0309/index.html",
    "SOURCE-SUZUKI-E-EVERY-EV": "https://www.suzuki.co.jp/car/eevery/performance_ev/",
    "SOURCE-HINO-DUTRO-Z-EV": "https://www.hino.co.jp/corp/news/2026/20260602-004699.shtml",
    "SOURCE-ISUZU-ELF-EV": "https://www.isuzu.co.jp/product/elf/ev/",
    "SOURCE-YAMATO-ECANTER": "https://www.yamato-hd.co.jp/news/2023/newsrelease_20230912_1.html",
    "SOURCE-SAGAWA-LIGHT-EV-LAST-MILE": "https://www.sagawa-exp.co.jp/about-csr/column/article_65.html",
    "SOURCE-YAMATO-NVAN-TEST": "https://www.yamato-hd.co.jp/news/2023/newsrelease_20230414_1.html",
}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VehiclePopulationError(f"YAML root must be object: {path}")
    return value


def _schema(name: str) -> dict[str, Any]:
    return json.loads((CONFIG / "schemas" / name).read_text(encoding="utf-8"))


def _unique(items: list[dict[str, Any]], field: str) -> None:
    values = [item[field] for item in items]
    if len(values) != len(set(values)):
        raise VehiclePopulationError(f"duplicate {field}")


def validate() -> dict[str, Any]:
    sources = _yaml(CONFIG / "evidence/lastmile_delivery_sources_v1.yml")
    deployments = _yaml(DEPLOYMENT_PATH)
    records = _yaml(RECORDS_PATH)
    universe = _yaml(UNIVERSE_PATH)
    population = _yaml(CONFIG / "vehicle_populations/ota_area_urban_lastmile_fourwheel_population_v1.yml")
    strata = _yaml(STRATA_PATH)
    for value, schema_name in [
        (sources, "lastmile_delivery_sources_v1.schema.json"),
        (deployments, "lastmile_delivery_deployment_evidence_v1.schema.json"),
        (records, "urban_lastmile_vehicle_record_v1.schema.json"),
        (universe, "urban_lastmile_vehicle_population_v1.schema.json"),
        (population, "urban_lastmile_vehicle_population_v1.schema.json"),
        (strata, "urban_lastmile_vehicle_strata_v1.schema.json"),
    ]:
        jsonschema.Draft202012Validator(_schema(schema_name)).validate(value)
    _unique(sources["sources"], "source_id")
    _unique(deployments["evidence"], "evidence_id")
    _unique(records["records"], "record_id")
    source_ids = {item["source_id"] for item in sources["sources"]}
    source_urls = {item["source_id"]: item["url"] for item in sources["sources"]}
    if source_urls != AUTHORITATIVE_SOURCES:
        raise VehiclePopulationError("source registry differs from authoritative source set")
    evidence_ids = {item["evidence_id"] for item in deployments["evidence"]}
    strata_ids = set(strata["strata"])
    family_strata: dict[str, str] = {}
    family_records: dict[str, list[str]] = {}
    for record in records["records"]:
        if record["vehicle_stratum_id"] not in strata_ids:
            raise VehiclePopulationError("unknown stratum")
        prior = family_strata.setdefault(record["platform_family_id"], record["vehicle_stratum_id"])
        if prior != record["vehicle_stratum_id"]:
            raise VehiclePopulationError("platform family crosses strata")
        family_records.setdefault(record["platform_family_id"], []).append(record["record_id"])
        if not set(record["deployment_evidence_ids"]) <= evidence_ids:
            raise VehiclePopulationError("unknown deployment evidence")
        if "model_assumed" in json.dumps(record, sort_keys=True):
            raise VehiclePopulationError("model_assumed empirical value")
        for section in ("physical", "energy", "charging"):
            for field, value in record[section].items():
                if value is None or value == [] or field == "range_test_cycle":
                    continue
                provenance_field = f"{section}.{field}"
                if provenance_field not in record["field_provenance"]:
                    raise VehiclePopulationError(f"missing provenance: {record['record_id']} {provenance_field}")
                if record["field_provenance"][provenance_field] not in source_ids:
                    raise VehiclePopulationError("unknown source provenance")
        if record["energy"]["range_km"] is not None and not record["energy"]["range_test_cycle"]:
            raise VehiclePopulationError("range test cycle missing")
        if record["record_type"] == "completed_vehicle_variant":
            if record["model_year"] is None:
                raise VehiclePopulationError("completed vehicle must identify model year")
            if record["physical"]["gross_vehicle_mass_constraint"] is not None or record["physical"]["maximum_payload_options_kg"]:
                raise VehiclePopulationError("completed vehicle uses chassis capability fields")
            if any(token in record["variant"].lower() for token in ("common", "capability")):
                raise VehiclePopulationError("completed vehicle variant identity is not specific")
    duplicate_families = {key: value for key, value in family_records.items() if len(value) > 1}
    if duplicate_families:
        raise VehiclePopulationError(f"platform family double counting: {duplicate_families}")
    for evidence in deployments["evidence"]:
        if evidence["source_id"] not in source_ids:
            raise VehiclePopulationError("deployment evidence has unknown source")
        if evidence["platform_family_id"] not in family_strata:
            raise VehiclePopulationError("deployment evidence has unknown platform family")
        if evidence["stratum_id"] != family_strata[evidence["platform_family_id"]]:
            raise VehiclePopulationError("deployment evidence stratum differs from platform family")
    if population["sampling_policy"] != "source_record_only" or population["independent_min_max_sampling"] != "prohibited":
        raise VehiclePopulationError("independent min/max sampling is prohibited")
    if strata["strata"]["F1"]["independent_platform_family_count"] != 3:
        raise VehiclePopulationError("F1 independent platform family count differs")
    generated_strata = generated_content()[STRATA_PATH]
    generated_strata_doc = yaml.safe_load(generated_strata)
    for stratum_id, item in generated_strata_doc["strata"].items():
        if item["contributing_record_count"] != len(item["source_record_ids"]):
            raise VehiclePopulationError(f"stratum source-record count differs: {stratum_id}")
        for field, envelope in item["empirical_envelope"].items():
            count = envelope["contributing_record_count"]
            if count != len(envelope["source_record_ids"]):
                raise VehiclePopulationError(f"envelope source-record count differs: {stratum_id} {field}")
            if count == 0 and (envelope["observed_min"] is not None or envelope["observed_max"] is not None):
                raise VehiclePopulationError(f"empty envelope has values: {stratum_id} {field}")
            if count > 0 and envelope["observed_min"] > envelope["observed_max"]:
                raise VehiclePopulationError(f"envelope min exceeds max: {stratum_id} {field}")
    for path, expected in generated_content().items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            raise VehiclePopulationError(f"generated projection differs: {path}")
    return {
        "schema_validation": "passed",
        "record_count": len(records["records"]),
        "source_count": len(sources["sources"]),
        "deployment_evidence_count": len(deployments["evidence"]),
        "deterministic_projections": "passed",
    }


def main() -> int:
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
