"""Apply the frozen controlled-DC battery model to matched R0 Classical/Quantum trajectories.

No routing.
No SUMO.
No Quantum execution.
No trajectory modification.
"""

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

from run_full_controlled_dc import evaluate, scalar_check


R = Path(__file__).resolve().parents[2]
O = R / "01_research_design/methodology"
S = R / "01_research_design/scenario_evaluation"

T = S / "matched_quantum_r0_trajectories_20261007"
W = S / "matched_r0_method_battery_20261007"

MANIFEST = T / "MATCHED_R0_METHOD_TRAJECTORY_MANIFEST.csv"
BINDING = T / "METHOD_TRAJECTORY_BINDING_VALIDATION.json"

MODEL = O / "CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json"
KERNEL = R / "05_src/literature_analysis/run_full_controlled_dc.py"


def sha(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def js(p):
    return json.loads(Path(p).read_text())


def write_json(p, x):
    assert not p.exists(), p
    p.write_text(
        json.dumps(
            x,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n"
    )


def write_csv(p, rows):
    assert rows
    assert not p.exists(), p
    pd.DataFrame(rows).to_csv(p, index=False)


# ==================================================
# 0. Frozen-input gates
# ==================================================

assert MANIFEST.exists()
assert BINDING.exists()

bind = js(BINDING)

assert bind["status"] == "PASS"
assert bind["paired_method_trajectory_rows"] == 80
assert bind["identical_route_pairs"] == 29
assert bind["different_route_pairs"] == 11
assert bind["identical_route_trajectory_hash_gate"] == "PASS_29_OF_29"
assert bind["battery_applied"] is False
assert sha(MANIFEST) == bind["paired_manifest_sha256"]

model = js(MODEL)
model_hash = sha(MODEL)

assert (
    model["CdA"]["value"],
    model["rho"]["value"],
    model["g"]["value"],
    model["rotational_equivalent_mass"]["value"],
    model["eta_prop"],
) == (
    1.175,
    1.2041,
    9.80665,
    61,
    0.9,
)

assert [
    x["running_mass_kg"]
    for x in model["stage_inputs"]
] == [
    1155,
    1134.79797979798,
    1123.888888888889,
]

assert [
    x["e_pack_Wh_kg"]
    for x in model["stage_inputs"]
] == [
    180,
    220,
    250,
]

assert model["Crr_model"]["formula"] == (
    "0.005+(0.01+0.0095*(v_kmh/100)^2)/p_bar"
)

for p, h in model["input_hashes"].items():
    assert sha(R / p) == h

robust = js(
    S /
    "controlled_dc_robustness_20261006/"
    "EXECUTION_PLAN.json"
)

assert sha(KERNEL) == robust["kernel_sha256"]


# ==================================================
# 1. Matched method trajectory manifest
# ==================================================

m = pd.read_csv(MANIFEST)

assert len(m) == 80
assert set(m["method"]) == {"CLASSICAL", "QUANTUM"}

g = m.groupby("physical_instance_id")

assert g["method"].nunique().eq(2).all()
assert m["physical_instance_id"].nunique() == 40

assert (
    m[m["method"] == "CLASSICAL"]
    ["physical_instance_id"]
    .nunique()
    == 40
)

assert (
    m[m["method"] == "QUANTUM"]
    ["physical_instance_id"]
    .nunique()
    == 40
)

identical = m[
    m["route_identity"] == "IDENTICAL"
]

different = m[
    m["route_identity"] == "DIFFERENT"
]

assert identical["physical_instance_id"].nunique() == 29
assert different["physical_instance_id"].nunique() == 11


# ==================================================
# 2. Preflight trajectory hashes
# ==================================================

for row in m.itertuples():

    p = R / row.trajectory_path

    assert p.exists(), p
    assert sha(p) == row.trajectory_sha256


# ==================================================
# 3. Execute frozen Battery model
# ==================================================

W.mkdir(exist_ok=True)

physical = []
effects = []
components = []
violations = []

first_scalar_check = True

for ix, row in enumerate(m.itertuples()):

    df = pd.read_csv(
        R / row.trajectory_path,
        usecols=[
            "timestamp_s",
            "speed_m_s",
        ],
    )

    t = df["timestamp_s"].to_numpy()
    speed = df["speed_m_s"].to_numpy()

    assert len(t) == int(row.sample_count)
    assert len(t) - 1 == int(row.integration_interval_count)

    assert float(t[0]) == float(row.first_sample_s)
    assert float(t[-1]) == float(row.last_sample_s)

    base = {
        "method":
            row.method,

        "route_identity":
            row.route_identity,

        "trajectory_source_type":
            row.trajectory_source_type,

        "physical_instance_id":
            row.physical_instance_id,

        "scale_id":
            row.scale_id,

        "n":
            int(row.n),

        "canonical_trajectory_id":
            row.canonical_trajectory_id,

        "trajectory_path":
            row.trajectory_path,

        "trajectory_hash":
            row.trajectory_sha256,

        "model_freeze_hash":
            model_hash,

        "observed_duration_s":
            float(t[-1] - t[0]),

        "stop_count":
            int(row.customer_service_stop_count),

        "positive_acceleration_interval_count":
            int(row.positive_acceleration_interval_count),

        "negative_acceleration_interval_count":
            int(row.negative_acceleration_interval_count),

        "heading_change_count":
            int(row.heading_change_count),

        "boundary":
            "OBSERVED_WINDOW_CONTROLLED_DC",
    }

    for case, config in model["Crr_model"]["cases"].items():

        vals = []
        arrays = []

        for stage in model["stage_inputs"]:

            out, arr = evaluate(
                t,
                speed,
                model,
                config["p_bar"],
                stage,
            )

            if first_scalar_check:
                scalar_check(
                    t,
                    speed,
                    model,
                    config["p_bar"],
                    stage,
                    out,
                )
                first_scalar_check = False

            physical.append({
                **base,

                "stage":
                    stage["stage_id"],

                "e_pack_Wh_kg":
                    stage["e_pack_Wh_kg"],

                "vehicle_mass_kg":
                    stage["vehicle_mass_kg"],

                "running_mass_kg":
                    stage["running_mass_kg"],

                "rolling_case":
                    case,

                **out,
            })

            vals.append(out)
            arrays.append(arr)

        # Aero and rotational terms must remain common across Battery stages.
        assert (
            len({
                x["aero_Wh"]
                for x in vals
            }) == 1
        )

        assert (
            len({
                x["rotational_signed_Wh"]
                for x in vals
            }) == 1
        )

        energies = [
            x["net_DC_Wh"]
            for x in vals
        ]

        ordering = (
            energies[0]
            >= energies[1]
            >= energies[2]
        )

        if not ordering:
            violations.append({
                "method":
                    row.method,
                "physical_instance_id":
                    row.physical_instance_id,
                "rolling_case":
                    case,
                "energies":
                    energies,
            })

        effect = {
            **base,

            "rolling_case":
                case,

            "E_B0_Wh":
                energies[0],

            "E_B1_Wh":
                energies[1],

            "E_B2_Wh":
                energies[2],

            "energy_ordering":
                ordering,

            "ratio_status":
                "DEFINED"
                if energies[0] > 0
                else "UNDEFINED",
        }

        for k in [1, 2]:

            effect[f"Delta_E_B{k}_Wh"] = (
                energies[0]
                - energies[k]
            )

            effect[f"R_B{k}_percent"] = (
                100
                * (
                    energies[0]
                    - energies[k]
                )
                / energies[0]
                if energies[0] > 0
                else None
            )

            a0 = arrays[0]
            ak = arrays[k]

            i0 = a0["wheel"] > 0
            ik = ak["wheel"] > 0

            co = {
                **base,
                "rolling_case":
                    case,
                "comparison":
                    f"B0_TO_B{k}",
            }

            for key in [
                "roll",
                "translational",
                "rotational",
                "aero",
            ]:

                co[
                    key
                    + "_baseline_mask_DC_saving_Wh"
                ] = (
                    float(
                        np.sum(
                            (
                                a0[key]
                                - ak[key]
                            )[i0]
                        )
                    )
                    / model["eta_prop"]
                )

                co[
                    key
                    + "_signed_mechanical_delta_Bk_minus_B0_Wh"
                ] = float(
                    np.sum(
                        ak[key]
                        - a0[key]
                    )
                )

            co["grade_delta_Wh"] = 0

            co[
                "directional_branch_correction_Wh"
            ] = (
                float(
                    np.sum(
                        (
                            i0.astype(int)
                            - ik.astype(int)
                        )
                        * ak["wheel"]
                    )
                )
                / model["eta_prop"]
            )

            co["branch_switch_count"] = int(
                np.count_nonzero(
                    i0 != ik
                )
            )

            co["DC_saving_Wh"] = (
                energies[0]
                - energies[k]
            )

            co["accounting_residual_Wh"] = (
                co["DC_saving_Wh"]
                - sum(
                    co[
                        key
                        + "_baseline_mask_DC_saving_Wh"
                    ]
                    for key in [
                        "roll",
                        "translational",
                        "rotational",
                        "aero",
                    ]
                )
                - co[
                    "directional_branch_correction_Wh"
                ]
            )

            assert abs(
                co["accounting_residual_Wh"]
            ) < 1e-7

            co["largest_component"] = (
                "translational"
                if (
                    co[
                        "translational_baseline_mask_DC_saving_Wh"
                    ]
                    >
                    co[
                        "roll_baseline_mask_DC_saving_Wh"
                    ]
                )
                else "rolling"
            )

            components.append(co)

        effects.append(effect)

    if ix % 10 == 0:
        print(
            "BATTERY_APPLIED",
            ix + 1,
            "/80",
            flush=True,
        )


# ==================================================
# 4. Accounting
# ==================================================

assert len(physical) == 480
assert len(effects) == 160
assert len(components) == 320
assert not violations


# ==================================================
# 5. Pair Classical and Quantum effects
# ==================================================

ef = pd.DataFrame(effects)

pairs = []

for (
    pid,
    rolling_case,
), sub in ef.groupby([
    "physical_instance_id",
    "rolling_case",
]):

    assert len(sub) == 2
    assert set(sub["method"]) == {
        "CLASSICAL",
        "QUANTUM",
    }

    c = sub[
        sub["method"] == "CLASSICAL"
    ].iloc[0]

    q = sub[
        sub["method"] == "QUANTUM"
    ].iloc[0]

    assert c["route_identity"] == q["route_identity"]

    row = {
        "physical_instance_id":
            pid,

        "route_identity":
            c["route_identity"],

        "rolling_case":
            rolling_case,

        "classical_trajectory_hash":
            c["trajectory_hash"],

        "quantum_trajectory_hash":
            q["trajectory_hash"],

        "C_E_B0_Wh":
            c["E_B0_Wh"],
        "Q_E_B0_Wh":
            q["E_B0_Wh"],

        "C_E_B1_Wh":
            c["E_B1_Wh"],
        "Q_E_B1_Wh":
            q["E_B1_Wh"],

        "C_E_B2_Wh":
            c["E_B2_Wh"],
        "Q_E_B2_Wh":
            q["E_B2_Wh"],

        "C_R_B1_percent":
            c["R_B1_percent"],
        "Q_R_B1_percent":
            q["R_B1_percent"],

        "C_R_B2_percent":
            c["R_B2_percent"],
        "Q_R_B2_percent":
            q["R_B2_percent"],

        # Earlier-defined direction:
        # D = Classical battery effect - Quantum battery effect
        "C_minus_Q_R_B1_pp":
            c["R_B1_percent"]
            - q["R_B1_percent"],

        "C_minus_Q_R_B2_pp":
            c["R_B2_percent"]
            - q["R_B2_percent"],

        "Q_minus_C_E_B0_Wh":
            q["E_B0_Wh"]
            - c["E_B0_Wh"],

        "Q_minus_C_E_B1_Wh":
            q["E_B1_Wh"]
            - c["E_B1_Wh"],

        "Q_minus_C_E_B2_Wh":
            q["E_B2_Wh"]
            - c["E_B2_Wh"],
    }

    pairs.append(row)

assert len(pairs) == 80


# ==================================================
# 6. Strong gate for 29 identical trajectories
# ==================================================

identical_pairs = [
    x for x in pairs
    if x["route_identity"] == "IDENTICAL"
]

different_pairs = [
    x for x in pairs
    if x["route_identity"] == "DIFFERENT"
]

assert len(identical_pairs) == 29 * 2
assert len(different_pairs) == 11 * 2

max_identical_energy_diff = 0.0
max_identical_effect_diff = 0.0

for x in identical_pairs:

    assert (
        x["classical_trajectory_hash"]
        == x["quantum_trajectory_hash"]
    )

    for st in ["B0", "B1", "B2"]:

        diff = abs(
            x[f"C_E_{st}_Wh"]
            - x[f"Q_E_{st}_Wh"]
        )

        max_identical_energy_diff = max(
            max_identical_energy_diff,
            diff,
        )

    for st in ["B1", "B2"]:

        diff = abs(
            x[f"C_R_{st}_percent"]
            - x[f"Q_R_{st}_percent"]
        )

        max_identical_effect_diff = max(
            max_identical_effect_diff,
            diff,
        )

assert max_identical_energy_diff <= 1e-12
assert max_identical_effect_diff <= 1e-12


# ==================================================
# 7. Descriptive summaries
# ==================================================

summary_rows = []

for (
    method,
    rolling_case,
), sub in ef.groupby([
    "method",
    "rolling_case",
]):

    for battery in [
        "B1",
        "B2",
    ]:

        vals = sub[
            f"R_{battery}_percent"
        ].dropna()

        summary_rows.append({
            "method":
                method,
            "rolling_case":
                rolling_case,
            "battery_effect":
                battery,
            "count":
                len(vals),
            "mean":
                float(vals.mean()),
            "min":
                float(vals.min()),
            "P25":
                float(vals.quantile(.25)),
            "median":
                float(vals.quantile(.5)),
            "P75":
                float(vals.quantile(.75)),
            "max":
                float(vals.max()),
            "scope":
                "CONDITIONAL_ON_QUANTUM_FINAL_ROUTE_AVAILABLE_40",
        })


# ==================================================
# 8. Save
# ==================================================

write_csv(
    W / "R0_METHOD_BATTERY_ENERGY_ROWS.csv",
    physical,
)

write_csv(
    W / "R0_METHOD_BATTERY_EFFECTS.csv",
    effects,
)

write_csv(
    W / "R0_METHOD_BATTERY_COMPONENTS.csv",
    components,
)

write_csv(
    W / "R0_METHOD_BATTERY_PAIR_CONTRASTS.csv",
    pairs,
)

write_csv(
    W / "R0_METHOD_BATTERY_SUMMARY.csv",
    summary_rows,
)


validation = {
    "status":
        "PASS",

    "scope":
        "R0_CONDITIONAL_MATCHED_40",

    "physical_population":
        78,

    "quantum_final_route_available":
        40,

    "method_trajectory_rows":
        80,

    "energy_rows":
        480,

    "effect_rows":
        160,

    "component_rows":
        320,

    "paired_method_effect_cells":
        80,

    "identical_route_pairs":
        29,

    "different_route_pairs":
        11,

    "identical_route_energy_gate":
        "PASS_29_OF_29",

    "max_identical_energy_difference_Wh":
        max_identical_energy_diff,

    "max_identical_battery_effect_difference_pp":
        max_identical_effect_diff,

    "energy_ordering":
        "PASS",

    "energy_accounting":
        "PASS",

    "model_freeze_sha256":
        model_hash,

    "kernel_sha256":
        sha(KERNEL),

    "new_routing_executed":
        False,

    "SUMO_executed_in_this_stage":
        False,

    "additional_quantum_sampling":
        False,

    "full_population_78_method_x_battery":
        "NOT_IDENTIFIABLE",

    "conditional_40_instance_method_x_battery":
        "CALCULATED",

    "next_stage":
        "ANALYZE_R0_CLASSICAL_X_QUANTUM_BATTERY_EFFECT",
}

write_json(
    W / "VALIDATION.json",
    validation,
)

print()
print(json.dumps(validation, indent=2))
