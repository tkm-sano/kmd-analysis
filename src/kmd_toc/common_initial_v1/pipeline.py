from pathlib import Path
import json
from .analysis import CommonReader,analyze
from .plans import dump,sha,VERSION
from kmd_toc.measurement_audit_v1.analysis import load_audited
from kmd_toc.measurement_audit_v1.pipeline import csvwrite


def write_analysis(registration,output,*,figures=True):
    from .policy import require_policy,EXPECTED
    require_policy()
    path=Path(registration).resolve();out=Path(output).resolve()
    if out.exists():raise ValueError('NEW_OUTPUT_REQUIRED')
    reg=json.loads(path.read_text())
    if reg.get('design_version')!=VERSION:raise ValueError('NEW_DESIGN_VERSION_REQUIRED')
    reader=CommonReader(path);before=sha(path);rows=load_audited(reg,reader)
    if reg['data_role']!='synthetic_statistics_fixture':
        for r in rows:r['common_initial_plan_sha256']=reader.initial_bindings.get(r['trial_id'])
    result=analyze(reg,rows,reader.evidence)
    if reader.unchanged() or before!=sha(path):raise ValueError('ANALYSIS_INPUT_CHANGED')
    out.mkdir(parents=True,exist_ok=False)
    dump(out/'ANALYSIS.json',result);csvwrite(out/'METHOD_SUMMARY.csv',result['summaries'])
    csvwrite(out/'COMPARISONS_6.csv',result['comparisons'])
    csvwrite(out/'HYPOTHESIS_MEAN_VALUES.csv',result['common_initial_mean_hypothesis'])
    csvwrite(out/'HYPOTHESIS_TRIAL_VALUES.csv',result['common_initial_trial_hypothesis'])
    csvwrite(out/'TRIAL_INDEX_SUMMARY.csv',result['trial_index_summaries'])
    csvwrite(out/'JUDGMENT_SUMMARY.csv',result['paired_judgment_summaries'])
    csvwrite(out/'TRIAL_STATUS.csv',result['audited_rows']);csvwrite(out/'FAILURES.csv',result['failures'])
    csvwrite(out/'MCSE_SUMMARY.csv',[{k:r[k] for k in ('scale','method','metric','J','MCSE','MCSE_status')} for r in result['summaries']]+[
        {'scale':r['scale'],'method':r['quantity'],'metric':'trial_index_percent','J':r['J'],'MCSE':r['MCSE'],'MCSE_status':r['MCSE_status']} for r in result['trial_index_summaries']])
    if figures:
        from .plots import render
        dump(out/'FIGURE_SPEC.json',render(result,out/'figures'))
    code={str(p):sha(p) for p in Path(__file__).parent.glob('*.py')}
    dump(out/'MANIFEST.json',{'design_version':VERSION,'policy_sha256':EXPECTED,'registration_sha256':before,'input_hashes':reader.hashes,
        'new_code_hashes':code,'data_role':reg['data_role'],'comparisons':36,'main_experiment':'HOLD',
        'J':'HOLD','n_K_R':'HOLD','C_reference_not_used_for_hybrid_selection':True,
        'primary_error_bar':'sample_SD','nonlinear_primary_index_MCSE':'HOLD_NOT_TRIAL_INDEX_MCSE'})
    if reader.unchanged():raise ValueError('ANALYSIS_SOURCE_CHANGED')
    return result
