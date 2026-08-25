#!/usr/bin/env bash
set -euo pipefail

mode=${1:-dry-run}
source_root=${RESEARCH_LOCAL_ROOT:-$(git rev-parse --show-toplevel)}
destination=${RESEARCH_REMOTE_DESTINATION:-takuma@hayate.q-est.wide.ad.jp:/home/takuma/research_canonical/repo/research/}

if [[ ! -d "$source_root/.git" ]]; then
    printf 'Not a Git working tree: %s\n' "$source_root" >&2
    exit 2
fi
if [[ "$destination" != takuma@hayate.q-est.wide.ad.jp:/home/takuma/research_canonical/repo/research/ ]]; then
    printf 'Unexpected destination: %s\n' "$destination" >&2
    exit 2
fi

options=(
    -a
    --safe-links
    --itemize-changes
    --exclude=.DS_Store
    --exclude=.mypy_cache/
    --exclude=.pytest_cache/
    --exclude=.ruff_cache/
    --exclude=.venv/
    --exclude=__pycache__/
)
if [[ "$mode" == dry-run ]]; then
    options+=(--dry-run)
elif [[ "$mode" != execute ]]; then
    printf 'Usage: %s [dry-run|execute]\n' "$0" >&2
    exit 2
fi

# Deliberately no --delete: historical and failed evidence must never be removed.
rsync "${options[@]}" "$source_root/" "$destination"
