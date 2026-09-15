# Kei-class EV routing compatibility

## Model mapping

`kei-class electric commercial van -> SUMO vClass delivery`

This is accepted for R24 as a controlled routing abstraction because the selected class is a four-wheel commercial goods-delivery van and the accepted network has a governed `delivery` permission domain. It is not inferred merely from generic passenger-car access.

## Restriction audit

| Restriction | Current treatment | Limitation |
|---|---|---|
| one-way | encoded in directed run_3 edges | source/model validity remains inherited |
| motor-vehicle and delivery access | encoded in lane permissions; all mapped/depot edges checked | SUMO `delivery` is a class abstraction |
| pedestrian-only roads | excluded where `delivery` is not permitted | no physical entrance claim |
| private/service roads | governed access decisions inherited by `delivery` permissions | private authorization and legal stopping are not newly established |
| turn restrictions/connections | connection-aware SCC used in this audit | current R13 shortest-path implementation needs per-path connection validation |
| road width | no complete kei-specific legal-width filter demonstrated | 1.475 m vehicle width does not prove access |
| vehicle height | no complete 1.9 m clearance filter demonstrated | height-limited facilities may be missing |
| vehicle length/turning geometry | not modeled as swept path | 3.395 m length alone is insufficient |
| gross-weight restriction | no variant-complete legal-weight filter demonstrated | low kei mass reduces risk but is not proof |
| time/temporary restrictions | not represented as an operational schedule | controlled static benchmark only |

The current graph is therefore `CURRENT_GRAPH_COMPATIBLE_WITH_LIMITATIONS`, not a physical/legal-access certificate. No additional vehicle-specific graph regeneration is warranted for primary R24, while larger truck scenarios require separate validation.
