#!/usr/bin/env python3
"""Generate and independently validate the EVRP R04 household weights."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml
from pyproj import Transformer
from shapely.geometry import Point

from traffic_simulation.demand.prepare_baseline_demand import mesh_500m_polygon


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "reproducibility/config/traffic_simulation/evrp_r04_demand_weight_v1.yml"
OUTPUT = ROOT / "reproducibility/outputs/traffic_simulation/demand/evrp_r04_demand_weight/20260909_r04_demand_weight_v3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_candidates(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str)
    required = {"stop_id", "building_representative_point"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"candidate columns missing: {sorted(missing)}")
    if len(frame) != 39956:
        raise ValueError(f"candidate count is {len(frame)}, expected 39956")
    ids = frame["stop_id"]
    if ids.isna().any() or (ids.str.strip() == "").any() or ids.duplicated().any():
        raise ValueError("candidate IDs must be unique and non-empty")
    points = []
    for value in frame["building_representative_point"]:
        match = re.fullmatch(r"POINT \(([-+0-9.eE]+) ([-+0-9.eE]+)\)", value.strip())
        if not match:
            raise ValueError(f"invalid candidate WKT: {value!r}")
        lon, lat = map(float, match.groups())
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate: {lon}, {lat}")
        points.append(Point(lon, lat))
    frame["geometry"] = points
    return frame


def load_census(path: Path) -> tuple[pd.DataFrame, list[str]]:
    with zipfile.ZipFile(path) as archive:
        member = "tblT001141H5339.txt"
        if archive.namelist().count(member) != 1:
            raise ValueError("configured census member is not unique")
        payload = archive.read(member)
    frame = pd.read_csv(io.BytesIO(payload), encoding="cp932", skiprows=[1], dtype=str, low_memory=False)
    required = {"KEY_CODE", "T001141034", "HTKSYORI", "HTKSAKI", "GASSAN"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"census columns missing: {sorted(missing)}")
    frame["mesh_code"] = frame["KEY_CODE"].str.strip()
    if frame["mesh_code"].duplicated().any() or frame["mesh_code"].isna().any():
        raise ValueError("census mesh codes must be unique and non-empty")
    household_text = frame["T001141034"].fillna("").str.strip()
    if household_text.isin(["", "-", "X"]).any():
        raise ValueError("required household values are suppressed or missing")
    frame["households"] = pd.to_numeric(household_text, errors="raise")
    if not frame["households"].map(lambda value: float(value).is_integer()).all() or (frame["households"] < 0).any():
        raise ValueError("household values must be finite non-negative integers")
    return frame, ["KEY_CODE", "HTKSYORI", "HTKSAKI", "GASSAN", "T001141034"]


def map_candidates_to_mesh(candidates: pd.DataFrame, census: pd.DataFrame) -> pd.DataFrame:
    polygons = gpd.GeoDataFrame(
        census[["mesh_code", "households", "HTKSYORI", "HTKSAKI", "GASSAN", "T001141034"]].copy(),
        geometry=[mesh_500m_polygon(code) for code in census["mesh_code"]],
        crs="EPSG:6668",
    )
    points = gpd.GeoDataFrame(candidates.copy(), geometry="geometry", crs="EPSG:4326")
    points = points.to_crs("EPSG:6668")
    joined = gpd.sjoin(points, polygons, how="left", predicate="within", lsuffix="candidate", rsuffix="mesh")
    if joined.index.duplicated().any():
        raise ValueError("candidate-to-mesh mapping is not one-to-one")
    if joined["mesh_code"].isna().any():
        raise ValueError("candidate-to-mesh mapping has unmatched candidates")
    joined = joined.sort_index().drop(columns=["index_mesh", "geometry"], errors="ignore")
    joined["mesh_code"] = joined["mesh_code"].astype(str)
    return joined


def main() -> int:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    candidate_path = ROOT / config["candidate"]["path"]
    census_path = ROOT / config["statistics"]["source_path"]
    if sha256(census_path) != config["statistics"]["source_sha256"]:
        raise ValueError("census source hash mismatch")
    if OUTPUT.exists():
        raise FileExistsError(f"run output already exists: {OUTPUT}")
    OUTPUT.mkdir(parents=True)

    candidates = load_candidates(candidate_path)
    census, source_columns = load_census(census_path)
    mapped = map_candidates_to_mesh(candidates, census)
    counts = mapped.groupby("mesh_code", sort=True).size().rename("candidate_count")
    mesh = census.set_index("mesh_code").join(counts, how="left").fillna({"candidate_count": 0})
    mesh["candidate_count"] = mesh["candidate_count"].astype(int)
    mesh["mesh_status"] = mesh["candidate_count"].map(
        lambda value: "adopted_candidate_mesh" if value > 0 else "N_m_zero_no_allocation"
    )
    adopted = mesh[mesh["candidate_count"] > 0].copy()
    if adopted.empty:
        raise ValueError("no candidate-linked census mesh")
    adopted["weight_sum_expected"] = adopted["households"].astype(float)
    adopted["weight_sum_observed"] = adopted["weight_sum_expected"]
    adopted["conservation_error"] = 0.0
    mesh_out = mesh.reset_index()[
        ["mesh_code", "households", "candidate_count", "HTKSYORI", "HTKSAKI", "GASSAN", "T001141034", "mesh_status"]
    ].rename(columns={"households": "H_m", "candidate_count": "N_m"})
    mesh_out.to_csv(OUTPUT / "mesh_weight_summary.csv", index=False)

    mapped["N_m"] = mapped["mesh_code"].map(mesh["candidate_count"]).astype(int)
    mapped["H_m"] = mapped["mesh_code"].map(mesh["households"]).astype(float)
    mapped["w_i"] = mapped["H_m"] / mapped["N_m"]
    mapped["weight_numerator_H_m"] = mapped["H_m"].astype(int)
    mapped["weight_denominator_N_m"] = mapped["N_m"].astype(int)
    mapped["weight_formula"] = "H_m/N_m"
    mapped["weight_unit"] = "household_equivalents_per_candidate"
    mapped["classification_H_m"] = "OBSERVED"
    mapped["classification_w_i"] = "COMPUTED"
    mapped["source"] = "e-Stat 2020 Census T001141034"
    mapped["source_mesh_crs"] = "EPSG:6668"
    mapped["transformation"] = "candidate WGS84 point within decoded 500m JGD2011 mesh; H_m divided by N_m"
    mapped[["stop_id", "building_id", "building_representative_point", "mesh_code", "H_m", "N_m", "w_i", "weight_numerator_H_m", "weight_denominator_N_m", "weight_formula", "weight_unit", "classification_H_m", "classification_w_i", "source", "source_mesh_crs", "transformation", "HTKSYORI", "HTKSAKI", "GASSAN", "T001141034"]].to_csv(OUTPUT / "candidate_demand_weights.csv", index=False)

    by_mesh = mapped.groupby("mesh_code", sort=True)["w_i"].sum()
    expected = adopted["households"].astype(float)
    conservation = (by_mesh - expected).abs()
    exact_conservation = {
        mesh_code: sum(
            (Fraction(int(row["H_m"]), int(row["N_m"])))
            for _, row in mapped[mapped["mesh_code"] == mesh_code].iterrows()
        ) == Fraction(int(households), 1)
        for mesh_code, households in adopted["households"].items()
    }
    exact_weight_total = sum(
        (Fraction(int(row["H_m"]), int(row["N_m"]))) for _, row in mapped.iterrows()
    )
    total_weight = float(mapped["w_i"].sum())
    total_households = float(expected.sum())
    validation = {
        "candidate_count": int(len(mapped)),
        "candidate_id_unique_nonempty": bool(mapped["stop_id"].is_unique and mapped["stop_id"].notna().all() and (mapped["stop_id"].str.strip() != "").all()),
        "candidate_to_mesh_unique": bool(len(mapped) == len(candidates) and mapped["mesh_code"].notna().all()),
        "finite_nonnegative": bool(mapped[["H_m", "N_m", "w_i"]].map(lambda value: pd.notna(value) and float(value) >= 0 and float(value) not in {float("inf"), float("-inf")}).all().all()),
        "N_m_zero_count": int((mesh["candidate_count"] == 0).sum()),
        "N_m_zero_rule": "recorded as N_m_zero_no_allocation; no adjacent mesh reallocation",
        "confidentiality_fields_preserved": source_columns[1:4],
        "aggregate_values_reallocated": False,
        "mesh_conservation_max_abs_error": float(conservation.max()),
        "mesh_conservation_float_tolerance": 1e-12,
        "mesh_conservation_float_pass": bool((conservation <= 1e-12).all()),
        "mesh_conservation_exact_rational_pass": bool(all(exact_conservation.values())),
        "mesh_conservation_pass": bool(all(exact_conservation.values())),
        "adopted_mesh_count": int(len(adopted)),
        "adopted_households_total": total_households,
        "weight_total": total_weight,
        "weight_total_matches_households": bool(total_weight == total_households),
        "weight_total_exact_rational_matches_households": bool(exact_weight_total == Fraction(int(total_households), 1)),
        "sampling_stratification": False,
        "quota": False,
    }
    (OUTPUT / "r04_weight_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "evrp-r04-demand-weight-v1",
        "run_id": config["run_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "code": {"path": "05_src/traffic_simulation/demand/generate_evrp_r04_demand_weights.py", "sha256": sha256(Path(__file__))},
        "config": {"path": str(CONFIG_PATH.relative_to(ROOT)), "sha256": sha256(CONFIG_PATH)},
        "inputs": {"candidate_csv": {"path": str(candidate_path.relative_to(ROOT)), "sha256": sha256(candidate_path)}, "census_zip": {"path": str(census_path.relative_to(ROOT)), "sha256": sha256(census_path), "member": config["statistics"]["member"], "household_column": "T001141034"}},
        "outputs": {},
        "transformation": "w_i = H_m / N_m; 500m mesh is a statistical input unit only",
        "validation": validation,
    }
    for path in sorted(OUTPUT.iterdir()):
        if path.name != "r04_weight_manifest.json":
            manifest["outputs"][path.name] = {"sha256": sha256(path), "path": str(path.relative_to(ROOT))}
    (OUTPUT / "r04_weight_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": config["run_id"], "validation": validation, "output": str(OUTPUT.relative_to(ROOT))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
