"""Read-only replacement for a historical report/authorization generator.

Original source is preserved in git and the I03 source snapshot.
This entrypoint never overwrites historical evidence or authorizes execution.
All reported outcomes come from the shared evidence validator.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "05_src"))
from traffic_simulation.validation.r23_evidence_gate import cli

def main():
    return cli("B2_FAILURE")

if __name__ == "__main__":
    raise SystemExit(main())
