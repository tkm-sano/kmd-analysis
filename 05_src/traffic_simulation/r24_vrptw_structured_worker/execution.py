"""Reuse the validated executor/supervisor bodies with explicit dependency wiring.
No execution happens on import. Preflight entry rejects launch before any side effect.
The source transformation is narrow, checked and emitted into the audit manifest.
"""
import ast,inspect,textwrap,types
from .contract import *
from .ledger import Ledger
from .guard import ExecutionForbidden
from traffic_simulation.r24_vrptw_qaoa_worker import execution as original
ORIGINAL_PERFORM=original.perform
ORIGINAL_SUPERVISOR=original.supervised_run

ACTIVE_PREFLIGHT=BASE/'r24_vrptw_structured_initial_state/20260922_v6_ledger_lock_preflight'

def preflight_gate(ident):
    # v6 adds NFS lock acceptance; prior scientific and direct-build receipts stay immutable.
    root=ACTIVE_PREFLIGHT
    v=read(root/'VALIDATION.json')
    require(v['status']=='PASS' and v['GO_STOP']=='GO' and v['Uniform_construction']==0,'direct-build preflight receipt')
    for path,h in read(root/'ARTIFACT_MANIFEST.json').items():
        require(sha(ROOT/path)==h,path,'PREFLIGHT_ARTIFACT_CHANGED')
    for path,h in read(root/'RUNTIME_DEPENDENCIES.json').items():
        require(sha(ROOT/path)==h,path,'RUNTIME_DEPENDENCY_CHANGED')
    for path,h in read(root/'COMPARISON_REFERENCE_AUTHORITIES.json').items():
        require(sha(ROOT/path)==h,path,'COMPARISON_REFERENCE_CHANGED')
    require(ident==run_identity(ident['run_id']),'live identity')
    # Separate broad preservation inventory is not mislabeled as runtime dependency.

class Wiring(ast.NodeTransformer):
    def __init__(self):self.changed=[]
    def visit_Assign(self,n):
        if len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            name=n.targets[0].id
            if name=='ledger':
                self.changed.append('ledger namespace');return ast.parse("ledger=Ledger(ROOT/read(SPEC/'BUDGET_PLAN.json')['ledger_namespace'])").body[0]
            if name=='sanity':self.changed.append('Standard-only Aer sanity receipt');return ast.Pass()
        return self.generic_visit(n)
    def visit_Expr(self,n):
        if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require' and any(isinstance(x,ast.Name) and x.id=='sanity' for x in ast.walk(n)):
            self.changed.append('Standard-only sanity identity gate');return ast.Pass()
        return self.generic_visit(n)

def wired():
    source=textwrap.dedent(inspect.getsource(ORIGINAL_SUPERVISOR));tree=ast.parse(source);w=Wiring();tree=w.visit(tree)
    # Immediately after authorization validation, before import/ledger/worker effects.
    tree.body[0].body.insert(2,ast.parse("preflight_gate(run_identity(run_id))").body[0]);ast.fix_missing_locations(tree)
    require(w.changed==['ledger namespace','Standard-only Aer sanity receipt','Standard-only sanity identity gate','Standard-only sanity identity gate'],'unexpected supervisor source shape')
    g=dict(original.__dict__);g.update(__package__=__package__,Ledger=Ledger,MANIFEST_SHA256=COMPARISON_HASH,SPEC=SPEC,preflight_gate=preflight_gate,run_identity=run_identity,plan=lambda spec,rid:run_plan(rid)[0],identity=lambda spec,r:run_identity(r['run_id']))
    # The original objective/binding/incumbent/result pipeline shares supervisor PID token.
    g['perform']=types.FunctionType(ORIGINAL_PERFORM.__code__,g,'perform',ORIGINAL_PERFORM.__defaults__,ORIGINAL_PERFORM.__closure__);g['perform'].__kwdefaults__=ORIGINAL_PERFORM.__kwdefaults__
    exec(compile(tree,str(Path(__file__).resolve())+':wired_supervisor','exec'),g)
    return g['supervised_run'],ast.unparse(tree),w.changed

def supervised_run(run_id,authorization=None,*,preflight=True):
    if preflight:raise ExecutionForbidden('PREFLIGHT_FORBIDS_CONTROLLED_LAUNCH')
    require(authorization==dict(execution_spec_sha256=COMPARISON_HASH,scientific_execution_authorized=True),'separate explicit controlled launch authorization')
    launch,_,_=wired();return launch(run_id,authorization)
