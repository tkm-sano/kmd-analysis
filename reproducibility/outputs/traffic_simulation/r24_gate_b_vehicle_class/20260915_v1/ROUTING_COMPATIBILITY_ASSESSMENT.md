# Routing compatibility assessment

## Decision

`ROUTING_REVALIDATION_REQUIRED_AFTER_VEHICLE_FREEZE`

Gate A's 39,956 mappings were produced on historical run_2 using generic `delivery_permitted`; accepted run_3 Routing Baseline endpoints and directed costs cover an old 10-customer fixture. Neither artifact establishes full-population access for the newly selected kei-class electric commercial van.

## Class effects

| class | access/size/weight dependency | assessment |
|---|---|---|
| Kei electric commercial van | 3.395 m length, 1.475 m width and roughly 1.9 m height in all three reference families; low GVW relative to trucks | lowest expected physical access burden, but network permissions and proxy endpoints still require explicit validation |
| Compact electric delivery van | dimensions and legal class unresolved | cannot validate |
| Light-duty electric truck | approximately 1.695–1.910 m width in reviewed completed/relevant records; GVW from <3.5 t to 5.87 t; body heights and lengths vary | width, weight, height, turn and SUMO `delivery`/`truck` classification can change allowed edges; separate scenario validation required |
| Fixed research profile | 4.70×1.70×2.00 m, maximum permissible mass 3.5 t, SUMO `delivery` | historical assumption only; its acceptance cannot be transferred to kei or truck classes |

## Required later checks

After the vehicle/access profile is concretized, remap or verify all candidate proxies against the same accepted network hash and class permissions; record width/height/weight restriction handling; validate `DEP_006 -> customer` and `customer -> DEP_006`; and validate every ordered pair selected for an instance. Unreachable or class-incompatible candidates remain explicit exceptions.

Selecting a smaller class suggests—but does not prove—greater access. No physical entrance, curb/loading permission or real stop is inferred. Gate B is not blocked because the class and revalidation contract are now unambiguous.

