"""Read-only authority consistency review; no execution authorization or historical writes."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '05_src'))
from traffic_simulation.validation.r23_evidence_gate import cli

def main():
    return cli('B1')

if __name__ == '__main__':
    raise SystemExit(main())
