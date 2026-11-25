"""D3 operations v3 with the immutable v2 science and seed contract."""
from collections import Counter
from contextlib import contextmanager
from functools import partial
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from kmd_toc.iterative_d3 import revision as rev
from kmd_toc.iterative_v3.io import ROOT, dump, read, sha
from kmd_toc.objective_alignment_v1.objective import measure
from kmd_toc.iterative_v3.physical import metrics
from kmd_toc.iterative_v3_study.analysis import delta

from . import reporting, resources

VERSION = "iterative-d3-ops-v3"
ENTRY = ROOT/"scripts/run_iterative_d3_ops_v3.py"
BASE = rev.CANONICAL/"output/iterative_d3/formal_J30_v3"
POLICY = dict(host="hayate",worker_cpus=[0,1,2,3],controller_cpu=4,reserve_MiB=40960,
              scope="single same-uid managed D3 lease; OS remains shared")
OLD_APPROVED = rev.approved
OLD_PREFLIGHT = rev.preflight
REQUIRED_AUDIT = {"T04","T05","R06","R09"}


def approved(out, manifest):
    if manifest.get("operations_version")!=VERSION:
        return False
    path=out/"FREEZE_RECORD.json"
    if not path.is_file():
        return False
    freeze=read(path)
    if freeze["state"]!="EXPERIMENT_READY" or freeze["manifest_sha256"]!=sha(out/"MANIFEST.json"):
        raise ValueError("OPERATIONS_FREEZE_BINDING")
    evidence=Path(freeze["evidence"])
    if freeze["evidence_sha256"]!=sha(evidence):
        raise ValueError("OPERATIONS_EVIDENCE_CHANGED")
    validate_evidence(out,manifest,read(evidence))
    return True


def validate_evidence(out, manifest, evidence):
    if (evidence.get("manifest_sha256")!=sha(out/"MANIFEST.json") or evidence.get("start_blockers")!=[]
        or evidence.get("operations_version")!=VERSION or
        any(evidence.get("criteria",{}).get(x)!="PASS" for x in REQUIRED_AUDIT)):
        raise ValueError("OPERATIONS_REAUDIT_REQUIRED")
    rev.verify_pins(evidence["evidence_hashes"])
    if manifest["seed_sha256"]!=sha(BASE/"SEEDS.csv"):
        raise ValueError("OPERATIONS_MUST_REUSE_SEEDS")


@contextmanager
def entry_binding():
    entry, check = rev.ENTRY, rev.approved
    rev.ENTRY, rev.approved = ENTRY, approved
    try:
        yield
    finally:
        rev.ENTRY, rev.approved = entry, check


def config_check(m, out):
    if (m["operations_version"],m["root"],m["output"],m["resource_policy"]) != (VERSION,str(ROOT),str(out),POLICY):
        raise ValueError("OPERATIONS_REGISTRATION_BINDING")
    parent=read(BASE/"MANIFEST.json")
    if m["operations_parent_manifest"]!=sha(BASE/"MANIFEST.json"):
        raise ValueError("PARENT_MANIFEST_CHANGED")
    for key in ("version","rng_version","configuration","classical_configuration","seed_sha256","fixed_initials","formal_J","counts","excluded"):
        if m[key]!=parent[key]:
            raise ValueError(f"SCIENTIFIC_CONTRACT_CHANGED:{key}")
    if any(m["code_hashes"].get(k)!=v for k,v in parent["code_hashes"].items()):
        raise ValueError("INHERITED_CODE_CHANGED")
    if any(m["asset_hashes"].get(k)!=v for k,v in parent["asset_hashes"].items()):
        raise ValueError("INHERITED_ASSET_INVALIDATED")
    if len(m["cases"])!=len(parent["cases"]):
        raise ValueError("CASE_COUNT_CHANGED")
    for case, old in zip(m["cases"],parent["cases"]):
        if {k:v for k,v in case.items() if k!="initial_directory"} != {k:v for k,v in old.items() if k!="initial_directory"}:
            raise ValueError("CASE_OR_SEED_CHANGED")


