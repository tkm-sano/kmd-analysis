# Environment cleanup dry run

- Project root: `/Users/tstakuma/Desktop/github/research`
- Git root matches project root: yes
- Branch: `main`
- Delete candidates: 5
- Quarantine candidates: 1
- Needs review: 1
- Estimated reduction: 449,593,017 bytes
- Dry-run mutations: none

## Largest deletion candidates

| Path | Bytes | Git status | Reason |
|---|---:|---|---|
| `/Users/tstakuma/Desktop/github/research/.venv` | 417479303 | untracked | requirements file exists; environment contains installed packages and symlinked interpreter, not project source |
| `/Users/tstakuma/Desktop/github/research/99_quarantine/unused_generated/mypy_cache` | 31498262 | untracked | previously identified cache/temporary output; quarantined and regenerable |
| `/Users/tstakuma/Desktop/github/research/99_quarantine/unused_generated/scripts_pycache` | 615452 | untracked | previously identified cache/temporary output; quarantined and regenerable |
| `/Users/tstakuma/Desktop/github/research/99_quarantine/unused_generated/tmp` | 0 | untracked | previously identified cache/temporary output; quarantined and regenerable |
| `/Users/tstakuma/Desktop/github/research/99_quarantine/unused_generated/rendered_tmp` | 0 | untracked | previously identified cache/temporary output; quarantined and regenerable |

## Virtual environments

- `.venv/`: delete after confirming `00_project_management/001_20260711_requirements.txt` and documented rebuild command.

## Cache and temporary classes

- Python caches and the quarantined mypy/pycache directories
- macOS metadata
- LaTeX auxiliaries (`aux`, `fls`, `fdb_latexmk`, `synctex.gz`)
- quarantined temporary/render directories

## Unused renderings

Only already-quarantined temporary/render directories are automatic deletion candidates. Research figures and PowerPoint assets remain protected.

## Sensitive candidates

Paths only are recorded in the inventory; no contents were read or copied.

## Recommended .gitignore additions

Preserve existing rules and add Windows metadata, editor caches, Node caches, Office temporary files, remaining Python caches, LaTeX auxiliaries, temporary directories, and local secret variants.
