"""New pilot adapter: immutable sector implementation, fixed p/shots, boundary oracle.

No main-D/old-study sources are edited. Diagnostic optimizer budget is explicit.
"""
from dataclasses import asdict
import gzip
import json
import math
from pathlib import Path
import resource
import time

import numpy as np
from scipy.optimize import minimize

from kmd_toc.main_experiment_d import depth, shots
from kmd_toc.main_experiment_d.quantum import backend_modules
from kmd_toc.main_experiment_d.circuit import build_circuit, executed_layers
from kmd_toc.main_experiment_d.depth import checked_angles


def run(p, plan, local, protocol, folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=False)
    settings = protocol['optimizer_pilot_only']; numeric = protocol['numerical']
    depth_cfg = depth.frozen_config(); shots_cfg = shots.frozen_config()
    fixed_p = depth_cfg['qaoa']['depth_p']; pair = shots_cfg['qaoa_shots']
    angles0 = checked_angles(settings['initial_angles'])
    if fixed_p != 2 or pair['optimization'] != 1000 or pair['final_extraction'] != 10000:
        raise ValueError('PILOT_FREEZE_MISMATCH')
    begin = time.perf_counter(); cpu = time.process_time(); q, sector = backend_modules()
    start = time.perf_counter(); lookup = q.boundary_lookups(p, plan, local)
    problem_s = time.perf_counter() - start
    # Fresh private q module: use the existing boundary coefficients in its
    # unchanged SDK constructor and in the corresponding MPS update sequence.
    q.proxy_lookups = lambda _local: lookup
    start = time.perf_counter(); _, circuit_metadata = build_circuit(local, q)
    construction_s = time.perf_counter() - start
    history = []; final = None; evaluation = 0
    elapsed = dict(evolution_s=0., sampling_s=0., scoring_s=0.)
    width, _, total_q = q.register_layout(local.n)
    meta = {'depth_p': fixed_p, 'optimization_shots': pair['optimization'], 'final_extraction_shots': pair['final_extraction'],
            'depth_config_sha256': depth.CONFIG_SHA256, 'shots_config_sha256': shots.CONFIG_SHA256,
            'n': local.n, 'bond': numeric['bond_by_n'][str(local.n)], 'cutoff': numeric['cutoff'],
            'TV_threshold': numeric['TV_bound_max'], 'seed': local.seed, 'settings': settings,
            'oracle': lookup, 'circuit': circuit_metadata, 'local': local.payload()}
    (folder/'CALL.json').write_text(json.dumps(meta, allow_nan=False)+'\n')
    with gzip.open(folder/'updates.jsonl.gz', 'wt') as updates, (folder/'evaluations.jsonl').open('x') as progress:
        def execute(angles, phase, count, seed):
            nonlocal evaluation
            evaluation += 1; angles = checked_angles(angles)
            if depth.frozen_config() != depth_cfg or shots.frozen_config() != shots_cfg:
                raise ValueError('FREEZE_CHANGED_DURING_CALL')
            def update(row):
                updates.write(json.dumps({'evaluation': evaluation, 'phase': phase, **row}, allow_nan=False)+'\n')
                error = row['truncation_trace_bound']
                if not math.isfinite(error) or not 0 <= error <= numeric['TV_bound_max']:
                    raise ValueError('NUMERICAL_TV_CRITERION_NOT_MET')
                if time.perf_counter()-begin > protocol['safety_only']['local_wall_s']:
                    raise TimeoutError('LOCAL_SAFETY_WALL_STOP')
            start = time.perf_counter()
            M = sector.SectorMPS(q.initial_order(local), 1 << width, numeric['bond_by_n'][str(local.n)], numeric['cutoff'], update)
            M.prepare_sweep()
            for layer in range(fixed_p):
                M.layer = layer + 1
                M.phase(lookup, angles[2*layer], lookup['bound_m']); M.mixer(angles[2*layer+1])
            layers = executed_layers(M.logs, local.n); state = M.state()
            evolution_s = time.perf_counter()-start; elapsed['evolution_s'] += evolution_s
            bound = state['trace_distance_error_bound']
            if not math.isfinite(bound) or not 0 <= bound <= numeric['TV_bound_max']:
                raise ValueError('NUMERICAL_TV_CRITERION_NOT_MET')
            progress.write(json.dumps({'event':'sampling_started','phase':phase,'evaluation':evaluation,'requested_shots':count,'seed':seed})+'\n');progress.flush()
            start = time.perf_counter(); counts = sector.sample(state, count, seed, width, total_q)
            sampling_s = time.perf_counter()-start; elapsed['sampling_s'] += sampling_s
            actual = sum(counts.values())
            row = {'event':'sampling_completed','phase':phase,'evaluation':evaluation,'requested_shots':count,'actual_shots':actual,
                   'seed':seed,'angles':angles,'counts':counts,'TV_bound':bound,'combined_error_estimate':state['combined_error_estimate'],
                   'evolution_s':evolution_s,'sampling_s':sampling_s,**layers}
            progress.write(json.dumps(row, allow_nan=False)+'\n');progress.flush(); updates.flush()
            if actual != count: raise ValueError('ACTUAL_SHOTS_MISMATCH')
            start = time.perf_counter(); costs = []; label = {s:i+1 for i,s in enumerate(local.customer_ids)}
            for bits, value in counts.items():
                decision = q.decode_register(int(bits,2), local.customer_ids)
                order = tuple(label[s] for s in decision.trip_1)+(0,)+tuple(label[s] for s in decision.trip_2)
                costs.append((q.lookup_cost(order, lookup)/lookup['bound_m'], int(bits,2), decision, value))
            mean = math.fsum(cost*c for cost,_,_,c in costs)/actual
            elapsed['scoring_s'] += time.perf_counter()-start
            return row, mean, costs
        def objective(angles):
            if len(history) >= settings['max_evaluations']: raise ValueError('EVALUATION_CAP_EXCEEDED')
            row, value, _ = execute(angles,'optimization',pair['optimization'],local.seed+len(history))
            history.append({k:v for k,v in row.items() if k!='counts'})
            return value
        try:
            start = time.perf_counter()
            fit = minimize(objective, angles0, method=settings['method'],
                options={'maxiter':settings['max_evaluations'],'rhobeg':settings['rhobeg'],'tol':settings['tol']})
            optimizer_s = time.perf_counter()-start
            final, _, decoded = execute(fit.x,'final_extraction',pair['final_extraction'],local.seed+100000)
            start = time.perf_counter(); decoded.sort(key=lambda x:(x[0],x[1])); decode_s = time.perf_counter()-start
            result = {'status':'MEASURED','depth_p':fixed_p,'optimization_shots':pair['optimization'],
                'final_extraction_shots':pair['final_extraction'],'nfev':len(history),'scipy_nfev':int(fit.nfev),
                'optimizer_success':bool(fit.success),'optimizer_message':str(fit.message),'optimizer_fun':float(fit.fun),
                'angles':list(map(float,fit.x)),'training_shots_actual':sum(h['actual_shots'] for h in history),
                'final_shots_actual':final['actual_shots'],'max_TV_bound':max([h['TV_bound'] for h in history]+[final['TV_bound']]),
                'timing':{'problem_s':problem_s,'circuit_s':construction_s,'optimizer_inclusive_s':optimizer_s,
                    'final_evolution_s':final['evolution_s'],'final_sampling_s':final['sampling_s'],'decode_sort_s':decode_s,
                    **elapsed},'wall_s':time.perf_counter()-begin,'CPU_s':time.process_time()-cpu,
                'RSS_highwater_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                'unique_samples':len(decoded),'decode_rate':1.,'all_shots_physical_rate':None}
            (folder/'RESULT.json').write_text(json.dumps(result,allow_nan=False)+'\n')
            return decoded, result
        except Exception as error:
            (folder/'FAILURE.json').write_text(json.dumps({'status':'FAILED','error':f'{type(error).__name__}:{error}',
                'completed_optimization_shots':sum(h['actual_shots'] for h in history), 'inflight_shots':None,
                'settings_changed':False,'depth_p':fixed_p,'shots':pair})+'\n')
            raise
