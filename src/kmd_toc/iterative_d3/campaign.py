"""Versioned study entry reusing v3 orchestration and descriptive aggregation."""
from contextlib import contextmanager
from pathlib import Path
import copy
import fcntl

from kmd_toc.iterative_v3 import experiment
from kmd_toc.iterative_v3.io import ROOT, atomic, digest_payload, dump, read, sha, sources, verify_pins
from kmd_toc.iterative_v3_study import plan, runtime, readiness as old_readiness
from .overlay import pilot_trial, variant_worker

VERSION = 'iterative-d3-v1'
ENTRY = ROOT/'scripts/run_iterative_d3.py'
PILOT_METHODS = {
    'D1': ['D_quantum'],
    'D2': ['D_classical', 'D_quantum'],
    'D3': ['D_classical', 'D_quantum'],
}


def validate(configuration):
    if configuration['version'] != VERSION or configuration['search']['variant'] != 'D3':
        raise ValueError('D3_FORMAL_PROFILE_REQUIRED')
    if configuration['search']['transfer_attempts'] != 64:
        raise ValueError('FIXED_TRANSFER_LIMIT_REQUIRED')
    modified = copy.deepcopy(configuration)
    modified['version'] = plan.VERSION
    LEGACY_VALIDATE(modified)


LEGACY_VALIDATE = plan.validate


@contextmanager
def entry_binding():
    bindings = [(plan, 'validate', validate), (plan, 'VERSION', VERSION),
                (plan, 'CLI', ENTRY), (runtime, 'CLI', ENTRY),
                (runtime, 'preflight', preflight), (old_readiness, 'readiness', formal_state)]
    originals = [(module, name, getattr(module, name)) for module, name, _ in bindings]
    for module, name, replacement in bindings:
        setattr(module, name, replacement)
    try:
        yield
    finally:
        for module, name, original in reversed(originals):
            setattr(module, name, original)


def preflight(manifest, output):
    with entry_binding():
        return plan.preflight(manifest, output)


def register(config, output):
    with entry_binding():
        return plan.register(config, output)


def branch(job):
    # Work specification is pinned before compiling the narrow v3 overlay.
    verify_pins(job['code_hashes'])
    with entry_binding(), variant_worker(job.get('replay_root')):
        return runtime.branch_worker(job)


def register_pilot(config, output):
    base = read(config)
    validate(base)
    old = Path(base['D0_archive']).resolve()
    original = experiment.verify_manifest(old)
    if (base['search'] | {'variant': None, 'transfer_attempts': None}) != (
            original['configuration']['search'] | {'variant': None, 'transfer_attempts': None}):
        raise ValueError('D0_D3_BASE_BUDGET_DIFFERENCE')
    expected = dict(S1=2026112231, S2=2026112232, S3=2026112233)
    if {p['scale']:p['seed'] for p in original['cases']} != expected:
        raise ValueError('PILOT_D0_SEEDS_CHANGED')
    if any(case['seed'] in expected.values() for case in read(base['D0_formal_manifest'])['cases']):
        raise ValueError('PILOT_FORMAL_SEED_OVERLAP')
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    config_hash = sha(config)
    pins = sources() | {str(ENTRY.relative_to(ROOT)):sha(ENTRY)}
    receipts = {}
    for case in original['cases']:
        folder = old / case['output_subdir']
        r = read(folder/'RESULT.json')
        initial = read(folder/'B/B_CURRENT.json')['directory']
        c_dir = read(folder/'C_Idual/C_CURRENT.json')['directory']
        c_result = read(Path(c_dir)/'RESULT.json')
        if c_result['trial_id'] != case['trial_id'] or c_result['initial_plan_sha256'] != r['initial_sha256']:
            raise ValueError('PILOT_C_REFERENCE_NOT_PAIRED')
        if r['trial_id'] != case['trial_id'] or r['seed'] != case['seed'] or r['status'] != 'COMPLETE':
            raise ValueError('D0_TRIAL_IDENTITY_MISMATCH')
        if r['initial_sha256'] != sha(Path(initial)/'plan.json'):
            raise ValueError('D0_INITIAL_CHANGED')
        if any(r['conditions'][name]['status'] != 'COMPLETE_FOUR_BRANCHES'
               for name in ('D_classical','D_quantum')):
            raise ValueError('D0_NOT_COMPLETE')
        receipts[case['scale']] = dict(initial=initial, C_result=c_dir,
            reused_sha={str(f):sha(f) for f in (
                folder/'RESULT.json', folder/'B/B_CURRENT.json', folder/'C_Idual/C_CURRENT.json',
                Path(initial)/'INITIAL.json', Path(initial)/'plan.json', Path(c_dir)/'RESULT.json',
                *(Path(row['plan']) for row in r['conditions'].values()))})
    record = dict(version=VERSION, profile='PILOT_ONLY_J0', configuration=base,
                  configuration_source=str(Path(config).resolve()), configuration_sha256=config_hash,
                  input_hashes=original['input_hashes'], code_hashes=pins, D0_code_hashes=original['code_hashes'],
                  cases=original['cases'], classical_configuration=original['classical_configuration'],
                  formal_J_contribution=0, variants=PILOT_METHODS, D0_and_C_reused=receipts,
                  output=str(out))
    dump(out/'MANIFEST.json', record)
    (out/'MANIFEST.json').chmod(0o444)
    dump(out/'REGISTRATION.json',dict(manifest_sha256=sha(out/'MANIFEST.json')))
    return dict(status='REGISTERED',profile=record['profile'],worker_jobs=0,
                planned_new_methods=15,referenced_D0_methods=6)


