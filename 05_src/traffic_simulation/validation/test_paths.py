from __future__ import annotations

from traffic_simulation import paths


def test_repository_root_is_discovered_from_package_location() -> None:
    assert paths.REPOSITORY_ROOT == paths.find_repository_root(__file__)
    assert (paths.REPOSITORY_ROOT / "compose.yaml").is_file()


def test_traffic_paths_are_repository_relative_and_canonical() -> None:
    assert paths.RAW_ROOT.relative_to(paths.REPOSITORY_ROOT).as_posix() == (
        "03_data/raw/traffic_simulation"
    )
    assert paths.PROCESSED_ROOT.relative_to(paths.REPOSITORY_ROOT).as_posix() == (
        "03_data/processed/traffic_simulation"
    )
    assert paths.SOURCE_REGISTRY.relative_to(paths.REPOSITORY_ROOT).as_posix() == (
        "03_data/metadata/traffic_simulation_sources.csv"
    )
    assert all(path.is_relative_to(paths.REPOSITORY_ROOT) for path in paths.RAW_DATASETS.values())


def test_source_specific_directories_match_tracked_skeleton() -> None:
    assert set(paths.RAW_DATASETS) == {
        "boundaries",
        "charging",
        "driver_behavior",
        "freight",
        "freight_network",
        "gtfs",
        "jartic",
        "logistics_hubs",
        "osm",
        "population",
        "road_census",
        "tokyo_police",
        "vehicles",
    }
    assert all(directory.is_dir() for directory in paths.RAW_DATASETS.values())
