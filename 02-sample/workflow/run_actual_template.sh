#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python src/validate_inputs.py --input_dir data/actual_input
python src/run_analysis_environment.py actual --input_dir data/actual_input --output_dir data/output/actual_run
