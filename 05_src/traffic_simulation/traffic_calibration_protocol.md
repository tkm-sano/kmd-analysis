# Tokyo Traffic Calibration Protocol

## Preconditions

Calibration starts only after the formal road network and signal-link structure pass their gates. Structural placeholders are prohibited. Changing the formal network, signal structure or demand definition invalidates affected calibration and validation results.

## Observation Alignment

Collect time-limited JARTIC snapshots in parallel with network development. Traffic count, speed, travel time, congestion and signal observations should use the same date and time window. Any mixed-time combination requires an adjustment method and additional uncertainty record. Preserve weekday/holiday status, weather, incidents, roadworks, school holidays, special events, regulations and sensor missingness.

## Calibration Order

1. Fix network, lanes and signal structure.
2. Fit observable demand.
3. Fit capacity and saturation flow.
4. Fit route choice.
5. Fit travel time, speed and queues.
6. Apply local parameter refinement.

Each adjustable parameter requires an initial value, search range, evidence, objective metric, fixed conditions and stopping rule. Parameter groups must not all be free simultaneously.

## Metrics and Validation

Define each metric, aggregation period, weighting and acceptance threshold before viewing the calibration result. Calibration and independent validation use disjoint observations. Excluded observations follow predeclared missingness or sensor-quality rules.

Use preregistered multiple seeds and a preregistered warm-up rule. Replication count is based on output variance and the required confidence interval. Common random numbers apply to scenario comparisons, not to unrelated algorithm-internal randomness.

Seed roles are separate: instance, demand-generation and traffic-simulation seeds define shared environments; classical-solver, QAOA-parameter and QAOA-sampling seeds use independent preregistered sets.
