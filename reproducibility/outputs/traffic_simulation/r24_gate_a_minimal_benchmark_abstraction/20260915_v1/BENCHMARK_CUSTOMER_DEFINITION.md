# Benchmark customer definition

## Formal definition

For R24, one positive-demand mapped building in the frozen source horizon is one benchmark customer identity:

`benchmark_customer_id = "R24-20260101-BUILDING::" + source_building_id`

The realized demand of that customer is the exact sum of `parcel_equivalent` over its child synthetic household-day records. The source building ID and child-record lineage are retained. The definition is by building record, **not** by an observed delivery service event.

## Semantics

The benchmark customer is a computational demand entity grounded in Ota geography and saved synthetic demand. It is not evidence of:

- an observed customer, shipment or transaction;
- a physical delivery stop or entrance;
- one compatible visit or one carrier service event;
- a curb, parking or loading position;
- a dispatch, wave, shift, tour or real carrier day.

Multiple child demand records at one building are aggregated once for benchmark identity and demand accounting. This is an explicit model abstraction. It does not assert simultaneous arrival, common recipient, one visit, or operational consolidation.

## Service-event decision

`service_event_observational_identity` is **not a mandatory R24 Gate A input**. No `service_event_id` is created or inferred. A later operational model may introduce request times, compatibility rules and service-event aggregation as a separately versioned layer; it must not silently reinterpret the R24 building customer.

