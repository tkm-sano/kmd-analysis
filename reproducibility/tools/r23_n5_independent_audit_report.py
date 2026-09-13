"""Independent human-reviewed judgments; never reads previous audit artifacts.

Requires probe evidence. Seals conclusions before a separate comparison step.
Does not modify scientific sources or existing reports.
"""
from __future__ import annotations
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_code_audit/20260913_v2_independent'
S='05_src/traffic_simulation/'
A='reproducibility/outputs/traffic_simulation/'
AUTH=A+'r23_n5_scaling_authority/20260911_v1/'
V2=A+'r23_n5_scaling_authority/20260911_v2/'
OPT=A+'r23_n5_runtime_optimization_review/20260913_v2/'
PROF=A+'r23_n5_runtime_optimization_review/20260913_v1/'
Q=S+'r23_qaoa_aer/'
RUN=S+'r23_n5_scaling/run_n5_scaling.py'
BASE='9a4ce5600a211ffb92adf3b84fe2468d70be2b26'
HEAD='d4a8d78a04316414a9f19ff143264d96c88b3c9b'

def load(n):return json.loads((OUT/n).read_text())
def write(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
def report(n, conclusion, evidence, **kw):write(n,{'conclusion':conclusion,'evidence':evidence,**kw})

def main():
    assert not (OUT/'independent_seal.json').exists(), 'Do not rewrite sealed conclusions'
    probes=load('actual_equivalence_probes.json'); source=load('source_provenance_probes.json')
    assert load('probe_completion.json')['all_assertions_passed']
    assert load('selection_recomputation.json')['selected_match']
    findings=[]
    def finding(fid,severity,title,evidence,impact,remediation):
        findings.append({'id':fid,'severity':severity,'title':title,'evidence':evidence,'impact':impact,
                         'status':'REMEDIATION_REQUIRED','remediation':remediation})
    finding('I01','MAJOR','Candidate does not enforce original probability integrity contract',
        [Q+'metrics.py:53-57',Q+'optimized_metrics_v4.py:72-86','failure_path_probes.json'],
        'Zero-norm and norm-four states return ordinary metrics. Finite 1e308 amplitudes overflow to inf/nan without rejection. Original range/sum guard rejects these. Constants stay 1e-12, but enforcement is removed: accepted scientific domain differs.',
        'In a separately authorized source change, enforce original absolute 1e-12 range/sum and finite-result contract; add failing zero-norm, scaled-norm and overflow tests. Do not renormalize or relax tolerance.')
    finding('I02','MAJOR','Recorded run commits do not reconstruct the scientific execution entrypoint',
        ['source_provenance_probes.json',RUN,Q+'qaoa.py',A+'r23_n5_scaling_progress_review/20260912_v3/progress_review.json'],
        'rank01 runner is absent at its recorded commit and has no execution-time source SHA. rank02/03 recorded ff1d579 has the helper SHA but qaoa.run_single has no implementation argument and runner is absent. Wiring and runner first appear at 0e149ed, after run completion. Current helper differs again at d4a8d78. A helper hash alone cannot certify executed bytes; no inference of fabrication is made.',
        'Recover contemporaneous runner, qaoa and dependency snapshots or logs with hashes and start-time dirty diff; explicitly qualify historical results if recovery is impossible. Preserve existing results and identify any future reproduction as new evidence.')
    finding('I03','MAJOR','Existing equivalence acceptance is not computed from assertions and does not exercise the shipped helper',
        [OPT+'build_artifact.py:8-29',OPT+'run_equivalence.py:58-139'],
        'Report generator writes PASS/all_gates_pass=True independently of numerical differences. Harness reimplements candidate arithmetic instead of calling indexed_probability_metrics; small_full_method flag does not execute full enumeration; best_feasible_route maximizes probability rather than minimizing route cost. New probes substantiate normalized-domain equivalence but do not validate historical acceptance generation.',
        'Use actual candidate and original functions with an independent reference; derive every gate from measured assertions; mutation-test failing gates; make labels reflect actual coverage and best-route semantics.')
    finding('I04','MAJOR','Current canonical status asserts unsupported convergence 3/3',
        [S+'R23_STATUS.md:24',A+'r23_n5_scaling/20260911_v1/runs/routing_v18_n5_rank01/scientific_result.json',A+'r23_n5_scaling_evidence_review/20260913_v1/n5_optimizer_summary.json'],
        'rank01 optimizer_success=false and OBJECTIVE_EVALUATION_CAP_REACHED at 300 contradict convergence 3/3. Other summary data retain the unfavorable result. rank02/03 only report native optimizer success; no global convergence is established.',
        'Correct status claim to exact route recovery 3/3; rank01 cap reached, native optimizer reported success 2/3; retain low raw probabilities and uncertainty. This audit leaves status documents unchanged.')
    finding('I05','MODERATE','Runtime and memory comparisons lack matched workloads and complete execution conditions',
        [PROF+'before_after_benchmark.json',PROF+'profiling_run_manifest.json',OPT+'runtime_benchmark.json',OPT+'memory_benchmark.json',OPT+'run_equivalence.py:132-136'],
        '33.70x uses full rank01 run/nfev versus prototype single evaluation. Timed v2 region omits simulation, index construction, actual guards and route reporting. ru_maxrss absolute peak, peak increments and approximate observed RSS are different metrics. rank02/03 reported peaks 0.309/0.278 GiB are below a fully touched complex128 25q state (0.5 GiB), requiring provenance/process-boundary reconciliation.',
        'Retain PRELIMINARY_ONLY; measure matched source versions, parameters, timer and process boundaries with all thread settings and all repetitions, including setup/final reporting. Use identical absolute peak metrics; do not claim a formal reduction factor.')
    finding('I06','MODERATE','V4 drops reported scientific diagnostics under unchanged result schema',
        [Q+'qaoa.py:231-241',Q+'metrics.py:69-80'],
        'energy_variance becomes None; most_probable_state, most_probable_feasible_state, records and tolerance metadata are absent. Reduced compact route/probability results can agree, but complete run_single result equivalence is false. Threshold and route-cost tie order are preserved in current adapter.',
        'Document a versioned compact output contract and missing diagnostics; restore required diagnostics in a separately reviewed implementation if consumers require them. Do not advertise full output equivalence.')
    finding('I07','MODERATE','Numerical dtype contract accepts lower precision inputs',
        [Q+'optimized_metrics_v4.py:30-35',Q+'optimized_metrics_v4.py:79-81','failure_path_probes.json','supplemental_contract_probes.json'],
        'dtype.kind accepts complex64/float32; vdot and optimal dot retain input precision. No implicit downcast occurs for governed complex128 Aer states, but the public helper does not enforce that scientific precision contract.',
        'Specify and enforce supported precision, then test error bounds with complex64/float32 and overflow. Preserve complex128/float64 production behavior and 1e-12 tolerance.')
    finding('I08','MODERATE','Historical immutability and optimizer replay evidence are incomplete',
        ['artifact_immutability_audit.json',RUN+':86-115',OPT+'n5_parameter_point_comparison.json'],
        'rank01 raw files are ignored/untracked. Current compact records omit final parameters, objective trace and explicit configured cap/options. Tracked rank02/03 records are unchanged since addition, but exact historical execution/replay cannot be established by the retained data.',
        'Archive immutable raw snapshots and execution-time hashes outside any existing output namespace; retain full compact optimizer trace/parameters/config in future runs. Record historical gaps explicitly rather than reconstructing unobserved facts.')
    finding('I09','MINOR','Penalty authority contains inconsistent margin arithmetic',
        [AUTH+'n5_penalty_authority.json'],
        'lambda=4 and bound=3 are correct, but lambda_minus_bound=0.5 and penalty_energy_margin=1.0 are inconsistent with 4-3=1 and 2*4-6=2. The sufficient inequality remains valid.',
        'Issue an authority erratum for derived margin fields while keeping lambda=4.0 and the scientific definition fixed.')
    finding('I10','MODERATE','Benchmark P_optimal_lookup is an arbitrary feasible index proxy',
        [OPT+'run_equivalence.py:135',OPT+'runtime_benchmark.json'],
        'The timed benchmark uses idx[-1:] rather than the exact optimum set. It reports 8.817886471048181e-7 where actual rank01 initial P_optimal is 8.911426703519106e-7. This is not leakage into the optimizer or production helper, but benchmark output must not be used as scientific P_optimal.',
        'Label the existing value as an arbitrary feasible lookup proxy; benchmark the actual candidate reporting function with the authoritative optimum set and account for lookup setup.')
    # Degrees of freedom count units are decisions, not findings.
    decisions=[]
    def decision(name,value,alternatives,when,authority,result_dependent,risk,reason):
        decisions.append({'Decision':name,'value':value,'Alternatives':alternatives,'When fixed':when,'Authority':authority,'Result-dependent?':result_dependent,'Risk':risk,'reason':reason})
    pre='66d8d73 (2026-09-11 22:18:24 +09), before rank01 22:32:21'
    decision('instance','three SHA-ranked n5 combinations','other combinations / more ranks',pre,AUTH+'n5_instance_selection.json','No evidence; independently recomputed', 'LOW','252 combinations, seed 2301; no difficulty term or exclusions')
    decision('n',5,'n4 / n6 / different encoding',pre,AUTH+'n5_planned_run_manifest.json','No observed n5 outcome dependency','LOW','next-size resource observation; n6 not recommended')
    decision('p',1,'p2 / p3',pre,AUTH+'n5_planned_run_manifest.json','Fixed before n5, after earlier n4 depth outcomes','MEDIUM','minimal resource experiment; cannot establish optimal depth or absence of influence from earlier studies')
    decision('lambda',4.0,'any real lambda>3',pre,AUTH+'n5_penalty_authority.json','No empirical tuning evidence','LOW','smallest integer satisfying strict sufficient bound; numeric margin typo separate')
    decision('optimizer','COBYLA','Nelder-Mead / other optimizers',pre,AUTH+'n5_planned_run_manifest.json','Fixed before n5; B2 results already available','MEDIUM','baseline continuity plausible; comparative selection rationale not fully recorded, no general superiority')
    decision('initialization',[0.1,0.1],'other fixed / random initializations',pre,AUTH+'n5_planned_run_manifest.json','Fixed before n5; B1 outcomes available','MEDIUM','baseline not robust over initializations; no n5 seed/initialization sweep evidence')
    decision('cap',300,'900 / other budget','schema default pre-run; explicit n5 runner committed after outcomes',Q+'schema.py:94','Historical override cannot be fully excluded','HIGH','n5 manifest does not explicitly freeze cap/maxiter/options; executed runner bytes absent; B design uses cap 900 so it is not n5 cap authority')
    decision('seed','simulation/transpile 17; selection 2301; validation 2501','other fixed seeds','schema default / pre-run selection and validation authority',AUTH+'n5_validation_authority.json','No n5 best-seed selection evidence','LOW','deterministic baseline; fixed_0.1 has no initialization RNG')
    decision('tolerance',1e-12,'other tolerances','R23 schema before n5',Q+'schema.py:19-21','No numeric relaxation; candidate enforcement removed','LOW','fixed definition; implementation gap is I01, not evidence of tuned numeric tolerance')
    decision('denominator','raw full state mass','conditional feasible normalization','R23 canonical before n5',Q+'metrics.py','No evidence of renormalization','LOW','both sum raw probabilities; no division by feasible mass')
    decision('benchmark metric','mixed full-run/eval/postprocess time','matched end-to-end or matched microbenchmark','after original runtime observed',PROF+'before_after_benchmark.json','Yes: diagnostic choice after bottleneck observation','MEDIUM','reasonable diagnosis, formal speedup unsupported')
    decision('memory metric','ru_maxrss / delta / sampled RSS','uniform absolute process peak','after original resource observation',PROF+'profiling_harness.py','Yes: exploratory measurement design','MEDIUM','must remain preliminary; no formal factor')
    decision('optimization approach','constraint-indexed amplitudes','full probability ndarray / dictionary','after rank01 runtime',Q+'optimized_metrics_v4.py','Yes: performance diagnosis, not QAOA tuning','MEDIUM','mathematical probability sum valid; actual contract and source lineage need remediation')
    decision('validation cases','existing n2/3/4 points and n5 A/C; new audit negative probes','more states / mutations / tied routes','after candidate; audit cases before new probes',OPT+'run_equivalence.py','Post-implementation validation, not selection of scientific runs','MEDIUM','legacy hardcoded PASS does not reject failing evidence; independent probes improve coverage')
    decision('continuation rule','complete rank02/03 after equivalence; n6 stop','stop n5 / defer optimized execution','pre-run safety conditions; post-rank01 performance review',V2+'n5_execution_authorization_v2.json','Yes: resource feasibility review; all three records retained','MEDIUM','continuation rationale explicit but validation/provenance acceptance deficient; R24 remains blocked in this audit')
    risk_counts=dict(Counter(d['Risk'] for d in decisions))
    write('researcher_degrees_of_freedom.json',{'unit':'one decision row','decisions':decisions,'risk_counts':risk_counts,'HIGH_reason':'Authority insufficiency for execution-time cap/options; not an accusation of intentional tuning.'})
    parameters=[{'parameter':d['Decision'],'value':d['value'],'authority':d['Authority'],'when_fixed':d['When fixed'],'result_dependent':d['Result-dependent?'],'risk':d['Risk']} for d in decisions[:10]]
    parameters.extend([
        {'parameter':'maxiter','value':300,'authority':RUN+':134','when_fixed':'explicit n5 code first committed after outcomes; frozen before-run assertion NOT_VERIFIED'},
        {'parameter':'optimizer_options','value':'None -> {maxiter:300}; other SciPy COBYLA defaults','authority':Q+'optimizers.py:60-79','when_fixed':'current code known; actual run dirty-source options unverified'},
        {'parameter':'repetition','value':1,'authority':AUTH+'n5_planned_run_manifest.json','when_fixed':pre},
        {'parameter':'backend','value':'AerSimulator CPU','authority':V2+'n5_execution_authorization_v2.json','when_fixed':pre},
        {'parameter':'Aer method','value':'statevector','authority':V2+'n5_execution_authorization_v2.json','when_fixed':pre},
        {'parameter':'shots','value':'NONE; saved statevector; no measurement sampling','authority':AUTH+'n5_planned_run_manifest.json','when_fixed':pre},
        {'parameter':'exact-reference policy','value':'all permutations; abs cost tolerance 1e-12; fixed selected instances unique; ties supported in metrics','authority':AUTH+'n5_exact_references.json','when_fixed':pre},
        {'parameter':'frozen environment','value':'/home/takuma/.conda/envs/evrp-quantum-temp/bin/python','authority':V2+'frozen_environment_validation.json','when_fixed':'ec476f3 before execution','observed_match':load('start_state.json')['versions']},
    ])
    write('parameter_authority_audit.json',{'parameters':parameters,'no_parameter_changed_by_audit':True,'no_posthoc_tuning_proven':True,'complete_pre_run_freeze_verified':False})
    report('source_authority_review.json','Original qaoa snapshot strongly supported; complete executed source authority NOT_VERIFIED',
        ['source_provenance_probes.json',A+'r23_n5_scaling_progress_review/20260912_v3/progress_review.json',V2+'frozen_environment_validation.json'],
        original={'commit':BASE,'qaoa_sha256':source['original_qaoa_sha256'],'execution_entrypoint':RUN+' routing_v18_n5_rank01',
            'functions':['make_input','normalize_travel_time_matrix','enumerate_routes','build_expanded_qubo','convert_qubo_to_ising','run_single','minimize_objective','_statevector_and_expectation','build_qaoa_circuit','build_cost_operator','probability_metrics','energy_statistics'],
            'execution_time_hash_available':False,'authority_confidence':'INFERRED from artifact commit plus process snapshot; snapshot qaoa identical from ec476f3 through ff1d579'},
        candidate={'relation':['direct modification of qaoa dispatch','separate helper','separate implementation version via original/v4 flag','runner wrapper'],
            'first_commit':'ff1d579bad8e7c635406b2a5a620fc733f96e912','historical_helper_sha256':'c0892b96e375fe2c274eaab74dfeb59cb8ec3a8a1331bb44bca3bd22dc9a9691',
            'integration_commit':'0e149edbf000ffdb187c21123beddb373b8bcff5','current_commit':HEAD,'current_helper_sha256':source['current_helper_sha256'],
            'current_qaoa_sha256':source['current_qaoa_sha256'],'historical_run_bytes_not_recovered':True},
        environment={'authority_python':'/home/takuma/.conda/envs/evrp-quantum-temp/bin/python','current_frozen_versions_match':True,'shell_python':'/opt/miniconda/bin/python (3.13.5)','shell_CONDA_PREFIX':'/home/takuma/kmd-analysis/.conda'})
    report('scientific_model_equivalence.json','Model, canonical QUBO, Hamiltonian and scalar objective unchanged for the same input; full reporting/validation semantics NOT_EQUIVALENT',
        ['canonical_comparisons.json','actual_equivalence_probes.json','line_diff_classification.json'],
        definitions={'decision_variables':'customer-only n*n binary x[i,t]','ordering':'i*n+t, 0-based','travel':'directed depot->first + consecutive customers + last->depot',
            'normalization':'raw directed time / maximum selected off-diagonal time; asymmetry preserved','penalty':'lambda times row and column squared one-hot errors','lambda':4.0,
            'qubo_offset':40.0,'mixer':'-sum X, RX(-2 beta)','ansatz_depth':1,'initial_state':'Hadamard uniform superposition','objective':'min Re(<psi|H_without_identity|psi>)+Ising constant','sign':'minimize unchanged','scaling':'no additional division or normalization'},
        exact_numerical_hash_equality='all three instances',objective_differences=probes['objectives'],
        exact_reference_in_objective=False,probability_metric_in_objective=False,
        limitations=['n5 historical full Python dictionary evaluation not rerun','objective is mathematically identical, not a universal claim of bitwise floating equality','report output fields and accepted probability domain differ'])
    report('instance_selection_audit.json','LOW; deterministic top three recomputed; no outcome-based exclusions found',
        [AUTH+'n5_instance_selection.json','selection_recomputation.json'],
        population='10 customers, 252 five-customer subsets',rule="ascending SHA256('2301|DEP_006|comma-joined sorted IDs|5')",selected_before_n5_outcomes=True,
        exclusions='249 unselected by fixed top-three quota; no difficulty/reachability exclusion among the population recorded',
        limitation='Three subsets of one fixture are not a representative population sample; no global claim about hidden unrecorded experiments.')
    report('optimizer_selection_audit.json','MEDIUM', [AUTH+'n5_planned_run_manifest.json',S+'specifications/R23_EXPERIMENT_B_DESIGN_V1.md'],
        before_n5=True,before_B2=False,rationale='COBYLA baseline continuity plausible; authority freezes selection but does not prove independence from already observed B2 comparisons',
        alternatives=['Nelder-Mead','other derivative-free algorithms'],general_superiority='NOT_SUPPORTED',result_dependent_n5_selection_evidence=False)
    report('stopping_rule_audit.json','HIGH authority uncertainty; current implementation guard correct; historical pre-run cap freeze NOT_VERIFIED',
        [Q+'optimizers.py:68-80',RUN+':134-138',AUTH+'n5_planned_run_manifest.json','source_provenance_probes.json'],
        current_cap=300,current_maxiter=300,current_wall_time_cap=None,current_policy_all_ranks_same=True,
        actual_nfev={'rank01':300,'rank02':209,'rank03':138},rank01='cap reached, optimizer success=false, exact route recovery does not imply convergence',
        no_observed_rank01_extension=True,no_observed_midrun_cap_change=True,
        limitation='Neither absence of observed edits nor schema default proves missing execution wrapper options; do not use B cap=900 as n5 authority.')
    report('seed_audit.json','No selective best-seed evidence in retained n5 records; LOW with audit-trail limits',
        [AUTH+'n5_instance_selection.json',AUTH+'n5_validation_authority.json',Q+'schema.py',PROF+'profiling_run_manifest.json',OPT+'run_equivalence.py'],
        seeds={'selection':2301,'classical_validation':2501,'simulator':17,'transpiler':17,'profiling':17,'legacy_equivalence':17,'independent_audit_simulator':17,'optimizer':'no RNG option supplied','initialization':'fixed_0.1, no RNG'},
        historical_B1_seeds=[11,23,37,53,71],B1_interpretation='separate prior design; not an n5 best-seed sweep',all_known_n5_runs_retained=True)
    report('probability_definition_audit.json','Same raw mass definitions on normalized complex128 states; integrity enforcement differs (I01)',
        [Q+'metrics.py',Q+'optimized_metrics_v4.py','actual_equivalence_probes.json','failure_path_probes.json'],
        P_feasible='sum over constraint-derived permutation indices of |psi[k]|^2',P_optimal='sum over all exact-optimal bitstrings; multiple optimum supported',
        P_invalid='P_total-P_feasible',P_total='raw full state norm; no division, no renormalization',tolerance=1e-12,
        threshold='only route reporting, not P_feasible or P_optimal aggregation',dtype='actual Aer complex128; feasible sum float64; vdot/input precision risk for complex64',
        guard_equivalence=False,sum_order='float sums vs vector sums differ within 1e-12 on probes',index_overflow='n5 max <2**25, int64 safe; n>=8 outside resource scope')
    report('hard_coding_audit.json','No injected scientific result constants in candidate; fixed-instance runner and benchmark proxy require distinctions',
        ['source_search_evidence.json',RUN,OPT+'run_equivalence.py'],
        candidate='n general; factorial feasible set from customers; no 120,25,rank routes or probability literals used as result',
        runner='n=5,25,120,IDs fixed by authority; unique-optimum check fails closed for this fixed set and is not a general multi-optimum runner',
        fixtures='known basis states and n=2/3/4/5 are legitimate structural fixtures',
        problematic=['unconditional PASS literals in report generator (I03)','idx[-1:] pseudo-optimal benchmark lookup (I10)'])
    report('exact_optimum_leakage_audit.json','No optimum information enters circuit, scalar objective, update, stopping or best-route cost selection',
        [Q+'qaoa.py',Q+'hamiltonian.py',Q+'optimized_metrics_v4.py',RUN],
        feasible_knowledge='F constructed solely by permutations and one-hot constraints; helper checks supplied optimum belongs to F, never uses it to generate F',
        best_route='minimum travel cost among all threshold-surviving feasible states, sorted label order for ties; no exact reference lookup',
        allowed_reporting=['P_optimal','exact route match','ground-energy/gap diagnostics already present in original'],
        strict_policy_note='Exact reference is also used in legacy reporting diagnostics, not solely a field named P_optimal. No optimization leakage follows from that reporting use.',
        multiple_optimum='helper sum covers all supplied optimal states; independent two-optimum fixture P_opt=1; runner explicitly restricts frozen instances to unique optimum')
    report('runtime_benchmark_audit.json','PRELIMINARY_ONLY', [PROF+'before_after_benchmark.json',PROF+'profiling_harness.py',OPT+'run_equivalence.py',OPT+'runtime_benchmark.json',V2+'machine_resource_validation.json'],
        formal_speedup_allowed=False,scientific_speedup_allowed=False,
        conditions={'host':'hayate inferred from run/resource context; benchmark lacks full per-process capture','CPU':'AMD EPYC 9684X; authority 192 physical /384 logical',
            'original_threads':'896 observed process threads in progress snapshot','candidate_threads':'not captured','CPU_affinity':'historical matched setting not captured',
            'OMP':'not captured in compared benchmark','BLAS':'not captured','Aer_parallelism':'defaults, no matched explicit recording','environment':'frozen authority identified; full per-benchmark dependency capture incomplete',
            'warmup':'no explicit prior rule; no first repetition removed in saved completed arrays','repetitions':'prototype3 and candidate3; original one attempt aborted >900s',
            'timer':'original full T_total/nfev vs prototype evaluate; v2 arithmetic-only timer','setup':'v2 indices/simulation outside timer','postprocessing':'v2 skips actual helper validation and best-route adapter'},
        repetition_policy='all three completed times preserved; aborted original disclosed but not present as completed timing record; no evidence of fastest-only or slow successful exclusion',
        cache='no persistent feasible/circuit/Hamiltonian cache or backend reuse in current path; benchmark idx prepared before timer',
        precomputation='T_end_to_end = T_input_and_reference_setup + T_run_single; T_run_single includes initialization + optimizer evaluations + final evaluator + decoding. Existing compact T_total excludes make_input; v2 arithmetic benchmark excludes most work.',
        warm_bias='no matched cold/warm process design or pre-fixed exclusion policy verified')
    report('memory_benchmark_audit.json','No formal reduction factor', [PROF+'profiling_harness.py',OPT+'memory_benchmark.json',RUN+':107-110'],
        original={'VmHWM':'not directly recorded in final raw file; Linux ru_maxrss is process peak RSS','absolute_peak_RSS_GiB':201.5834732055664,'sampled_RSS':'~180 GiB incomplete direct profile'},
        candidate={'benchmark_absolute_ru_maxrss_GiB':1.6754150390625,'prototype_increment':'after-before ru_maxrss, not live RSS and not allocation peak','prototype_observed_RSS_GiB':'approximately 0.615',
            'rank02_peak_GiB':0.30858612060546875,'rank03_peak_GiB':0.2781257629394531},
        caveat='Some labels share absolute ru_maxrss units but workloads/process histories differ; peak delta is not comparable to absolute peak. Low rank02/03 peaks need reconciliation with claimed full 0.5GiB complex128 state.',formal_reduction_allowed=False)
    report('validation_independence_audit.json','Independent current normalized-input probes PASS; historical acceptance NOT_SUFFICIENT',
        [OPT+'run_equivalence.py',OPT+'build_artifact.py','actual_equivalence_probes.json','failure_path_probes.json'],
        existing_reference='own_reference_indices independent one-hot derivation; same Hamiltonian data and optimal index membership shared; actual helper never called',
        existing_tests='contract tests use encode_route fixtures and actual helper; finite/dimension tests can fail, but omit norm and lower precision; assertions are legitimate structural expectations',
        historical_report='all gates hardcoded PASS; numerical comparison object merely serialized; no threshold guard; no actual full small-state branch',
        new_reference='full basis one-hot masks n2/3/4, historical real dictionary method, independent n5 permutation set, full numeric norm, chunk diagonal expectation; actual helper called',
        fixed_cases=['valid route','nonoptimal valid route','duplicate customer','missing customer','duplicate position','empty assignment','malformed bitstring','known optimum','invalid index bit encoding','multiple optimum','zero norm','scaled norm','finite overflow'],
        expected_values='derived from constraints and simple .25/.75 fixtures before execution; no copying output probabilities; tolerance fixed 1e-12',
        limitations=['no optimizer trajectory replay: final parameters not retained','not full 2**25 state-by-state validity enumeration','current source validation does not recover execution-time source bytes'])
    report('failure_path_audit.json','REMEDIATION_REQUIRED', ['failure_path_probes.json',Q+'qaoa.py',Q+'schema.py'],
        fail_closed=['NaN/inf amplitudes','wrong dimension/rank','empty state','empty optimum set','duplicate optimum','malformed/nonfeasible optimal bits'],
        fail_open=['zero norm','norm four','finite input overflow yielding inf/nan','complex64 precision contract'],
        external_indices='not an input; internally generated unique index set; duplicate customer IDs rejected',
        silent_fallback_search={'broad_except':'run_single serializes OPTIMIZER_FAILURE/BACKEND_FAILURE explicitly; not hidden success',
            'default_zeros':'payload.get(ising_global_minimum_energy,0.0) can silently fabricate reporting reference if missing; current runner supplies it; historical unchanged diagnostic limitation',
            'missing_file':'formal loader checks and rejects missing required exact reference; progress file default is execution bookkeeping only',
            'warning_only':'existing report generator ignores failing numerical evidence (I03)'},
        no_source_fix_in_this_audit=True)
    report('post_hoc_change_audit.json','No observed QUBO/Hamiltonian/parameter tuning; post-result code and authority changes documented; full freeze NOT_VERIFIED',
        ['canonical_comparisons.json','git_provenance_audit.json','source_provenance_probes.json'],
        unchanged=['model','lambda=4','p=1','COBYLA','fixed initialization','1e-12 constants','raw denominator','SHA ranking rule'],
        changed=['postprocessing representation','qaoa dispatch and output contract after rank01','d4a8d78 helper guards and label sorting after rank02/03'],
        cap='current300; missing execution-time runner prevents proof of no override',
        sorting='current helper sorts binary labels; makes tied-cost first-route order agree with original. Previous unsorted helper membership was equivalent but order was not.',
        intentional_tuning_evidence=False)
    report('selective_reporting_audit.json','Unfavorable raw facts retained, but current status contains materially misleading convergence claim',
        [S+'R23_STATUS.md:24',A+'r23_n5_scaling_evidence_review/20260913_v1/n5_optimizer_summary.json',PROF+'before_after_benchmark.json',S+'specifications/R23_REDUCED_PROBLEM_CANONICAL.md'],
        retained={'rank01_success':False,'rank01_cap_reached':True,'rank01_P_feasible':0.006366971625605308,'rank01_P_optimal':5.447231886991554e-5,
            'rank01_hours':153434.09043177636/3600,'rank01_peak_GiB':201.5834732055664,'implementation_optimization_disclosed':True,'benchmark_limitation_in_profiling_artifact':True,'n6_not_recommended':True},
        defect='Current R23_STATUS.md says COBYLA convergence 3/3; false against native termination metadata. Not corrected in this audit.',
        blind_procedure='Status content inspected by targeted non-audit claim search and pre-audit 0e149ed snapshots; previous audit classification/finding paths not opened.')
    claims=[
        ('rank01 exact route found','DIRECTLY_OBSERVED','retained scientific_result; historic execution provenance limited'),
        ('rank01 success=false and cap reached','DIRECTLY_OBSERVED','native termination stored'),
        ('all three raw P_feasible<1%','DERIVED','numeric result fields'),
        ('COBYLA convergence 3/3','NOT_SUPPORTED','rank01 cap reached; optimizer reported success only rank02/03'),
        ('robustness across seeds/initializations at n5','NOT_SUPPORTED','one fixed initialization/repetition'),
        ('n5 descriptive probability decline vs n4','INFERRED','different instance populations, not controlled scaling law'),
        ('statevector size 2^(n*n)','DERIVED','n*n qubits; 25q complex128 raw array 0.5GiB; n6 raw1TiB'),
        ('formal 33.7x speedup','NOT_SUPPORTED','mismatched boundaries/conditions; PRELIMINARY_ONLY'),
        ('indexed processing avoids dictionary overhead','DERIVED','source representation; magnitude workload-dependent'),
        ('COBYLA general superiority','NOT_SUPPORTED','limited B2 comparisons; no global result'),
        ('n5 generalizability / Full EVRP','NOT_SUPPORTED','three fixed reduced instances, no EV constraints'),
        ('quantum advantage','NOT_SUPPORTED','CPU exact statevector, no QPU advantage benchmark'),
        ('all execution bytes equal recorded commits','ASSUMED','contradicted by missing runner and v4 dispatcher'),
    ]
    write('claim_audit.json',{'claims':[{'claim':c,'classification':cl,'basis':b} for c,cl,b in claims]})
    severity=dict(Counter(f['severity'] for f in findings)); severity.setdefault('CRITICAL',0)
    write('finding_register.json',{'independent':True,'previous_audit_read':False,'findings':findings,'severity_counts':severity,'count':len(findings)})
    gates={'scientific_model_unchanged':True,'QUBO_unchanged':True,'Hamiltonian_unchanged':True,'optimizer_objective_unchanged':True,
           'bit_ordering_verified':True,'no_optimum_leakage':True,'no_result_hardcoding_in_scientific_candidate':True,'no_denominator_change':True,
           'no_tolerance_relaxation_in_effect':False,'no_posthoc_parameter_tuning_verified':False,'no_result_dependent_instance_selection':True,
           'no_selective_scientific_run_exclusion_found':True,'historical_artifacts_immutable_fully_verified':False,
           'validation_sufficiently_independent_and_fail_sensitive':False,'no_unresolved_HIGH':risk_counts.get('HIGH',0)==0,
           'no_unresolved_CRITICAL':severity['CRITICAL']==0,'no_unresolved_MAJOR':severity.get('MAJOR',0)==0}
    classification='CODE_AUDIT_FAIL' if severity.get('MAJOR',0) or severity.get('CRITICAL',0) or risk_counts.get('HIGH',0) else 'CODE_AUDIT_PASS_WITH_REMEDIATION'
    write('acceptance_gate.json',{'classification':classification,'gates':gates,'severity_counts':severity,'arbitrariness_counts':risk_counts,
        'scope':'Current main independently audited; normalized-domain mathematics passes; incomplete integrity guards, validation and historical provenance prevent code acceptance.',
        'false_gate_meaning':'False includes NOT_VERIFIED evidence requirements; it is not proof of intentional misconduct.',
        'R24':'Do not advance; no authority promotion','required_remediation':[f['id'] for f in findings]})

    # Add all cited files to scope, hash current status but do not open audit-bearing sections.
    scope=load('audit_scope.json'); known={r['path'] for r in scope['files']}
    extra=[V2+'frozen_environment_validation.json',A+'r23_n5_scaling_progress_review/20260912_v3/progress_review.json',
        A+'r23_n5_scaling_evidence_review/20260913_v1/n5_optimizer_summary.json',A+'r23_n5_scaling_evidence_review/20260913_v1/implementation_provenance_review.json',
        'reproducibility/tools/r23_n5_independent_audit.py','reproducibility/tools/r23_n5_independent_audit_report.py',
        'reproducibility/tools/r23_n5_independent_audit_contracts.py']
    for path in extra:
        if path not in known:
            scope['files'].append({'path':path,'purpose':'audit evidence / read-only audit script','sha256':sh(ROOT/path),'commit_provenance':git('log','-1','--format=%H %aI','--',path) or None,'state':'current','inspection':'content inspected'})
    for row in scope['files']:
        if row['path'].endswith(('R23_STATUS.md','R23_NEXT_STEPS.md','R23_ROADMAP.md','RESEARCH_STATUS.md')):
            row['inspection']='hash plus selected scientific-claim lines / pre-audit historical status snapshots; audit-bearing lines excluded until seal'
    write('audit_scope.json',scope)
    notes={'n5_no_more_optimizer_runs':True,'rank02_rank03':'Existing records remain retained observations; not newly reproduced or reauthorized. Execution-source linkage and resource records need reconciliation.',
        'R23_overall':'Existing reduced-model evidence retained with limitations; current runtime-optimization code audit FAIL / REMEDIATION_REQUIRED.',
        'Full_EVRP':'R20 BLOCKED; R21 NOT_STARTED; capacity/time window/battery/charging/multiple vehicles not implemented by this audit.',
        'next_task':'R23_N5_RUNTIME_OPTIMIZATION_AUDIT_REMEDIATION; do not advance R24',
        'no_web_needed':'Evidence is local source, frozen dependencies, artifacts and git; no external scientific claim inferred from live web.',
        'model_identity':'Runtime scientific model and conditions fixed. Identity of the assistant model used by previous audit is not recorded in execution authority; cannot verify same LLM across audits.'}
    write('audit_limitations.json',notes)
    (OUT/'README.md').write_text('# R23 N5 independent runtime optimization code audit\n\n'
        +classification+'; REMEDIATION_REQUIRED.\n\n'
        +'Starting main: '+HEAD+'. Previous v1 code audit was not opened during independent finding generation. '
        +'Normalized complex128 scientific model, QUBO, Hamiltonian, scalar objective and bit ordering agree. '
        +'The full acceptance gate fails: probability integrity guards, historical execution provenance, fail-sensitive validation and the convergence claim require correction.\n\n'
        +'Read acceptance_gate.json, finding_register.json, researcher_degrees_of_freedom.json, and the measured *_probes.json files. '
        +'Every finding is independent of previous audit classifications. independent_seal.json fixes all independent artifacts before comparison; comparison is a separate later artifact.\n\n'
        +'Reproduce probes (no optimizer/scientific source writes):\n\n```bash\n'
        +'PYTHONDONTWRITEBYTECODE=1 /home/takuma/.conda/envs/evrp-quantum-temp/bin/python reproducibility/tools/r23_n5_independent_audit.py\n```\n\n'
        +'For archival verification use sha256sum -c SHA256SUMS in this directory. Do not overwrite sealed evidence when reproducing: run from a disposable checkout with a new output root. '
        +'The report builder refuses to replace an existing seal. Historical final parameters and execution-time dirty sources are unavailable; this audit does not claim trajectory replay. '
        +'All source changes are prohibited here; remediation and R24 are not executed.\n')
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in {'SHA256SUMS','independent_seal.json'})
    write('independent_seal.json',{'sealed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'previous_audit_opened':False,
        'classification':classification,'finding_count':len(findings),'files':{p.name:sh(p) for p in files},
        'procedure':'Freeze classification, findings and all independent report bytes before first previous-audit content read. Later comparison must not edit these files.'})
    print(json.dumps({'classification':classification,'findings':severity,'arbitrariness':risk_counts,'seal':sh(OUT/'independent_seal.json')}))

if __name__=='__main__':main()
