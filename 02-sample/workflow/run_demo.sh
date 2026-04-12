#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python src/run_analysis_environment.py demo
