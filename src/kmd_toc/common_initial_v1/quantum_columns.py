"""Measured local QAOA proposals as route columns, without any C result input."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from kmd_toc.nkr_p2_study.model import pick
from kmd_toc.nkr_unlimited.kernel import run as quantum_kernel
from kmd_toc.duty_break_v1.local import complete
from .plans import dump,sha


class QuantumColumns:
    def __init__(self,*,n,seed,protocol,tiny_validation=False):
        self.n=n;self.seed=seed;self.protocol=deepcopy(protocol);self.seen=set();self.calls=0
        self.tiny_validation=tiny_validation
        if n not in (10,12):
            if not tiny_validation or n!=2:raise ValueError('UNAPPROVED_RESEARCH_N')
            self.protocol['numerical']['bond_by_n']['2']=32
        if tiny_validation and n!=2:raise ValueError('TINY_VALIDATION_N2_ONLY')

    def __call__(self,p,incumbent,own_relaxation,output):
        if self.tiny_validation and (len(p.stops)>8 or self.calls):raise ValueError('TINY_QUANTUM_SINGLE_CALL_ONLY')
        self.calls+=1;output=Path(output);output.mkdir(parents=True,exist_ok=False)
        local=pick(p,incumbent,self.seen,self.n,self.seed+self.calls-1)
        if local is None:
            dump(output/'NO_LOCAL.json',{'status':'NO_ELIGIBLE_TWO_TRIP_BLOCK','no_classical_replacement':True})
            return []
        self.seen.update(local.customer_ids)
        decoded,meta=quantum_kernel(p,incumbent,local,self.protocol,output/'quantum')
        index={s:i for i,s in enumerate(p.od.ids)};proposals=[];checked=0
        for _,bits,decision,count in decoded:
            if checked>=3:break
            try:
                candidate=complete(p,incumbent,local,decision,quantum_provenance={
                    'CALL_sha256':sha(output/'quantum/CALL.json'),'RESULT_sha256':sha(output/'quantum/RESULT.json'),
                    'source':'common_initial_v1_quantum_columns','measured':True})
            except ValueError:continue
            checked+=1;path=output/f'candidate_{checked}.json';dump(path,asdict(candidate))
            for t in candidate.trips:
                if (t.vehicle_id,t.trip_no) not in local.trip_ids:continue
                proposals.append({'route':[index[v.stop_id] for v in t.visits],
                    'provenance_role':'measured_quantum','measured_bits':bits,'sample_count':count,
                    'candidate_plan_path':str(path),'candidate_plan_sha256':sha(path),
                    'quantum_objective':'boundary distance proxy; not full physical reduced cost'})
        dump(output/'COLUMN_PROVENANCE.json',{'quantum':meta,'columns':proposals,
            'own_relaxation':own_relaxation,'uses_classical_final':False,
            'full_physical_pricing':'HOLD','tiny_validation':self.tiny_validation})
        return proposals
