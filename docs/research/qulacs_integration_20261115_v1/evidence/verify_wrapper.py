"""Exercise fresh-worker watchdog and standard synthetic export for registered Qulacs D."""
import json
from pathlib import Path
from kmd_toc.dwt.experiment import run_spec
from kmd_toc.dwt.standard import REQUIRED


def main():
    root = Path(__file__).resolve().parent
    registration = json.loads((root/'parallel_smoke/qulacs/pilot_REGISTERED.json').read_text())
    spec = registration['specs'][0]
    out = root/'wrapper_smoke'
    out.mkdir(exist_ok=False)
    # Synthetic roads intentionally use export_standard's documented null geometry.
    # No study road resolver or B/C output is accessed.
    row = run_spec(spec, out, geometry=None, import_only_fork=False)
    assert row['status'] == 'COMPLETE' and row['standard_output_complete']
    assert row['configured_statevector_backend'] == 'qulacs'
    assert row['quantum_backend_environment'] == spec['quantum_backend_environment']
    assert row['quantum_accounting_complete']
    assert all(r['children_joined'] and r['exitcode'] == 0 for r in row['parallel_branches'])
    trial = out/'trials'/spec['trial_id']
    assert all((trial/name).is_file() for name in REQUIRED)
    assert row['T_program_s'] == row['timing_events'][-1]['elapsed_s']
    (out/'VERIFICATION.json').write_text(json.dumps({'passed':True,
        'scope':'ART_N6 fresh-worker/export integration; no statistical performance claim',
        'status':row['status'], 'D_km':row['D_km'], 'W_min':row['W_min'],
        'T_program_s':row['T_program_s'], 'quantum_calls':row['total_quantum_calls'],
        'final_shots':row['total_final_shots'], 'required_products':REQUIRED}, indent=2)+'\n')
    print('Registered Qulacs fresh-worker, watchdog, four branches and synthetic export passed')


if __name__ == '__main__':
    main()
