# Repeated Random Suite Specification

## Design

For each `n in {2,3,4,5,8,10,15,20}` and `r in {1,...,10}`, generate exactly one base subset:

\[
C_{n,r}\sim\operatorname{SRSWOR}(C_{eligible},n).
\]

Thus `R24_RANDOM_REPETITIONS_PER_N = 10` and the suite contains 80 base subsets before validation. Each subset is keyed independently; subsets need not be nested or mutually disjoint.

## Canonical frame and realization

1. Verify the frozen source manifest SHA-256 and filter exactly `eligibility_status=ELIGIBLE`.
2. Assert 39,930 unique `benchmark_customer_id` values and total `q_i=81,793`.
3. Sort rows by UTF-8 bytewise ascending `benchmark_customer_id`; this is the canonical frame.
4. Derive the key specified in `SEED_POLICY.md`.
5. Assign every row a SHA-256 selection score and select the n smallest `(score, benchmark_customer_id)` pairs.
6. Store selected customers in canonical customer-ID order, not score order.

Under the cryptographic random-permutation interpretation of the keyed scores, each n-subset has equal probability and selection is without replacement. The frozen realization avoids library-dependent sampling behavior.

No demand weighting, PPS, strata, quartiles, tertiles, manual choice, replacement, or later top-up is allowed. Each selected subset is persisted even if validation rejects it. Hard invalidity yields a rejected record under the fixed ID; no alternate sample fills its slot.
