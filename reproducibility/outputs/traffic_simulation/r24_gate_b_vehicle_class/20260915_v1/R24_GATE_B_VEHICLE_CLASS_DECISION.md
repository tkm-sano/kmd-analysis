# R24 Gate B vehicle-class decision

Decision ID: `R24-GATE-B-VEHICLE-CLASS-20260915-v1`  
Scope: `VEHICLE CLASS EVIDENCE / COMPARISON / DECISION ONLY`  
Verdict: **`GATE_B_ACCEPTED_WITH_LIMITATIONS`**

`R24_PRIMARY_VEHICLE_CLASS = kei-class electric commercial van`

No single commercial model is adopted as the R24 model vehicle. Specific vehicles are external reference records under a source-record-preserving class envelope. `managed_urban_ev_delivery_v1` remains a `FIXED_MODEL_ASSUMPTION` and is not real-vehicle evidence or the primary class.

## Vehicle class versus specific vehicle

A vehicle class fixes the operational/physical family relevant to the benchmark: here, Japanese kei-category battery-electric cargo vans used for urban residential last-mile work. A specific vehicle is a manufacturer-defined model/variant used to supply bounded external evidence. Selecting the class does not copy any model's payload, volume, battery or charging value into `Q` or an instance.

## Predeclared selection criteria

The eight user-specified criteria were adopted before classification, without post-hoc numeric weights: residential B2C relevance; urban last-mile suitability; public specification authority; capacity-data availability; EVRP-data availability; routing compatibility; modeling simplicity; researcher arbitrariness. No payload-maximizing rule or composite score was used.

## Decision

- **Kei-class electric commercial van — `PRIMARY_CANDIDATE` and selected primary.** It has the strongest direct match to dense residential parcel delivery, narrow roads and frequent stops; three independent platform families have manufacturer specifications; and official operator evidence explicitly connects lightweight EVs to last-mile delivery and residential-area use.
- **Light-duty electric truck — `SECONDARY_SCENARIO`.** It has strong manufacturer and operator evidence and much larger payload, but completed-body size, GVW, access and upfit vary materially. It represents a different operational scale and must not set the residential primary merely because its payload is larger.
- **Compact electric delivery van — `INSUFFICIENT_EVIDENCE`.** The repository contains no matched Japanese completed-BEV record for this class. Renaming a kei van, truck or fixed research profile would erase real class differences.
- **`managed_urban_ev_delivery_v1` — `REFERENCE_ONLY`.** It remains a reproducible legacy/comparison scenario, not an observed vehicle or class authority.

## Specific-vehicle reference policy

**Option B — class envelope is selected**, constrained to coherent source records. It records min/max and exact variant values; it creates no ungrounded mean or synthetic cross-model vehicle. For the primary class, Minicab EV 2-seat, e Every 2-seat, and Honda N-VAN e: variant-specific evidence are references. Minicab EV is the most complete coherent specification record, e Every supplies current official deployment/energy evidence, and N-VAN e: supplies an additional manufacturer and Tokyo-23 collection/delivery pilot boundary. None is automatically `REFERENCE_VEHICLE` or `Q`.

Option A is reproducible but over-identifies one variant with the class. Option C is reproducible but physically unsupported as a real vehicle and mismatched to the selected class. Option B best separates class selection from later parameter decisions while preserving physical combinations.

## Gate boundary

The class decision does not freeze capacity dimension, `q_i`, `Q`, `m`, parcel mass/volume, routes, instances or solver inputs. The current all-population mapping and accepted routing baseline were not validated for this newly frozen class. Therefore:

`ROUTING_REVALIDATION_REQUIRED_AFTER_VEHICLE_FREEZE`

This is a downstream compatibility task, not a reason to keep Gate B open.

`NEXT_EXECUTABLE_TASK = capacity-dimension evidence review`

