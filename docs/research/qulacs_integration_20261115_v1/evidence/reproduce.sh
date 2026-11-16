#!/usr/bin/env bash
# Run from the repository root. New absolute paths only; existing results are kept.
# bash docs/research/qulacs_integration_20261115_v1/evidence/reproduce.sh \
#   /tmp/new-qulacs-venv /tmp/new-qulacs-check /path/to/python3.12.11
set -euo pipefail
integration_env=${1:?Specify a NEW absolute isolated environment path}
result_root=${2:?Specify a NEW absolute verification output path}
base_python=${3:-python3.12}
case "$integration_env" in /*) ;; *) exit 2 ;; esac
case "$result_root" in /*) ;; *) exit 2 ;; esac
test ! -e "$integration_env"
test ! -e "$result_root"
test -f src/kmd_toc/column_generation/backends.py
"$base_python" -c 'import sys; assert sys.version_info[:3] == (3, 12, 11), sys.version'
"$base_python" -m venv "$integration_env"
evidence_source=docs/research/qulacs_integration_20261115_v1/evidence
"$integration_env/bin/python" -m pip install -r "$evidence_source/requirements.lock.txt"
# VeRyPy is not the unrelated similarly named PyPI package.
git clone --no-checkout https://github.com/yorak/VeRyPy.git "$integration_env/verypy-source"
git -C "$integration_env/verypy-source" checkout --detach 8698f910ffcfb4bc8743aedbf203d6de72fbe006
"$integration_env/bin/python" -m pip install --no-deps "$integration_env/verypy-source"
mkdir "$result_root"
cp "$evidence_source/verify_wrapper.py" "$evidence_source/verify_legacy_kernel.py" "$result_root/"
cp -R "$evidence_source/SOURCE_BEFORE" "$result_root/"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
"$integration_env/bin/python" -B -m pytest -q -p no:cacheprovider \
  tests/toc_cg tests/toc_vehicle_day tests/toc_pipeline tests/toc_dwt \
  > "$result_root/regression_tests.log" 2>&1
"$integration_env/bin/python" -B scripts/verify_dwt_statevector_backends.py \
  --output "$result_root/parallel_smoke" > "$result_root/parallel_smoke.log" 2>&1
"$integration_env/bin/python" -B "$result_root/verify_wrapper.py" > "$result_root/wrapper_smoke.log" 2>&1
"$integration_env/bin/python" -B "$result_root/verify_legacy_kernel.py" > "$result_root/legacy_kernel.log" 2>&1
"$integration_env/bin/python" -m pip freeze > "$result_root/pip_freeze.txt"
# Only artificial small validation problems; no main-experiment CLI invocation.
