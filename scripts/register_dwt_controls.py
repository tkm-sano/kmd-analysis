"""Register all prespecified D quantum-off controls, plus fixed single A."""
import hashlib
import json
from pathlib import Path
import time
import sys
import numpy as np

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'output/toc_delivery/dwt_balance_20261113_v1/revision_1_1')
registered = json.loads((root / 'limited_REGISTERED.json').read_text())
control = []
for source in registered['specs']:
    if source['method'] != 'D':
        continue
    spec = {**source, 'phase': 'control', 'method': 'D_CLASSICAL_CONTROL',
            'trial_id': source['trial_id'].replace('limited_', 'control_', 1).replace('_D_', '_D_CLASSICAL_CONTROL_'),
            'paired_quantum_trial': source['trial_id'],
            'seed_pairing': 'same classical seed for controlled ablation; not an independent repetition; quantum_seed reserved but unused'}
    control.append(spec)
seed = int(np.random.SeedSequence([registered['specs'][0]['config']['root_seed'], 3, 0]).generate_state(1)[0]) % (2 ** 31 - 1)
case = registered['specs'][0]['scenario_id']
base = {**registered['specs'][0], 'phase': 'baseline', 'method': 'A', 'epsilon_W_min': 422.45,
        'trial_id': f'baseline_{case}_A2_fixed_T30', 'tau_s': 30,
        'seeds': {'solver_seed': seed, 'quantum_seed': None, 'validation_seed': None},
        'baseline_policy': 'single A2 offset0, fixed before inspecting new B/C/D outcomes; common completion; human T uncalibrated'}
for phase, specs in [('control', control), ('baseline', [base])]:
    target = root / (phase + '_REGISTERED.json')
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps({**registered, 'phase': phase, 'registered_unix_s': time.time(), 'specs': specs,
                                 'setup_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, ensure_ascii=False, indent=2) + '\n')
    print(target)
