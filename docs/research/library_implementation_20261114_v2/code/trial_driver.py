"""Fresh-process actual four-branch DWT trial using independent adapter hooks."""
import os,sys,json,time,resource
from pathlib import Path
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',RAYON_NUM_THREADS='1',POLARS_MAX_THREADS='1')
from adapters import *

def install_hooks(backend,algorithm):
    from kmd_toc.dwt import methods
    import kmd_toc.column_generation.aoa as aoa
    if backend!='original':aoa.PricingAOA=backend_class(backend)
    if algorithm=='updated':
        from cg_trial import generate_updated
        methods.generate=generate_updated

# Spawn children import this module before their target. Install code-only hooks
# from inherited labels, never load an instance or execute a circuit here.
if 'KMD_LIBRARY_TRIAL_BACKEND' in os.environ:
    install_hooks(os.environ['KMD_LIBRARY_TRIAL_BACKEND'],os.environ['KMD_LIBRARY_TRIAL_ALGORITHM'])

def main():
    spec_path=Path(sys.argv[1]);spec=json.loads(spec_path.read_text());out=spec_path.parent
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    from kmd_toc.dwt.setup import preload_dependencies
    from kmd_toc.dwt.parallel import execute_parallel
    begin=time.perf_counter();preload_dependencies()
    os.environ['KMD_LIBRARY_TRIAL_BACKEND']=spec['trial_backend']
    os.environ['KMD_LIBRARY_TRIAL_ALGORITHM']=spec['trial_algorithm']
    install_hooks(spec['trial_backend'],spec['trial_algorithm'])
    threads=len(list(Path('/proc/self/task').iterdir()))
    (out/'trial_preparation.json').write_text(json.dumps({'seconds':time.perf_counter()-begin,'threads':threads,'no_input_solver_or_circuit_before_T':True,'mode':'uniform fresh spawn, safe with imported runtime threads'}))
    row=execute_parallel(spec,out,allow_import_only_fork=False)
    # execute_parallel exports raw result.json/worker_result.json after T.
    (out/'trial_result.json').write_text(json.dumps(row,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v)))
    print(json.dumps({k:row.get(k) for k in ['trial_id','status','D_km','W_min','T_program_s','total_quantum_calls','total_final_shots']}))

if __name__=='__main__':main()
