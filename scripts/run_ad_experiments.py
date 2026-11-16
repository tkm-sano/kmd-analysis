"""Registered order: freeze A ranges and epsilon references BEFORE B/C/D."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'))
CASES=['ROAD_N6','ROAD_N20','ROAD_N120','ROAD_N240','S1']

def launch(case,method,label,primary='D',limit=None,offset=0):
    out=ROOT/'experiments'/case/(method+'_'+label)
    if (out/'result.json').exists():return json.loads((out/'result.json').read_text())
    log=ROOT/'logs';log.mkdir(exist_ok=True)
    args=[sys.executable,'scripts/run_ad_method.py','--input',str(ROOT/'roads/inputs'/case),'--method',method,'--output',str(out),'--primary',primary,'--offset',str(offset)]
    if limit is not None:args+=['--other-limit',str(limit)]
    print('START',case,method,label,flush=True);start=time.perf_counter()
    try:
        with (log/f'{case}_{method}_{label}.log').open('w') as f:
            r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=300 if method=='D' else 240,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
        if not (out/'result.json').exists():raise RuntimeError('CHILD_EXIT_'+str(r.returncode))
        result=json.loads((out/'result.json').read_text())
    except (subprocess.TimeoutExpired,RuntimeError) as e:
        out.mkdir(parents=True,exist_ok=True);result={'status':'TIMEOUT' if isinstance(e,subprocess.TimeoutExpired) else 'ERROR','reason':str(e),'method':method,'scenario_id':case,'primary':primary,'other_limit':limit,'D_km':None,'W_min':None,'T_program_s':None,'elapsed_wall_s':time.perf_counter()-start}
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('END',case,method,label,result['status'],result['D_km'],result['W_min'],flush=True)
    return result

def main():
    references={}
    for case in CASES:
        first=None
        for method in ['A1','A2','A3']:
            for offset in [0,120,240]:
                r=launch(case,method,f'angle{offset}',offset=offset)
                if first is None and r['status']=='FEASIBLE':first={'method':method,'offset':offset,'D_km':r['D_km'],'W_min':r['W_min'],'input_hash':r['input_hash'],'OD_hash':r['OD_hash']}
        references[case]=first
    refpath=ROOT/'EPSILON_REFERENCES.json'
    text=json.dumps(references,indent=2)+'\n'
    if refpath.exists() and refpath.read_text()!=text:raise ValueError('EPSILON_REFERENCE_CHANGED')
    refpath.write_text(text)
    print('A AND EPSILON REFERENCES FROZEN',flush=True)
    for case in CASES:
        ref=references[case]
        if ref is None:
            print('NO_FEASIBLE_A_REFERENCE',case,flush=True);continue
        for method in ['B','C','D']:
            launch(case,method,'primaryD_epsW_1',limit=ref['W_min'])
    # Bidirectional epsilon profiles on S1; absolute common levels are fixed by
    # the first feasible registered A plan, never by B/C/D outcomes.
    ref=references['S1']
    if ref:
        for method in ['B','C','D']:
            for multiplier in [1.,1.25,1.5]:
                if multiplier==1. or ref['W_min']==0:continue
                launch('S1',method,f'primaryD_epsW_{multiplier:g}',limit=ref['W_min']*multiplier)
            for multiplier in [1.,1.1,1.25]:
                launch('S1',method,f'primaryW_epsD_{multiplier:g}',primary='W',limit=ref['D_km']*multiplier)

if __name__=='__main__':main()
