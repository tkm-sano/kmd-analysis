"""Formal fixed-input/fixed-pi0 J30 registration and non-executing preflight."""
from pathlib import Path
import copy,os,sys,platform,csv,subprocess,hashlib,shutil
import numpy as np
from kmd_toc.iterative_v3.io import ROOT,read,dump,atomic,sha,sources,verify_pins,load_problem,identity,read_initial
from kmd_toc.iterative_v3.experiment import validate_config
from kmd_toc.cd_comparison_v2.runner import physical_cores

VERSION='iterative-study-20261122-v1'
CLI=ROOT/'scripts/run_iterative_v3_study.py'
METHODS=['C_Idual','D_classical','D_quantum']

def validate(c):
    validate_config(c)
    assert c['version']==VERSION and c['role']=='MAIN_REGISTERED_J30'
    assert c['formal_J']==30 and c['formal_J_confirmed'] is True
    assert c['scales']==['S1','S2','S3'] and c['methods']==METHODS
    assert c['search']['outer_iterations']==10 and c['search']['physical_completion_budget']==70
    assert c['search']['local_order_size']==12 and c['search']['returned_order_candidates']==4
    assert c['search']['local_calls_per_iteration']==1 and c['search']['moves_per_family']==1
    assert c['search']['reallocation_families']==['inter_relocate','inter_swap','intra_transfer']
    assert c['search']['quantum']['optimizer_max_evaluations']==24
    assert c['precision_policy']['kind']=='achieved_precision_fixed_J' and c['precision_policy']['target'] is None
    assert c['statistics']['strict_dual_tolerance_D_km']==0 and c['statistics']['strict_dual_tolerance_W_min']==0
    assert c['main_experiment_authorized'] is False, 'legacy entry must remain disabled'

def alias_initial(canonical,directory,trial_id):
    canonical,directory=Path(canonical).resolve(),Path(directory).resolve()
    if directory.exists():
        r=read_initial(directory)
        if r.manifest['trial_id']!=trial_id or r.manifest['plan_sha256']!=sha(canonical/'plan.json'):raise ValueError('INITIAL_ALIAS_CONFLICT')
        return r
    directory.mkdir(parents=True);os.symlink(os.path.relpath(canonical/'plan.json',directory),directory/'plan.json')
    m=read(canonical/'INITIAL.json');m.update(trial_id=trial_id,alias_of=str(canonical),fixed_reference=True,independent_observation=False)
    dump(directory/'INITIAL.json',m);(directory/'INITIAL.json').chmod(0o444)
    return read_initial(directory)

