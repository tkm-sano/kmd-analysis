"""Executable, import and native-thread evidence for the revised D3 runners."""
import ctypes
from functools import lru_cache
from pathlib import Path
import importlib
import importlib.metadata
import os
import platform
import sys

from kmd_toc.iterative_v3.io import ROOT, sha
from .rng_v2 import VERSION

THREAD_VARIABLES = ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS',
                    'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS')
LIBRARIES = ('numpy','scipy','qiskit','qiskit-aer','ortools','matplotlib')
LIBRARY_NAMES = ('blas','lapack','mkl','libomp','libgomp','libiomp','libgfortran',
                 'libstdc++','libquadmath','libc.so','libm.so','libpthread')
PROBES = (
    ('scipy_openblas_get_num_threads64_', 'OpenBLAS'),
    ('scipy_openblas_get_num_threads', 'OpenBLAS'),
    ('openblas_get_num_threads64_', 'OpenBLAS'),
    ('openblas_get_num_threads', 'OpenBLAS'),
    ('omp_get_max_threads', 'OpenMP'),
    ('MKL_Get_Max_Threads', 'MKL'),
    ('bli_thread_get_num_threads', 'BLIS'),
)


@lru_cache(maxsize=None)
def file_record(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path)}


def version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def mapped_libraries():
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[-1].startswith('/'):
            path = Path(fields[-1])
            if '.so' in path.name and any(k in path.name.lower() for k in LIBRARY_NAMES) and path.is_file():
                yield str(path.resolve())


def thread_limits(mapped):
    result = []
    for path in mapped:
        if not any(n in Path(path).name.lower() for n in ('blas','mkl','omp','blis')):
            continue
        library = ctypes.CDLL(path)
        for symbol, kind in PROBES:
            function = getattr(library, symbol, None)
            if function is not None:
                function.argtypes = []
                function.restype = ctypes.c_int
                result.append({'path':path,'kind':kind,'symbol':symbol,'threads':function()})
                break
    return result


def observe_process(pid):
    """Capture actual accumulated CPU ticks per thread, including idle threads."""
    values = {}
    try:
        for path in Path(f'/proc/{pid}/task').glob('*/stat'):
            try:
                stat = path.read_text().rsplit(')',1)[-1].split()
                values[path.parent.name] = int(stat[11]) + int(stat[12])
            except (FileNotFoundError, ProcessLookupError):
                continue
    except FileNotFoundError:
        pass
    return {'os_thread_count':len(values),'native_thread_cpu_ticks':values}


def fingerprint(role):
    modules = ['numpy','scipy.linalg','scipy.optimize']
    modules += (['ortools.constraint_solver._pywrapcp','ortools.sat.python.cp_model_helper']
                if role=='classical' else ['qiskit','qiskit._accelerate'])
    loaded = {}
    for name in modules:
        module = importlib.import_module(name)
        if getattr(module,'__file__',None):
            loaded[name]=file_record(module.__file__)
    extensions = {}
    for name, module in tuple(sys.modules.items()):
        path = getattr(module,'__file__',None)
        if name.split('.')[0] in ('numpy','scipy','qiskit','qiskit_aer','ortools') and isinstance(path,str) and '.so' in Path(path).name:
            extensions[name]=file_record(path)
    mapped = sorted(set(mapped_libraries()))
    cpu = next((s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines()
                if s.startswith('model name')), platform.machine())
    sources = ('iterative_d3.revision','iterative_d3.rng_v2','iterative_v3.search',
               'iterative_v3.quantum','iterative_d3.overlay')
    return dict(role=role, python=file_record(sys.executable) | {'version': sys.version},
        packages={k:version(k) for k in LIBRARIES}, imports=loaded, extensions=extensions,
        native=[file_record(p) for p in mapped], native_limits=thread_limits(mapped),
        thread_environment={k:os.environ.get(k) for k in THREAD_VARIABLES},
        source_root=str(ROOT), source={n:file_record(importlib.import_module('kmd_toc.'+n).__file__) for n in sources},
        system=dict(system=platform.system(),release=platform.release(),machine=platform.machine(),
                    libc=list(platform.libc_ver()),cpu=cpu),
        rng=dict(design=VERSION,python='MT19937',sampler='NumPy PCG64',seed_derivation='SHA-256'))
