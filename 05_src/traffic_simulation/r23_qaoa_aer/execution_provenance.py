"""Future formal-evidence admission contract; does not execute scientific runs."""
from __future__ import annotations
import datetime as dt
import math
import re
from collections.abc import Mapping

class FormalRunProvenanceIncomplete(ValueError):
    reason_code = "FORMAL_RUN_PROVENANCE_INCOMPLETE"

REQUIRED = (
    "git_commit", "source_sha256", "runner_sha256", "helper_sha256", "authority_manifest_sha256",
    "environment_path", "dependency_versions", "hostname", "cpu", "thread_settings", "command_line",
    "start_timestamp", "end_timestamp", "optimizer_options", "seeds", "termination_status", "resource_metrics",
    "source_manifest", "dirty_worktree", "final_parameters", "objective_trace_sha256",
)
THREAD_KEYS = ("logical_cpus", "physical_cores", "process_threads", "affinity", "OMP_NUM_THREADS",
               "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "Aer_max_parallel_threads")
VERSIONS = {"python":"3.11.16", "qiskit":"2.5.2", "qiskit_aer":"0.17.2", "qiskit_algorithms":"0.4.0",
            "qiskit_optimization":"0.7.0", "numpy":"2.4.6", "scipy":"1.17.1"}

def validate_formal_run_metadata(metadata: Mapping) -> None:
    """Fail closed on missing evidence. Valid metadata is necessary, never sufficient for acceptance."""
    def require(condition, message):
        if not condition: raise FormalRunProvenanceIncomplete(message)
    require(isinstance(metadata, Mapping), "metadata must be a mapping")
    missing=[k for k in REQUIRED if k not in metadata or metadata[k] is None]
    require(not missing, "missing metadata: " + ", ".join(missing))
    require(bool(re.fullmatch(r"[0-9a-f]{40}",str(metadata["git_commit"]))), "invalid commit")
    for k in ("source_sha256","runner_sha256","helper_sha256","authority_manifest_sha256","objective_trace_sha256"):
        require(bool(re.fullmatch(r"[0-9a-f]{64}",str(metadata[k]))), "invalid " + k)
    require(metadata["environment_path"]=="/home/takuma/.conda/envs/evrp-quantum-temp", "wrong authority environment")
    require(metadata["dependency_versions"]==VERSIONS, "dependency authority mismatch")
    require(isinstance(metadata["source_manifest"], Mapping) and bool(metadata["source_manifest"]), "empty source manifest")
    for path,value in metadata["source_manifest"].items():
        require(bool(path) and bool(re.fullmatch(r"[0-9a-f]{64}",str(value))), "invalid source-manifest entry")
    require(metadata["dirty_worktree"] is False, "formal source must be committed and clean")
    for k in ("hostname","cpu","command_line","termination_status"):
        require(isinstance(metadata[k],str) and bool(metadata[k].strip()), "empty " + k)
    threads=metadata["thread_settings"]
    require(isinstance(threads, Mapping) and all(k in threads and threads[k] is not None for k in THREAD_KEYS), "thread settings incomplete")
    require(isinstance(threads["affinity"],list) and bool(threads["affinity"]), "empty affinity")
    require(isinstance(metadata["optimizer_options"],Mapping) and bool(metadata["optimizer_options"]), "effective optimizer options required")
    require(isinstance(metadata["seeds"],Mapping) and all(k in metadata["seeds"] for k in ("simulator","transpiler","initialization","optimizer")), "seeds incomplete")
    try:
        start=dt.datetime.fromisoformat(metadata["start_timestamp"].replace("Z","+00:00"))
        end=dt.datetime.fromisoformat(metadata["end_timestamp"].replace("Z","+00:00"))
        require(start.tzinfo is not None and end.tzinfo is not None and end>=start, "timestamps must be ordered with timezone")
    except (AttributeError,TypeError,ValueError) as exc:
        raise FormalRunProvenanceIncomplete("invalid timestamps") from exc
    resources=metadata["resource_metrics"]
    require(isinstance(resources, Mapping) and all(k in resources for k in ("metric","units","process_id","absolute_peak_rss","timer_boundaries")), "resource metrics incomplete")
    require(resources["metric"]=="absolute_process_peak_RSS" and resources["units"]=="bytes", "resource metric mismatch")
    require(isinstance(resources["absolute_peak_rss"],(int,float)) and math.isfinite(resources["absolute_peak_rss"]) and resources["absolute_peak_rss"]>0, "invalid RSS")
    require(isinstance(metadata["final_parameters"],list) and len(metadata["final_parameters"])==2 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in metadata["final_parameters"]), "final parameters missing")
