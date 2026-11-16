"""Post-measurement audits: actual common-capacity model snapshots and evidence."""
from adapters import *
import json,hashlib,subprocess
from pathlib import Path
from kmd_toc.common.models import load_problem
from kmd_toc.common.adapters import to_vehicle_day
from kmd_toc.column_generation.reduction import contract

def error(a,b):return max((abs(a.get(k,0)-b.get(k,0)) for k in set(a)|set(b)),default=0.)
results=[]
for n in [6,8]:
 directory=ROOT/'evidence/trials'/f'main_N{n}_1101_legacy_quri'
 branch=directory/'branches/0'
 raw=json.loads((branch/'worker_result.json').read_text());m=raw['plan']['method_settings']
 p=load_problem(ROOT/'evidence/inputs'/f'ART_N{n}');day=to_vehicle_day(p,delta_s=1)
 dual=m['base']['LP']['dual_customer']
 for qfile in sorted((branch/'stages').glob('D_AOA_0_*.json')):
  q=json.loads(qfile.read_text());cfg=AOAConfig(**q['result']['config'])
  domain=contract(day.base,dual,q['fragment_groups'],'actual_snapshot',slots=cfg.slots)
  native=OriginalAOA(domain.pricing,domain.dual,cfg);qm=QamomilePolynomial(native)
  a,z,zz=native.ising;b,qz,qzz=qm.ising()
  maxerror=max(abs(native.polynomial.value(mask)-qm.value(mask)) for mask in range(1<<native.q))
  assert error(native.polynomial.terms,qm.terms)<1e-10 and maxerror<1e-9
  results.append({'n':n,'capacity':native.instance.capacity,'qubits':native.q,'all_states':1<<native.q,'QUBO_coeff_max':error(native.polynomial.terms,qm.terms),'Ising_max':max(abs(a-b),error(z,qz),error(zz,qzz)),'energy_max':maxerror})
E=ROOT/'evidence'
(E/'actual_capacity_model_audit.json').write_text(json.dumps(results,indent=2))
# All files below old directories and production roots are read-only to this task.
before=json.loads((E/'preservation_before.json').read_text())
changes=[p for p,h in before.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
(E/'preservation_check.json').write_text(json.dumps({'checked':len(before),'changed_or_missing':changes,'README_unchanged':'README.md' not in changes,'scope':'all original survey artifacts and selected source/config/test/dependency files'},indent=2))
(E/'git_status_after.txt').write_bytes(subprocess.check_output(['git','status','--short','--untracked-files=normal'],cwd=REPO))
size={}
for p in (ROOT/'code').glob('*.py'):
 lines=p.read_text().splitlines();size[p.name]={'total_lines':len(lines),'nonblank_noncomment_lines':sum(bool(x.strip()) and not x.lstrip().startswith('#') for x in lines)}
(E/'implementation_size.json').write_text(json.dumps({'production_files_modified':0,'independent_files':size,'note':'line counts are not migration effort estimates'},indent=2))
print('Common-capacity model snapshots checked',len(results),'Preservation changes',changes)
