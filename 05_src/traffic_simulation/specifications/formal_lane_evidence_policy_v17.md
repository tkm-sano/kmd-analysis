<a id="ota-ward-formal-lane-evidence-policy-v17"></a>

# Ota Ward 正式車線根拠方針 v17

## 文書管理

- Policy ID: `ota_ward_formal_lane_evidence_policy_v17`
- Policy version: `1.0.0`
- Status: adopted formal policy component
- Target configuration: `ota_ward_sumo_network_v17`
- Effective decision: Step 4 Research Decision, 2026-08-31
- Network acceptance: independent gate; current Acceptance v2 remains rejected

This component fixes the meaning and evidence boundary for Formal lane values.
It does not assert that the current network has complete lane evidence.

<a id="1-formal-target-quantity"></a>

## 1. 正式対象量

Formal lane structure represents the number of **governed directional moving
lanes** and their `forward`, `backward`, and `both_ways` allocation for the
governed SUMO vehicle classes. Lane structure and vehicle permission are
separate Formal attributes. A lane count is not redefined as a count of lanes
usable by a particular class, and physical moving lane is not assumed equal to
governed usable lane.

Included are governed moving lanes, one-way active-direction lanes,
bidirectional directional lanes, approved both-ways semantics, and values
materializable by an approved rule. Parking, shoulders, bicycle-only
facilities, unapproved turn-lane representations, unresolved reversible or
conditional lanes, and shared physical lanes without an approved materializer
are excluded from Formal lane structure. `highway=service` alone never
determines a lane count.

<a id="2-evidence-hierarchy"></a>

## 2. 根拠階層

The Formal hierarchy is:

1. `SOURCE_EXPLICIT`: explicit total lane evidence;
2. `SOURCE_DIRECTIONAL`: explicit forward/backward/both-ways evidence;
3. `SOURCE_VECTOR`: only the approved vector families under the rule below;
4. `DERIVED_DETERMINISTIC`: one of the two approved bounded rules;
5. otherwise `UNRESOLVED`.

Conflicts do not fall back to a lower priority. They fail closed. SUMO
defaults, class defaults, statistical estimates, majority/median, nearest
category, and undocumented defaults are never Formal evidence.

<a id="3-approved-vector-evidence-and-rules"></a>

## 3. 承認済みベクトル根拠 ・ 規則

`SOURCE_VECTOR` is limited to `turn:lanes`, `destination:lanes`, and
`destination:ref:lanes`, and is valid only when all of the following hold:

- canonical one-way;
- no explicit total or active-direction count;
- positive vector length;
- all relevant approved vectors have the same length;
- no conditional/reversible/alternating ambiguity;
- no bicycle-specific or other mode-only semantics;
- no source conflict.

`DEC-P13-LANE-COUNT-FROM-ROAD-LANE-VECTOR-001` then derives that length as
the active-direction moving-lane count. Out-of-domain and conflicts are
`UNRESOLVED`.

`DEC-P13-LANE-BIDIRECTIONAL-TOTAL-2-FORMAL-001` applies only to canonical
`oneway=no`, explicit `lanes=2`, with no directional, `lanes:both_ways`,
conditional, reversible, alternating, or contradictory evidence. It derives
`forward=1`, `backward=1`, `both_ways=0`. It does not generalize to `lanes=4`,
other even totals, odd totals, `lanes=1`, or missing totals.

Explicit directional pairs and explicit one-way active counts remain source
evidence subject to the existing v17 consistency equations and fail-closed
conflict rules.

<a id="4-unresolved-and-simulation-only-values"></a>

## 4. 未解決 ・ シミュレーション専用の値

Shared physical, reversible, and conditional lanes remain unresolved for SUMO
Formal materialization until a separate materializer is approved. A source
semantic record may therefore be `resolved` while its Formal materialization
is `unresolved`.

`SIMULATION_MODEL_ASSUMED` includes conservative, baseline, and high-capacity
fallbacks and all class-based/statistical imputation. These values remain
simulation-only and must never promote a Formal lane value.

<a id="5-provenance-contract"></a>

## 5. 出典・来歴 取り決め

Formal records retain source Way ID, source snapshot hash, input tags, rule ID
and version where applicable, applicability result, resolved directional
values, and conflict/unresolved reason. The allowed Formal provenance classes
are `SOURCE_EXPLICIT`, `SOURCE_DIRECTIONAL`, `SOURCE_VECTOR`, and
`DERIVED_DETERMINISTIC`. `UNRESOLVED` and `SIMULATION_MODEL_ASSUMED` are
explicit non-Formal states.

<a id="6-acceptance-boundary"></a>

## 6. 受入境界

Adopting this policy does not waive lane completeness. Acceptance still
requires every governed Way to have a Formal lane structure with allowed
provenance and zero lane blockers. The 22,934 current blockers therefore
remain unchanged after policy adoption.
