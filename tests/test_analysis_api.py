"""Saved-evidence regression only; no scientific runner is imported or executed."""
from pathlib import Path
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'src'))
from kmd_quantitative.analysis import method_battery as mb, scale_analysis as sa
from kmd_quantitative.analysis import result_io as io


class AnalysisTests(unittest.TestCase):
    def test_all_artifacts_exact_read(self):
        import pandas as pd
        for key, spec in io.artifacts().items():
            path = ROOT / spec['path']
            if spec['format'] == 'csv':
                with path.open() as f:
                    self.assertEqual(io.read_table(key, raw=True), list(csv.DictReader(f)))
                pd.testing.assert_frame_equal(io.read_table(key), pd.read_csv(path), check_exact=True)
            else:
                self.assertEqual(io.read_json(key), json.loads(path.read_text()))
        # Callers cannot mutate the registered authority or future return values.
        a = io.artifacts(); a['final_freeze']['sha256'] = 'bad'
        self.assertNotEqual(a, io.artifacts())
        f = mb.freeze(); f['R0']['population'] = -1
        self.assertEqual(mb.freeze()['R0']['population'], 78)

    def test_missing_tampered_schema_and_unknown_inputs(self):
        key = 'method_summary'; spec = io.artifacts()[key]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                mb.summary(root=tmp)
            p = Path(tmp) / spec['path']; p.parent.mkdir(parents=True)
            p.write_text('bad')
            with self.assertRaises(ValueError):
                mb.summary(root=tmp)
            # Hash verification and structural validation are separate checks.
            bad = b'wrong,header\n1,2\n'
            p.write_bytes(bad)
            fake = dict(spec, sha256=hashlib.sha256(bad).hexdigest(), size_bytes=len(bad))
            with patch.dict(io._CATALOG, {key: fake}):
                with self.assertRaises(ValueError):
                    mb.summary(root=tmp)
        with self.assertRaises(KeyError):
            io.read_table('not_a_registered_result')
        with self.assertRaises(ValueError):
            io.read_json('method_summary')

    def test_matched_population_and_exclusions(self):
        f = mb.freeze(); rows = mb.population(raw=True)
        self.assertEqual((f['R0']['route_available'], f['R1']['route_available']), (78,64))
        self.assertEqual(len(rows),78)
        keys = [(r['parent_id'],r['replicate_id']) for r in rows]
        self.assertEqual(len(set(keys)),78)
        included = [r for r in rows if r['both_available']=='True']
        excluded = [r for r in rows if r['both_available']=='False']
        self.assertEqual((len(included),len(excluded)),(64,14))
        self.assertTrue(all(r['exclusion_reason']=='R1_FINAL_ROUTE_NON_ACQUISITION' and r['R1_identity']=='' for r in excluded))
        counts = {k:sum(r['transition']==k for r in included) for k in ['I→I','I→D']}
        self.assertEqual(counts,{'I→I':59,'I→D':5})
        for scale in ['R0','R1']:
            self.assertEqual(len({r[scale+'_PID'] for r in included}),64)
        common={r['matched_block_id'] for r in included}
        self.assertEqual({r['matched_block_id'] for r in mb.contrasts(raw=True)},common)

    def test_saved_D_T_and_summary_exact(self):
        rows=mb.contrasts(raw=True); f=mb.freeze()
        self.assertEqual(len(rows),256)
        for r in rows:
            for unit in ['pp','Wh']:
                for scale in ['R0','R1']:
                    self.assertEqual(Decimal(r['D_'+scale+'_'+unit]),Decimal(r[scale+'_Classical_effect_'+unit])-Decimal(r[scale+'_Quantum_effect_'+unit]))
                self.assertEqual(Decimal(r['T_R1_minus_R0_'+unit]),Decimal(r['D_R1_'+unit])-Decimal(r['D_R0_'+unit]))
                self.assertEqual(Decimal(r['D_R0_'+unit]),0)
            self.assertEqual(Decimal(r['T_R1_minus_R0_pp'])!=0,r['transition']=='I→D')
        for saved, frozen in zip(mb.summary(raw=True),f['scale_contrast_summary']):
            sub=[r for r in rows if r['rolling_case']==saved['rolling_case'] and r['comparison']==saved['comparison']]
            vals=[Decimal(r['T_R1_minus_R0_pp']) for r in sub]
            self.assertEqual(len(vals),64)
            self.assertEqual((sum(v>0 for v in vals),sum(v==0 for v in vals),sum(v<0 for v in vals)),(1,59,4))
            self.assertEqual(sum(vals)/len(vals),Decimal(saved['mean_decimal']))
            self.assertEqual(saved['mean_decimal'],frozen['mean_decimal'])
            self.assertEqual(saved['units'],'percentage_points')
            for k,v in frozen.items():
                self.assertEqual(saved[k],str(v))

    def test_energy_and_saving_contract(self):
        energies=mb.energies(raw=True)
        idx={(r['matched_block_id'],r['rolling_case'],r['stage']):r for r in energies}
        self.assertEqual(len(idx),384)
        self.assertEqual({r['stage'] for r in energies},{'B0','B1','B2'})
        model=mb.battery_conditions()
        self.assertEqual([r['stage_id'] for r in model['stage_inputs']],['B0','B1','B2'])
        with localcontext() as context:
            context.prec=50
            for r in mb.contrasts(raw=True):
                a=idx[r['matched_block_id'],r['rolling_case'],'B0']
                b=idx[r['matched_block_id'],r['rolling_case'],r['comparison'][-2:]]
                for scale in ['R0','R1']:
                    for method in ['Classical','Quantum']:
                        col=scale+'_'+method
                        e0=Decimal(a[col+'_energy_Wh']); ek=Decimal(b[col+'_energy_Wh'])
                        # Existing analyze_frozen_results.py accounting tolerances,
                        # not a relaxed API-output tolerance (read outputs are exact).
                        self.assertLess(abs(e0-ek-Decimal(r[col+'_effect_Wh'])),Decimal('1e-9'))
                        self.assertLess(abs(100*(e0-ek)/e0-Decimal(r[col+'_effect_pp'])),Decimal('1e-12'))
        for r in energies:
            for scale in ['R0','R1']:
                self.assertEqual(Decimal(r[scale+'_Q_minus_C_Wh']),Decimal(r[scale+'_Quantum_energy_Wh'])-Decimal(r[scale+'_Classical_energy_Wh']))

    def test_six_scales_and_algorithms(self):
        rows=sa.routes(raw=True); conditions=sa.conditions(raw=True); methods=sa.methods(raw=True)
        self.assertEqual([int(r['n']) for r in rows],[3,4,5,25,99,125])
        self.assertEqual(sum(int(r['planned_logical_instances']) for r in rows),468)
        self.assertEqual(sum(int(r['distinct_physical_instances']) for r in rows),460)
        for i,(r,c,m) in enumerate(zip(rows,conditions,methods)):
            self.assertEqual(r['scale_id'],c['scale_id']);self.assertEqual(c['scale_id'],m['scale_id'])
            self.assertEqual(r['planned_logical_instances'],c['logical_instances'])
            self.assertEqual(r['distinct_physical_instances'],c['physical_instances'])
            self.assertEqual(r['valid_logical_routes'],'78')
            self.assertEqual(c['solver'],m['classical_solver'])
            self.assertEqual(c['solver'],'EXHAUSTIVE_PERMUTATIONS' if i<3 else 'DETERMINISTIC_HEURISTIC_3_SWEEPS_PLUS_HIGHS_ASSIGNMENT_LP')
            self.assertEqual(c['capacity_unit'],'parcel_equivalent_NOT_kg')
            self.assertEqual(c['tw_due_test'],'service_start <= due')
        self.assertEqual(sa.trajectory_validation()['status']['LOGICAL_INSTANCE_COUNT'],468)

    def test_saved_native_diagnostics_not_removed(self):
        rows=sa.service_diagnostics(raw=True)
        late=[int(r['L3_late_stop_records']) for r in rows]
        routes=[int(r['L3_routes_with_late_stop']) for r in rows]
        returns=[int(r['L3_native_return_after_32400_routes']) for r in rows]
        self.assertEqual(late,[0,0,0,0,73,63]);self.assertEqual(routes,[0,0,0,0,61,55])
        self.assertEqual(returns,[0,0,0,0,1,3])
        self.assertEqual(sum(int(r['L2_native_completion']) for r in rows),460)
        self.assertTrue(all(r['L4_actual_operations']=='UNKNOWN_NOT_VALIDATED' for r in rows))
        self.assertIs(sa.trajectory_validation()['VRPTW_native_revalidation'],False)
        self.assertEqual(sa.trajectory_validation()['native_starts_after_due_diagnostic'],sum(late))

    def test_scale_summary_estimands_and_units(self):
        rows=sa.battery_summary(raw=True)
        self.assertEqual(len(rows),24)
        self.assertTrue(all(r['count']=='78' for r in rows))
        self.assertEqual({r['battery_effect'] for r in rows},{'B1','B2'})
        self.assertTrue(all(r['interpretation']=='DESCRIPTIVE_LOGICAL_DISTRIBUTION_NOT_INDEPENDENT_SAMPLE_OR_INTERACTION' for r in rows))
        interaction=sa.interaction_summary(raw=True)
        self.assertEqual(len(interaction),112)
        parent=[r for r in interaction if r['summary_type']=='EQUAL_PARENT_MEAN_CONTRAST']
        self.assertEqual(len(parent),40)
        self.assertTrue(all(r['unit']=='percentage_points' and r['count']=='26' for r in parent))
        self.assertTrue(all(r['unit']=='percent' for r in interaction if r not in parent))


if __name__ == '__main__':
    unittest.main()
