"""Frequency-weighted independent validation and durable future-run artifacts."""
from fractions import Fraction
from collections import Counter
import gzip
from .contract import *
from .ledger import atomic

CSV_SCHEMAS={
 'OBJECTIVE_HISTORY.csv':['evaluation','alpha','beta','gamma','seed','shots','mean_energy','scaled_objective'],
 'FINAL_SAMPLE_COUNTS.csv':['display_bitstring','count'],
 'CONSTRAINT_VALIDITY.csv':['display_bitstring','count','visit','route','capacity','temporal','depot','overall_feasible','optimal_or_null','temporal_evaluability','nearest_feasible_distance_or_null'],
 'TEMPORAL_REPLAY.csv':['display_bitstring','count','overall_feasible','record_type','record'],
 'PENALTY_DECOMPOSITION.csv':['display_bitstring','count','base_objective','penalty_residuals','penalty_contributions','existing_CVRP_penalty','temporal_nogood_penalty','quadratization_penalty','coefficient_energy','factorized_energy'],
 'RESOURCE_TRACE.csv':['timestamp_utc','monotonic','process','cgroups','host','decision'],
}

def summarize(ad,counts,shots):
    require(isinstance(counts,dict) and counts and all(type(c) is int and c>0 for c in counts.values()),'counts','INVALID_SAMPLE_COUNT')
    require(sum(counts.values())==shots,'shot total','INVALID_SAMPLE_COUNT')
    diagnostics=[ad.inspect(k,c) for k,c in sorted(counts.items())]
    def weighted(predicate):return sum(d['count'] for d in diagnostics if predicate(d))
    feasible=weighted(lambda d:d['overall_feasible']);optimal=weighted(lambda d:d['optimal_or_null'])
    metrics=dict(shots=shots,unique_bitstrings=len(counts),feasible_count=feasible,optimal_count=optimal,
        feasible_sample_rate=feasible/shots,optimal_sample_rate=optimal/shots,
        mean_nearest_feasible_distance=sum(d['count']*d['nearest_feasible_distance_or_null'] for d in diagnostics)/shots if ad.feasible else None)
    histogram=Counter()
    for d in diagnostics:histogram[str(d['nearest_feasible_distance_or_null'])]+=d['count']
    metrics['nearest_feasible_distance_histogram']=dict(histogram)
    for k in ['visit','route','capacity','temporal','depot']:
        valid=weighted(lambda d:d[k] is True);invalid=weighted(lambda d:d[k] is False);evaluable=valid+invalid
        metrics.update({k+'_valid_count':valid,k+'_invalid_count':invalid,k+'_not_evaluable_count':shots-evaluable,
            k+'_evaluable_count':evaluable,k+'_valid_rate':valid/shots,k+'_evaluable_rate':evaluable/shots,
            k+'_valid_rate_among_evaluable':valid/evaluable if evaluable else None})
    for name,residual in [('capacity_encoding_valid','capacity'),('temporal_nogood_zero','temporal'),('ancilla_consistent','ancilla')]:
        metrics[name+'_rate']=weighted(lambda d:d['penalty_residuals'][residual]==0)/shots
    violations=Counter()
    for d in diagnostics:
        if not d['overall_feasible']:
            for v in d['violation_labels']:violations[v]+=d['count']
    metrics['violation_counts_multi_label']=dict(violations)
    metrics['temporal_precedence_sampled_violation']=None
    metrics['early_service_sampled_violation']=None
    metrics['temporal_precedence_observability']='NOT_INDEPENDENTLY_ENCODED'
    waits=[(Fraction(d['waiting_seconds']),d['count']) for d in diagnostics if d['overall_feasible']]
    metrics['feasible_waiting']=dict(denominator=feasible,
        mean_seconds=float(sum(w*c for w,c in waits)/feasible) if feasible else None,
        min_seconds=float(min(w for w,c in waits)) if feasible else None,
        max_seconds=float(max(w for w,c in waits)) if feasible else None,
        positive_wait_fraction=sum(c for w,c in waits if w>0)/feasible if feasible else None)
    customers={}
    for d in diagnostics:
        if not d['overall_feasible']:continue
        for row in d['replay_customer_rows']:
            cid=str(row['customer_id']);item=customers.setdefault(cid,dict(count=0,waiting=Fraction(0)))
            item['count']+=d['count'];item['waiting']+=Fraction(str(row['waiting_time']))*d['count']
    metrics['feasible_waiting']['per_customer']={k:dict(count=v['count'],mean_waiting_seconds=float(v['waiting']/v['count'])) for k,v in customers.items()}
    metrics['mean_QUBO_energy']=sum(d['count']*d['coefficient_energy'] for d in diagnostics)/shots
    metrics['best_infeasible_sampled_energy']=min((d['coefficient_energy'] for d in diagnostics if not d['overall_feasible']),default=None)
    return metrics,diagnostics

def schemas():
    return dict(csv=CSV_SCHEMAS,json=['RUN_SPEC.json','RUN_IDENTITY.json','INCUMBENT.json','RUN_RESULT.json','RESULT.json','VALIDATION.json','FINAL_METRICS.json','ARTIFACT_SHA256.json'],
        additional=['FINAL_RAW_COUNTS.json','BITSTRING_DIAGNOSTICS.jsonl.gz','RESOURCE_TRACE.jsonl','receipts/'],
        authority=str(FREEZE/'METRIC_SPEC.json'),non_evaluable='null plus NOT_EVALUABLE; never silently valid',
        temporal_precedence='not independently encoded; replay invariant only',time_arithmetic='exact rational; serialized decimal source fields, aggregate Fraction strings or floats explicitly labeled')

