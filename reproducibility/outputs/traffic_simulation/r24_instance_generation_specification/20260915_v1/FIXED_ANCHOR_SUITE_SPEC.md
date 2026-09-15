# Fixed Anchor Suite Specification

The Fixed Anchor Suite contains exactly three base aliases:

| Anchor ID | Source base instance |
|---|---|
| `R24-ANCHOR-N004` | `R24-RND-N004-R01` |
| `R24-ANCHOR-N010` | `R24-RND-N010-R01` |
| `R24-ANCHOR-N020` | `R24-RND-N020-R01` |

At generation time, copy/reference the source base's customer list, order, seed provenance, demand vector, OD artifacts, duplicate statistics, validation result, and capacity conditions exactly. Record `anchor_source_base_instance_id`. Do not resample and do not choose the first favorable, easiest, packing-feasible, or solver-successful instance.

If a source base is hard-rejected, its anchor remains a rejected fixed anchor; no later repetition substitutes for it. If a capacity condition is `PACKING_INFEASIBLE` or degenerate, the anchor preserves that state. Anchor results are for regression and cross-implementation/version comparison and must not be counted as independent primary observations.

Anchor IDs become mechanically determined when the source R01 records are generated; no customer ID is selected manually.
