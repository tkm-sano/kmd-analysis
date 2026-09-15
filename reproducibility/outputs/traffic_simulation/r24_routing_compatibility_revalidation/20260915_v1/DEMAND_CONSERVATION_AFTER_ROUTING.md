# Demand conservation after routing

The Gate A chain remains intact:

| Stage | Source records | Building customers | Parcel-equivalents |
|---|---:|---:|---:|
| frozen source horizon | 73,547 | — | 82,246 |
| stable building assignment | 73,200 | 39,956 | 81,859 |
| pre-building exclusion | 347 | — | 387 |
| final routing-eligible | not re-expanded in this audit | **39,930** | **81,793** |
| routing exclusion | not re-expanded in this audit | **26** | **66** |

Checks:

\[
82,246=81,859+387,
\]

\[
81,859=81,793+66,
\]

\[
39,956=39,930+26.
\]

Routing exclusions comprise 24 customers/62 units outside depot reachability in both directions, one customer/3 units outbound-only, and one customer/1 unit inbound-only. No demand value was changed; retained building `q_i` is copied exactly.