def save(directory,p,counts,history,incumbent,*,synthetic=False):
    directory=Path(directory);ad=p['adapter'];metrics,diagnostics=summarize(ad,counts,p['spec']['shots']['independent_final'])
    atomic(directory/'RUN_SPEC.json',dict(identity=p['identity'],configuration=p['spec'],run=p['plan'],synthetic=synthetic))
    atomic(directory/'RUN_IDENTITY.json',p['identity']);atomic(directory/'INCUMBENT.json',incumbent)
    atomic(directory/'FINAL_RAW_COUNTS.json',counts);atomic(directory/'FINAL_METRICS.json',metrics)
    table(directory/'OBJECTIVE_HISTORY.csv',history,CSV_SCHEMAS['OBJECTIVE_HISTORY.csv'])
    table(directory/'OPTIMIZER_HISTORY.csv',history,CSV_SCHEMAS['OBJECTIVE_HISTORY.csv'])
    table(directory/'FINAL_SAMPLE_COUNTS.csv',[dict(display_bitstring=k,count=v) for k,v in sorted(counts.items())],CSV_SCHEMAS['FINAL_SAMPLE_COUNTS.csv'])
    for name in ['CONSTRAINT_VALIDITY.csv','PENALTY_DECOMPOSITION.csv']:
        table(directory/name,[{k:d.get(k) for k in CSV_SCHEMAS[name]} for d in diagnostics],CSV_SCHEMAS[name])
    replay=[]
    for d in diagnostics:
        for kind,key in [('customer','replay_customer_rows'),('vehicle','replay_vehicle_rows')]:
            for row in d[key]:replay.append(dict(display_bitstring=d['display_bitstring'],count=d['count'],overall_feasible=d['overall_feasible'],record_type=kind,record=row))
    table(directory/'TEMPORAL_REPLAY.csv',replay,CSV_SCHEMAS['TEMPORAL_REPLAY.csv'])
    with gzip.open(directory/'BITSTRING_DIAGNOSTICS.jsonl.gz','wt') as f:
        for d in diagnostics:f.write(json.dumps(d,allow_nan=False)+'\n')
    trace=directory/'RESOURCE_TRACE.jsonl'
    records=[json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
    table(directory/'RESOURCE_TRACE.csv',[{k:r.get(k) for k in CSV_SCHEMAS['RESOURCE_TRACE.csv']} for r in records],CSV_SCHEMAS['RESOURCE_TRACE.csv'])
    validation=dict(status='PASS',all_distinct_samples_validated=True,shots=sum(counts.values()),validator_authority='existing independent VRPTW validator',synthetic=synthetic)
    atomic(directory/'VALIDATION.json',validation)
    result=dict(status='SUCCEEDED',identity=p['identity'],synthetic=synthetic,metrics=metrics,training_circuits=len(history),final_circuits=1,
        automatic_retry=False,performance_is_not_acceptance=True,resources=p['resources'],
        resource_observations=len(records),resource_peak_rss_bytes=max((r['process']['peak_rss_bytes'] for r in records if isinstance(r.get('process',{}).get('peak_rss_bytes'),int)),default=None))
    atomic(directory/'RUN_RESULT.json',result);atomic(directory/'RESULT.json',result)
    atomic(directory/'ARTIFACT_SHA256.json',{str(f.relative_to(directory)):sha(f) for f in directory.rglob('*') if f.is_file() and f.name!='ARTIFACT_SHA256.json'})
    return result

def aggregate_batch(planned,results,ledger_state):
    require(len(planned)==3 and len({r['condition'] for r in planned})==1 and [int(r['repetition']) for r in planned]==[0,1,2],'batch shape')
    expected=[r['run_id'] for r in planned];byid={r['identity']['run_id']:r for r in results}
    require(len(byid)==len(results) and set(byid)<=set(expected),'batch results')
    missing=[r for r in expected if r not in byid];complete=not missing
    for rid,r in byid.items():require(r['identity']==identity(load(),plan(load(),rid)) and r['status']=='SUCCEEDED','batch identity')
    output=dict(condition=planned[0]['condition'],order=expected,missing=missing,complete=complete,ledger_state=ledger_state,
        completion=[dict(run_id=r,complete=r in byid) for r in expected],total_circuits=sum(r['training_circuits']+r['final_circuits'] for r in results),
        final_shots=sum(r['metrics']['shots'] for r in results),rates=None,classification='INCOMPLETE' if missing else 'COMPLETE')
    violations=Counter()
    for r in results:violations.update(r['metrics']['violation_counts_multi_label'])
    output['violation_breakdown']=dict(violations)
    output['resource_snapshot']=next(r for r in rows(FREEZE/'RESOURCE_SNAPSHOT.csv') if r['condition']==planned[0]['condition'])
    output['resource_summary']=[dict(run_id=r['identity']['run_id'],resources=r.get('resources')) for r in results]
    if complete:
        shots=output['final_shots'];output['rates']={}
        for metric in ['feasible_sample_rate','optimal_sample_rate','temporal_valid_rate','mean_nearest_feasible_distance']:
            vals=[byid[r]['metrics'][metric] for r in expected]
            output['rates'][metric]=dict(repetitions=vals,pooled=sum(byid[r]['metrics'][metric]*byid[r]['metrics']['shots'] for r in expected)/shots,mean=sum(vals)/3,min=min(vals),max=max(vals))
        output['classification']='VRPTW_QAOA_FEASIBLE_SAMPLING_OBSERVED' if any(r['metrics']['feasible_count'] for r in results) else 'VRPTW_QAOA_NO_FEASIBLE_SAMPLING'
        output['optimal_classification']='VRPTW_QAOA_OPTIMAL_SAMPLING_OBSERVED' if any(r['metrics']['optimal_count'] for r in results) else 'VRPTW_QAOA_NO_OPTIMAL_SAMPLING'
    return output
