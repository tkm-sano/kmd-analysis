"""Full-input demand checks and corruption tests; no routing or simulation."""

from collections import Counter
from dataclasses import FrozenInstanceError
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kmd_toc import freeze_demand as generation
from kmd_toc import frozen_demand as runtime


class FrozenDemandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = generation.load_inputs()
        cls.payload = generation.build_bundle(*cls.inputs)
        cls.manifest_hash = runtime.sha256(cls.payload["MANIFEST.json"])
        cls.checksum_hash = runtime.sha256(cls.payload["SHA256SUMS"])
        cls.manifest = json.loads(cls.payload["MANIFEST.json"])

    def bundle(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name) / "copy"
        generation.write_bundle(directory, self.payload)
        return directory

    def load(self, directory, scenario="S1", method="A"):
        with mock.patch.object(runtime, "_read_trust_root", return_value=(
                {"bundle_relative_path": generation.BUNDLE_REL}, self.manifest_hash, self.checksum_hash)):
            return runtime.load_frozen_demand(scenario, method_id=method, bundle_dir=directory)

    def test_full_inputs_and_source_identity(self):
        audit, master, regions, _, summary, _ = self.inputs
        self.assertEqual((len(audit), len(master), len(regions)), (39956, 39956, 182))
        self.assertEqual(Counter(r["overall_status"] for r in audit)["PASS"], 34912)
        for field in ("stop_id", "building_id"):
            self.assertEqual(len({r[field] for r in audit}), 39956)
        self.assertEqual(summary["target_count"], len(audit))

    def test_integer_quotas_pass_membership_and_attributes(self):
        audit = {r["stop_id"]: r for r in self.inputs[0]}
        counts = Counter(r["chocho_code"] for r in self.inputs[0])
        for scenario, (N, vehicles, berths) in runtime.SCENARIOS.items():
            rows = runtime.read_csv(self.payload[scenario + ".csv"])
            self.assertEqual(len(rows), N)
            self.assertEqual(sum(int(r["parcel_count"]) for r in rows), N)
            self.assertEqual(len({r["building_id"] for r in rows}), N)
            allocated = generation.allocate(counts, N)
            actual = Counter(r["chocho_code"] for r in rows)
            self.assertEqual({g: actual[g] for g in counts}, allocated)
            self.assertEqual(self.manifest["scenarios"][scenario]["vehicles"], vehicles)
            self.assertEqual(self.manifest["scenarios"][scenario]["berths"], berths)
            for row in rows:
                source = audit[row["stop_id"]]
                self.assertEqual(source["overall_status"], "PASS")
                self.assertEqual(row["parcel_count"], "1")
                for key in ("stop_id", "building_id", "chocho_code", "longitude", "latitude"):
                    self.assertEqual(row[key], source[key])

    def test_exact_hash_rank_and_verbatim_ids(self):
        for identifier in (" 001 ", "001", "é", "e\u0301", "x\x00y"):
            self.assertEqual(generation.rank_key(identifier), (
                hashlib.sha256(b"toc-stop-rank-v1\x00" + identifier.encode("utf-8")).digest(),
                identifier.encode("utf-8")))
        self.assertNotEqual(generation.rank_key("é"), generation.rank_key("e\u0301"))
        self.assertNotEqual(generation.rank_key(" 001 "), generation.rank_key("001"))
        self.assertNotIn("seed", inspect.signature(generation.build_bundle).parameters)

    def test_independent_hamilton_remainders_and_ties(self):
        counts = Counter(r["chocho_code"] for r in self.inputs[0])
        # Independent per-region error and seat-order checks (no call to allocate).
        allocation = runtime.read_csv(self.payload["REGIONAL_ALLOCATION.csv"])
        for scenario, (N, _, _) in runtime.SCENARIOS.items():
            records = [r for r in allocation if r["scenario_id"] == scenario]
            self.assertEqual(sum(int(r["allocated_count"]) for r in records), N)
            extras = {r["chocho_code"] for r in records
                      if int(r["allocated_count"]) > N * counts[r["chocho_code"]] // 39956}
            seat_count = N - sum(N * m // 39956 for m in counts.values())
            priority = sorted(counts, key=lambda g: (-(N * counts[g] % 39956), g.encode("utf-8")))
            self.assertEqual(extras, set(priority[:seat_count]))
            for r in records:
                self.assertLessEqual(int(r["allocated_count"]), int(r["pass_count"]))

    def test_common_prefix_selection_and_nested_sets(self):
        audit = self.inputs[0]
        sets = []
        for scenario in runtime.SCENARIOS:
            rows = runtime.read_csv(self.payload[scenario + ".csv"])
            selected = {r["stop_id"] for r in rows}
            sets.append(selected)
            for region, amount in Counter(r["chocho_code"] for r in rows).items():
                candidates = [r["stop_id"] for r in audit
                              if r["overall_status"] == "PASS" and r["chocho_code"] == region]
                ordered = sorted(candidates, key=lambda s: (
                    hashlib.sha256(b"toc-stop-rank-v1\x00" + s.encode("utf-8")).digest(), s.encode("utf-8")))
                self.assertEqual(selected.intersection(candidates), set(ordered[:amount]))
        self.assertTrue(sets[0] < sets[1] < sets[2])

    def test_regeneration_and_reversed_csv_row_order(self):
        self.assertEqual(self.payload, generation.build_bundle(*self.inputs))
        shuffled = []
        for value in self.inputs:
            if isinstance(value, list):
                # Serialize/reparse reversed CSV, rather than reversing IDs alone.
                data = generation.csv_bytes(tuple(value[0]), reversed(value))
                shuffled.append(runtime.read_csv(data))
            else:
                shuffled.append(value)
        self.assertEqual(self.payload, generation.build_bundle(*shuffled))

    def test_no_clock_dependence(self):
        with mock.patch("time.time", return_value=0):
            early = generation.build_bundle(*self.inputs)
        with mock.patch("time.time", return_value=9999999999):
            late = generation.build_bundle(*self.inputs)
        self.assertEqual(early, late)
        manifest = self.payload["MANIFEST.json"].decode()
        self.assertNotIn("demand_seed", manifest)
        self.assertNotIn("random_seed", manifest)

    def test_nonmonotone_quota_stops_without_reallocation(self):
        original_allocate = generation.allocate
        def changed(counts, N):
            allocation = original_allocate(counts, N)
            if N == 2000:
                region = next(g for g in allocation if original_allocate(counts, 1000)[g] > 0)
                allocation[region] = 0
            return allocation
        with mock.patch.object(generation, "allocate", side_effect=changed):
            with self.assertRaisesRegex(runtime.FrozenDemandError, "not monotone"):
                generation.build_bundle(*self.inputs)

    def test_rank_hash_collision_uses_utf8_id_order(self):
        class Collision:
            def digest(self):
                return bytes(32)
        with mock.patch("hashlib.sha256", return_value=Collision()):
            self.assertLess(generation.rank_key("a"), generation.rank_key("b"))

    def test_modified_config_rejected_by_real_trust_root(self):
        from types import SimpleNamespace
        directory = self.bundle()
        temp_root = directory.parent
        data = generation.json_bytes(dict(manifest_sha256=self.manifest_hash,
            methods=["A", "B", "C", "D"], bundle_relative_path=str(directory)))
        config = temp_root / "config.json"
        config.write_bytes(data)
        pin = SimpleNamespace(MANIFEST_SHA256=self.manifest_hash, CHECKSUMS_SHA256=self.checksum_hash,
                              CONFIG_SHA256=runtime.sha256(data), CONFIG_RELATIVE_PATH="config.json")
        with mock.patch.object(runtime, "ROOT", temp_root), mock.patch.dict(
                sys.modules, {"kmd_toc.frozen_demand_pin": pin}):
            self.assertEqual(runtime.load_frozen_demand("S1", method_id="A").N, 1000)
            config.write_bytes(data.replace(b'"A"', b'"X"'))
            for method in "ABCD":
                with self.assertRaises(runtime.FrozenDemandError):
                    runtime.load_frozen_demand("S1", method_id=method)

    def test_a_to_d_public_loader_immutable_same_input(self):
        directory = self.bundle()
        for scenario in runtime.SCENARIOS:
            demands = [self.load(directory, scenario, method) for method in "ABCD"]
            self.assertTrue(all(d.stops == demands[0].stops for d in demands))
            self.assertEqual(len({d.csv_sha256 for d in demands}), 1)
            self.assertEqual(len({d.stop_set_sha256 for d in demands}), 1)
            with self.assertRaises(FrozenInstanceError):
                demands[0].stops[0].parcel_count = 2
        with self.assertRaises(runtime.FrozenDemandError):
            self.load(directory, method="UNAPPROVED")

    def test_corrupted_values_rows_and_parcels_rejected_by_all_methods(self):
        original = self.payload["S1.csv"]
        rows = runtime.read_csv(original)
        mutations = {}
        for key, value in (("longitude", "139.0"), ("stop_id", "changed"),
                           ("building_id", "changed"), ("chocho_code", "000000"),
                           ("parcel_count", "2")):
            changed = [dict(r) for r in rows]
            changed[0][key] = value
            mutations[key] = generation.csv_bytes(runtime.COLUMNS, changed)
        mutations["deleted"] = generation.csv_bytes(runtime.COLUMNS, rows[1:])
        mutations["added"] = generation.csv_bytes(runtime.COLUMNS, rows + [rows[0]])
        mutations["reordered"] = generation.csv_bytes(runtime.COLUMNS, reversed(rows))
        directory = self.bundle()
        for name, data in mutations.items():
            (directory / "S1.csv").write_bytes(data)
            for method in "ABCD":
                with self.subTest(mutation=name, method=method), self.assertRaises(runtime.FrozenDemandError):
                    self.load(directory, method=method)
        self.assertEqual(self.payload["S1.csv"], original)  # original bundle never touched

    def test_changed_manifest_and_checksum_inventory_rejected(self):
        directory = self.bundle()
        manifest = json.loads(self.payload["MANIFEST.json"])
        manifest["files"]["S1.csv"]["sha256"] = "0" * 64
        (directory / "MANIFEST.json").write_bytes(generation.json_bytes(manifest))
        with self.assertRaises(runtime.FrozenDemandError):
            self.load(directory)
        (directory / "MANIFEST.json").write_bytes(self.payload["MANIFEST.json"])
        (directory / "SHA256SUMS").write_bytes(b"forged\n")
        with self.assertRaises(runtime.FrozenDemandError):
            self.load(directory)

    def test_missing_extra_files_and_other_scenario_changes_rejected(self):
        directory = self.bundle()
        (directory / "S3.csv").unlink()
        with self.assertRaises(runtime.FrozenDemandError):
            self.load(directory, "S1")
        (directory / "S3.csv").write_bytes(self.payload["S3.csv"])
        (directory / "extra.csv").write_text("extra")
        with self.assertRaises(runtime.FrozenDemandError):
            self.load(directory)

    def test_refuse_overwrite_and_idempotent_verification(self):
        directory = self.bundle()
        stats = {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in directory.iterdir()}
        self.assertEqual(generation.write_bundle(directory, self.payload), "VERIFIED_EXISTING_NO_WRITE")
        self.assertEqual(stats, {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in directory.iterdir()})
        (directory / "S1.csv").write_bytes(b"different")
        with self.assertRaises(runtime.FrozenDemandError):
            generation.write_bundle(directory, self.payload)
        self.assertEqual((directory / "S1.csv").read_bytes(), b"different")

    def test_duplicate_and_nonpass_input_inconsistency_refused(self):
        args = list(self.inputs)
        bad_audit = [dict(r) for r in args[0]]
        bad_audit[1]["stop_id"] = bad_audit[0]["stop_id"]
        args[0] = bad_audit
        with self.assertRaises(runtime.FrozenDemandError):
            generation.build_bundle(*args)
        args = list(self.inputs)
        bad_audit = [dict(r) for r in args[0]]
        row = next(r for r in bad_audit if r["overall_status"] != "PASS")
        row["overall_status"] = "PASS"
        args[0] = bad_audit
        with self.assertRaises(runtime.FrozenDemandError):
            generation.build_bundle(*args)

    def test_published_bundle_if_present(self):
        if not (ROOT / generation.CONFIG_REL).exists():
            self.skipTest("Publish follows successful pre-freeze tests")
        for scenario in runtime.SCENARIOS:
            demands = [runtime.load_frozen_demand(scenario, method_id=m) for m in "ABCD"]
            self.assertEqual(len(demands[0].stops), runtime.SCENARIOS[scenario][0])
            self.assertEqual(demands[0].csv_sha256, self.manifest["files"][scenario + ".csv"]["sha256"])


if __name__ == "__main__":
    unittest.main()
