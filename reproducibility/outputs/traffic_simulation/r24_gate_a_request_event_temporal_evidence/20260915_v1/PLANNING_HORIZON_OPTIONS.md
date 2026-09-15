# Planning Horizon options — evidence decision only
Planning Horizon is a finite reproducible service-set membership concept. Clock duration and carrier operations are not implied. No option is frozen here.

| Option | Classification | Reproduction / size | Interpretation and limitation |
|---|---|---|---|
| 1 One synthetic day | DATA_SUPPORTED for date-based demand membership; MODEL_ASSUMPTION_REQUIRED for one-tour operational interpretation | filter evaluation_date=2026-01-01; 73,547 primary demand rows / 82,246 content units; mapped 73,200 / 81,859, 39,956 building aggregates | no new randomness needed for source membership; event count, access eligibility and CVRP membership unaccepted |
| 2 One dispatch | UNSUPPORTED as operational horizon | no dispatch IDs/members/departure times or DEP_006 operator source | controlled policy would require NEW_ASSUMPTION_REQUIRED |
| 3 One delivery wave | UNSUPPORTED | no request-linked waves/time buckets; survey aggregate hours do not define waves | do not divide day/2 or assign AM/PM |
| 4 One shift | UNSUPPORTED | no worker/vehicle shifts or working-time source | no R24 duration feasibility guarantee |
| 5 Horizon remains abstract | PARTIALLY_SUPPORTED | frozen finite-set atemporal core; concrete controlled membership policy still missing | valid core concept; cannot close A or produce executable instances with undefined membership/event rule |

Most directly data-supported horizon component: **one designated synthetic day**. Fixed-date filtering is reproducible without an additional temporal model, but mapped-scope exclusion and event/access policy must be documented. synthetic day ≠ real carrier operating day. A controlled benchmark could use the date as source boundary while separately constructing small computational instances; full-day population is not automatically one feasible fleet tour set.

One-day special assessment: reproducibility HIGH from saved snapshot; semantic validity valid as synthetic household-day realization, not physical parcel manifests; operational interpretation unestablished; instance-generation compatibility conditional on eligibility/event/horizon and Routing Baseline acceptance; R24 compatibility conditional on finite required unsplittable events, at most one tour per used vehicle, no reload/re-dispatch, no scheduling claim. No vehicle or capacity is selected. Future VRPTW needs request/window/service/clock evidence or separately labeled models; date/hour survey aggregates alone cannot establish individual windows.

Decision: recommend one synthetic day as the **source-membership candidate**, retain horizon adoption OPEN. Dispatch is not required. Required next review finalizes source-use/horizon policy and field-scoped authority amendment; event/access acceptance remains a separate condition. No artificial timestamps, departure times or demand splits adopted.