def register(out):
    if ROOT == rev.CANONICAL:
        raise ValueError("USE_SEPARATE_EXECUTION_MIRROR")
    m=read(BASE/"MANIFEST.json")
    if not OLD_APPROVED(BASE,m):
        raise ValueError("PARENT_NOT_FROZEN")
    rev.verify_pins(m["code_hashes"])
    rev.verify_pins(m["asset_hashes"])
    new_files=[ENTRY,*sorted((ROOT/"src/kmd_toc/iterative_d3_ops").glob("*.py"))]
    m["code_hashes"].update({str(p.relative_to(ROOT)):sha(p) for p in new_files})
    rev.verify_pins({str(rev.CANONICAL / p):h for p,h in m["code_hashes"].items()})
    with entry_binding():
        env=rev.environment(m["configuration"])
    resources.budget(POLICY)
    out.mkdir(parents=True,exist_ok=False)
    for case in m["cases"]:
        fixed=m["fixed_initials"][case["scale"]]["directory"]
        location=out/"initial_aliases"/case["trial_id"]
        alias=rev.plan.alias_initial(fixed, location, case["trial_id"])
        if alias.manifest["plan_sha256"]!=case["initial_plan_sha256"]:
            raise ValueError("INITIAL_ALIAS_HASH")
        case["initial_directory"]=str(location)
        m["asset_hashes"][str(location/"INITIAL.json")]=sha(location/"INITIAL.json")
    shutil.copyfile(BASE/"EFFECTIVE_CONFIGURATION.json",out/"EFFECTIVE_CONFIGURATION.json")
    shutil.copyfile(BASE/"SEEDS.csv",out/"SEEDS.csv")
    dump(out/"ENVIRONMENT.json",env)
    m.update(root=str(ROOT),output=str(out),environment_sha256=sha(out/"ENVIRONMENT.json"),
             operations_version=VERSION,operations_parent_manifest=sha(BASE/"MANIFEST.json"),resource_policy=POLICY)
    config_check(m,out)
    dump(out/"MANIFEST.json",m)
    dump(out/"REGISTRATION.json",dict(manifest_sha256=sha(out/"MANIFEST.json"),workers_submitted=0,operations_version=VERSION))
    for name in ("MANIFEST.json","REGISTRATION.json","SEEDS.csv","ENVIRONMENT.json","EFFECTIVE_CONFIGURATION.json"):
        (out/name).chmod(0o444)
    return dict(state="REGISTERED_HOLD",counts=m["counts"],workers_submitted=0)


def preflight(out, *, probe=True):
    m=read(out/"MANIFEST.json")
    config_check(m,out)
    with entry_binding():
        result=OLD_PREFLIGHT(out,probe=probe)
    if probe:
        result["visible_resources"]=resources.budget(POLICY)
    result["operations_version"]=VERSION
    return result


def freeze(out,evidence):
    m=read(out/"MANIFEST.json")
    preflight(out)
    validate_evidence(out,m,read(evidence))
    dump(out/"FREEZE_RECORD.json",dict(manifest_sha256=sha(out/"MANIFEST.json"),
        evidence=str(evidence),evidence_sha256=sha(evidence),operations_version=VERSION,state="EXPERIMENT_READY"))
    (out/"FREEZE_RECORD.json").chmod(0o444)
    return dict(state="EXPERIMENT_READY",workers_submitted=0)


def collect(out, m):
    execution=rev.live_state(out)
    observed=[]
    scales={}
    for case in m["cases"]:
        scale=case["scale"]
        if scale not in scales:
            problem=rev.load_problem(case["input"],m["configuration"]["rest_options"])
            base=rev.read_initial(case["initial_directory"]).checked_plan(problem)
            measurement=metrics(problem,base,measure(problem,base))
            demands={r["stop_id"]:r["demand"] for r in read(Path(case["input"])/"input.json")["stops"]}
            if any(type(n) is not int or n<=0 for n in demands.values()):
                raise ValueError(f"INVALID_REGISTERED_DEMAND:{scale}")
            number=reporting.parcel_evidence(Path(case["initial_directory"])/"plan.json",demands)
            scales[scale]=(problem,base,measurement,demands,number)
        problem,base,measurement,demands,number=scales[scale]
        methods={name:rev.method_record(m,case,problem,base,out/case["output_subdir"],name,execution) for name in rev.METHODS}
        cc=methods["C_Idual"]["metrics"]
        parcel_counts={"B":number}
        parcel_errors={}
        for method, value in methods.items():
            if cc is not None and value["metrics"] is not None:
                value["I_dual_C_posthoc_percent"]=delta(value["metrics"],cc)["I_dual_percent"]
            if value["eligible"]:
                try:
                    parcel_counts[method]=reporting.parcel_evidence(value["saved_plan"],demands)
                except (ValueError, KeyError, OSError) as error:
                    parcel_errors[method]=str(error)
        observed.append({k:case[k] for k in ("trial_id","scale","seed","initial_plan_sha256","problem_hash","od_hash")} |
                    dict(baseline_metrics=measurement,methods=methods,parcel_counts=parcel_counts,parcel_evidence_errors=parcel_errors))
    return execution,observed


