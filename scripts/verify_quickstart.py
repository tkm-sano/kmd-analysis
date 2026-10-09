"""One-command lightweight API and six-notebook verification; no scientific reruns."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    if not __debug__:
        raise SystemExit("Do not use -O: scientific fixture assertions must be enabled")
    env = dict(os.environ)
    for key in ("PYTHONPATH", "LD_LIBRARY_PATH", "PYTHONHOME"):
        env.pop(key, None)
    env.update(PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    routing_cases = [
        "test_exact_and_independent_schedule", "test_changed_time_window",
        "test_unavailable_route", "test_capacity_is_independently_checked",
        "test_dual_certificate_validation", "test_equal_cost_tie_break",
    ]
    commands = [
        ["tests/test_distribution_layout.py"],
        ["tests/test_frozen_runtime_sources.py"],
        ["tests/test_routing_migration.py", *["RoutingMigrationTests." + n for n in routing_cases]],
        ["tests/test_quantum_migration.py", "QuantumCoreTests"],
        ["tests/test_formal_quantum_api.py"],
        ["tests/test_simulation_api.py"],
        ["tests/test_battery_energy_api.py"],
        ["tests/test_analysis_api.py"],
        ["notebooks/test_notebooks.py"],
    ]
    for args in commands:
        print("RUN", " ".join(args), flush=True)
        subprocess.run([sys.executable, "-B", *args], cwd=ROOT, env=env, check=True, timeout=240)
    print("PASS: 45 API/contract tests + 1 frozen-runtime integrity test and six default notebooks. Full research and legacy aliases excluded.")

if __name__ == "__main__":
    main()
