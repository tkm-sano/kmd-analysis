from pathlib import Path
import csv,json,hashlib,collections
import numpy as np
R=Path('/home/takuma/kmd-analysis');B=Path(__file__).resolve().parents[1];rows=list(csv.DictReader((R/'review_outputs/no_sumo_full_analysis_20261102/run01/INPUT_LEDGER.csv').open()));summary={};outputs=[]
for x in rows:
 p=Path(x['input_path'])
 if not p.exists():continue
 assert hashlib.sha256(p.read_bytes()).hexdigest()==x['input_sha256'], str(p)
 with np.load(p,allow_pickle=False) as z:
  if not all(k in z for k in ['ready','due','service','demand']):continue
  a={k:z[k] for k in z.files};d=a['demand'][1:];ready=a['ready'][1:];due=a['due'][1:]
  outputs.append(dict(series=x['series_id'],problem=x['problem_id'],path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),n=len(d),demand_sum=int(d.sum()),max_demand=int(d.max()),service_values=np.unique(a['service'][1:]).tolist(),ready_values=np.unique(ready).tolist(),due_values=np.unique(due).tolist(),depot_due=int(a['due'][0]),no_customer_windows=bool(np.all(ready==0) and np.all(due==32400)),capacity216=bool(d.sum()<=216)))
for ser in sorted(set(x['series'] for x in outputs)):
 rr=[x for x in outputs if x['series']==ser];summary[ser]=dict(inputs=len(rr),n_counts=dict(collections.Counter(x['n'] for x in rr)),no_customer_windows=sum(x['no_customer_windows'] for x in rr),all_capacity216=all(x['capacity216'] for x in rr),max_individual_demand=max(x['max_demand'] for x in rr),demand_per_customer_total=sum(x['demand_sum'] for x in rr)/sum(x['n'] for x in rr))
(B/'probes/local_input_audit.json').write_text(json.dumps(dict(summary=summary,inputs=outputs),indent=2));print(summary)
