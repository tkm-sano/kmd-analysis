# Exact reference strategy

For each frozen instance, enumerate every customer subset assigned to trip 1, its complement to trip 2, and every permutation within each nonempty trip. Reject capacity violations and unreachable arcs, canonicalize the unused-trip symmetry, then select the minimum total travel cost. This is exhaustive permutation × partition enumeration and is independently implemented from the QUBO builder.

Raw labelled route structures before capacity filtering are `(n+1)n!`: 6, 24, 120, 720, 5,040 for n=2,...,6. Canonicalization and capacity filtering are recorded separately. For n=2–4 this is mandatory validation; n=5 is permitted only as a predeclared small-scale extension; n=6 is resource-estimation only unless the gate is re-reviewed. Dynamic programming is a later cross-check, not a replacement for the small-n exhaustive reference.

