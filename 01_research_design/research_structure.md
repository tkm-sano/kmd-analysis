# Research Structure

## Motivation and research question

Transportation applications require more than a small routing formulation: meaningful evaluation must connect problem instances, operational constraints, validation modality, and quantum-resource evidence. The current research asks how transportation-relevant problem scale and constraints are represented in quantum-routing studies, and how that evidence compares with a synthetic Tokyo EVRP scenario.

## Literature review and circuit-width extraction

The review records the problem instance, mathematical formulation, quantum encoding, reported circuit width, depth definition where available, hardware or simulator modality, and evaluation status. QAOA layer count, ansatz layers, compiled depth, logical qubits, and physical-resource estimates are kept distinct. Application-oriented benchmarking, quantum utility, and practical quantum advantage literature provide methodological context rather than deployment claims.

## Application-side requirements

The comparison separates whether a requirement is represented from how it is evaluated or validated. Current requirement groups include scale, payload, operating time, range, SOC, charging access, evidence type, and classical comparison.

## Synthetic Tokyo EVRP analysis

Population mesh data supports synthetic customer sampling; public logistics facilities provide depot proxies; charging records provide candidate-location proxies; vehicle specifications define scenario parameters; and a route proxy supports exploratory constraint evaluation. Outputs must not be interpreted as observed demand, optimized real routes, charging utilization, grid load, or operational failure rates.

## Discussion and next stage

Two directions remain open:

1. Real-world optimization: road-network distances, calibrated or observed demand, time windows, sequential SOC and charging dynamics, classical optimization baselines, and operational validation.
2. Application-stage framework: link problem instances and constraints with expected quantum-technology stages, staged quantum utility, adjacent battery/material/charging technologies, expert expectations, and evolving social requirements.

## Current limitations

- Customer demand and locations are synthetic or proxy-based.
- Route construction is not a validated road-network optimization baseline.
- Sequential SOC, charger-arrival SOC, public access, congestion, operating hours, and connector compatibility are incomplete or not evaluated.
- Circuit-width evidence is heterogeneous across encodings and validation modalities.
- Representation of a constraint is not equivalent to application validation.