def register(config,output):
    c=read(config);validate(c);out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    old=Path(c['reference_pilot']).resolve();evidence=read(old/'MANIFEST.json');verify_pins(evidence['code_hashes'])
    code=sources();code[str(CLI.relative_to(ROOT))]=sha(CLI)
    fixed={};cases=[];files={};assets={};cpus=physical_cores();seeds=set()
    cfg=read(ROOT/'configs/toc_delivery/termination_rules_20261116_v1.json')
    for k,scale in enumerate(c['scales']):
        old_case=next(x for x in evidence['cases'] if x['scale']==scale)
        inp=Path(old_case['input']);p=load_problem(inp,c['rest_options'])
        assert (len(p.stops),len(p.vehicles),len(p.berths))=={'S1':(1000,10,2),'S2':(2000,20,4),'S3':(4000,40,8)}[scale]
        for f in inp.rglob('*'):
            if f.is_file():files[str(f.resolve())]=sha(f)
        pointer=read(old/old_case['output_subdir']/'B/B_CURRENT.json');original=read_initial(pointer['directory']);base=original.checked_plan(p)
        assert original.manifest['generator_role']=='existing_B_algorithm'
        directory=out/'fixed_inputs'/scale;directory.mkdir(parents=True)
        (directory/'plan.json').write_bytes(original.plan_bytes);(directory/'plan.json').chmod(0o444)
        im=copy.deepcopy(original.manifest);im.update(experiment_id=VERSION,trial_id=f'FIXED_PI0_{scale}',fixed_reference=True,
            independent_observation=False,original_initial_directory=str(original.directory),original_initial_manifest_sha256=sha(original.directory/'INITIAL.json'))
        dump(directory/'INITIAL.json',im);(directory/'INITIAL.json').chmod(0o444)
        canonical=read_initial(directory);canonical.checked_plan(p)
        fixed[scale]=dict(directory=str(directory),plan_sha256=im['plan_sha256'],physical_hash=identity(base),
            problem_hash=p.fingerprint,od_hash=p.od.fingerprint,generation_seed=im['seed'],metrics=im['metrics'],
            generation_algorithm=im['algorithm'],generator_unique_executions=1,formal_generation_executions=0,
            original_runtime_manifest=str(old/'MANIFEST.json'),conditions_sha256=p.experiment.conditions_sha256,
            duty_policy_sha256=p.activated_policy_sha256)
        for j in range(30):
            seed=int(np.random.SeedSequence([c['formal_seed_root'],k,j,113]).generate_state(1)[0])
            if seed in seeds or seed in c['excluded_pilot_seeds']:raise ValueError('FORMAL_SEED_COLLISION')
            seeds.add(seed);trial=f'{VERSION}_{scale}_T{j:03d}';capsule=alias_initial(directory,out/'initial_aliases'/trial,trial)
            branch=[int(np.random.SeedSequence([seed,b,3]).generate_state(1)[0]) for b in range(4)]
            cases.append(dict(scale=scale,trial_id=trial,outer_index=j,seed=seed,input=str(inp.resolve()),
                output_subdir=f'trials/{scale}/T{j:03d}',initial_directory=str(capsule.directory),
                initial_plan_sha256=im['plan_sha256'],initial_physical_hash=identity(base),
                problem_hash=p.fingerprint,od_hash=p.od.fingerprint,N=len(p.stops),V=len(p.vehicles),berths=len(p.berths),C_cpu=cpus[0],
                streams=dict(C_Idual_seed=seed%(2**31-1),D_classical_branch_seeds=branch,D_quantum_branch_seeds=branch,
                    reallocation_rng='random.Random(branch_seed); saved/restored per commit',
                    local_seed='branch_seed + iteration*10007 + eligible_move_offset*101',
                    training_seed='local_seed + evaluation_index',final_sample_seed='local_seed + 100000',
                    adaptive_paths_may_diverge=True)))
        for f in directory.glob('*.json'):assets[str(f)]=sha(f)
    for f in (out/'initial_aliases').glob('*/INITIAL.json'):assets[str(f)]=sha(f)
    diff=subprocess.check_output(['git','diff','--binary'],cwd=ROOT);(out/'TRACKED_DIFF.patch').write_bytes(diff)
    manifest=dict(version=VERSION,configuration=c,configuration_source=str(Path(config).resolve()),configuration_sha256=sha(config),
        git_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        tracked_diff_sha256=hashlib.sha256(diff).hexdigest(),tracked_diff_snapshot=str(out/'TRACKED_DIFF.patch'),
        registered_output=str(out),profile='FORMAL_FIXED_INPUT_J30',cases=cases,fixed_initials=fixed,
        input_hashes=files,asset_hashes=assets,code_hashes=code,classical_configuration=cfg,formal_J_contribution=1,
        python_environments=dict(classical=c['classical_python'],branch=c['branch_python'],registration_python=sys.version,platform=platform.platform()),
        counts=dict(comparison_cases=90,per_scale=30,fixed_B_plans=3,B_reference_uses=90,B_independent_observations=0,
            C_Idual_executions=90,D_classical_executions=90,D_quantum_executions=90,C_worker_jobs=90,D_branch_jobs_per_method=360,
            D_branch_jobs_total=720,optimizer_executions_total=270,solver_worker_jobs_total=810,
            quantum_local_calls_upper_bound=3600,training_callback_evaluations_upper_bound=86400,
            MPS_state_evolutions_upper_bound=90000,virtual_quantum_shots_upper_bound=122400000,
            physical_completion_requests_per_D_method_upper_bound=25200),
        counting=dict(completion_includes='every attempted returned reallocation/order candidate including infeasible or duplicate plans',
            completion_excludes='pi0 validation, incumbent/archive loading, final fallback and selection revalidation',
            maximum_completions_per_iteration=7,return_cap='4 distinct decoded order candidates per local API call, not raw shots',
            stop_order='10 iterations first if fewer than 70 requests; otherwise both coincide; 70 cannot precede iteration 10 under fixed per-iteration maxima'),
        execution_state='NOT_STARTED',explicit_execute_action_required=True,
        primary_comparison=['B','C_Idual','D_quantum'],control_comparison=['D_classical','D_quantum'],
        no_C_final_in_D=True,independence_scope='independent exploration streams conditional on fixed demand, OD, physical policy and fixed pi0; not independent delivery days')
    dump(out/'MANIFEST.json',manifest);(out/'MANIFEST.json').chmod(0o444)
    dump(out/'REGISTRATION.json',dict(manifest_sha256=sha(out/'MANIFEST.json'),case_seeds_fixed_before_execution=True,
        main_experiment_state='NOT_STARTED',J=30,precision_target_required=False))
    with (out/'SEEDS.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['scale','trial_id','method','branch','outer_seed','solver_seed','cpu','pi0_sha256']);w.writeheader()
        for case in cases:
            for method in METHODS:
                for b in range(1 if method=='C_Idual' else 4):
                    w.writerow(dict(scale=case['scale'],trial_id=case['trial_id'],method=method,branch=b,outer_seed=case['seed'],
                        solver_seed=case['streams']['C_Idual_seed'] if method=='C_Idual' else case['streams'][method+'_branch_seeds'][b],
                        cpu=cpus[0] if method=='C_Idual' else cpus[b],pi0_sha256=case['initial_plan_sha256']))
    return manifest

def preflight(manifest,output,*,check_resources=True):
    path=Path(manifest).resolve();out=Path(output).resolve();m=read(path);c=m['configuration'];validate(c)
    if path!=out/'MANIFEST.json' or str(out)!=m['registered_output']:raise ValueError('MANIFEST_OUTPUT_BINDING_MISMATCH')
    if sha(path)!=read(out/'REGISTRATION.json')['manifest_sha256']:raise ValueError('MANIFEST_HASH_CHANGED')
    if m['profile']!='FORMAL_FIXED_INPUT_J30' or len(m['cases'])!=90:raise ValueError('NOT_REGISTERED_FORMAL_J30')
    verify_pins(m['code_hashes'])
    if sha(m['configuration_source'])!=m['configuration_sha256']:raise ValueError('REGISTERED_CONFIGURATION_CHANGED')
    if sha(c['freeze_spec'])!=c['freeze_spec_sha256']:raise ValueError('REGISTERED_FREEZE_CHANGED')
    if sha(c['environment_reference'])!=c['environment_reference_sha256']:raise ValueError('ENVIRONMENT_REFERENCE_CHANGED')
    if sha(m['tracked_diff_snapshot'])!=m['tracked_diff_sha256']:raise ValueError('TRACKED_DIFF_SNAPSHOT_CHANGED')
    frozen=out/'FREEZE_RECORD.json'
    if frozen.exists():
        binding=read(frozen)
        if binding['manifest_sha256']!=sha(path) or binding['seed_registry_sha256']!=sha(out/'SEEDS.csv'):raise ValueError('FREEZE_OR_SEED_REGISTRY_CHANGED')
    for name,pins in [('input',m['input_hashes']),('fixed_asset',m['asset_hashes'])]:
        for file,h in pins.items():
            if sha(file)!=h:raise ValueError('REGISTERED_'+name.upper()+'_CHANGED:'+file)
    for executable in (c['classical_python'],c['branch_python']):
        if not os.path.isfile(executable) or not os.access(executable,os.X_OK):raise ValueError('PYTHON_ENVIRONMENT_UNAVAILABLE')
    seen=set()
    for scale in c['scales']:
        fixed=m['fixed_initials'][scale];case=next(x for x in m['cases'] if x['scale']==scale)
        p=load_problem(case['input'],c['rest_options']);base=read_initial(fixed['directory']).checked_plan(p)
        if identity(base)!=fixed['physical_hash']:raise ValueError('FIXED_PI0_CHANGED')
        subset=[x for x in m['cases'] if x['scale']==scale]
        if len(subset)!=30:raise ValueError('PER_SCALE_J_NOT_30')
        for x in subset:
            if x['seed'] in seen or x['seed'] in c['excluded_pilot_seeds']:raise ValueError('SEED_COLLISION')
            seen.add(x['seed']);capsule=read_initial(x['initial_directory'])
            if capsule.manifest['trial_id']!=x['trial_id'] or capsule.manifest['plan_sha256']!=fixed['plan_sha256'] or sha(capsule.directory/'plan.json')!=fixed['plan_sha256'] or x['initial_physical_hash']!=fixed['physical_hash']:
                raise ValueError('TRIAL_PI0_BINDING_CHANGED')
            branch=[int(np.random.SeedSequence([x['seed'],b,3]).generate_state(1)[0]) for b in range(4)]
            if x['streams']['D_classical_branch_seeds']!=branch or x['streams']['D_quantum_branch_seeds']!=branch or x['streams']['C_Idual_seed']!=x['seed']%(2**31-1):raise ValueError('STREAM_BINDING_CHANGED')
    if check_resources and physical_cores()!=m['configuration']['cpu_ids']:raise ValueError('REGISTERED_CPU_BINDING_CHANGED')
    if check_resources and shutil.disk_usage(out).free<c['limits']['minimum_free_disk_gib']*2**30:raise ValueError('MINIMUM_FREE_DISK_NOT_AVAILABLE')
    result=dict(status='PREFLIGHT_PASS',workers_submitted=0,manifest=str(path),manifest_sha256=sha(path),output=str(out),
        effective_configuration=c,counts=m['counts'],execution_state=read(out/'EXECUTION_STATE.json')['state'] if (out/'EXECUTION_STATE.json').exists() else 'NOT_STARTED')
    atomic(out/'PREFLIGHT.json',result);return result
