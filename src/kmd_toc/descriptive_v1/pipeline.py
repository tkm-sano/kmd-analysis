import csv
import json
import platform
import sys
from importlib.metadata import version,PackageNotFoundError
from pathlib import Path

from kmd_toc.common.config import read_json
from .policy import ROOT,VERSION,PINS,digest,require_frozen
from .inputs import Reader,load_rows
from .analysis import analyze
from .statistics import summary


def dump(path,data):
    with Path(path).open('x') as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')


def csvfile(path,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r)) or ['status']
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})


def write_analysis(registration,output,*,figures=True):
    require_frozen();registration=Path(registration).resolve();output=Path(output).resolve()
    if output==registration.parent or output in registration.parents:raise ValueError('NEW_SEPARATE_OUTPUT_REQUIRED')
    reg_hash=digest(registration);reg=read_json(registration);reader=Reader(registration)
    sources=[*Path(__file__).parent.glob('*.py'),ROOT/'scripts/analyze_descriptive_v1.py',ROOT/'scripts/analyze_dw.py']
    code_hashes={str(path.resolve()):digest(path) for path in sources}
    reader.hashes.update(code_hashes)
    if 'eligibility_audit' in reg:reader.json(reg['eligibility_audit'])
    rows=load_rows(reg,reader);result=analyze(reg,rows,reader.evidence)
    result.update(version=VERSION,data_role=reg['data_role'],registration_path=str(registration),registration_sha256=reg_hash,
                  primary_metrics=['D','W'],derived_indicator='I_dual',error_bars='mean +/- 1 sample SD',
                  A_has_no_trial_distribution=True,policy_sha256=PINS,
                  variation_scope='one registered fixed problem per scale; algorithm execution variation only; no pooling across problems')
    packages={}
    for name in ('numpy','matplotlib'):
        try:packages[name]=version(name)
        except PackageNotFoundError:packages[name]=None
    result.update(analysis_code_sha256=code_hashes,environment={'python':sys.version,'executable':sys.executable,
                  'platform':platform.platform(),'packages':packages})
    if reader.unchanged() or digest(registration)!=reg_hash:raise ValueError('SOURCE_CHANGED_DURING_READONLY_ANALYSIS')
    output.mkdir(parents=True,exist_ok=False)
    dump(output/'ANALYSIS.json',result);dump(output/'SOURCE_HASHES.json',{str(registration):reg_hash,**reader.hashes})
    csvfile(output/'SUMMARY.csv',result['summaries']);csvfile(output/'COMPARISONS.csv',result['comparisons'])
    csvfile(output/'FAILURES.csv',result['failures']);csvfile(output/'TRIAL_AUDIT.csv',rows)
    internal=output/'internal';internal.mkdir()
    csvfile(internal/'J_PREFIXES.csv',result['prefixes'])
    csvfile(internal/'RESOURCES.csv',[{k:r.get(k) for k in ('trial_id','scale','method','status','planning_wall_s','CPU_s','max_RSS_MiB')} for r in rows])
    derived=[]
    for r in result['comparisons']:
        if r['delta_values'] is None:continue
        # Prefix MCSE is permitted only when the same registered design supports
        # the complete contrast MCSE, not because an SD or seed happens to match.
        independent=r['MCSE_status'] in ('DEFINED_INDEPENDENT_OUTER_UNITS','UNDEFINED_J_LT_2')
        for n in range(1,len(r['delta_values'])+1):
            derived.append({'scale':r['scale'],'baseline':r['baseline'],'comparison':r['comparison'],
                            'metric':r['metric'],'valid_prefix':n,
                            **summary(r['delta_values'][:n],independent=independent)})
    csvfile(internal/'CONTRAST_PREFIXES.csv',derived)
    dpre=[]
    for r in result['dual_trials']:
        for n in range(1,len(r['values'])+1):
            dpre.append({'scale':r['scale'],'method':r['method'],'matched_prefix':n,
                         **summary([v for v in r['values'][:n] if v is not None],independent=r['summary']['MCSE_status'] in
                                   ('DEFINED_INDEPENDENT_OUTER_UNITS','UNDEFINED_J_LT_2'))})
    csvfile(internal/'I_DUAL_PREFIXES.csv',dpre)
    dump(output/'J_DECISION.json',{'status':'HOLD','formal_J':None,'old_30_adopted':False,'MCSE_tolerance':None,
                                  'resource_budget':None,'SESOI':None,'selection_uses_p_or_power':False,
                                  'requirements':['documented independent outer trials','D/W and contrast stability',
                                     'MCSE tolerance and resource bounds fixed before J selection',
                                     'failure/missing estimand handling','separate user approval for formal J']})
    if figures:
        from .plots import render
        dump(output/'FIGURE_SPEC.json',render(result,rows,output/'figures'))
    if reader.unchanged() or digest(registration)!=reg_hash:raise ValueError('SOURCE_CHANGED_DURING_ANALYSIS')
    require_frozen()
    return result
