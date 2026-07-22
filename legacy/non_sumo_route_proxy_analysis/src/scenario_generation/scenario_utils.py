"""Scenario construction utilities for the Tokyo synthetic EVRP analysis.

The functions in this module construct synthetic customer configurations and
route proxies.  They do not solve an EVRP and do not infer charging events,
charging demand, charger utilization, or electricity-grid load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class BaselineAssumptions:
    """Explicit baseline assumptions used by the route-proxy evaluation."""

    assumed_speed_kmh: float = 25.0
    road_distance_multiplier: float = 1.25
    operating_time_limit_min: float = 480.0
    initial_soc_ratio: float = 0.90
    reserve_soc_ratio: float = 0.20
    charging_time_limit_min: float = 60.0
    customer_demand_min_kg: int = 5
    customer_demand_max_kg: int = 30
    service_time_minimum_min: int = 5
    service_time_maximum_min: int = 15
    mainland_lat_min: float = 35.45
    mainland_lat_max: float = 35.95
    mainland_lon_min: float = 138.85
    mainland_lon_max: float = 140.25


def mesh_centroid(mesh_code: object) -> tuple[float, float]:
    """Return an approximate centroid for a Japanese 3rd/4th mesh code.

    The input data contain nine-digit codes.  The first eight digits are
    interpreted as the third-level mesh and the last digit as a 2x2
    subdivision using the conventional 1=SW, 2=SE, 3=NW, 4=NE ordering.
    The result is a spatial sampling proxy, not cadastral positioning.
    """

    try:
        text = str(int(float(mesh_code))).zfill(9)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid mesh_code {mesh_code!r}; expected a numeric nine-digit code.") from exc
    if len(text) != 9 or not text.isdigit():
        raise ValueError(f"Invalid mesh_code {mesh_code!r}; expected a numeric nine-digit code.")

    p, q = int(text[0:2]), int(text[2:4])
    latitude = p / 1.5
    longitude = q + 100.0
    latitude += int(text[4]) * (5.0 / 60.0)
    longitude += int(text[5]) * (7.5 / 60.0)
    latitude += int(text[6]) * (30.0 / 3600.0)
    longitude += int(text[7]) * (45.0 / 3600.0)
    lat_height = 30.0 / 3600.0
    lon_width = 45.0 / 3600.0

    quadrant = int(text[8])
    if quadrant in {1, 2, 3, 4}:
        lat_height /= 2.0
        lon_width /= 2.0
        if quadrant in {3, 4}:
            latitude += lat_height
        if quadrant in {2, 4}:
            longitude += lon_width
    return latitude + lat_height / 2.0, longitude + lon_width / 2.0


def haversine_km(
    latitude_1: np.ndarray | float,
    longitude_1: np.ndarray | float,
    latitude_2: np.ndarray | float,
    longitude_2: np.ndarray | float,
) -> np.ndarray:
    """Calculate great-circle distance in kilometres with broadcasting."""

    lat1 = np.radians(np.asarray(latitude_1, dtype=float))
    lon1 = np.radians(np.asarray(longitude_1, dtype=float))
    lat2 = np.radians(np.asarray(latitude_2, dtype=float))
    lon2 = np.radians(np.asarray(longitude_2, dtype=float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return EARTH_RADIUS_KM * 2.0 * np.arcsin(np.minimum(1.0, np.sqrt(a)))


def prepare_population_mesh(mesh: pd.DataFrame, assumptions: BaselineAssumptions) -> pd.DataFrame:
    """Validate and prepare population mesh cells for weighted sampling."""

    required = {"mesh_code", "total_population"}
    missing = sorted(required - set(mesh.columns))
    if missing:
        raise ValueError(f"Population mesh is missing required columns: {missing}.")
    output = mesh.copy()
    output["total_population"] = pd.to_numeric(output["total_population"], errors="raise")
    coordinates = output["mesh_code"].map(mesh_centroid)
    output["latitude"] = [item[0] for item in coordinates]
    output["longitude"] = [item[1] for item in coordinates]
    output = output[
        output["latitude"].between(assumptions.mainland_lat_min, assumptions.mainland_lat_max)
        & output["longitude"].between(assumptions.mainland_lon_min, assumptions.mainland_lon_max)
        & output["total_population"].gt(0)
    ].copy()
    if output.empty:
        raise ValueError("Population-mesh filtering produced zero eligible mainland cells.")
    output["sampling_weight"] = output["total_population"] / output["total_population"].sum()
    return output.reset_index(drop=True)


def generate_synthetic_customers(
    mesh: pd.DataFrame,
    customer_counts: Sequence[int],
    seeds: Sequence[int],
    assumptions: BaselineAssumptions,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate paired synthetic customer configurations.

    Locations are sampled without replacement using population weights.
    Demand and service time use explicitly synthetic discrete-uniform
    distributions.  The same customer-count/seed configuration is reused
    across vehicle-count and charger-condition comparisons.
    """

    prepared = prepare_population_mesh(mesh, assumptions)
    rows: list[dict[str, object]] = []
    registry: list[dict[str, object]] = []
    probabilities = prepared["sampling_weight"].to_numpy(dtype=float)

    for customer_count in customer_counts:
        if customer_count <= 0 or customer_count > len(prepared):
            raise ValueError(
                f"customer_count={customer_count} must be between 1 and {len(prepared)} eligible mesh cells."
            )
        for seed in seeds:
            configuration_id = f"C{customer_count:03d}_S{seed:03d}"
            rng = np.random.default_rng(int(seed) * 100_000 + int(customer_count))
            selected_index = rng.choice(len(prepared), size=int(customer_count), replace=False, p=probabilities)
            selected = prepared.iloc[selected_index].reset_index(drop=True)
            demand = rng.integers(
                assumptions.customer_demand_min_kg,
                assumptions.customer_demand_max_kg + 1,
                size=int(customer_count),
            )
            service = rng.integers(
                assumptions.service_time_minimum_min,
                assumptions.service_time_maximum_min + 1,
                size=int(customer_count),
            )
            for index, mesh_row in selected.iterrows():
                rows.append(
                    {
                        "customer_configuration_id": configuration_id,
                        "customer_count": int(customer_count),
                        "seed": int(seed),
                        "customer_id": f"{configuration_id}_N{index + 1:03d}",
                        "sampling_weight_source": "e-Stat total_population by mesh cell",
                        "mesh_code": str(int(float(mesh_row["mesh_code"]))).zfill(9),
                        "mesh_population": float(mesh_row["total_population"]),
                        "latitude": float(mesh_row["latitude"]),
                        "longitude": float(mesh_row["longitude"]),
                        "demand_kg": int(demand[index]),
                        "service_time_min": int(service[index]),
                        "time_window_start": 0.0,
                        "time_window_end": assumptions.operating_time_limit_min,
                        "customer_demand_source": "Synthetic discrete-uniform integer 5-30 kg assumption",
                        "customer_location_source": "Population-weighted synthetic sample; not observed orders",
                        "evidence_status": "Synthetic data with assumed parameters",
                    }
                )
            registry.append(
                {
                    "customer_configuration_id": configuration_id,
                    "seed": int(seed),
                    "customer_count": int(customer_count),
                    "customer_locations_randomized": True,
                    "customer_demands_randomized": True,
                    "service_times_randomized": True,
                    "vehicle_assignment_randomized": True,
                    "charger_availability_randomized": False,
                    "speed_randomized": False,
                    "pairing_rule": "Seed identifier retained across all vehicle-count and charger conditions",
                    "analysis_name": "Monte Carlo spatial sensitivity analysis",
                }
            )
    customers = pd.DataFrame(rows)
    randomization = pd.DataFrame(registry)
    if customers.duplicated(["customer_configuration_id", "customer_id"]).any():
        raise ValueError("Synthetic customer generation produced duplicate configuration/customer keys.")
    return customers, randomization


