# Service event evidence
Definition: request group compatible with one vehicle visit at one access location within a selected Planning Horizon. Dispatch is optional specialization.

| Relation | Evidence | Decision |
|---|---|---|
| multiple demand records at same building | 17,652 scoped building-day aggregates; child IDs/counts verified | EXISTS building grouping; not service-event identity |
| multiple request rows at same household on selected day | daily household_id is unique | no such multiple rows; 8,001 rows contain multiple content units without child parcel IDs |
| multiple buildings at same access point | no primary access/entrance IDs | NOT_AVAILABLE; access-point evidence needed |
| multiple destinations on same mapped edge | 10,022 edges shared by multiple building-day records | routing relation EXISTS; not common entrance or one visit |
| multiple destinations on same edge endpoint node | 9,308 shared from-nodes / 9,442 shared to-nodes | topology relation EXISTS, not physical service evidence |

Existing evidence supports building-level aggregation **only**. Final one-visit aggregation requires access-point and service/operational compatibility evidence, or a separately accepted controlled proxy rule. Even one household-day row as one indivisible event requires explicit unit/access policy; count-bearing row is not proof of a single operational visit. Shared road locations can support distinct events. No distance-based merging, entrance assumption or event groups/IDs are generated.
NEW_ASSUMPTION_REQUIRED: building-day=single visit; request-row=single visit; shared node=single access; timeless service compatibility. None adopted. Event cardinality is unaccepted; 39,956 is building aggregate count, not known service-event count.
