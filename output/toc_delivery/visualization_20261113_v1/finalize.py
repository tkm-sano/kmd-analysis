"""Record the visualization environment and recheck protected inputs read-only."""
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def read(name):
    return json.loads((ROOT / name).read_text())


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    cpu = next((x.split(':', 1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines()
                if x.startswith('model name')), 'unknown')
    save('ENVIRONMENT.json', {
        'recorded_UTC': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'CPU': cpu, 'logical_CPUs': os.cpu_count(),
        'packages': {p: importlib.metadata.version(p) for p in
                     ['numpy', 'scipy', 'matplotlib', 'osmium', 'pyproj', 'playwright']},
        'chrome': subprocess.check_output(['/usr/bin/google-chrome', '--version'], text=True).strip(),
        'Japanese_figure_font': str(Path.home() / '.local/share/fonts/NotoSansJP-Regular.ttf'),
        'scope': 'visualization-only venv; delivery algorithm environment unchanged',
    })
    before = read('PRESERVATION_BEFORE.json')
    changed = [p for p, h in before['files'].items()
               if not (REPO / p).exists() or digest(REPO / p) != h]
    status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=REPO, text=True)
    manifest = read('DATA_MANIFEST.json')
    bad_inputs = [p for p, entry in manifest['inputs'].items()
                  if not (REPO / p).exists() or digest(REPO / p) != entry['sha256']]
    independent = read('INDEPENDENT_VALIDATION.json')
    browser = read('BROWSER_VALIDATION.json')
    checks = {
        'protected_existing_files': len(before['files']), 'changed_existing_files': changed,
        'frozen_files': len([p for p in before['files'] if '/frozen_demand/v1/' in p]),
        'manifest_input_files': len(manifest['inputs']), 'mismatched_manifest_inputs': bad_inputs,
        'tracked_status_before': before['tracked_status'], 'tracked_status_after': status,
        'tracked_changes_preserved': status == before['tracked_status'],
        'independent_checks_passed': independent['passed'], 'independent_checks_total': independent['checks'],
        'browser_checks_passed': browser['passed'], 'browser_checks_total': browser['checks'],
        'algorithm_or_OD_regeneration': False, 'commit_or_push': False,
    }
    checks['passed'] = (not changed and not bad_inputs and checks['tracked_changes_preserved']
                        and independent['passed'] == independent['checks']
                        and browser['passed'] == browser['checks'])
    save('FINAL_VALIDATION.json', checks)
    captions = read('figures/CAPTIONS.json')
    (ROOT / 'figures/CAPTIONS.md').write_text('# 論文用図キャプション\n\n' + '\n\n'.join(
        f'**{name}**\n\n{text}' for name, text in captions.items()) + '\n')
    # Live HTTP logs can grow as the user browses, and the index cannot hash itself.
    excluded = {'ARTIFACT_INDEX.json', 'SERVER.log'}
    artifacts = {str(p.relative_to(ROOT)): {'bytes': p.stat().st_size, 'sha256': digest(p)}
                 for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in excluded
                 and '__pycache__' not in p.parts}
    save('ARTIFACT_INDEX.json', {'excluded_volatile_files': sorted(excluded), 'files': artifacts})
    print(json.dumps({'passed': checks['passed'], 'protected': len(before['files']),
                      'changed': changed, 'input_hash_mismatch': bad_inputs,
                      'new_artifacts': len(artifacts)}, ensure_ascii=False))
    if not checks['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