def build_charger_condition_definitions() -> pd.DataFrame:
    """Return explicit conservative, balanced, and broad charger policies."""

    return pd.DataFrame(
        [
            {
                "charger_condition": "conservative",
                "minimum_power_kw": 50.0,
                "maximum_access_distance_km": 3.0,
                "usage_type_policy": "Retain missing usage type and flag public access as unknown",
                "missing_power_policy": "Exclude",
                "missing_usage_type_policy": "Retain and flag Unknown",
                "public_access_required": False,
                "charging_time_limit_min": 60.0,
                "connector_compatibility_policy": "Require reported CHAdeMO",
                "operating_status_policy": "Require reported Operational",
                "condition_definition": "Operational CHAdeMO connection with known power >= 50 kW; 3 km access threshold",
            },
            {
                "charger_condition": "balanced",
                "minimum_power_kw": 40.0,
                "maximum_access_distance_km": 5.0,
                "usage_type_policy": "Retain missing usage type and flag public access as unknown",
                "missing_power_policy": "Exclude",
                "missing_usage_type_policy": "Retain and flag Unknown",
                "public_access_required": False,
                "charging_time_limit_min": 60.0,
                "connector_compatibility_policy": "Require reported CHAdeMO",
                "operating_status_policy": "Exclude only explicitly unavailable records; retain missing status as Unknown",
                "condition_definition": "CHAdeMO connection not explicitly unavailable with known power >= 40 kW; 5 km access threshold",
            },
            {
                "charger_condition": "broad",
                "minimum_power_kw": np.nan,
                "maximum_access_distance_km": 10.0,
                "usage_type_policy": "Retain missing usage type and flag public access as unknown",
                "missing_power_policy": "Retain for geography; exclude from duration evaluation",
                "missing_usage_type_policy": "Retain and flag Unknown",
                "public_access_required": False,
                "charging_time_limit_min": 90.0,
                "connector_compatibility_policy": "Retain non-Tesla candidates; compatibility must be reported CHAdeMO for range assistance",
                "operating_status_policy": "Exclude only explicitly unavailable records; retain missing status as Unknown",
                "condition_definition": "Non-Tesla candidate not explicitly unavailable; 10 km geographic threshold; unknown power/connector retained only for access",
            },
        ]
    )


