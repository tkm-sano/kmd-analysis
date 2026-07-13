from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "03_data/processed"

def test_expected_counts():
    assert len(pd.read_csv(DATA / "scenario/scenario_configurations.csv")) == 27
    assert len(pd.read_csv(DATA / "scenario/synthetic_customers.csv")) == 17500
    routes = pd.read_csv(DATA / "route_proxy/route_proxy_results.csv")
    assert len(routes) == 8100
    assert routes[["scenario_id", "seed"]].drop_duplicates().shape[0] == 2700

def test_core_ranges_and_flags():
    routes = pd.read_csv(DATA / "route_proxy/route_proxy_results.csv")
    assert (routes["route_proxy_distance_km"] >= 0).all()
    assert (routes["nearest_charger_distance_km"].dropna() >= 0).all()
    summary = pd.read_csv(DATA / "constraints/constraint_summary.csv")
    assert summary["route_weighted_unmet_rate"].dropna().between(0, 1).all()

def test_customer_schema_and_coordinates():
    c = pd.read_csv(DATA / "scenario/synthetic_customers.csv")
    required = {"customer_configuration_id","customer_id","seed","latitude","longitude","demand_kg"}
    assert required <= set(c.columns)
    assert not c.duplicated(["customer_configuration_id", "customer_id"]).any()
    assert c.latitude.between(35.45, 35.95).all()
    assert c.longitude.between(138.85, 140.25).all()

def test_haversine_known_example():
    import sys
    sys.path.insert(0, str(ROOT / "05_src/scenario_generation"))
    from scenario_utils import haversine_km
    assert abs(float(haversine_km(35.6812,139.7671,35.6895,139.6917)) - 6.88) < 0.25
