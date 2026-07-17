"""Canonical repository-relative paths for Tokyo traffic simulation."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Final


_REPOSITORY_SENTINELS: Final = (
    "compose.yaml",
    "00_project_management",
    "03_data",
    "05_src",
)


def find_repository_root(start: Path | str | None = None) -> Path:
    """Find the repository root without relying on a fixed parent index."""

    candidate = Path(start or __file__).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for directory in (candidate, *candidate.parents):
        if all((directory / sentinel).exists() for sentinel in _REPOSITORY_SENTINELS):
            return directory
    raise RuntimeError(f"Could not locate repository root from {candidate}")


REPOSITORY_ROOT: Final = find_repository_root()
RAW_ROOT: Final = REPOSITORY_ROOT / "03_data" / "raw" / "traffic_simulation"
PROCESSED_ROOT: Final = REPOSITORY_ROOT / "03_data" / "processed" / "traffic_simulation"
METADATA_ROOT: Final = REPOSITORY_ROOT / "03_data" / "metadata"
SOURCE_REGISTRY: Final = METADATA_ROOT / "traffic_simulation_sources.csv"
RUN_OUTPUT_ROOT: Final = REPOSITORY_ROOT / "reproducibility" / "outputs" / "traffic_simulation"
CURATED_OUTPUT_ROOT: Final = REPOSITORY_ROOT / "06_outputs" / "traffic_simulation"

RAW_DATASETS: Final = MappingProxyType(
    {
        "boundaries": RAW_ROOT / "boundaries",
        "charging": RAW_ROOT / "charging",
        "driver_behavior": RAW_ROOT / "driver_behavior",
        "freight": RAW_ROOT / "freight",
        "freight_network": RAW_ROOT / "freight_network",
        "gtfs": RAW_ROOT / "gtfs",
        "jartic": RAW_ROOT / "jartic",
        "logistics_hubs": RAW_ROOT / "logistics_hubs",
        "osm": RAW_ROOT / "osm",
        "population": RAW_ROOT / "population",
        "road_census": RAW_ROOT / "road_census",
        "tokyo_police": RAW_ROOT / "tokyo_police",
        "vehicles": RAW_ROOT / "vehicles",
    }
)

PROCESSED_DATASETS: Final = MappingProxyType(
    {
        "calibration": PROCESSED_ROOT / "calibration",
        "demand": PROCESSED_ROOT / "demand",
        "driver_behavior": PROCESSED_ROOT / "driver_behavior",
        "road_network": PROCESSED_ROOT / "road_network",
        "sumo_inputs": PROCESSED_ROOT / "sumo_inputs",
        "traffic_profiles": PROCESSED_ROOT / "traffic_profiles",
        "validation": PROCESSED_ROOT / "validation",
    }
)


def ensure_runtime_directories() -> None:
    """Create ignored runtime output directories when an environment starts."""

    for directory in (
        *RAW_DATASETS.values(),
        *PROCESSED_DATASETS.values(),
        RUN_OUTPUT_ROOT,
        CURATED_OUTPUT_ROOT,
    ):
        directory.mkdir(parents=True, exist_ok=True)
