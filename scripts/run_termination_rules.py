#!/usr/bin/env python3
"""Finite-work comparison validation; no main-experiment entry point."""

# 2026-11-17: this entry point retains the historical timing-based contract.
# Check before imports so rejection cannot initialize solvers or write files.
if __name__ == "__main__":
    import sys as _history_sys
    if "--historical-reproduction" in _history_sys.argv:
        _history_sys.argv.remove("--historical-reproduction")
    elif any(arg in _history_sys.argv for arg in ("--help", "-h")):
        print("Historical entry point. Current analysis: scripts/analyze_dw.py. "
              "Use --historical-reproduction --help for the previous command options.")
        raise SystemExit(0)
    else:
        raise SystemExit("HISTORICAL_ENTRYPOINT: use scripts/analyze_dw.py for current D/W analysis; "
                         "pass --historical-reproduction only to reproduce the previous study")

from kmd_toc.termination_v1.runner import main
if __name__=='__main__':main()
