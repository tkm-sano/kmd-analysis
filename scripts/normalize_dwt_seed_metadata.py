"""Correct published seed semantics, preserving every raw measured worker record.

Frozen demand is deterministic SHA256 ranking, not a seeded PRNG draw. The
worker's inherited experiment.random_seed is input metadata, not demand_seed.
No accepted D/W/T, feasibility, threshold, budget, algorithm seed or plan is
changed. A failed attempt's elapsed duration is retained in its own field,
not presented as the time to acquire a verified plan.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'output/toc_delivery/dwt_balance_20261113_v1/revision_1_1')
changes = []
for path in sorted((root / 'trials').glob('*/metrics.json')):
    row = json.loads(path.read_text())
    if row.get('demand_seed_semantics_corrected'):
        continue
    original = dict(row)
    backup = path.with_name('metrics_pre_seed_semantics.json')
    if backup.exists():
        raise FileExistsError(backup)
    started = time.perf_counter()
    shutil.copy2(path, backup)
    row['input_experiment_seed'] = row.get('demand_seed')
    row['demand_seed'] = None
    row['demand_random_generator'] = None
    row['demand_generation'] = 'frozen deterministic SHA256 toc-stop-rank-v1; small road subsets deterministic, no PRNG demand draw'
    row['demand_seed_semantics_corrected'] = True
    row['T_attempt_wall_s'] = row.get('T_program_s') if row.get('T_program_s') is not None else row.get('failure_elapsed_s')
    if not row.get('feasible'):
        row['T_program_s'] = None
    row['raw_worker_record'] = 'worker_result.json' if (path.parent / 'worker_result.json').exists() else 'result.json'
    row['metadata_publication_wall_s'] = time.perf_counter() - started
    assert all(row.get(k) == original.get(k) for k in ['D_km', 'W_min', 'status', 'solver_seed', 'quantum_seed'])
    assert not original.get('feasible') or row['T_program_s'] == original['T_program_s']
    path.write_text(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    manifest_path = path.with_name('manifest.json')
    manifest = json.loads(manifest_path.read_text())
    manifest_backup = path.with_name('manifest_pre_seed_semantics.json')
    shutil.copy2(manifest_path, manifest_backup)
    if 'files' in manifest:
        manifest['files']['metrics.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['metadata_correction'] = 'input experiment seed separated from deterministic frozen-demand sampling; failed elapsed not labelled verified-plan T; raw worker and pre-correction metrics/manifest retained; accepted DWT unchanged'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False) + '\n')
    changes.append({'trial_id': row['trial_id'], 'before_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(),
                    'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'accepted_DWT_unchanged': True,
                    'measured_durations_retained': True})
target = root / 'SEED_METADATA_CORRECTION.json'
prior = json.loads(target.read_text()) if target.exists() else {'changes': []}
prior['changes'].extend(changes)
prior['reason'] = 'frozen demand uses deterministic SHA256 ranking, not experiment.random_seed; preserve raw records and correct published standard metadata'
target.write_text(json.dumps(prior, ensure_ascii=False, indent=2) + '\n')
print('Seed metadata published corrections:', len(changes))
