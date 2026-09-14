# Demand representation review

Demand is represented at two distinct levels. Population-level demand uses the repository's derived `w_i` household-equivalent weight and the candidate stop fields for stratum construction and sampling inclusion probabilities. Subproblem operational demand uses an explicitly frozen integer `q_i` in a single declared unit; `request_count` may be used only after its synthetic interpretation is adopted in the R24 input authority.

The 500m mesh baseline is useful for ward-scale density context, but it is not a customer/order table. No step may convert 82,023 parcel-equivalents/day into 82,023 customers or stops. Sampling must preserve the joint distribution of spatial stratum, demand value, and depot distance, with inclusion weights retained for later aggregation.

