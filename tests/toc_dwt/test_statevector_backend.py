"""DWT selection, explicit optional environment and preparation boundaries."""
import copy
import json
from pathlib import Path
import pytest
from kmd_toc.column_generation import backends


CONFIG = Path('configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json')
OPTIONAL = Path('configs/toc_delivery/dwt_balance_v1_4_cpu_parallel_qulacs.json')


def test_optional_profile_changes_execution_only():
    original = json.loads(CONFIG.read_text());optional = json.loads(OPTIONAL.read_text())
    assert backends.configured_backend(original) == 'qiskit'
    assert backends.configured_backend(optional) == 'qulacs'
    assert original['output_root'] != optional['output_root']
    for c in [original, optional]:
        assert c['threads'] == c['cpu_parallel']['workers'] == 4
        assert c['cpu_parallel']['native_threads_per_branch'] == 1
    for key in ['version', 'output_root', 'backend_adoption_note']:
        optional.pop(key, None);original.pop(key, None)
    optional['D'].pop('statevector_backend')
    assert original == optional


def test_qulacs_preparation_never_constructs_a_state_or_loads_input(monkeypatch):
    qulacs = pytest.importorskip('qulacs')
    from kmd_toc.common import models
    from kmd_toc.dwt import worker
    from kmd_toc.dwt.setup import preload_dependencies
    def forbidden(*args, **kwargs):
        raise AssertionError('Problem or quantum execution in preparation')
    monkeypatch.setattr(qulacs, 'QuantumState', forbidden)
    monkeypatch.setattr(models, 'load_problem', forbidden)
    monkeypatch.setattr(worker, 'load_problem', forbidden)
    assert preload_dependencies(json.loads(OPTIONAL.read_text())) >= 0


def test_registration_records_optional_version_and_rejects_changed_environment(tmp_path, monkeypatch):
    pytest.importorskip('qulacs')
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.common.models import save_problem
    from kmd_toc.dwt.experiment import register, run_registered
    config = json.loads(OPTIONAL.read_text())
    config['output_root'] = str(tmp_path/'results');config['input_root'] = str(tmp_path/'inputs')
    config['pilot'] = dict(scenarios=['ART_N6'], W_limits_min=[30], budgets_s=[20], repetitions=1)
    save_problem(artificial_problem(6, 2, 1), tmp_path/'inputs/ART_N6')
    source = tmp_path/'config.json';source.write_text(json.dumps(config))
    path = register(source, 'pilot', methods=['D']);registration = json.loads(path.read_text())
    assert registration['environment_version']['qulacs']
    spec = registration['specs'][0]
    assert spec['execution_cpu_profile']['workers'] == 4
    assert spec['quantum_backend_environment']['statevector_backend'] == 'qulacs'
    actual = backends.backend_environment
    monkeypatch.setattr(backends, 'backend_environment', lambda c: {**actual(c), 'statevector_version':'changed'})
    with pytest.raises(ValueError, match='REGISTERED_QUANTUM_BACKEND_ENVIRONMENT_CHANGED'):
        run_registered(path)
    assert not (tmp_path/'results/trials').exists()


def test_unknown_backend_registration_fails_before_input_access(tmp_path):
    from kmd_toc.dwt.experiment import register
    config = json.loads(CONFIG.read_text());config['D']['statevector_backend'] = 'auto'
    config['input_root'] = str(tmp_path/'nonexistent');config['output_root'] = str(tmp_path/'results')
    path = tmp_path/'config.json';path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='statevector_backend'):
        register(path, 'pilot')
    assert not (tmp_path/'results').exists()
