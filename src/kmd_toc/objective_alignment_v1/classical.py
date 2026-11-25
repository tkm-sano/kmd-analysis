"""C_Idual adapter: exact physical CP + common archive fallback, no old edits."""
from dataclasses import asdict
from pathlib import Path
import time,resource
from kmd_toc.common_initial_v1.plans import start,dump,exact_metrics
from kmd_toc.common_initial_v1.engines import routing_from_initial,slot_routes
from .archive import Archive
from .objective import ObjectiveHold,measure
from fractions import Fraction as F
from .cp import solve

def run(p,initial,output,*,config,seed,route_pool=None,cp_solver=solve):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);begin=time.perf_counter();cpu=time.process_time()
    original=start(p,initial,'C',out)
    if original is None:
        result={'condition_id':'C_Idual','status':'COMMON_INITIAL_UNAVAILABLE','main_experiment':'HOLD'}
        dump(out/'RESULT.json',result);return result
    archive=Archive(p,original,out/'candidates')
    rt=time.perf_counter()
    if route_pool is None:
        pool,bridge=routing_from_initial(p,original,config,seed);dump(out/'ROUTING_BRIDGE.json',bridge)
    else:pool=list(route_pool)
    routing_s=time.perf_counter()-rt;cp_report=None;cp_error=None;t=time.perf_counter()
    try:
        proposal,cp_report=cp_solver(p,pool,original,config,seed)
        m=measure(p,proposal)
        if (cp_report.get('CP_D_exact') is None or cp_report.get('CP_W_exact') is None or
                F(cp_report['CP_D_exact'])!=m.D or F(cp_report['CP_W_exact'])!=m.W):
            raise ObjectiveHold('CP_REPORTED_DW_NOT_EQUAL_FINAL_COMMON_EVALUATOR')
        archive.add(proposal,origin='C_Idual_exact_physical_CP')
        if archive.rows[-1]['status']=='INFEASIBLE_OR_MEASUREMENT_FAIL':
            raise ObjectiveHold('CP_FINAL_PHYSICAL_OR_INDEPENDENT_MEASUREMENT_REJECTED')
    except ObjectiveHold as error:cp_error=str(error)
    cp_s=time.perf_counter()-t
    selected,why=archive.best();initial.checked_plan(p)
    archive.save(out/'ARCHIVE.json');dump(out/'plan.json',asdict(selected))
    result={'condition_id':'C_Idual','status':'HOLD_CP_REPRESENTATION_OR_SOLVE' if cp_error else 'COMPLETE_COMPONENT_VALIDATION',
        'CP':cp_report,'CP_HOLD_reason':cp_error,'selected':why,'metrics':exact_metrics(p,selected),
        'initial_plan_sha256':initial.manifest['plan_sha256'],'candidate_pool_size':len(pool),
        'candidate_generation':'distance Routing' if route_pool is None else 'explicit supplied route pool',
        'routing_s':routing_s,'CP_s':cp_s,'CPU_s':time.process_time()-cpu,'wall_s':time.perf_counter()-begin,
        'RSS_highwater_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'RSS_scope':'OS-reported process lifetime highwater, including startup/prior calls; not per-condition incremental peak',
        'fallback':'same common pi0 I_dual archive, never distance key',
        'formal_budget':'HOLD; up to four lexicographic CP stages with separately recorded limits',
        'main_experiment':'HOLD','formal_J':'HOLD'}
    dump(out/'RESULT.json',result);return result