def aggregate(out):
    preflight(out,probe=False)
    m=read(out/"MANIFEST.json")
    execution,observed=collect(out,m)
    native,comparisons=reporting.selection(m,observed)
    parent=out/"analysis"
    parent.mkdir(exist_ok=True)
    with rev.locked(parent/"REPORT.lock"):
        n=max((int(p.name) for p in parent.iterdir() if p.name.isdecimal()),default=0)+1
        target=parent/f"{n:04d}"
        stage=Path(tempfile.mkdtemp(prefix=".report-",dir=parent))
        try:
            dump(stage/"OBSERVATIONS.json",observed)
            dump(stage/"DESCRIPTIVE.json",native)
            dump(stage/"COMPARISONS.json",dict(manifest_sha256=sha(out/"MANIFEST.json"),comparisons=comparisons))
            reports=reporting.report(stage,observed,comparisons)
            rows=[dict(trial_id=r["trial_id"],scale=r["scale"],method=name,status=v["status"],
                       eligible=v["eligible"],reason_code=v["reason_code"],attempt_count=len(v["attempts"]),
                       worker_attempt_count=len(v["worker_attempts"])) for r in observed for name,v in r["methods"].items()]
            reporting.csvfile(stage,"TRIAL_STATUS.csv",list(rows[0]),rows)
            result=dict(state=execution.get("effective_status",execution["state"]),
                        report_state="INVALID_DENOMINATOR" if any(x["denominator_errors"] for x in reports) else "OK",
                        planned_cases=len(observed),method_rows=len(rows),eligible=sum(x["eligible"] for x in rows),
                        status_counts=dict(Counter(x["status"] for x in rows)),directory=str(target),workers_submitted=0,
                        J_eff={c["scale"]:{g:c[g+"_J_eff"] for g in ("primary","control")} for c in native["cohorts"]})
            dump(stage/"SUMMARY.json",result)
            stage.rename(target)
        except BaseException:
            shutil.rmtree(stage)
            raise
    return result


def fixture_check(out, m):
    if (out.parent.parent!=Path("/tmp") or not out.parent.name.startswith("kmd-d3-ops-probe-")
        or out.parent.stat().st_uid!=os.getuid() or out.parent.stat().st_mode & 0o077
        or m.get("stage")!="diagnostic_lease" or m.get("scenario") not in ("normal","spawn-failure")
        or m.get("duration",0) not in (0.15,2.0,4.0)):
        raise ValueError("DIAGNOSTIC_ONLY_IN_PRIVATE_TEMP_ROOT")


def execute_fixture(out,m,resume,lease):
    state=out/"EXECUTION_STATE.json"
    with rev.locked(out/"EXECUTION.lock"):
        if state.exists()!=resume or (state.exists() and read(state)["state"]=="COMPLETE"):
            raise ValueError("PROBE_RUN_STATE")
        jobpath=out/"JOB.json"
        if not jobpath.exists():
            dump(jobpath,dict(cpu=0, scope="diagnostic_lease", duration=m["duration"]))
        resources.durable(state,dict(state="RUNNING"))
        config=dict(branch_python="/nonexistent/diagnostic-python" if m["scenario"]=="spawn-failure" else sys.executable,
            limits=dict(per_worker_rss_mib=8192,tree_rss_mib=32768,minimum_free_disk_gib=1))
        codes,alarm=resources.supervise(lease,ENTRY,[dict(path=jobpath,action="_dummy")],out,config)
        value=dict(state="COMPLETE" if codes==[0] and not alarm else "FAILED",codes=codes,alarm=alarm,
                   run_id=lease.info["run_id"],formal_workers_submitted=0)
        resources.durable(state,value)
        return value


def execute(out, *, resume):
    m=read(out/"MANIFEST.json")
    fixture=m.get("stage")=="diagnostic_lease"
    if fixture:
        fixture_check(out,m)
        readiness=None
    else:
        readiness=preflight(out)
        if readiness["state"]!="EXPERIMENT_READY":
            raise ValueError("OPERATIONS_EXECUTION_HOLD")
    with resources.acquire(out,sha(out/"MANIFEST.json"),POLICY,VERSION,"resume" if resume else "run") as lease:
        if fixture:
            return execute_fixture(out,m,resume,lease)
        if sha(out/"MANIFEST.json")!=lease.info["manifest_sha256"] or not approved(out,m):
            raise ValueError("REGISTRATION_CHANGED_DURING_RESOURCE_ACQUISITION")
        supervisor, check = rev.experiment.supervise,rev.preflight
        with entry_binding():
            rev.experiment.supervise=partial(resources.supervise,lease,ENTRY)
            # The public check ran before narrowing controller affinity to its own core.
            rev.preflight=lambda path: readiness if path.resolve()==out else check(path)
            try:
                return rev.execute(out,resume=resume)
            finally:
                rev.experiment.supervise,rev.preflight=supervisor,check


def worker(job,action):
    intent=Path(os.environ["KMD_D3_LEASE_INTENT"])
    lease,binding,_=resources.authorized(intent,worker=True)
    out=Path(lease["output"])
    if str(job.resolve())!=binding["job"] or sha(out/"MANIFEST.json")!=lease["manifest_sha256"]:
        raise ValueError("WORKER_LEASE_REGISTRATION_MISMATCH")
    m=read(out/"MANIFEST.json")
    if action=="_dummy":
        fixture_check(out,m)
        data=read(job)
        if data["scope"]!="diagnostic_lease":
            raise ValueError("DIAGNOSTIC_JOB_ONLY")
        # A child without the lease FD exercises the guardian's drain behavior.
        subprocess.Popen([sys.executable,"-c",f"import time; time.sleep({data['duration']})"],
                         start_new_session=True)
        return 0
    with entry_binding():
        return rev.worker(job,action)
