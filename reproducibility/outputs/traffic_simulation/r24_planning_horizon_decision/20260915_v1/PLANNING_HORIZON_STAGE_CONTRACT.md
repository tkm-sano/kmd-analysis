# Planning Horizon stage contract

## Inputs

Immutable daily-demand snapshot and hashes; `evaluation_date`; request-unit dictionary; saved mapping exception ledger; parent authority and decision IDs.

## Frozen output

`planning_horizon_id=R24-SOURCE-DAY-2026-01-01-v1`; `horizon_type=DESIGNATED_SYNTHETIC_DAY_SOURCE`; date 2026-01-01; day-level resolution; source snapshot references; included-record rule; mapped/unmapped accounting; classification `MODEL_BASED_SYNTHETIC`; observation status `SYNTHETIC`; operational interpretation `NONE`; decision version/hash.

The ID above names the semantic decision, not a newly materialized membership file. Saved source records remain authoritative bytes.

## Invariants

- Include every saved demand record whose `evaluation_date` equals 2026-01-01; do not invent sub-day membership.
- Preserve 73,547 records / 82,246 content units and explicitly carry 347 unmapped records / 387 units into the exception boundary.
- Do not equate source horizon membership with eligibility or instance membership.
- Any future temporal source change requires a new horizon version and dependent-frame review.
- Dispatch/wave/shift IDs are nullable and absent for this baseline.

## Out of scope / handoff

Planning Horizon does not choose n, seeds, replicates, sampling algorithm parameters, clustered/dispersed cases, anchors, event IDs, access points, vehicle, q/Q/m or OD matrices. Eligibility and Instance Generation own those decisions after their gates. An optimization instance may contain only a subset of the source-horizon eligible frame and must preserve parent IDs/hashes.
