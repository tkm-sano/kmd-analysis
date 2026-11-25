"""Host-local cooperative lease. A guardian holds the same flock until its process tree drains."""
from contextlib import contextmanager
import ctypes
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid

from kmd_toc.iterative_v3.io import dump, read, sha

TOKEN = "KMD_D3_LEASE_ID"
FD = "KMD_D3_LEASE_FD"
BOOT = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
HOST = socket.gethostname()
MIB = 2**20


class Unavailable(RuntimeError):
    pass


def durable(path, value):
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def registry_path():
    root = Path(f"/tmp/kmd-d3-hayate-lease-{os.getuid()}")
    root.mkdir(mode=0o700, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise Unavailable("UNSAFE_COOPERATIVE_REGISTRY")
    return root


def proc(pid):
    path = Path(f"/proc/{pid}")
    try:
        parts = (path / "stat").read_text().rpartition(")")[2].split()
        if parts[0] == "Z":
            return None
        args = (path/"cmdline").read_bytes().decode(errors="replace").rstrip("\0").split("\0")
        return dict(pid=pid, boot_id=BOOT, host=HOST, ticks=int(parts[19]),
                    cwd=os.readlink(path/"cwd"), argv=args, state=parts[0],
                    session=int(parts[3]), affinity=sorted(os.sched_getaffinity(pid)))
    except (FileNotFoundError, ProcessLookupError):
        return None


def same_process(saved):
    if (saved["host"],saved["boot_id"]) != (HOST,BOOT):
        return False
    actual = proc(saved["pid"])
    return actual is not None and all(actual[k]==saved[k] for k in ("ticks","cwd","argv"))


def legacy_live():
    names = {"run_iterative_d3.py","run_iterative_d3_v2.py","run_iterative_v3.py",
             "run_iterative_v3_study.py","run_nkr_unlimited.py","run_nkr_unlimited_20261121.py"}
    found = []
    for p in Path("/proc").iterdir():
        if not p.name.isdecimal():
            continue
        try:
            if p.stat().st_uid != os.getuid():
                continue
            argv = (p/"cmdline").read_bytes().rstrip(b"\0").split(b"\0")
            if len(argv) < 2 or not Path(os.fsdecode(argv[0])).name.startswith("python"):
                continue
            if any(Path(os.fsdecode(x)).name in names for x in argv[1:4]) and (
                    set(argv) & {b"run",b"resume",b"_branch",b"_classical"}):
                found.append(int(p.name))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return found


def cgroup_path():
    path = Path("/proc/self/cgroup").read_text().split("::",1)[1].strip()
    return Path("/sys/fs/cgroup") / path.lstrip("/")


def budget(policy):
    allowed = os.sched_getaffinity(0)
    wanted = [*policy["worker_cpus"], policy["controller_cpu"]]
    if socket.gethostname() != policy["host"] or not set(wanted)<=allowed:
        raise Unavailable("HOST_OR_CPU_AFFINITY_INSUFFICIENT")
    topology = Path("/sys/devices/system/cpu")
    cores = set()
    for cpu in wanted:
        p = topology / f"cpu{cpu}/topology"
        cores.add(tuple((p/f).read_text().strip() for f in ("physical_package_id","core_id")))
    if len(cores) != len(wanted):
        raise Unavailable("SMT_SIBLINGS_ARE_NOT_PHYSICAL_CORES")
    memory = next(int(s.split()[1])*1024 for s in Path("/proc/meminfo").read_text().splitlines()
                  if s.startswith("MemAvailable:"))
    group = cgroup_path()
    limits = []
    for path in (group,*group.parents):
        if not path.is_relative_to("/sys/fs/cgroup"):
            break
        for name in ("memory.max", "memory.high"):
            f = path/name
            if f.is_file() and (limit:=f.read_text().strip())!="max":
                memory=min(memory,int(limit)-int((path/"memory.current").read_text()))
        f = path/"cpu.max"
        if f.is_file():
            quota,period=f.read_text().split()
            limits.append([str(f),quota,int(period)])
            if quota!="max" and int(quota)<len(wanted)*int(period):
                raise Unavailable("CPU_QUOTA_INSUFFICIENT")
    if memory < policy["reserve_MiB"]*MIB:
        raise Unavailable("VISIBLE_MEMORY_HEADROOM_INSUFFICIENT")
    return dict(allowed_cpus=sorted(allowed), physical_cores=len(cores), available_memory_bytes=memory,
                requested_cpus=wanted, requested_memory_MiB=policy["reserve_MiB"], quota=limits,
                scope="cooperative lease for this uid's managed D3 runners")


def directory(root, token):
    if len(token)!=32 or any(x not in "0123456789abcdef" for x in token):
        raise Unavailable("MALFORMED_RUN_ID")
    return root/"runs"/token


def residuals(root, marker):
    """Check old receipts and token-bearing processes after the shared lock is acquired."""
    token = marker["run_id"]
    if marker["host"] != HOST:
        raise Unavailable("REGISTRY_HOST_MISMATCH")
    if marker["boot_id"] != BOOT:
        return []
    run = directory(root, token)
    members = []
    for name in ("guard.json", "worker.json"):
        for record in run.glob(f"*/{name}"):
            if same_process(saved:=read(record)):
                members.append(saved["pid"])
    for p in Path("/proc").iterdir():
        if not p.name.isdecimal():
            continue
        try:
            if p.stat().st_uid != os.getuid():
                continue
            environment = (p/"environ").read_bytes().split(b"\0")
            if f"{TOKEN}={token}".encode() in environment and proc(int(p.name)):
                members.append(int(p.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            # Known tree membership is also protected by the inherited flock.
            continue
    return sorted(set(members))


@contextmanager
def acquire(out, manifest_sha, policy, version, action):
    root=registry_path()
    fd=os.open(root/"LEASE.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    marker=root/"ACTIVE.json"
    try:
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise Unavailable("COOPERATIVE_LEASE_BUSY") from error
        if marker.exists():
            previous=read(marker)
            if residuals(root,previous):
                raise Unavailable("RESIDUAL_PROCESS_PRESENT")
            end=directory(root,previous["run_id"])/"RELEASE.json"
            if not end.exists():
                durable(end,dict(reason="recovered_after_tree_exit",utc=time.time()))
            marker.unlink()
        if live:=legacy_live():
            raise Unavailable(f"UNMANAGED_LEGACY_RUN_PRESENT:{live}")
        capacity=budget(policy)
        token=uuid.uuid4().hex
        run=directory(root,token)
        run.mkdir(parents=True)
        info=dict(run_id=token,host=HOST,boot_id=BOOT,version=version,output=str(out),action=action,
                  manifest_sha256=manifest_sha,policy=policy,controller=proc(os.getpid()),capacity=capacity,
                  state="ACQUIRED",utc=time.time())
        durable(run/"ACQUIRE.json",info)
        durable(marker,info)
        affinity=os.sched_getaffinity(0)
        try:
            os.sched_setaffinity(0,{policy["controller_cpu"]})
            yield Lease(root,run,info,fd)
        finally:
            try:
                os.sched_setaffinity(0,affinity)
            finally:
                # A guard may still hold this OFD. Do not issue LOCK_UN.
                live = residuals(root,info)
                durable(run/"CONTROLLER_EXIT.json",dict(utc=time.time(),residual_processes=live))
                if not live:
                    durable(run/"RELEASE.json",dict(reason="tree_drained",utc=time.time()))
                    marker.unlink()
    finally:
        os.close(fd)


class Lease:
    def __init__(self, root, run, info, fd):
        self.root=root
        self.run=run
        self.info=info
        self.fd=fd

    def spawn(self, command, job, worker_cpu, log, entry):
        job=job.resolve()
        if not job.is_relative_to(Path(self.info["output"])) or worker_cpu not in self.info["policy"]["worker_cpus"]:
            raise Unavailable("JOB_OUTSIDE_RESERVATION")
        intent=self.run/uuid.uuid4().hex
        intent.mkdir()
        durable(intent/"INTENT.json", dict(job=str(job),job_sha256=sha(job),command=command,cpu=worker_cpu,
                                       scope=self.info["output"],run_id=self.info["run_id"],utc=time.time()))
        env=dict(os.environ,**{TOKEN:self.info["run_id"],FD:str(self.fd)})
        try:
            return subprocess.Popen([sys.executable,"-B",str(entry),"_guard","--intent",str(intent)],
                 cwd=entry.parent.parent,env=env,pass_fds=(self.fd,),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        except OSError as e:
            durable(intent/"SPAWN_FAILED.json",dict(reason=repr(e),utc=time.time()))
            raise


def authorized(intent, *, worker=False):
    token, fd = os.environ.get(TOKEN,""), int(os.environ.get(FD,"-1"))
    root=registry_path()
    live = root/"LEASE.lock"
    f=os.fstat(fd)
    s=live.stat()
    if (f.st_dev,f.st_ino)!=(s.st_dev,s.st_ino):
        raise Unavailable("LEASE_FD_REQUIRED")
    run=directory(root,token)
    if intent.resolve().parent != run:
        raise Unavailable("RUN_INTENT_REQUIRED")
    # Lock this inherited description non-blocking. A substituted descriptor
    # cannot acquire while the registered controller/guard holds it.
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lease=read(root/"ACTIVE.json")
    binding=read(intent/"INTENT.json")
    if (lease["run_id"],binding["run_id"],lease["output"],lease["boot_id"])!=(token,token,binding["scope"],BOOT):
        raise Unavailable("LEASE_IDENTITY_MISMATCH")
    job=Path(binding["job"])
    if not job.is_relative_to(Path(lease["output"])) or sha(job)!=binding["job_sha256"]:
        raise Unavailable("LEASE_JOB_MISMATCH")
    if worker:
        guard=read(intent/"guard.json")
        actual=proc(os.getpid())
        if os.getppid()!=guard["pid"] or not same_process(guard) or actual["argv"][1:]!=binding["command"][1:]:
            raise Unavailable("WORKER_COMMAND_OR_PARENT_MISMATCH")
        os.sched_setaffinity(0,{binding["cpu"]})
        durable(intent/"worker.json",proc(os.getpid()) | {"job_sha256":binding["job_sha256"], "run_id":token})
    return lease,binding,fd


def descendants(pid):
    result=[]
    pending=[pid]
    while pending:
        p=pending.pop()
        try:
            tasks=Path(f"/proc/{p}/task")
            for task in tasks.iterdir():
                pending.extend(int(x) for x in (task/"children").read_text().split() if int(x) not in result)
        except (FileNotFoundError,ProcessLookupError):
            pass
        if p not in result:
            result.append(p)
    return result


def supervisor_sample(pid):
    items=[]
    for child in descendants(pid):
        p=Path(f"/proc/{child}")
        try:
            parts=(p/"stat").read_text().rpartition(")")[2].split()
            if parts[0]=="Z":
                continue
            rss=int(parts[21])*os.sysconf("SC_PAGE_SIZE")
            items.append(dict(pid=child,RSS_bytes=max(0,rss),start_ticks=int(parts[19]),state=parts[0],
                              affinity=sorted(os.sched_getaffinity(child)),threads=int(parts[17])))
        except (FileNotFoundError,ProcessLookupError):
            continue
    return items


def guard(intent):
    lease,binding,fd=authorized(intent)
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0)!=0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(),"prctl(PR_SET_CHILD_SUBREAPER)")
    durable(intent/"guard.json", proc(os.getpid()) | {"run_id":lease["run_id"],"job_sha256":binding["job_sha256"]})
    worker=None
    stopped=False

    def stop(sig, _frame):
        nonlocal stopped
        stopped=True
        # Recheck the processes in our tree; foreign jobs are never targeted.
        for p in descendants(os.getpid())[1:]:
            try:
                os.kill(p,sig)
            except ProcessLookupError:
                pass

    signal.signal(signal.SIGTERM,stop)
    try:
        if stopped:
            return 130
        env=dict(os.environ,KMD_D3_LEASE_INTENT=str(intent))
        worker=subprocess.Popen(binding["command"],env=env,pass_fds=(fd,))
        if stopped:
            stop(signal.SIGTERM,None)
        code=worker.wait()
        while True:
            try:
                os.waitpid(-1,0)
            except ChildProcessError:
                break
        durable(intent/"EXIT.json",dict(code=code,tree_drained=True,utc=time.time()))
        return code if code>=0 else 128-code
    except OSError as e:
        durable(intent/"GUARD_ERROR.json",dict(reason=repr(e),utc=time.time()))
        raise


def supervise(lease, entry, jobs, directory, config):
    """Preserve v2 limits and finite-work behavior, with inherited tree ownership."""
    executions=directory/"executions"
    executions.mkdir(exist_ok=True)
    attempt=executions/f"{len(list(executions.iterdir()))+1:03d}"
    attempt.mkdir()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    start=time.perf_counter()
    cpu=time.process_time()
    children, logs=[],[]
    peak=0
    reason=None
    limits=config["limits"]
    try:
        for i, item in enumerate(jobs):
            job=read(item["path"])
            file=(attempt/f"process_{i}.log").open("x")
            logs.append(file)
            exe=config["classical_python"] if item["action"]=="_classical" else config["branch_python"]
            command=[exe,"-B",str(entry),item["action"],"--job",str(item["path"])]
            children.append(lease.spawn(command,item["path"],job["cpu"],file,entry))
        with (attempt/"RESOURCES.jsonl").open("x") as trace:
            while any(c.poll() is None for c in children):
                trees=[supervisor_sample(c.pid) for c in children if c.poll() is None]
                rss=sum(m["RSS_bytes"] for tree in trees for m in tree)
                rss += supervisor_sample(os.getpid())[0]["RSS_bytes"]
                peak=max(peak,rss)
                trace.write(json.dumps(dict(elapsed_s=time.perf_counter()-start, tree_RSS_bytes=rss,worker_trees=trees))+"\n")
                trace.flush()
                if any(sum(m["RSS_bytes"] for m in tree)>limits["per_worker_rss_mib"]*MIB for tree in trees):
                    reason="MEASURED_WORKER_RSS_LIMIT"
                if rss>limits["tree_rss_mib"]*MIB:
                    reason="MEASURED_TREE_RSS_LIMIT"
                if shutil.disk_usage(directory).free<limits["minimum_free_disk_gib"]*2**30:
                    reason="MEASURED_DISK_LIMIT"
                if reason:
                    for c in children:
                        if c.poll() is None:
                            c.terminate()
                    break
                time.sleep(.25)
        return [c.wait() for c in children],reason
    except BaseException:
        for c in children:
            if c.poll() is None:
                c.terminate()
        for c in children:
            c.wait()
        raise
    finally:
        for f in logs:
            f.close()
        end=resource.getrusage(resource.RUSAGE_CHILDREN)
        dump(attempt/"RESOURCES.json",dict(run_id=lease.info["run_id"],wall_s=time.perf_counter()-start,
            parent_CPU_s=time.process_time()-cpu,all_child_CPU_s=(end.ru_utime+end.ru_stime)-(before.ru_utime+before.ru_stime),
            sampled_tree_RSS_MiB=peak/MIB,reason=reason,scope="sampled controller + managed guardian/worker trees"))