def build_eligible_charger_candidates(
    connections: pd.DataFrame, definitions: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply condition-specific charger screening without claiming availability."""

    required = {
        "ocm_id",
        "connection_id",
        "latitude",
        "longitude",
        "connection_type",
        "power_kw",
        "operator",
        "usage_type",
        "status_type",
    }
    missing = sorted(required - set(connections.columns))
    if missing:
        raise ValueError(f"Charger connection input is missing required columns: {missing}.")
    source = connections.copy()
    source["power_kw_numeric"] = pd.to_numeric(source["power_kw"], errors="coerce")
    source["charger_candidate_id"] = (
        source["ocm_id"].astype("Int64").astype(str)
        + "_"
        + source["connection_id"].astype("Int64").astype(str)
    )
    combined = (
        source["operator"].fillna("").astype(str)
        + " "
        + source["connection_type"].fillna("").astype(str)
    )
    valid_location = source[["latitude", "longitude"]].notna().all(axis=1)
    non_tesla = ~combined.str.contains("Tesla|NACS", case=False, regex=True)
    chademo = source["connection_type"].fillna("").str.contains("CHAdeMO", case=False)
    operational = source["status_type"].fillna("").str.fullmatch("Operational", case=False)
    explicitly_unavailable = source["status_type"].fillna("").str.contains(
        "not operational|removed|closed|unavailable", case=False, regex=True
    )
    known_power = source["power_kw_numeric"].notna() & source["power_kw_numeric"].gt(0)

    masks = {
        "conservative": valid_location & non_tesla & chademo & operational & known_power & source["power_kw_numeric"].ge(50),
        "balanced": valid_location & non_tesla & chademo & ~explicitly_unavailable & known_power & source["power_kw_numeric"].ge(40),
        "broad": valid_location & non_tesla & ~explicitly_unavailable,
    }
    output: list[pd.DataFrame] = []
    for condition in definitions["charger_condition"]:
        selected = source.loc[masks[str(condition)]].copy()
        selected["charger_condition"] = str(condition)
        selected["charger_public_access_known"] = selected["usage_type"].notna()
        selected["charger_power_known"] = selected["power_kw_numeric"].notna()
        selected["charger_connector_compatibility_known"] = selected["connection_type"].eq("CHAdeMO")
        selected["charger_operating_status_known"] = selected["status_type"].notna()
        selected["assistance_eligible"] = (
            selected["connection_type"].eq("CHAdeMO") & selected["power_kw_numeric"].gt(0)
        )
        selected["screening_interpretation"] = (
            "Candidate retained under an analytical condition; actual access and availability are not established."
        )
        output.append(selected)
    candidates = pd.concat(output, ignore_index=True)
    counts = (
        candidates.groupby("charger_condition", as_index=False)
        .agg(
            eligible_charger_candidate_count=("charger_candidate_id", "nunique"),
            selected_charger_count=("charger_candidate_id", "nunique"),
            assistance_eligible_charger_count=("assistance_eligible", "sum"),
        )
    )
    definitions_with_counts = definitions.merge(counts, on="charger_condition", how="left")
    for column in [
        "eligible_charger_candidate_count",
        "selected_charger_count",
        "assistance_eligible_charger_count",
    ]:
        definitions_with_counts[column] = definitions_with_counts[column].fillna(0).astype(int)
    return candidates, definitions_with_counts


def select_baseline_vehicle(vehicle_specs: pd.DataFrame) -> pd.Series:
    """Select one coherent vehicle scenario instead of combining minima/maxima."""

    required = {
        "scenario_vehicle_id",
        "vehicle_model",
        "battery_kwh",
        "catalog_range_km",
        "payload_kg",
        "energy_consumption_kwh_per_km",
    }
    missing = sorted(required - set(vehicle_specs.columns))
    if missing:
        raise ValueError(f"Vehicle input is missing required columns: {missing}.")
    preferred_id = "mitsubishi_fuso_ecanter_s_yamato"
    selected = vehicle_specs[vehicle_specs["scenario_vehicle_id"].eq(preferred_id)]
    if len(selected) != 1:
        raise ValueError(
            f"Expected one coherent baseline vehicle row {preferred_id!r}; found {len(selected)}."
        )
    row = selected.iloc[0].copy()
    for column in ["battery_kwh", "catalog_range_km", "payload_kg", "energy_consumption_kwh_per_km"]:
        row[column] = float(pd.to_numeric(row[column], errors="raise"))
    return row


def build_analysis_configurations(
    customer_counts: Sequence[int],
    vehicle_counts: Sequence[int],
    charger_definitions: pd.DataFrame,
    vehicle: pd.Series,
    assumptions: BaselineAssumptions,
    independent_seed_count: int,
) -> pd.DataFrame:
    """Build the full customer x vehicle x charger factorial design."""

    rows: list[dict[str, object]] = []
    usable_ratio = assumptions.initial_soc_ratio - assumptions.reserve_soc_ratio
    if usable_ratio <= 0:
        raise ValueError("initial_soc_ratio must exceed reserve_soc_ratio.")
    for customer_count in customer_counts:
        for vehicle_count in vehicle_counts:
            for charger in charger_definitions.itertuples(index=False):
                scenario_id = (
                    f"C{int(customer_count):03d}_V{int(vehicle_count):02d}_"
                    f"CHG_{charger.charger_condition}_SPEED{assumptions.assumed_speed_kmh:g}_"
                    f"T{assumptions.operating_time_limit_min:g}"
                )
                rows.append(
                    {
                        "scenario_id": scenario_id,
                        "analysis_configuration_id": scenario_id,
                        "experimental_condition": "Factorial synthetic EVRP constraint evaluation",
                        "scenario_size": {25: "small", 50: "medium", 100: "large"}.get(
                            int(customer_count), f"C{int(customer_count)}"
                        ),
                        "customer_count": int(customer_count),
                        "vehicle_count": int(vehicle_count),
                        "customers_per_vehicle": float(customer_count) / float(vehicle_count),
                        "charger_condition": charger.charger_condition,
                        "eligible_charger_candidate_count": int(charger.eligible_charger_candidate_count),
                        "selected_charger_count": int(charger.selected_charger_count),
                        "minimum_power_kw": charger.minimum_power_kw,
                        "maximum_access_distance_km": float(charger.maximum_access_distance_km),
                        "usage_type_policy": charger.usage_type_policy,
                        "missing_power_policy": charger.missing_power_policy,
                        "missing_usage_type_policy": charger.missing_usage_type_policy,
                        "public_access_required": bool(charger.public_access_required),
                        "charging_time_limit_min": float(charger.charging_time_limit_min),
                        "connector_compatibility_policy": charger.connector_compatibility_policy,
                        "vehicle_type": vehicle["vehicle_model"],
                        "vehicle_scenario_id": vehicle["scenario_vehicle_id"],
                        "payload_capacity_kg": float(vehicle["payload_kg"]),
                        "battery_capacity_kwh": float(vehicle["battery_kwh"]),
                        "nominal_range_km": float(vehicle["catalog_range_km"]),
                        "usable_range_km": float(vehicle["catalog_range_km"]) * usable_ratio,
                        "initial_soc_ratio": assumptions.initial_soc_ratio,
                        "reserve_soc_ratio": assumptions.reserve_soc_ratio,
                        "operating_time_limit_min": assumptions.operating_time_limit_min,
                        "assumed_speed_kmh": assumptions.assumed_speed_kmh,
                        "road_distance_multiplier": assumptions.road_distance_multiplier,
                        "service_time_per_customer_min": "Synthetic discrete uniform integer 5-15",
                        "route_generation_method": "KMeans customer assignment plus nearest-neighbor visit-order proxy",
                        "customer_demand_source": "Synthetic discrete-uniform integer 5-30 kg assumption",
                        "customer_location_source": "Population-weighted synthetic sample from e-Stat mesh",
                        "independent_seed_count": int(independent_seed_count),
                        "conditional_case_count": int(independent_seed_count),
                        "route_proxy_status": "Not an optimized EVRP solution or road-network route",
                    }
                )
    result = pd.DataFrame(rows)
    if result["scenario_id"].duplicated().any():
        raise ValueError("Scenario ID construction produced duplicate identifiers.")
    return result


def _nearest_depot(customer_group: pd.DataFrame, depots: pd.DataFrame) -> pd.Series:
    centroid_lat = float(customer_group["latitude"].mean())
    centroid_lon = float(customer_group["longitude"].mean())
    distances = haversine_km(
        centroid_lat,
        centroid_lon,
        depots["latitude"].to_numpy(),
        depots["longitude"].to_numpy(),
    )
    return depots.iloc[int(np.nanargmin(distances))]


def _nearest_neighbor_order(
    customer_group: pd.DataFrame, depot_latitude: float, depot_longitude: float
) -> list[int]:
    remaining = list(range(len(customer_group)))
    order: list[int] = []
    current_lat, current_lon = depot_latitude, depot_longitude
    coordinates = customer_group[["latitude", "longitude"]].to_numpy(dtype=float)
    while remaining:
        candidate = coordinates[remaining]
        distances = haversine_km(current_lat, current_lon, candidate[:, 0], candidate[:, 1])
        position = int(np.argmin(distances))
        selected = remaining.pop(position)
        order.append(selected)
        current_lat, current_lon = coordinates[selected]
    return order


def construct_route_proxies(
    customers: pd.DataFrame,
    depots: pd.DataFrame,
    customer_counts: Sequence[int],
    vehicle_counts: Sequence[int],
    seeds: Sequence[int],
    assumptions: BaselineAssumptions,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Construct KMeans/nearest-neighbour route proxies and traceable edges."""

    depot_required = {"scenario_depot_id", "latitude", "longitude"}
    missing = sorted(depot_required - set(depots.columns))
    if missing:
        raise ValueError(f"Depot input is missing required columns: {missing}.")
    depots_clean = depots.dropna(subset=["latitude", "longitude"]).copy()
    if depots_clean.empty:
        raise ValueError("No depot candidate has valid coordinates.")

    route_rows: list[dict[str, object]] = []
    edge_rows: list[dict[str, object]] = []
    member_rows: list[dict[str, object]] = []

    for customer_count in customer_counts:
        for seed in seeds:
            configuration_id = f"C{int(customer_count):03d}_S{int(seed):03d}"
            customer_group = customers[
                customers["customer_configuration_id"].eq(configuration_id)
            ].reset_index(drop=True)
            if len(customer_group) != int(customer_count):
                raise ValueError(
                    f"Configuration {configuration_id} expected {customer_count} customers; found {len(customer_group)}."
                )
            depot = _nearest_depot(customer_group, depots_clean)
            coordinates = customer_group[["latitude", "longitude"]].to_numpy(dtype=float)
            for vehicle_count in vehicle_counts:
                if int(vehicle_count) > len(customer_group):
                    raise ValueError("vehicle_count cannot exceed customer_count in the proxy construction.")
                if int(vehicle_count) == 1:
                    labels = np.zeros(len(customer_group), dtype=int)
                else:
                    model = KMeans(
                        n_clusters=int(vehicle_count),
                        random_state=int(seed),
                        n_init=20,
                    )
                    labels = model.fit_predict(coordinates)
                assigned = customer_group.copy()
                assigned["route_cluster"] = labels
                for route_index, (_, route_customers) in enumerate(
                    assigned.groupby("route_cluster", sort=True), start=1
                ):
                    route_customers = route_customers.reset_index(drop=True)
                    base_route_id = (
                        f"C{int(customer_count):03d}_V{int(vehicle_count):02d}_"
                        f"S{int(seed):03d}_R{route_index:02d}"
                    )
                    visit_order = _nearest_neighbor_order(
                        route_customers, float(depot["latitude"]), float(depot["longitude"])
                    )
                    ordered = route_customers.iloc[visit_order].reset_index(drop=True)
                    previous_id = str(depot["scenario_depot_id"])
                    previous_type = "depot_proxy"
                    previous_lat = float(depot["latitude"])
                    previous_lon = float(depot["longitude"])
                    total_haversine = 0.0
                    for visit_position, customer in enumerate(ordered.itertuples(index=False), start=1):
                        edge_distance = float(
                            haversine_km(previous_lat, previous_lon, customer.latitude, customer.longitude)
                        )
                        total_haversine += edge_distance
                        edge_rows.append(
                            {
                                "base_route_proxy_id": base_route_id,
                                "customer_configuration_id": configuration_id,
                                "customer_count": int(customer_count),
                                "vehicle_count": int(vehicle_count),
                                "seed": int(seed),
                                "proxy_edge_order": int(visit_position),
                                "from_node_id": previous_id,
                                "from_node_type": previous_type,
                                "from_latitude": previous_lat,
                                "from_longitude": previous_lon,
                                "to_node_id": customer.customer_id,
                                "to_node_type": "synthetic_customer",
                                "to_latitude": float(customer.latitude),
                                "to_longitude": float(customer.longitude),
                                "haversine_distance_km": edge_distance,
                                "road_adjusted_distance_km": edge_distance
                                * assumptions.road_distance_multiplier,
                                "network_distance_km": np.nan,
                                "edge_interpretation": "Proxy edge showing visit order; not an actual road path.",
                            }
                        )
                        member_rows.append(
                            {
                                "base_route_proxy_id": base_route_id,
                                "customer_configuration_id": configuration_id,
                                "customer_count": int(customer_count),
                                "vehicle_count": int(vehicle_count),
                                "seed": int(seed),
                                "proxy_visit_order": int(visit_position),
                                "node_id": customer.customer_id,
                                "node_type": "synthetic_customer",
                                "latitude": float(customer.latitude),
                                "longitude": float(customer.longitude),
                                "demand_kg": float(customer.demand_kg),
                                "service_time_min": float(customer.service_time_min),
                            }
                        )
                        previous_id = customer.customer_id
                        previous_type = "synthetic_customer"
                        previous_lat = float(customer.latitude)
                        previous_lon = float(customer.longitude)
                    return_distance = float(
                        haversine_km(
                            previous_lat,
                            previous_lon,
                            float(depot["latitude"]),
                            float(depot["longitude"]),
                        )
                    )
                    total_haversine += return_distance
                    edge_rows.append(
                        {
                            "base_route_proxy_id": base_route_id,
                            "customer_configuration_id": configuration_id,
                            "customer_count": int(customer_count),
                            "vehicle_count": int(vehicle_count),
                            "seed": int(seed),
                            "proxy_edge_order": int(len(ordered) + 1),
                            "from_node_id": previous_id,
                            "from_node_type": previous_type,
                            "from_latitude": previous_lat,
                            "from_longitude": previous_lon,
                            "to_node_id": str(depot["scenario_depot_id"]),
                            "to_node_type": "depot_proxy",
                            "to_latitude": float(depot["latitude"]),
                            "to_longitude": float(depot["longitude"]),
                            "haversine_distance_km": return_distance,
                            "road_adjusted_distance_km": return_distance
                            * assumptions.road_distance_multiplier,
                            "network_distance_km": np.nan,
                            "edge_interpretation": "Proxy edge showing visit order; not an actual road path.",
                        }
                    )
                    member_rows.append(
                        {
                            "base_route_proxy_id": base_route_id,
                            "customer_configuration_id": configuration_id,
                            "customer_count": int(customer_count),
                            "vehicle_count": int(vehicle_count),
                            "seed": int(seed),
                            "proxy_visit_order": 0,
                            "node_id": str(depot["scenario_depot_id"]),
                            "node_type": "depot_proxy",
                            "latitude": float(depot["latitude"]),
                            "longitude": float(depot["longitude"]),
                            "demand_kg": 0.0,
                            "service_time_min": 0.0,
                        }
                    )
                    route_rows.append(
                        {
                            "base_route_proxy_id": base_route_id,
                            "customer_configuration_id": configuration_id,
                            "customer_count": int(customer_count),
                            "vehicle_count": int(vehicle_count),
                            "seed": int(seed),
                            "route_index": int(route_index),
                            "depot_candidate_id": str(depot["scenario_depot_id"]),
                            "eligible_depot_candidate_count": int(len(depots_clean)),
                            "selected_depot_count": 1,
                            "customer_count_on_route": int(len(ordered)),
                            "haversine_distance_km": total_haversine,
                            "road_adjusted_distance_km": total_haversine
                            * assumptions.road_distance_multiplier,
                            "network_distance_km": np.nan,
                            "route_proxy_distance_km": total_haversine
                            * assumptions.road_distance_multiplier,
                            "route_total_demand_kg": float(ordered["demand_kg"].sum()),
                            "service_time_total_min": float(ordered["service_time_min"].sum()),
                            "route_generation_method": "KMeans assignment plus nearest-neighbor visit-order proxy",
                            "route_proxy_limitation": "Not an EVRP optimum; not time-window/SOC optimized; not a road-network path.",
                        }
                    )
    routes = pd.DataFrame(route_rows)
    edges = pd.DataFrame(edge_rows)
    members = pd.DataFrame(member_rows)
    expected_routes = len(seeds) * sum(int(v) for v in vehicle_counts) * len(customer_counts)
    if len(routes) != expected_routes:
        raise ValueError(f"Expected {expected_routes} base route proxies; generated {len(routes)}.")
    return routes, edges, members


def _nearest_candidate_for_route(
    route_members: pd.DataFrame, candidates: pd.DataFrame
) -> tuple[pd.Series | None, float]:
    if candidates.empty:
        return None, float("nan")
    points_lat = route_members["latitude"].to_numpy(dtype=float)[:, None]
    points_lon = route_members["longitude"].to_numpy(dtype=float)[:, None]
    candidate_lat = candidates["latitude"].to_numpy(dtype=float)[None, :]
    candidate_lon = candidates["longitude"].to_numpy(dtype=float)[None, :]
    matrix = haversine_km(points_lat, points_lon, candidate_lat, candidate_lon)
    flat_index = int(np.nanargmin(matrix))
    _, candidate_position = np.unravel_index(flat_index, matrix.shape)
    return candidates.iloc[int(candidate_position)], float(matrix.flat[flat_index])


def evaluate_routes_by_condition(
    base_routes: pd.DataFrame,
    route_members: pd.DataFrame,
    configurations: pd.DataFrame,
    charger_candidates: pd.DataFrame,
    vehicle: pd.Series,
    assumptions: BaselineAssumptions,
) -> pd.DataFrame:
    """Evaluate route proxies under each analytical charger condition.

    Charging-related outputs are limited to geographic access, simplified
    range assistance, and constant-power duration feasibility.  No charger
    choice behaviour, event time, energy demand, utilization, or grid load is
    inferred.
    """

    member_groups = {key: group for key, group in route_members.groupby("base_route_proxy_id")}
    configuration_lookup = configurations.set_index(
        ["customer_count", "vehicle_count", "charger_condition"]
    )
    battery_capacity = float(vehicle["battery_kwh"])
    nominal_range = float(vehicle["catalog_range_km"])
    energy_per_km = float(vehicle["energy_consumption_kwh_per_km"])
    payload_capacity = float(vehicle["payload_kg"])
    initial_soc_kwh = battery_capacity * assumptions.initial_soc_ratio
    reserve_soc_kwh = battery_capacity * assumptions.reserve_soc_ratio
    usable_energy_kwh = initial_soc_kwh - reserve_soc_kwh
    usable_range_km = nominal_range * (
        assumptions.initial_soc_ratio - assumptions.reserve_soc_ratio
    )

    rows: list[dict[str, object]] = []
    for route in base_routes.itertuples(index=False):
        members = member_groups[route.base_route_proxy_id]
        for condition, condition_candidates in charger_candidates.groupby("charger_condition"):
            configuration = configuration_lookup.loc[
                (int(route.customer_count), int(route.vehicle_count), str(condition))
            ]
            nearest, nearest_haversine = _nearest_candidate_for_route(members, condition_candidates)
            assistance_candidates = condition_candidates[condition_candidates["assistance_eligible"]]
            assistance, assistance_haversine = _nearest_candidate_for_route(
                members, assistance_candidates
            )
            multiplier = float(configuration["road_distance_multiplier"])
            nearest_distance = nearest_haversine * multiplier if nearest is not None else np.nan
            assistance_distance = (
                assistance_haversine * multiplier if assistance is not None else np.nan
            )
            access_threshold = float(configuration["maximum_access_distance_km"])
            geographic_access = bool(np.isfinite(nearest_distance) and nearest_distance <= access_threshold)
            assistance_access = bool(
                np.isfinite(assistance_distance) and assistance_distance <= access_threshold
            )
            route_distance = float(route.route_proxy_distance_km)
            estimated_energy = route_distance * energy_per_km
            range_feasible = route_distance <= usable_range_km
            required_proxy = not range_feasible
            supplemental_energy = max(0.0, estimated_energy - usable_energy_kwh)
            assistance_power = (
                float(assistance["power_kw_numeric"])
                if assistance is not None and pd.notna(assistance["power_kw_numeric"])
                else np.nan
            )
            estimated_duration = (
                supplemental_energy / assistance_power * 60.0
                if required_proxy and assistance_power > 0
                else (0.0 if not required_proxy else np.nan)
            )
            assisted_evaluated = required_proxy
            assisted_range = (
                bool(assistance_access and route_distance <= 2.0 * usable_range_km)
                if assisted_evaluated
                else pd.NA
            )
            duration_evaluated = bool(
                required_proxy and assistance_access and np.isfinite(estimated_duration)
            )
            duration_feasible = (
                bool(estimated_duration <= float(configuration["charging_time_limit_min"]))
                if duration_evaluated
                else pd.NA
            )
            travel_time = route_distance / float(configuration["assumed_speed_kmh"]) * 60.0
            service_time = float(route.service_time_total_min)
            charging_time_total = 0.0
            waiting_time = 0.0
            detour_time = 0.0
            total_duration = travel_time + service_time + charging_time_total + waiting_time + detour_time
            operating_limit = float(configuration["operating_time_limit_min"])
            route_demand = float(route.route_total_demand_kg)
            row = route._asdict()
            row.update(
                {
                    "scenario_id": configuration["scenario_id"],
                    "analysis_configuration_id": configuration["analysis_configuration_id"],
                    "charger_condition": str(condition),
                    "scenario_route_proxy_id": f"{configuration['scenario_id']}__S{int(route.seed):03d}_R{int(route.route_index):02d}",
                    "charger_candidate_count": int(condition_candidates["charger_candidate_id"].nunique()),
                    "nearest_candidate_charger_id": nearest["charger_candidate_id"] if nearest is not None else "Data unavailable",
                    "nearest_charger_haversine_distance_km": nearest_haversine,
                    "nearest_charger_distance_km": nearest_distance,
                    "maximum_charger_access_distance_km": access_threshold,
                    "charger_geographically_accessible": geographic_access,
                    "charger_public_access_known": bool(nearest["charger_public_access_known"]) if nearest is not None else False,
                    "charger_power_known": bool(nearest["charger_power_known"]) if nearest is not None else False,
                    "charger_connector_compatibility_known": bool(nearest["charger_connector_compatibility_known"]) if nearest is not None else False,
                    "charger_operating_status_known": bool(nearest["charger_operating_status_known"]) if nearest is not None else False,
                    "assistance_candidate_charger_id": assistance["charger_candidate_id"] if assistance is not None else "Data unavailable",
                    "assistance_candidate_distance_km": assistance_distance,
                    "assistance_candidate_power_kw": assistance_power,
                    "nominal_range_km": nominal_range,
                    "usable_range_km": usable_range_km,
                    "battery_capacity_kwh": battery_capacity,
                    "initial_soc_kwh": initial_soc_kwh,
                    "reserve_soc_kwh": reserve_soc_kwh,
                    "minimum_soc_kwh": reserve_soc_kwh,
                    "estimated_energy_kwh": estimated_energy,
                    "base_consumption_kwh_per_km": energy_per_km,
                    "payload_adjustment": "Not modeled",
                    "speed_adjustment": "Not modeled",
                    "temperature_adjustment": "Not modeled",
                    "charging_efficiency": "Not modeled",
                    "range_feasible": bool(range_feasible),
                    "soc_feasible": "Not evaluated",
                    "energy_feasible": "Not evaluated",
                    "range_based_charging_required_proxy": bool(required_proxy),
                    "charging_assisted_range_evaluated": bool(assisted_evaluated),
                    "charging_assisted_range_feasible": assisted_range,
                    "charger_arrival_soc_feasible": "Not evaluated",
                    "estimated_supplemental_energy_kwh_for_duration_proxy": supplemental_energy,
                    "estimated_supplemental_charging_duration_min": estimated_duration,
                    "charging_duration_evaluated": duration_evaluated,
                    "charging_duration_feasible": duration_feasible,
                    "charging_time_limit_min": float(configuration["charging_time_limit_min"]),
                    "vehicle_payload_capacity_kg": payload_capacity,
                    "payload_utilization_ratio": route_demand / payload_capacity,
                    "payload_excess_kg": max(0.0, route_demand - payload_capacity),
                    "payload_feasible": bool(route_demand <= payload_capacity),
                    "travel_time_min": travel_time,
                    "service_time_total_min": service_time,
                    "charging_time_total_min": charging_time_total,
                    "waiting_time_total_min": waiting_time,
                    "detour_time_min": detour_time,
                    "total_route_duration_min": total_duration,
                    "operating_time_limit_min": operating_limit,
                    "time_overrun_min": max(0.0, total_duration - operating_limit),
                    "operating_time_feasible": bool(total_duration <= operating_limit),
                    "charging_time_in_operating_time_evaluation": False,
                    "waiting_time_status": "Not modeled; fixed to 0",
                    "detour_time_status": "Not modeled; fixed to 0",
                    "time_window_feasibility": "Not evaluated",
                    "network_mode_status": "Data unavailable; baseline haversine-plus-multiplier mode used",
                    "evaluation_scope": "Synthetic route-proxy constraint evaluation; not observed delivery performance",
                }
            )
            rows.append(row)
    output = pd.DataFrame(rows)
    boolean_nullable = ["charging_assisted_range_feasible", "charging_duration_feasible"]
    for column in boolean_nullable:
        output[column] = output[column].astype("boolean")
    expected = len(base_routes) * configurations["charger_condition"].nunique()
    if len(output) != expected:
        raise ValueError(f"Expected {expected} condition-route evaluations; generated {len(output)}.")
    return output


def summarize_distance(route_results: pd.DataFrame) -> pd.DataFrame:
    """Summarize route-proxy distance as a continuous outcome, not a constraint."""

    values = pd.to_numeric(route_results["route_proxy_distance_km"], errors="raise")
    return pd.DataFrame(
        [
            {
                "metric": "route_proxy_distance_km",
                "mean": float(values.mean()),
                "median": float(values.median()),
                "standard_deviation": float(values.std(ddof=1)),
                "percentile_5": float(values.quantile(0.05)),
                "percentile_95": float(values.quantile(0.95)),
                "maximum": float(values.max()),
                "distance_unmet_rate": "Not applicable",
                "travel_cost_unmet_rate": "Not applicable",
                "interpretation": "Continuous route-proxy outcome; no distance or cost budget threshold is defined.",
            }
        ]
    )
