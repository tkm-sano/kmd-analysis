"""Generate new, non-overwriting zero-charge regression artifacts; no optimization.

Run from repo: PYTHONPATH=05_src/traffic_simulation python -m
r24_minimal_evrp.run_regression --output <new directory>
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from .replay import replay
from .independent import validate_saved

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reproducibility/outputs/traffic_simulation'
DESIGN=BASE/'r24_minimal_evrp_design_authority/20260926_v1'
LEDGER=BASE/'r24_vrptw_uniform_vs_structured_comparison/20260922_v1/COMPARISON_CIRCUIT_LEDGER.json'
FORBIDDEN=('qiskit','qiskit_aer','highspy','scipy.optimize')

def guard(event,args):
    if event=='import' and any(args[0]==p or args[0].startswith(p+'.') for p in FORBIDDEN):
        raise RuntimeError('STOP: prohibited execution dependency import '+args[0])

def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def relative(path): return str(path.relative_to(ROOT))
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def verify(mapping):
    mismatches=[p for p,h in mapping.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    if mismatches: raise RuntimeError('STOP: protected input mismatch '+repr(mismatches[:20]))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    out=parser.parse_args().output.resolve()
    if out.exists(): raise RuntimeError('Refuse to overwrite existing outputs')
    sys.addaudithook(guard)
    if any(any(m==p or m.startswith(p+'.') for p in FORBIDDEN) for m in sys.modules):
        raise RuntimeError('STOP: prohibited dependency already loaded')
    before=read(DESIGN/'INPUT_MANIFEST.json')
    for path in DESIGN.rglob('*'):
        if path.is_file() and '__pycache__' not in str(path): before[relative(path)]=sha(path)
    verify(before)
    manifest=read(DESIGN/'ARTIFACT_MANIFEST.json')['artifacts']
    if any(sha(DESIGN/p)!=h for p,h in manifest.items()): raise RuntimeError('STOP: design manifest')
    authority=read(DESIGN/'MINIMAL_EVRP_AUTHORITY.json')
    fixture=read(DESIGN/'FROZEN_VALIDATION_INPUTS.json')['fixtures'][0]
    if fixture['condition']!=authority['initial_case']: raise RuntimeError('STOP: first case mismatch')
    instance_path=ROOT/fixture['base_instance'];exact_path=ROOT/fixture['exact_reference']
    milp_path=exact_path.parent/'MILP.json'
    for path in (instance_path,exact_path,milp_path,LEDGER):
        if relative(path) not in before: raise RuntimeError('Unpinned input '+str(path))
    if sha(instance_path)!=fixture['base_sha256'] or sha(exact_path)!=fixture['exact_sha256']:
        raise RuntimeError('STOP: fixture hashes')
    instance,exact,milp=read(instance_path),read(exact_path),read(milp_path)
    if exact['status']!='PROVEN_OPTIMAL' or not exact['complete'] or milp['status']!='PROVEN_OPTIMAL':
        raise RuntimeError('STOP: optimum authority')
    if exact['optimal_route_set']!=fixture['saved_optimal_route_set']: raise RuntimeError('STOP: witness drift')
    totals=read(LEDGER)['totals']
    if (totals['scientific_consumed'],totals['shots_consumed'],totals['reserved'])!=(541,1107968,0):
        raise RuntimeError('STOP: live ledger differs')
    fresh=dict(HEAD=git('rev-parse','HEAD'),origin_main=git('rev-parse','origin/main'),
        branch=git('branch','--show-current'),status_before_outputs=git('status','--short'),
        log=git('log','--oneline','-10'),protected_inputs=len(before),ledger_before=totals,
        baseline_note='Pre-existing untracked source registry is pinned by frozen authority; new r24_minimal_evrp code is intended. Historical exact/MILP modules absent under accepted cleanup.',GO_STOP='GO')
    routes=milp['audit']['routes']
    if not any(w['routes']==routes for w in exact['optimal_route_set']): raise RuntimeError('STOP: route witness')
    result=replay(instance,routes,authority,source_distance_unit='m')
    if result['vrptw']!=milp['audit']['replay']: raise RuntimeError('STOP: full temporal/VRPTW regression')
    if not result['combined_feasible']: raise RuntimeError('STOP: EV reserve violation')
    if result['vrptw']['routing_objective_seconds']!=exact['best_objective']: raise RuntimeError('STOP: objective')
    # Each labeled optimum is a separate plan; never combine duplicate customers into a fleet.
    witnesses=[]
    for i,w in enumerate(exact['optimal_route_set']):
        res=replay(instance,w['routes'],authority,source_distance_unit='m')
        val=validate_saved(instance,authority,w['routes'],json.loads(json.dumps(res)))
        if not res['combined_feasible'] or val['status']!='PASS': raise RuntimeError('STOP: witness EV validation')
        witnesses.append(dict(witness_index=i,result=res,independent_validation=val))
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('r24_minimal_evrp.test_replay'))
    if not tests.wasSuccessful(): raise RuntimeError('STOP: tests failed\n'+stream.getvalue())
    out.mkdir(parents=True)
    def write(name,obj): (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    def table(name,rows):
        with (out/name).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write('EV_VALIDATION.json',result)
    independent=validate_saved(read(instance_path),read(DESIGN/'MINIMAL_EVRP_AUTHORITY.json'),
                               read(milp_path)['audit']['routes'],read(out/'EV_VALIDATION.json'))
    write('INDEPENDENT_VALIDATION.json',independent)
    if independent['status']!='PASS': raise RuntimeError('STOP: independent saved-file disagreement')
    table('EV_ROUTE_REPLAY.csv',result['arcs']);table('EV_BATTERY_TRAJECTORY.csv',result['trajectory'])
    write('ALL_FROZEN_OPTIMAL_WITNESSES.json',witnesses)
    write('FROZEN_INPUT_REFERENCE.json',dict(fixture=fixture,instance_sha256=sha(instance_path),
        exact_sha256=sha(exact_path),milp_path=relative(milp_path),milp_sha256=sha(milp_path),
        frozen_routes=routes,frozen_replay=milp['audit']['replay'],
        frozen_objective=exact['best_objective'],parameter_authority_sha256=sha(DESIGN/'MINIMAL_EVRP_AUTHORITY.json')))
    checks=dict(authority_inputs_match=True,frozen_optimal_route_reused=True,
        all_saved_optimal_witnesses_ev_feasible=True,customer_assignment_unchanged=True,visit_order_unchanged=True,
        primary_objective_unchanged=True,full_vrptw_validation_payload_equal=True,
        temporal_result_unchanged=True,distance_metres_explicit=True,
        no_charging=True,energy_conservation=True,all_arrivals_above_reserve=True,
        depot_return_above_reserve=True,independent_validation_pass=True,tests_pass=True)
    write('REGRESSION_CHECK.json',dict(verdict='MINIMAL_EVRP_EXISTING_ROUTE_REGRESSION = PASS',
        checks=checks,proof='F_EV subset F_V; saved global VRPTW optimum x* belongs to F_EV. Same travel objective implies x* remains globally primary-optimal. Charging-time secondary is identically zero.',
        solver_execution=False,witness_count=len(witnesses),scope='first N002 WIDE only'))
    (out/'TEST_RESULTS.txt').write_text(stream.getvalue()+'\nInitial development test had a manually transcribed final-battery expected-value typo (18.477858385541); independent Decimal calculation confirmed 18.477857385541. Corrected only the new test literal; no parameter/input/replay change.\n')
    write('FRESH_GATE.json',fresh);write('PROTECTED_INPUTS_BEFORE.json',before)
    direct=[instance_path,exact_path,milp_path,LEDGER,LEDGER.parent/'CIRCUIT_LEDGER.jsonl',
            DESIGN/'MINIMAL_EVRP_AUTHORITY.json',DESIGN/'ARTIFACT_MANIFEST.json',
            DESIGN/'FROZEN_VALIDATION_INPUTS.json',ROOT/authority['source_registry'],
            ROOT/'05_src/traffic_simulation/r24_vrptw/instance.py',ROOT/'05_src/traffic_simulation/r24_vrptw/validator.py',
            ROOT/'05_src/traffic_simulation/r24_instance_generation/generate_r24_benchmark_instance_suite.py']
    write('DIRECT_INPUT_HASHES.json',{relative(p):sha(p) for p in direct})
    used=next(v for v in result['vehicles'] if v['used'])
    report=f'''# EV制約を追加しても既存経路が成立するケース

MINIMAL_EVRP_EXISTING_ROUTE_REGRESSION = PASS。MODEL_VALIDATION。

## A. Purpose
凍結VRPTWへ距離比例energy/SOC制約を独立したEV層として追加し、既存最適経路・目的値・時刻を保存する回帰検証。新規solver・optimizer実行なし。現在の依頼に従い、設計計画の将来solver検証をmembership証明で置き換える。充電が必要なケースには進まない。

## B. Frozen input
Instance `{fixture['condition']}`。depot DEP_006、顧客2026-01-01-13111-bldg-43666(demand1)、2026-01-01-13111-bldg-67228(demand7)。WIDE、RHO050、fleet上限2(V1,V2)、各Q=14 parcel-equivalent。V1が両顧客を担当、V2未使用。Qはkgでもbatteryでもない。

Frozen route: DEP_006 → 2026-01-01-13111-bldg-67228 → 2026-01-01-13111-bldg-43666 → DEP_006。
Frozen primary optimum {exact['best_objective']} seconds。MILP.json audit.replayが全arrival/wait/service/departure/returnの保存基準。EXACT.json complete optimum setにはV1/V2ラベル対称の2 witnessがあり、両方を独立planとして検証。両planを合算しない。

Instance: `{relative(instance_path)}`。Exact: `{relative(exact_path)}`。Temporal: `{relative(milp_path)}`。正確なSHA256はDIRECT_INPUT_HASHES.json/FROZEN_INPUT_REFERENCE.json。道路・時間行列は同instance.travel、経路生成元EdgeRouter.routeのdistance_m/travel_time_sを保存した値。距離最短化や新しい道路経路探索は行わない。design authorityのroad_path_distance行と生成元を照合し、source distance=m、EV distance=km、d[km]=travel_distance[m]/1000を明示。customer/depot/fleet/TW/service/road dataは変更なし。

## C. EV parameters
Reference: {authority['reference_vehicle']}。

| Quantity | Value | Provenance / model role |
|---|---|---|
| B_max / B_initial | 20 kWh / 20 kWh | research-defined model capacity / derived initial energy |
| initial SOC | 100% | RESEARCH_DEFINED_ASSUMPTION |
| minimum SOC / B_min | 10% / 2 kWh | research assumption / derived reserve |
| r | 127 Wh/km = 0.127 kWh/km | OFFICIAL_OBSERVED source; METHODOLOGICAL_PROXY model role |
| q_chg / t_chg | 0 kWh / 0 seconds at all occurrences | frozen charger-disabled validation scope |

20kWhはofficial usable battery capacityではない。127Wh/kmはofficial AC WLTC standardized valueを距離比例battery debitのproxyに使う。実配送時の実測電費でもbattery-side tractionの測定値でもない。出典は凍結registryとメーカーsnapshotに固定。新たな外部specへ置換しない。

## D. Equations and interpretation
E_ij=r d_ij [kWh]：既存道路距離[km]に一定係数[kWh/km]を掛け、当該移動の消費を近似。
B_0_dep=B_max [kWh]：各使用車両は満充電で出発し、出発前充電はroute horizon外。
B_i_dep=B_i_arr+q_i_chg=B_i_arr [kWh]：今回は充電なし、待機・サービス中の消費も除外。
B_j_arr=B_i_dep−E_ij [kWh]：移動ごとに残量を減算し、補正・clamp・repairなし。
B_min≤B_i_arr≤B_max [kWh]：全arrivalと最終depot returnでreserveを厳密判定。非負充電0によりdepartureも同じ条件。
SOC_i=100 B_i/B_max [%]：表示用derived quantity。feasibilityはkWhが主表現。
B_final=B_initial−ΣE [kWh]：各routeのenergy conservation。
t_j_arr=t_i_dep+tau_ij [s]：charging時間0なので既存max(arrival,earliest)・waiting・service-start TW・depot closingの規則を保持。
min T_travel [s]がprimary、primary-optimalの中でmin T_chg [s]がsecondary。このケースでは全解T_chg=0、weighted sumも経済目的もない。
Exact Fraction照合tolerance=0。独立Decimal精度80も本fixtureで正確。凍結diagnostic toleranceはenergy1e-9kWh/time1e-7s、reserve/TWの緩和には使わない。

## E. Implementation
`05_src/traffic_simulation/r24_minimal_evrp/replay.py`: parameters,distance_km,energy_kwh,battery_after,battery_feasible,replay。既存r24_vrptw.instance.validate_inputとvalidator.validate_routesへ元の入力を渡し、EV fieldsは別sidecarに格納。既存replay_sequenceと同じ時間意味を保持、quantum moduleはimportしない。
`independent.py`: validate_saved。replay helperをimportせずDecimalの累積energyから全batteryを独立再計算。
`run_regression.py`: authority/hash gate、保存済みwitness replay、saved-file再読込み検証、出力生成。quantum/optimizer dependency import guard付き。
`test_replay.py`: {tests.testsRun} tests。変換、逐次残量、reserve等号/直下のscalar境界、充電0、全VRPTW payload、depot return、独立照合、改ざん検出、2ラベル最適witness、欠損距離、NOT_EVALUABLE/unusedを検証。境界テストはscalar演算であり、車両条件を変更した配送scenarioではない。
EV JSONはarcs/trajectory/vehicles/fleet/vrptwを分離。unused vehicleはroute=[]、energy0、battery判定NOT_EVALUABLEを維持。初期depotに架空arrivalを作らず、final depotではarrival/departure energyは同値の記帳だけで追加移動を作らない。

## F. Route-level result
V1 distance {used['distance_km']} km、road travel {used['travel_time_s']} s、driving energy {used['energy_kwh']} kWh。V2未使用。fleet totalはV1と同じ。depot return時刻1252.007343058s、waiting0s、service154.12590727s。arrival/service/departure全字段が保存基準と完全一致。

## G. Battery trajectory
20 kWhから各arc後の残量は、{', '.join(str(a['battery_after_kwh'])+' kWh' for a in result['arcs'])}。最小残量=最終残量={used['final_battery_kwh']}kWh、最小/最終SOC={used['final_soc_pct']}%。2kWh reserveを全arrivalで満たす。全node q=t=0。詳細はEV_ROUTE_REPLAY.csv、EV_BATTERY_TRAJECTORY.csv。

## H. Independent validation
保存EV_VALIDATION.jsonを再読み込み、別Decimal実装で全distance、各arc energy、battery before/after、SOC、route/fleet集計、depot残量とreserve判定を再計算。INDEPENDENT_VALIDATION.json=PASS。初回開発テストの期待残量転記ミスのみ修正した履歴をTEST_RESULTS.txtに保持。実装・authority・パラメータを結果に合わせて変更していない。

## I. VRPTW regression result
| Check | Frozen VRPTW | Minimal EVRP | Result |
|---|---|---|---|
| customer set | 43666,67228 (full IDs above) | identical | PASS |
| route sequence | depot→67228→43666→depot;V1 | identical;V2 unused | PASS |
| travel time | {exact['best_objective']} s | {used['travel_time_s']} s | PASS |
| temporal feasibility | PASS; full saved replay | identical | PASS |
| charging amount | N/A | 0 kWh;0 s | PASS |
| driving energy | N/A | {used['energy_kwh']} kWh | PASS |
| minimum battery | N/A | {used['minimum_battery_kwh']} kWh | PASS |
| final battery | N/A | {used['final_battery_kwh']} kWh | PASS |
| minimum SOC constraint | N/A | {used['minimum_soc_pct']}% ≥10% | PASS |
| depot return EV feasibility | N/A | PASS | PASS |

F_EV⊆F_V。保存されたglobal VRPTW optimum x*が追加EV制約を満たしてx*∈F_EVと確認された。同じprimary objectiveの下で、F_EVにx*より小さい値の解があればF_Vの最適性に矛盾する。よってx*はEV層追加後もprimary-optimal。新しいEV optimizerは不要。これは難しいEV配送問題を新規に解いたという主張ではない。

## J. Limitations
今回はN002 WIDEの既存経路回帰のみ。N003、active-TW、充電必須、capacity縮小、SOC低下、電費/距離変更、劣化、将来battery、QUBO/QAOA、S0、経済評価は未実施。速度/payload/勾配/HVAC/温度/回生/加速/補機/idle損失なし。charger topology/access/power/vehicle acceptanceは未解決で、仮chargerを作らない。実車運用、経済便益、quantum advantageの証拠ではない。

## K. Next unresolved work / STOP
VRPTW results remain FROZEN。Minimal EVRP authority remains FROZEN。Energy accountingとbattery/SOC propagation IMPLEMENTED、existing-route regression COMPLETED。
Charging-required validation、charging optimization、battery degradation/technology scenarios、S0 baseline、economic evaluation、EVRP QUBO/QAOAはNOT STARTED。Charger topology NOT FROZEN。
科学回路/shot/optimizer/Aerの今回消費0。ledger541 circuits、1,107,968 shots、reserved0を前後SHA256で確認。新規予約0。VRPTWと設計authority保護ファイル不変性はREPRODUCIBILITY_AUDIT.json。
NEXT_TASK=Resolve charging infrastructure / charging-power authority and design the case where EV constraints require charging。今回開始しない。STOP。
'''
    (out/'MINIMAL_EVRP_NO_CHARGING_IMPLEMENTATION_REPORT.md').write_text(report)
    verify(before)
    if read(LEDGER)['totals']!=totals: raise RuntimeError('STOP: ledger changed')
    code={relative(p):sha(p) for p in Path(__file__).parent.glob('*.py')}
    write('CODE_MANIFEST.json',code)
    write('REPRODUCIBILITY_AUDIT.json',dict(status='PASS',protected_inputs=len(before),all_input_hashes_unchanged=True,
        VRPTW_freezes_unchanged=True,EV_authority_unchanged=True,ledger_before=totals,ledger_after=read(LEDGER)['totals'],
        execution_delta=dict(scientific_circuits=0,scientific_shots=0,optimizer_evaluations=0,Aer_calls=0,QAOA_runs=0,new_reservations=0,EVRP_solver_runs=0),
        execution_evidence='stdlib-only EV modules plus frozen validator; prohibited dependency import guard; no solver/backend entry point; ledger and journal byte hashes unchanged',
        tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),
        git_status=git('status','--short'),git_tracked_diff=git('diff','--stat'),
        changes='Only new r24_minimal_evrp code/tests and dedicated ignored output artifacts. Pre-existing source registry remains unmodified/untracked. No commit/push.',
        output_manifest_policy='ARTIFACT_MANIFEST.json hashes every output file except itself; code hashes separately pinned'))
    write('ARTIFACT_MANIFEST.json',dict(schema='sha256-relative-path-v1',self_excluded=True,
                                      artifacts={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}))
    for p,h in read(out/'ARTIFACT_MANIFEST.json')['artifacts'].items():
        if sha(out/p)!=h: raise RuntimeError('Output manifest mismatch')
    print(json.dumps(dict(verdict='PASS',output=str(out),fleet=result['fleet'],tests=tests.testsRun,protected_inputs=len(before)),indent=2))

if __name__=='__main__': main()
