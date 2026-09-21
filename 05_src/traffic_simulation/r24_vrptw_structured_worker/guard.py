"""Fail closed at real optimizer, backend, sampler and persistent-ledger boundaries."""
from contextlib import ExitStack
from unittest.mock import patch
class ExecutionForbidden(RuntimeError):pass
class ZeroShotGuard:
    def __init__(self):self.attempts=[];self.stack=ExitStack()
    def forbidden(self,name):
        def stop(*a,**k):
            self.attempts.append(name);raise ExecutionForbidden('PREFLIGHT_FORBIDS_'+name)
        return stop
    def __enter__(self):
        from qiskit_aer import AerSimulator,Aer
        import scipy.optimize
        from qiskit.primitives import StatevectorSampler
        from qiskit_aer.primitives import Sampler,SamplerV2
        from traffic_simulation.r24_vrptw_qaoa_worker import execution
        from traffic_simulation.r24_qaoa_initial_state_cross_condition_worker.ledger import Ledger
        targets=[(AerSimulator,'run'),(scipy.optimize,'minimize'),(StatevectorSampler,'run'),(Sampler,'run'),(SamplerV2,'run'),(execution,'supervised_run'),(execution,'perform'),(Ledger,'commit')]
        for backend in Aer.backends():targets.append((type(backend),'run'))
        seen=set()
        for obj,name in targets:
            if (id(obj),name) in seen:continue
            seen.add((id(obj),name));self.stack.enter_context(patch.object(obj,name,self.forbidden(str(obj)+'.'+name)))
        return self
    def __exit__(self,*args):return self.stack.__exit__(*args)
