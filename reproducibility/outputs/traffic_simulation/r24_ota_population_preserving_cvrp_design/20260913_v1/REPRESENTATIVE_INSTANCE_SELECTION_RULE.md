# Representative instance selection rule

After strata are frozen, standardize the predeclared feature vector using population statistics, calculate each candidate cluster's weighted feature centroid distance, and choose the minimum-distance cluster in each nonempty stratum. Ties are resolved by ascending SHA-256 of the sorted member stop IDs, then stop ID. Within a selected cluster, choose customers by successive PPS without replacement using `w_i`, with a frozen seed and a fixed target derived from the resource gate; never choose after inspecting route or solver outcomes.

If the selected cluster exceeds the resource gate, retain it as a system-level representative and create `C_{s,r}` by the same PPS rule. The target count is determined after the cluster and authority are known, not assumed globally as n=2 or n=3. Each sub-instance stores population size, sample size, inclusion approximation, seed, source hashes, and expansion weight.

