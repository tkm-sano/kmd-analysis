"""Compare preserved pre-change Qiskit kernel, current default and optional backend."""
import importlib.util
import json
from pathlib import Path
import sys
from dataclasses import asdict
import numpy as np
from kmd_toc.column_generation.aoa import AOAConfig, PricingAOA
from kmd_toc.column_generation.models import Instance


def main():
    root = Path(__file__).resolve().parent
    target = root/'legacy_kernel.json'
    if target.exists():
        raise FileExistsError(target)
    name = 'kmd_toc.column_generation._preserved_aoa'
    spec = importlib.util.spec_from_file_location(name, root/'SOURCE_BEFORE/src/kmd_toc/column_generation/aoa.py')
    original = importlib.util.module_from_spec(spec)
    sys.modules[name] = original
    spec.loader.exec_module(original)
    results = []
    for nodes, p, restarts in [(3, 2, 2), (4, 3, 1)]:
        d = np.array([[0. if i == j else .1 + ((7*i+3*j) % 11)/10
                       for j in range(nodes)] for i in range(nodes)])
        problem = Instance('legacy_kernel_check', d, (0,)+(1,)*(nodes-1), 2)
        kwargs = dict(slots=nodes, p=p, max_evaluations=35, restarts=restarts,
                      train_shots=1000, final_shots=4096, solver_seed=1101)
        dual = [.37*i for i in range(1, nodes)]
        reference = original.PricingAOA(problem, dual, original.AOAConfig(**kwargs)).run()
        row = {'nodes': nodes, 'qubits': nodes*(nodes-1), 'p': p, 'restarts': restarts}
        for backend in ['qiskit', 'qulacs']:
            engine = PricingAOA(problem, dual, AOAConfig(**kwargs, statevector_backend=backend))
            result = engine.run()
            fields = ['history', 'routes', 'reason_counts', 'measured_shots', 'feasible_shots',
                      'improving_shots', 'logical_depth']
            assert all(result[k] == reference[k] for k in fields)
            assert engine.polynomial.terms == original.PricingAOA(
                problem, dual, original.AOAConfig(**kwargs)).polynomial.terms
            angles = np.asarray(result['history'][0]['optimized_angles'])
            from qiskit.quantum_info import Statevector
            expected = Statevector.from_instruction(engine.circuit(angles)).data
            state, _, _, _ = engine.execution_state(angles)
            overlap = np.vdot(expected, state.data)
            aligned = state.data*np.conj(overlap/abs(overlap))
            err = float(np.max(np.abs(expected-aligned)))
            l1 = float(np.abs(abs(expected)**2-abs(state.data)**2).sum())
            energy = np.array([engine.polynomial.value(mask) for mask in range(1 << engine.q)])
            energy_error = float(abs(abs(expected)**2 @ energy - abs(state.data)**2 @ energy))
            assert err < 1e-10 and l1 < 1e-10 and energy_error < 1e-9
            row[backend] = {'legacy_equal_fields': fields, 'polynomial_exact_match': True,
                            'max_phase_aligned_amplitude_error': err,
                            'max_infidelity': float(abs(1-abs(overlap)**2)),
                            'probability_l1_error': l1, 'energy_absolute_error': energy_error,
                            'history': result['history'], 'routes': result['routes'],
                            'config': asdict(engine.config)}
        results.append(row)
    target.write_text(json.dumps({'scope':'kernel regression, not a new serial DWT experiment',
                                  'passed':True, 'results':results}, indent=2,
                                 default=lambda x: x.item() if isinstance(x, np.generic) else x.tolist())+'\n')
    print('Preserved/default/optional kernels agree in both cases')


if __name__ == '__main__':
    main()
