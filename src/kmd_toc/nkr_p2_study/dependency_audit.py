"""Classical-only impact check for unrelated workspace preservation drift."""
import sys
from collections import Counter
from pathlib import Path
from .study import ROOT,OUT,DOC,read,dump,load_case,backend_modules
from .model import pick,dw
from kmd_toc.d_local_design.completion import complete,physical,preserves


def main():
    before=read(DOC/'PRESERVATION_BEFORE.json')
    from .verify import sha
    changed={str(ROOT/name):name for name,h in before['files'].items() if sha(ROOT/name)!=h}
    calls=Counter();cases=[]
    def trace(frame,event,arg):
        if event=='call' and frame.f_code.co_filename in changed:
            calls[changed[frame.f_code.co_filename]]+=1
    q,_=backend_modules()
    sys.setprofile(trace)
    try:
        for scale in ['S1','S2','S3']:
            p,initial=load_case(scale);base=dw(p,initial)
            for n in [10,12]:
                local=pick(p,initial,set(),n,9201)
                decision=q.decode_register(q.encode_labels(q.initial_order(local)),local.customer_ids)
                proposal=complete(p,initial,local,decision)
                ok,_=physical(p,proposal)
                assert ok and preserves(proposal,local,decision,initial)
                after=dw(p,proposal)
                cases.append({'scale':scale,'n':n,'physical_and_preserves':ok,'before':base,'incumbent_completed':after,
                    'delta_D':after['D_km']-base['D_km'],'delta_W':after['W_mean_min_per_operation']-base['W_mean_min_per_operation']})
    finally:sys.setprofile(None)
    imported=[]
    for name,module in list(sys.modules.items()):
        file=getattr(module,'__file__',None)
        if file and str(Path(file).resolve()) in changed:imported.append(name)
    result={'status':'NO_CHANGED_FUNCTIONS_CALLED_IN_TESTED_PILOT_PATH' if not calls else 'CHANGED_FUNCTIONS_CALLED_REVIEW_REQUIRED',
        'scope':'classical load/pick/incumbent completion/dual physical validation/cargo-v2 evaluation for six scale/n cases; numerical core separately source-pinned',
        'not_a_blanket_preservation_pass':True,'quantum_executions':0,'changed_files':list(changed.values()),
        'called_changed_files':dict(calls),'imported_changed_modules':imported,'cases':cases}
    dump(OUT/'DEPENDENCY_IMPACT_AUDIT.json',result)
    print(result['status']);print('changed functions',dict(calls));print('incumbent deltas',[(c['scale'],c['n'],c['delta_D'],c['delta_W']) for c in cases])


if __name__=='__main__':main()
