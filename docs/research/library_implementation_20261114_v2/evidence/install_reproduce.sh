#!/usr/bin/env bash
set -euo pipefail
# Run from repository root. Every destination must be a fresh isolated path.
# Requires Python3.11 and a read-only checkout of VeRyPy at the pinned commit.
# The original research environments must not be activated for installation.
TASK_VENV=${TASK_VENV:-/tmp/kmd-library-validation-replay}
VERY_PY_CHECKOUT=${VERY_PY_CHECKOUT:-/tmp/kmd-verypy-replay}
python3.11 -m venv "$TASK_VENV"
git clone https://github.com/yorak/VeRyPy.git "$VERY_PY_CHECKOUT"
git -C "$VERY_PY_CHECKOUT" checkout 8698f910ffcfb4bc8743aedbf203d6de72fbe006
# The saved freeze includes a local VeRyPy URL; replace only that source locator.
sed '/^verypy @ /d' docs/research/library_implementation_20261114_v2/evidence/requirements.lock.txt > "$TASK_VENV/requirements-without-local-verypy.txt"
"$TASK_VENV/bin/python" -m pip install -r "$TASK_VENV/requirements-without-local-verypy.txt" "$VERY_PY_CHECKOUT"
# Keep original results intact. run_suite reuses existing successful outputs.
# For a fresh full replay, copy code/, evidence/protocol.json and the pinned
# freeze to a NEW sibling docs/research directory at the same depth, and run:
# "$TASK_VENV/bin/python" -B <new-directory>/code/run_suite.py components
# "$TASK_VENV/bin/python" -B <new-directory>/code/run_suite.py pricing
# "$TASK_VENV/bin/python" -B <new-directory>/code/run_suite.py end_to_end