def execute_pilot(manifest, output):
    out = Path(output).resolve()
    if Path(manifest).resolve() != out/'MANIFEST.json':
        raise ValueError('WRONG_PILOT_OUTPUT')
    m = experiment.verify_manifest(out)
    if m['profile'] != 'PILOT_ONLY_J0' or m['output'] != str(out) or m['formal_J_contribution']!=0:
        raise ValueError('PILOT_ENTRY_REFUSES_FORMAL_MANIFEST')
    if sha(m['configuration_source']) != m['configuration_sha256']:
        raise ValueError('PILOT_CONFIG_CHANGED')
    verify_pins(m['D0_code_hashes'])
    for receipt in m['D0_and_C_reused'].values():
        verify_pins(receipt['reused_sha'])
    worker = pilot_trial()
    with (out/'EXECUTION.lock').open('a') as lock, entry_binding(), runtime.study_workers():
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for case in m['cases']:
            for variant, methods in m['variants'].items():
                if variant not in PILOT_METHODS or methods != PILOT_METHODS[variant]:
                    raise ValueError('PILOT_VARIANTS_CHANGED')
                folder = out/case['scale']/variant
                complete = folder/'RESULT.json'
                if complete.exists():
                    continue
                evidence = m['D0_and_C_reused'][case['scale']]
                for name, pointer, directory in [('B','B_CURRENT',evidence['initial']),
                                                  ('C_Idual','C_CURRENT',evidence['C_result'])]:
                    target = folder/name/f'{pointer}.json'
                    target.parent.mkdir(parents=True,exist_ok=True)
                    expected = dict(status='COMPLETE',directory=directory)
                    if not target.exists():
                        dump(target, expected)
                    elif read(target)!=expected:
                        raise ValueError('PILOT_REFERENCE_CHANGED')
                c = copy.deepcopy(m['configuration'])
                c['search']['variant'] = variant
                c['pilot_methods'] = methods
                print(f"{case['scale']} {variant} start",flush=True)
                atomic(out/'PROGRESS.json',dict(scale=case['scale'],variant=variant,state='RUNNING'))
                row = worker(m | {'configuration':c}, case, folder)
                if row['status'] != 'COMPLETE':
                    atomic(out/'PROGRESS.json',dict(scale=case['scale'],variant=variant,state='INTERRUPTED_OR_FAILED'))
                    return dict(status=row['status'],scale=case['scale'],variant=variant)
        atomic(out/'PROGRESS.json',dict(state='COMPLETE',formal_J_contribution=0))
    return dict(status='COMPLETE',formal_J_contribution=0)


def formal_state(manifest, output):
    preflight(manifest, output)
    out = Path(output)
    config = read(manifest)['configuration']
    evidence = Path(config['validation_receipt'])
    if evidence.exists():
        validation = read(evidence)
        ready = (validation.get('status') == 'PASS'
                 and validation.get('formal_code_hashes') == read(manifest)['code_hashes'])
    else:
        ready = False
    frozen = out/'FREEZE_RECORD.json'
    if ready and frozen.exists() and read(frozen)['validation_sha256']==sha(evidence):
        state = 'HOLD_INDEPENDENT_AUDIT_FAIL'
    else:
        state = 'VALIDATION_PENDING'
    execution = read(out/'EXECUTION_STATE.json')['state'] if (out/'EXECUTION_STATE.json').exists() else 'NOT_STARTED'
    result = dict(preparation_state=state, execution_state=execution, EXPERIMENT_READY=state=='EXPERIMENT_READY',
                  workers_submitted=0, J=30, evidence=str(evidence), variant='D3')
    atomic(out/'READINESS.json', result)
    return result


def execute_formal(manifest, output, explicit_execute):
    raise ValueError('HOLD_D3_V1_INDEPENDENT_AUDIT_FAIL_USE_REVISED_REGISTRATION')


def freeze(manifest, output):
    manifest = Path(manifest)
    validate(read(manifest)['configuration'])
    preflight(manifest,output)
    m=read(manifest)
    evidence=Path(m['configuration']['validation_receipt'])
    validation=read(evidence)
    if validation['status']!='PASS' or validation['formal_code_hashes']!=m['code_hashes']:
        raise ValueError('D3_VALIDATION_EVIDENCE_MISMATCH')
    out=Path(output)
    binding=dict(variant='D3', version=VERSION, status='FREEZE', manifest_sha256=sha(manifest),
                 seed_registry_sha256=sha(out/'SEEDS.csv'), validation_sha256=sha(evidence),
                 configuration_sha256=m['configuration_sha256'], specification_sha256=m['configuration']['freeze_spec_sha256'],
                 J=30, comparison_cases=90, execution_state='NOT_STARTED')
    dump(out/'FREEZE_RECORD.json', binding)
    (out/'FREEZE_RECORD.json').chmod(0o444)
    return formal_state(manifest, output)
