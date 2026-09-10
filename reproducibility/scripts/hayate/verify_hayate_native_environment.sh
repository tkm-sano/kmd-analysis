#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
expected_repo_root=${RESEARCH_REPO_ROOT:-/home/takuma/kmd-analysis}
conda_prefix=${RESEARCH_CONDA_PREFIX:-$repo_root/.conda}
sumo_root=${RESEARCH_SUMO_ROOT:-$repo_root/.local/sumo-1.24.0}
requirements=${RESEARCH_REQUIREMENTS:-$repo_root/reproducibility/environment/requirements-analysis.txt}

if [[ $repo_root != "$expected_repo_root" ]]; then
    printf 'unexpected repository root: %s (expected %s)\n' "$repo_root" "$expected_repo_root" >&2
    exit 2
fi

test -f /opt/miniconda/etc/profile.d/conda.sh
test -f "$requirements"
test -x "$conda_prefix/bin/python"
test -x "$sumo_root/bin/sumo"
test -d "$sumo_root/share/sumo/tools"

# shellcheck disable=SC1091
source /opt/miniconda/etc/profile.d/conda.sh
conda activate "$conda_prefix"

export SUMO_HOME="$sumo_root/share/sumo"
export PATH="$sumo_root/bin:$PATH"
export PYTHONPATH="$sumo_root/share/sumo/tools:${PYTHONPATH:-}"
export LD_LIBRARY_PATH="$conda_prefix/lib:${LD_LIBRARY_PATH:-}"

python_path=$(command -v python)
python_version=$(python --version 2>&1)
sumo_path=$(command -v sumo)
sumo_version=$(sumo --version 2>&1 | head -1)
pytest_version=$(python -m pytest --version | head -1)

test "$python_path" = "$conda_prefix/bin/python"
test "$python_version" = "Python 3.11.15"
test "$sumo_path" = "$sumo_root/bin/sumo"
case "$sumo_version" in
    *"Version 1.24.0"*) ;;
    *) printf 'unexpected SUMO version: %s\n' "$sumo_version" >&2; exit 3 ;;
esac
test "$pytest_version" = "pytest 8.3.3"

python -m pip check

printf 'repository=%s\n' "$repo_root"
printf 'python=%s\n' "$python_path"
printf 'python_version=%s\n' "$python_version"
printf 'sumo=%s\n' "$sumo_path"
printf 'sumo_version=%s\n' "$sumo_version"
printf 'SUMO_HOME=%s\n' "$SUMO_HOME"
printf 'pytest_version=%s\n' "$pytest_version"
printf 'requirements=%s\n' "$requirements"
printf 'requirements_sha256=%s\n' "$(sha256sum "$requirements" | awk '{print $1}')"
printf 'environment_validation=PASS\n'
