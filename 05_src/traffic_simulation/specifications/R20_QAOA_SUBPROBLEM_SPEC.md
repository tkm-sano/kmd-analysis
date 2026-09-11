# R20 QAOA Subproblem Specification

Document ID: `R20-QAOA-SUBPROBLEM-SPEC`
Role: `CURRENT_NORMATIVE`
Lifecycle: `CURRENT`
Created: `2026-09-10`
Last Updated: `2026-09-10`
Current Authority: `Adopted reduced Single-Vehicle Route Ordering formulation and scope boundary.`
- Status: ADOPTED_AND_FORMULATION_VERIFIED_SCOPED
- Scope: frozen initial reduced route-ordering formulation; full-EVRP exclusions remain
- Current R20 Status: BLOCKED
- Current reduced downstream state: R21 PASS; R22 PASS; R23 ACCEPTED_WITH_LIMITATIONS
- Formal adoption: SUBPROBLEM_FORMULATION_ADOPTED; FORMULATION_VERIFIED = PASS for `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`
- Authority rule: This document does not supersede the current R20 formal artifacts, R15/R16/R19 authority, or the execution plan.

## 1. Purpose

本仕様書は、最初の量子サブ問題、QUBO formulation、exact validation method、bitstring decodeおよびvalidation ruleの数学的正本である。

今回の対象はSingle-Vehicle Route Ordering Problemである。このreduced formulationはscoped gateを通過し、同一係数についてR21 exact validationとR22 Ising equivalence validationもPASSした。R23 infrastructureは実装済みだが、formal QAOA pilot/baselineの実行を意味しない。

Full-EVRP R20は引き続きBLOCKEDであり、本仕様書のscoped PASSからfull EVRP、QAOA performance、QPU performanceを推論してはならない。

## 2. Current repository state and authority

### 2.1 Confirmed current state

- R20 Status: BLOCKED
- Reduced path: R21 PASS; R22 PASS; R23 ACCEPTED_WITH_LIMITATIONS (execution authorization remains separate)
- 既存R20はfull EVRPを対象とするposition-indexed formulation候補、variable registry、HC mapping、penalty framework、Rosenberg auxiliary registry、resource estimateを持つ。
- full-EVRP R20には、全制約を対象とするaccepted coefficient builder、numeric penalty certificate、decoder、independent validatorがない。本仕様のreduced route-orderingにはexact reference・exact enumeration・独立validator/decoderがあり、formal gate reviewによりFORMULATION_VERIFIEDがscoped PASSとなった。
- 既存R20のn=10 full-EVRP estimateは13,782 logical binary variables、estimated couplersは17,953であり、full exact formulationはAer/QAOAの正式実行対象として未準備である。
- CPU/Aer q=8〜30 diagnosticはTEMPORARY_IMPLEMENTATION_FEASIBILITY_DIAGNOSTICとしてのみ扱う。量子技術能力、将来QPU能力、formal problem-size limitではない。
- Hayateはsimulation execution platformであり、量子技術の性能限界ではない。
- Aer simulation limit != quantum computing technology limit

### 2.2 Inspected files

以下を読み取り専用で確認した。

- EVRP_EXECUTION_PLAN.md
- RESEARCH_PIPELINE_REFERENCE.md
- 05_src/traffic_simulation/specifications/00_research_simulation_requirements.md
- 05_src/traffic_simulation/optimization_comparison_protocol.md
- 05_src/traffic_simulation/evrp_r20_qubo_formulation/build_r20_spec.py
- 05_src/traffic_simulation/evrp_r20_qubo_formulation/
- reproducibility/outputs/traffic_simulation/demand/evrp_r20_qubo_formulation/20260910_r20_qubo_formulation_fixture_n10_v18/
- reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_qaoa_simulation_study_design_n10/
- reproducibility/outputs/traffic_simulation/temporary_quantum_diagnostic/20260910_temporary_cpu_aer_scaling_n10/
- 01_research_design/quantum_route_optimization_research_summary.md
- 01_research_design/quantum_route_optimization_slide_structure.md
- 05_src/traffic_simulation/temporary_quantum_diagnostic/run_diagnostic.py

### 2.3 Repository conflict or boundary

既存full-EVRP R20は13制約を表現する別経路であり、本書のSingle-Vehicle Route Ordering Problemはその完成を代替しない。本書は明示的なreduced branchのauthorityであり、full-EVRP statusと責任範囲は変更しない。

## 3. Adopted formal subproblem definition

### 3.1 Names and sets

- Depot: 0
- Customer set: C = {1, ..., n}
- Customer count: n = |C|
- Position set: T = {1, ..., n}
- Node set for the subproblem: V = {0} ∪ C
- Input directed-edge contract: every ordered pair (i,j), i,j in V and i != j, is explicitly classified as REACHABLE or UNREACHABLE; τ_ij exists as a formal numeric cost only for REACHABLE pairs
- Route/order: π = (π_1, ..., π_n), where π is a permutation of C
- Closed route: (0, π_1, ..., π_n, 0)

Distance may be retained as an auxiliary EVRP/fleet metric, but is not the formal objective of this initial QAOA subproblem. Time-dependent travel time τ_ij(t) is not introduced in the initial model.

### 3.2 Route

A route is the closed sequence:

R(π) = (0, π_1, π_2, ..., π_n, 0)

where every customer appears exactly once.

### 3.3 Candidate objective

The structural route objective is:

f_route(π) =
τ_(0,π_1)
+ Σ_(t=1)^(n-1) τ_(π_t,π_(t+1))
+ τ_(π_n,0)

The formal objective is total travel-time minimization. Travel time is generated, in principle, by the Routing Baseline's road-network-based travel-time design.

For an input containing UNREACHABLE pairs, f_route is defined only on permutations whose depot departure, every consecutive customer transition, and depot return are all REACHABLE. A permutation containing an unreachable leg is route-ordering-infeasible and has no numeric formal travel-time objective; no artificial infinity or large finite substitute is assigned.

### 3.4 Feasible route

A route is feasible for this subproblem if and only if:

1. π_t ∈ C for every t ∈ T;
2. π_t != π_u whenever t != u;
3. {π_1, ..., π_n} = C;
4. the route starts at depot 0 and returns to depot 0.
5. every directed leg (0,π_1), (π_t,π_(t+1)), and (π_n,0) is REACHABLE under the validated Routing Baseline input.

This is route-ordering feasibility only. It is not full EVRP feasibility.

### 3.5 Adopted subproblem status

The Single-Vehicle Route Ordering Problem is adopted as the first quantum subproblem. This adoption does not authorize QAOA execution, Ising conversion, or any later stage.

## 4. Scope exclusions

The following are explicitly outside the formal QUBO scope of this subproblem candidate:

- multi-vehicle assignment;
- vehicle capacity;
- delivery demand and payload propagation;
- time windows;
- service-time propagation;
- SOC and energy propagation;
- charging;
- charging-station selection;
- charging duration;
- fleet sizing;
- multi-depot decisions;
- full EVRP feasibility;
- SUMO traffic execution;
- future QPU hardware performance;
- provider or cloud-QPU performance;
- direct conversion from Aer runtime to future quantum runtime;
- any claim that this subproblem solves the full EVRP.

Full EVRP feasibility is re-evaluated later by Hayate and the independent validator. Directed reachability, however, is part of the reduced route-ordering input and route feasibility: an unreachable leg MUST NOT be treated as a zero-cost route leg. Excluding a full-EVRP constraint from this candidate QUBO does not delete or weaken that constraint in the formal EVRP model.

## 5. Adopted QUBO encoding

### 5.1 Position-based binary variables (adopted)

Define:

x_(i,t) ∈ {0,1}, for i ∈ C and t ∈ T

with the interpretation:

x_(i,t) = 1 if and only if customer i is assigned to visit position t.

The basic logical variable count is:

N_logical = n × n = n²

The depot is not a QUBO variable. It is fixed outside the binary assignment and is attached as the first and final node of the decoded route. No auxiliary variable is required for this basic formulation.

If a later formulation introduces auxiliary variables for higher-order terms, products, slack, or additional state, those variables MUST be counted separately:

N_total = N_logical + N_auxiliary

The auxiliary count is not included in n².

### 5.2 Customer exactly-once constraint

For each customer i:

Σ_(t∈T) x_(i,t) = 1

The authoritative customer-once penalty is:

P_customer(x) =
Σ_(i∈C) (Σ_(t∈T) x_(i,t) - 1)²

### 5.3 Position exactly-once constraint

For each position t:

Σ_(i∈C) x_(i,t) = 1

The authoritative position-once penalty is:

P_position(x) =
Σ_(t∈T) (Σ_(i∈C) x_(i,t) - 1)²

### 5.4 Normalized travel-time objective

Before QUBO construction, use the normalized static travel time for REACHABLE, non-self directed edges

τ̃_ij = τ_ij / τ_max, with 0 ≤ τ̃_ij ≤ 1.

τ_max is computed only from validated REACHABLE non-self edges required by the selected instance. UNREACHABLE/null, missing diagonal, NaN, infinity, negative, and otherwise invalid entries are excluded, not converted to numbers. τ_max MUST be finite and strictly positive. Directed asymmetry is retained; no averaging or symmetrization is permitted. The Routing Baseline zero-edge conflict is specified in Section 16.2 and MUST be resolved before accepting a zero-time real-data edge.

The QUBO travel term is:

H_travel(x) =
Σ_(i∈C) τ̃_(0,i) x_(i,1)
+ Σ_(t=1)^(n-1) Σ_(i∈C) Σ_(j∈C,j!=i) τ̃_(i,j) x_(i,t) x_(j,t+1)
+ Σ_(i∈C) τ̃_(i,0) x_(i,n)

The formal travel term excludes i=j. The coefficient builder MUST NOT require or create a self-loop τ̃_(i,i). Feasible routes never revisit the same customer consecutively, duplication is handled by the customer-once penalty, Routing Baseline does not treat self-loops as formal edges, and invalid-state energy must not depend on an undefined self-loop travel time.

### 5.5 Complete QUBO objective and full expansion

The authoritative formulation is the direct squared-penalty form:

H_QUBO(x) = H_travel(x) + λ(P_customer(x) + P_position(x))

Using x_(i,t)^2 = x_(i,t), the fully expanded form is:

H_QUBO(x) = 2λn
- 2λ Σ_i Σ_t x_(i,t)
+ 2λ Σ_i Σ_(1≤t<u≤n) x_(i,t)x_(i,u)
+ 2λ Σ_t Σ_(1≤i<j≤n) x_(i,t)x_(j,t)
+ Σ_i τ̃_(0,i)x_(i,1)
+ Σ_(t=1)^(n-1) Σ_i Σ_(j!=i) τ̃_(i,j)x_(i,t)x_(j,t+1)
+ Σ_i τ̃_(i,0)x_(i,n).

Thus the constant offset is 2nλ; the combined penalty linear coefficient is -2λ per variable, plus the applicable first-leg and/or final-leg travel coefficient. For n≥2, linear coefficients lie in [-2λ,1-2λ]; for n=1 both depot legs hit the same variable and the range is [-2λ,2-2λ]. Penalty quadratic coefficients are +2λ for same-customer/different-position pairs and +2λ for same-position/different-customer pairs. Travel quadratic coefficients lie in [0,1] and exist only for different customers at consecutive positions. If an implementation stores H_QUBO=Σ_a q_a x_a+Σ_(a<b)q_ab x_ax_b+const, these are the coefficients. A symmetric matrix convention MUST document the corresponding factor-of-two mapping.

The direct squared form and this expansion are mathematically identical under x²=x. The direct squared form is authoritative. A coefficient builder or validation artifact MUST demonstrate direct-versus-expanded equality before its output is used as formulation evidence.

### 5.5.1 FORMULATION_CORRECTION 2026-09-10

The previous expansion incorrectly recorded -λΣx and negative row/column pair coefficients. Those terms did not follow from the authoritative squared penalties and MUST NOT be used as validation evidence. The corrected combined penalty has linear coefficient -2λ and positive pair coefficient +2λ. This correction also formally excludes i=j customer-transition couplers.

This scalar form is the adopted formulation. The numerical λ value remains unresolved by policy; a hierarchical or lexicographic alternative is not permitted without a new USER_RESEARCH_DECISION.

### 5.6 Logical indexing, couplers, and density

Use row-major indexing:

index(i,t) = (i-1)n + (t-1), for i,t ∈ {1,...,n}; index values are 0,...,n²-1. The serialized order is x_(1,1),...,x_(1,n),x_(2,1),...,x_(n,n).

For a dense coefficient map, the exact count MUST be obtained after aggregation and removal of numerically zero coefficients. Before aggregation, the possible quadratic supports are:

- customer-row pairs: n·C(n,2);
- position-column pairs: n·C(n,2);
- adjacent-position, different-customer travel pairs: (n-1)n(n-1).

For a dense nonzero off-diagonal travel matrix, these supports do not overlap the row/column penalty supports. The generic count is

M_possible = 2nC(n,2)+(n-1)n(n-1) = n(n-1)(2n-1),

subject to zero coefficient removal. The authoritative method is to construct a canonical unordered pair key (min(index_a,index_b),max(index_a,index_b)), sum all contributions, remove zero coefficients under the declared tolerance, and count keys.

The exact number of nonzero quadratic terms/couplers MUST be generated from the final coefficient map after duplicate-term aggregation and zero removal. It MUST NOT be inferred only from n².

QUBO density MUST specify its denominator convention, for example:

density = M_nonzero / [N_logical(N_logical - 1)/2]

For this basic formulation N_logical=n² and N_auxiliary=0. If auxiliaries are later introduced, the denominator uses N_total and that change is separately recorded.

The exact count depends on whether the travel-time matrix is dense, sparse, symmetric, directed, and whether zero coefficients are removed. Density MUST use the same finalized coefficient map as coupler count.

## 6. Penalty design

### 6.1 No arbitrary coefficient

No fixed arbitrary penalty such as 1,000 or 1,000,000 is adopted without a coefficient-bound certificate. λ is a QUBO formulation parameter, not a QAOA tuning parameter, and MUST be verified and fixed before QAOA experiments.

With 0≤τ̃≤1, every valid route objective lies in [0,n+1]. Raw travel coefficients lie in [0,1]; complete aggregated coefficient ranges remain λ-dependent and depend on matrix sparsity. The constant offset is 2nλ.

### 6.2 Feasibility-dominance condition

Let:

- C_valid_min and C_valid_max be proven lower and upper bounds for the route-cost objective over the considered binary domain or valid-route domain;
- ΔP_min be the smallest positive penalty increase caused by a constraint violation under the selected penalty expression;
- λ be the associated penalty coefficient.

A sufficient candidate condition is:

λ × ΔP_min > C_valid_max - C_valid_min

For this formulation, a general bound can be proved under the accepted complete-reachability contract. Let r_i=Σ_t x_(i,t), c_t=Σ_i x_(i,t), and d=Σ_i(r_i-1)=Σ_t(c_t-1). The row and column deviations are integer-valued.

If d≠0, each of the row and column deviation vectors has squared norm at least 1, so P_customer+P_position≥2. If d=0 and the assignment is infeasible, at least one deviation vector is nonzero with integer entries summing to zero; its squared norm is at least 2, so the same total lower bound holds. It is attained by removing one 1 from any permutation matrix: one customer row and one position column have deviation -1, giving P_customer+P_position=2. Therefore:

`P_min = min{x not in F: P_customer(x)+P_position(x)>0} = 2`.

Because every travel coefficient is non-negative, H_travel(x)≥0 for every binary assignment. Complete reachability guarantees at least one feasible route, and every feasible route contains exactly n+1 directed legs with τ̃≤1, so f_route*≤n+1. Thus every infeasible x satisfies

`H_QUBO(x) = H_travel(x)+λP(x) ≥ 2λ`.

Consequently the conservative universal sufficient condition

`λ > (n+1)/2`

implies `H_QUBO(x)>n+1≥f_route*` for every infeasible x. Hence `argmin H_QUBO ⊆ F`. Strict inequality is required because equality can leave an infeasible state tied with a feasible global minimum.

This proof does not assume H_travel≤n+1 for arbitrary assignments. It uses only the feasible-route upper bound and the non-negativity of arbitrary-state travel energy. It is valid for asymmetric matrices, includes depot departure/return terms through the n+1 feasible-leg count, and does not use diagonal/self-loop values.

The bound is conservative, not necessary and sufficient: it bounds every infeasible state's travel energy below by zero and every feasible optimum above by n+1. A tighter finite-instance threshold is given below. The proof assumes normalized accepted non-self coefficients satisfy 0≤τ̃≤1 and that at least one complete feasible route exists; it does not depend on unresolved zero-time semantics because the current adapter rejects those inputs.

For arbitrary binary assignments, an independent term-count bound is:

`0 ≤ H_travel(x) ≤ n + n + (n-1)n(n-1) = n((n-1)^2+2)`.

The first n terms are depot departures, the second n terms are depot returns, and the final term counts all adjacent-position i≠j couplers. This upper bound is not needed to prove the universal feasibility condition, but it confirms why the feasible-route bound must not be applied to invalid states.

The exact finite-domain condition for a fixed instance is

`B_exact = max_(x not in F) (f_route* - H_travel(x)) / P(x)`, where `P(x)>0`.

For this fixed finite domain, `λ>B_exact` is necessary and sufficient for every global minimum to be feasible; `λ=B_exact` is not accepted when the maximum produces an infeasible tie. Computing B_exact requires the exact route optimum and all binary assignments, so it is an exact pre-validation quantity rather than a scalable general bound.

An instance-aware analytical sufficient bound avoids QUBO enumeration: choose any explicitly verified feasible route with normalized cost U_feasible. Since f_route*≤U_feasible and H_travel(x)≥0,

`λ > U_feasible/2`

is sufficient. The route may be the deterministic input-order route or another independently verified feasible route; selecting a cheaper route tightens the bound but does not change its proof status.

If a hierarchical objective is used, a separate proof is required for each priority level. The proof must include cross-term and auxiliary-product contributions.

### 6.3 Theoretical-bound method

The theoretical method should:

1. define the domain of every binary variable;
2. bound the maximum possible objective improvement from violating a constraint;
3. identify the minimum nonzero penalty contribution;
4. bound all linear, quadratic, auxiliary, and cross terms;
5. prove that every violating assignment is dominated by the intended valid assignment class;
6. record coefficient ranges, offsets, and numerical precision.

### 6.4 Formal λ policy and proven bound

The proven policy is size-aware and cost-aware: for any accepted complete-reachability instance, use either the universal sufficient bound `λ>(n+1)/2` or the tighter instance-aware sufficient bound `λ>U_feasible/2`, with a recorded strictly positive margin. For the initial R23 Formal Experiment A scope only (`n={2,3,4}`), the common numerical policy `R20_COMMON_GLOBAL_LAMBDA_V1` adopts `λ=3.0`; this is a controlled formulation setting, not a QAOA-tuned value. The policy is not adopted for `n>=5`, future formulations, or full EVRP.

`THEORETICAL_BOUND_PROVED`: the universal conservative sufficient bound above is established for the current formulation and input contract. `INSTANCE_AWARE_BOUND_PROVED`: `λ>U_feasible/2` is established when U_feasible is a verified normalized feasible-route upper bound.

The former `UNRESOLVED_THEORETICAL_BOUND` status is resolved for the current complete-reachability formulation. This does not prove a bound for future unreachable-transition penalties, full EVRP QUBOs, unresolved zero-time inputs, or other formulations.

### 6.5 Empirical-pilot method

An empirical pilot may be used to explore candidate λ ranges on very small instances. It may measure:

- whether exact enumeration finds valid ground states;
- whether invalid assignments occur at the minimum;
- sensitivity to cost scaling;
- sensitivity to coefficient normalization.

An empirical pilot alone does not prove formal penalty validity. Formal acceptance requires a theoretical certificate or another explicitly approved proof method.

For `R20_COMMON_GLOBAL_LAMBDA_V1`, exact/synthetic and real-data enumeration support the theorem but do not replace it. The bound margin, U_feasible, n, normalization rule, tau_max, and matrix identity must be recorded for every formal instance. The authority record is `reproducibility/config/traffic_simulation/r20_formal_penalty/20260911_r20_formal_lambda_v1.json` and its validation evidence.

## 7. Depot representation comparison

The adopted representation is fixed depot 0 outside the binary positions. The alternative is retained only as a rejected comparison, not as an active candidate.

| Dimension | Depot fixed outside binary positions | Depot included in binary position variables |
|---|---|---|
| Logical variables | n² for customer-position variables | typically at least (n+1)² or an equivalent expanded node-position representation |
| QUBO complexity | smaller and avoids depot assignment terms | additional depot assignment and start/end constraints |
| Decode simplicity | simple: decode n customer positions and attach 0 at both ends | more checks: locate depot and verify unique start/end semantics |
| Symmetry | removes depot-position symmetry by fixing start/end | can introduce equivalent depot placements unless strongly constrained |
| Exact validation | direct permutation comparison | additional validation of depot placement |
| Semantics | naturally represents fixed depot start and return | can represent flexible depot positions, which is outside this candidate unless explicitly constrained |

### Adopted decision

Keep depot 0 fixed outside the binary customer-position variables and use an n×n customer-position matrix. This gives N_logical=n², simple permutation decoding, and direct depot-to-first/final-to-depot objective terms.

## 8. Classical exact reference

### 8.1 Original route-ordering optimum

For very small n, enumerate every permutation π of C. For each permutation:

1. construct (0, π_1, ..., π_n, 0);
2. check every directed route leg against the explicit reachability set;
3. if every leg is REACHABLE, calculate f_route using the original static travel-time values τ (and separately record normalization metadata);
4. otherwise classify the permutation as route-ordering-infeasible without assigning a numeric cost;
5. record the minimum objective and all tied optimal reachable permutations;
6. record the exact optimum, reachable/infeasible permutation counts, and enumeration metadata; fail if no reachable permutation exists.

The number of permutations is n!.

### 8.2 Exact QUBO optimum

For very small n, perform exact QUBO enumeration over all binary assignments of length n², or use a separately specified exact binary optimizer that is proven exhaustive for the tested instance.

For every bitstring:

1. evaluate Q(x);
2. evaluate each assignment constraint;
3. classify QUBO-feasible or QUBO-infeasible;
4. decode valid one-hot assignments;
5. record the minimum QUBO energy;
6. record the minimum among QUBO-feasible assignments;
7. retain invalid minima separately rather than discarding them.

### 8.3 Equivalence checks

Before QAOA comparison, the following must hold for multiple very-small instances:

- every permutation maps to one valid one-hot assignment;
- every valid one-hot assignment maps to exactly one permutation;
- the decoded QUBO-feasible minimum has the same route objective as the original permutation minimum;
- the QUBO energy difference between valid routes equals the intended objective difference, up to a documented constant offset and scale;
- no QUBO-infeasible assignment has lower energy than the intended valid optimum;
- ties and directed-cost asymmetry are handled consistently.

The formal reference is travel-time-based. Distance may be retained only as an auxiliary diagnostic/fleet metric.

### 8.4 Exact validation design (specification only)

For each very-small instance, the future validation harness MUST compare:

- A. Original route enumeration over all n! customer permutations, yielding f*_route, all tied optimal routes, and route metadata;
- B. Exact QUBO enumeration over all 2^(n²) binary assignments, yielding global minimum energy, all corresponding bitstrings, feasibility, decoded routes, and invalid minima separately.

The harness MUST verify: (1) every QUBO global minimum is feasible; (2) every decoded QUBO optimum matches an original route optimum; (3) no infeasible state has lower energy than the best feasible state; (4) customer-once and position-once penalties are evaluated correctly; (5) normalization preserves route ranking; and (6) multiple optimal routes are all handled correctly. A formal validation run is not authorized in this task and may occur only after the existing gate rules and implementation prerequisites are confirmed.

## 9. Decode specification

### 9.1 Bitstring shape

The decoder expects exactly n² binary values under a fixed variable ordering:

x_(1,1), ..., x_(1,n), x_(2,1), ..., x_(n,n)

The variable ordering MUST be recorded in the final manifest. A bitstring of a different length is malformed.

### 9.2 Valid one-hot assignment

A bitstring is decode-valid if and only if:

- every value is binary;
- every customer row has exactly one 1;
- every position column has exactly one 1;
- the decoded customer IDs are exactly C;
- no position is empty;
- no position contains multiple customers.

The route is decoded by reading the customer i assigned to each position t:

π_t = i where x_(i,t)=1

The closed route is then (0, π_1, ..., π_n, 0).

### 9.3 Invalid conditions

| Condition | Classification |
|---|---|
| malformed bitstring length | DECODE_INVALID |
| non-binary value | DECODE_INVALID |
| duplicate customer assignment | QUBO_INFEASIBLE / DECODE_INVALID |
| missing customer | QUBO_INFEASIBLE / DECODE_INVALID |
| empty position | QUBO_INFEASIBLE / DECODE_INVALID |
| multiple customers at one position | QUBO_INFEASIBLE / DECODE_INVALID |
| decoded customer outside C | DECODE_INVALID |
| valid permutation matrix but one or more unreachable route legs | decode succeeds structurally; ROUTE_ORDERING_INFEASIBLE and discard |

### 9.4 Repair versus discard

The adopted initial policy is DISCARD: retain the raw bitstring, classify it as invalid, and do not repair it or present a repaired route as a primary QAOA result. Invalid includes duplicate/missing customers, empty/multiple-filled positions, malformed assignments, and either one-hot constraint violation.

If repair is later evaluated, Raw QAOA and QAOA + classical repair MUST be separate experimental pipelines. Raw and repaired samples, repair success, repair cost, and repair time MUST be retained under a new USER_RESEARCH_DECISION. Repaired output MUST NOT be reported as raw QAOA performance.

## 10. Validation levels

### 10.1 QUBO feasibility

QUBO feasibility checks only the internal assignment constraints:

- customer exactly-once;
- position exactly-once;
- any explicitly included binary-domain and coefficient checks.

A QUBO-feasible bitstring must decode to a permutation for this candidate encoding.

### 10.2 Route-ordering feasibility

Route-ordering feasibility checks:

- one depot start;
- every customer visited exactly once;
- no duplicate or missing customer;
- one depot return;
- valid cost-matrix indices;
- any explicitly adopted reachability rule for the subproblem.

The reachability rule is not yet formally fixed. If a disconnected or unavailable transition exists, the treatment requires a separate USER_RESEARCH_DECISION.

### 10.3 Full EVRP feasibility

Full EVRP feasibility is a later Hayate/validator check including, as applicable:

- Capacity;
- Time Window;
- service time;
- SOC;
- charging;
- charging-station behavior;
- reachability;
- all current common hard constraints.

QUBO-feasible does not imply full-EVRP-feasible.

Route-ordering-feasible does not imply full-EVRP-feasible.

## 11. Candidate solution-quality metrics

### 11.1 When exact optimum is known

For small instances with exact enumeration:

- best objective: minimum objective among returned samples;
- mean objective: mean objective over the declared sample set;
- optimality gap: (objective - exact optimum) / appropriate exact-optimum normalization, with the normalization explicitly defined;
- feasible solution probability: valid route samples / all counted samples;
- optimal solution probability: exact-optimal samples / all counted samples;
- best-solution probability: samples equal to the best returned objective / all counted samples;
- repeated-run variance: variance of the selected run-level metric.

Always store P_feasible = N_valid / N_total. For best objective, mean objective, optimality gap, optimal solution probability, and best-solution probability, the record MUST state whether the denominator is all samples or valid samples only. Invalid samples are never silently reassigned to a valid route.

### 11.2 When exact optimum is unavailable

Use:

- best objective;
- mean objective among valid decoded routes;
- reference-relative gap against a declared classical reference;
- feasible solution probability;
- best-solution probability relative to the declared sample set;
- repeated-run variance.

Do not label an empirical best result “optimal” without an exact or formally justified reference.

## 12. Problem-size recording rule

The encoding and formulation are invariant across problem sizes. The sequence n=2,3,4,5,... is an analysis ladder, not a QAOA authorization.

Every instance record MUST include:

- n_customers;
- n_logical_variables;
- n_auxiliary_variables;
- total binary variable count;
- quadratic coupler count;
- QUBO density and denominator convention;
- cost-matrix dimension and directionality;
- exact-enumeration availability;
- exact-reference method;
- expected circuit width;
- travel-time matrix source;
- distance is auxiliary only and not the formal objective;
- normalization metadata, including τ_max and zero/unreachable/asymmetry handling;
- penalty-policy metadata, including bound method, λ status, and certificate status;
- instance identifier and hash.

For the fixed-depot position-based candidate:

- n_logical_variables = n²;
- n_auxiliary_variables = 0 for the basic assignment-plus-route-cost form;
- expected logical circuit width is at least n² before any additional mapping or ancilla policy.

No formal maximum n is defined.

## 13. Reproducibility requirements

Before formal simulation, the following MUST be fixed and recorded:

- instance generation policy;
- customer-set selection and ordering;
- depot identity and fixed-depot rule;
- cost-matrix source;
- static travel-time objective semantics;
- units and normalization;
- τ_max definition and zero/unreachable/asymmetry handling (USER_RESEARCH_DECISION if not already fixed by Routing Baseline);
- directed versus symmetric cost treatment;
- variable ordering;
- QUBO coefficient convention;
- constant offset convention;
- penalty coefficient policy;
- decode rule;
- invalid sample policy;
- repair rule, if any;
- exact classical reference implementation and version;
- QAOA p range;
- shots;
- optimizer and iteration limits;
- repetitions;
- seed policy;
- runtime measurement definition;
- inclusion/exclusion of preprocessing, QUBO build, transpilation, optimization, sampling, decode, repair, and validation time;
- Python, Qiskit, qiskit-aer, qiskit-optimization, and qiskit-algorithms versions;
- execution environment metadata;
- CPU/GPU and Aer method;
- artifact paths, hashes, commands, and manifest.

Separate seeds SHOULD be used for instance generation, initial parameter generation, optimizer randomness, and shot sampling. Equal integer values across different roles do not make those random processes equivalent.

## 14. Required research decisions

| Item | Classification | Current state |
|---|---|---|
| formal objective | USER_RESEARCH_DECISION | adopted: static road-network-based total travel time |
| depot encoding | USER_RESEARCH_DECISION | adopted: depot fixed; customers only, n×n position encoding |
| exact QUBO encoding | USER_RESEARCH_DECISION | adopted for specification: customer-once + position-once penalties and normalized travel time |
| Routing Baseline edge input contract | USER_RESEARCH_DECISION | adopted: explicit directed REACHABLE/UNREACHABLE semantics, no diagonal requirement, no numeric unreachable cost, no symmetrization |
| initial unreachable-transition treatment | USER_RESEARCH_DECISION | adopted: initial R20 accepts only complete-reachability subsets; reject before QUBO if any directed pair is missing, unreachable, or malformed; hard constraint deferred |
| reachable non-self zero-time edge | ROUTING_BASELINE_SPEC_CONFLICT | R12 permits non-negative, R13 flags zero pair, R14 requires positive; R20 stops pending authority resolution |
| penalty coefficient policy | USER_RESEARCH_DECISION | theorem established: universal conservative λ>(n+1)/2; tighter instance-aware λ>U_feasible/2; no numerical λ adopted |
| invalid sample policy | USER_RESEARCH_DECISION | adopted: discard; no repair in initial study |
| exact classical reference implementation | USER_RESEARCH_DECISION | implemented for complete numeric synthetic matrices; explicit-reachability extension remains IMPLEMENTATION_TASK |
| problem-size ladder | USER_RESEARCH_DECISION | encoding/formulation common across n; ladder itself not an execution authorization |
| QAOA p range | USER_RESEARCH_DECISION | unresolved |
| shots | USER_RESEARCH_DECISION | unresolved |
| optimizer | USER_RESEARCH_DECISION | unresolved |
| iteration limits | USER_RESEARCH_DECISION | unresolved |
| repetitions | MUST_BE_FIXED_FOR_REPRODUCIBILITY | not fixed |
| seed policy | MUST_BE_FIXED_FOR_REPRODUCIBILITY | policy candidate defined, not fixed |
| runtime measurement definition | MUST_BE_FIXED_FOR_REPRODUCIBILITY | components identified, inclusion rule not fixed |
| formal solution-quality metrics | USER_RESEARCH_DECISION | candidate metrics defined, formal set unresolved |
| reduced exact reference / QUBO enumeration | IMPLEMENTATION_TASK | implemented; very-small synthetic evidence generated |
| independent decoder and validator | IMPLEMENTATION_TASK | implemented; tests pass |
| small-instance exact-equivalence harness | IMPLEMENTATION_TASK | implemented for n=2,3 synthetic instances; formal gate run remains separate |
| pilot penalty sensitivity | CAN_BE_EMPIRICALLY_TUNED | only after scope/encoding decisions |

## 15. Gate condition: FORMULATION_VERIFIED

The gate FORMULATION_VERIFIED may be PASS only when all of the following are satisfied:

1. original route-ordering formulation is finalized;
2. QUBO formulation is finalized;
3. variable ordering and coefficient convention are finalized;
4. decode rule is finalized;
5. invalid sample and repair policy are finalized;
6. exact classical reference is implemented;
7. multiple very-small instances are tested;
8. original route-ordering optimum and QUBO optimum agree;
9. valid-route objective differences agree up to documented scale/offset;
10. constraint-violating solutions are classified and handled as specified;
11. coefficient generation is reproducible;
12. independent validation confirms the result.

Historical pre-review gate status:

FORMULATION_VERIFIED = NOT_PASS

The restrictions above applied to the preceding implementation/evidence tasks. The separate gate review and transition record below supersede that historical status only for the explicitly scoped initial reduced formulation.

### 15.1 FORMULATION_VERIFIED gate transition — 2026-09-10

- Decision: `PASS_WITH_EXPLICIT_SCOPE_LIMITATIONS`
- Gate status: `FORMULATION_VERIFIED = PASS`
- Scope: `INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY`
- Evidence source freeze: `3d770b66eb8a053c22acbc38e3058f7845639929`
- Margin/tolerance evidence freeze: `fb8933c4b432f3bab9a2ea24142a85ab4355c320`
- Basis: corrected direct/expanded QUBO equality, independent decoder/validator, exact synthetic and real-data-derived validation, Routing Baseline complete-reachability adapter, and proved universal/instance-aware conservative penalty bounds.
- Numerical policy: `λ > B` remains the mathematical requirement. For initial R23 Formal Experiment A only, `R20_COMMON_GLOBAL_LAMBDA_V1` adopts common `λ=3.0`; `κ=10`, `δ_min=1e-6`, and `λ=B+max(10e_noise,1e-6B)` remain non-authoritative implementation-policy candidates.
- Scope limitations: complete-reachability subsets only; static normalized travel time; non-self zero-time inputs rejected; self-loops excluded; no unreachable-transition penalty; invalid samples discarded without repair; reduced route-ordering only.
- This scoped PASS does not validate full EVRP and did not itself authorize downstream execution. Subsequent separate governance and evidence records established R21 PASS, R22 PASS, and R23 ACCEPTED_WITH_LIMITATIONS for the same reduced scope only.

## 16. Historical gate-task execution record

The following actions were not performed during the R20 gate task. Later R21/R22 records supersede only the downstream stage state, not this historical execution statement:

- formal QAOA simulation;
- formal Ising conversion;
- R21 transition;
- p tuning;
- optimizer benchmark;
- shots benchmark;
- shots tuning;
- iteration benchmark;
- GPU benchmark;
- cloud QPU execution;
- production simulation;
- future quantum hardware performance estimation;
- future QPU runtime estimation;
- promotion of the existing q=8〜30 Aer diagnostic to a formal benchmark;
- full EVRP QUBO implementation;
- invalid bitstring repair experiment;
- R20 status release;
- Next Allowed Stage change.

QAOA/Aer remains a software simulation layer. Aer simulation limits are not quantum-computing technology limits.

## 16.1 Exact validation implementation record

- implementation: `05_src/traffic_simulation/r20_route_ordering/core.py`
- package export: `05_src/traffic_simulation/r20_route_ordering/__init__.py`
- synthetic validation runner: `05_src/traffic_simulation/r20_route_ordering/run_validation.py`
- automated tests: `05_src/traffic_simulation/validation/test_r20_route_ordering_exact.py`
- artifact convention: `reproducibility/outputs/traffic_simulation/r20_exact_validation/<run_id>/validation_results.json`
- method: all `n!` customer permutations and all `2^(n²)` binary assignments, with explicit enumeration guard
- repair: not implemented and not used; invalid bitstrings are discarded
- validation scope: synthetic n=2 and n=3 only; no Routing Baseline matrix was used
- coefficient builder: explicit constant, linear, and canonical quadratic maps; i=j travel terms excluded
- direct/expanded validation: exhaustive for all n=2 and n=3 synthetic states and every candidate λ
- corrected evidence artifact: `reproducibility/outputs/traffic_simulation/r20_exact_validation/20260910_corrected_expanded_qubo_v12/`
- implementation result: regression tests PASS; validation evidence is not a gate PASS

## 16.2 Routing Baseline edge semantics and R20 input contract

### 16.2.1 Evidence and observed Routing Baseline contract

This boundary specification was derived by inspecting the R12 routing schema/config and OD manifest generator, the R13 directed routing implementation and validators, the R14 independent routing validator, the R15 common-instance builder/validator, and the corresponding R12--R15 machine-readable artifacts.

The observed Routing Baseline contract is:

- R12 requires every directed ordered pair `origin_id != destination_id` over its selected endpoint set; self-loops are excluded, and duplicate or silently missing OD rows fail validation.
- `reachable=false` requires `distance_m=null` and `travel_time_s=null`; CSV serialization represents these nulls as empty fields. Zero is explicitly not an unreachable sentinel.
- A legitimate no-path result has status `LEGITIMATE_UNREACHABLE`. `INVALID_ENDPOINT`, `ROUTING_ENGINE_FAILURE`, and `MISSING_OD` are failures, not alternative spellings of unreachable.
- A reachable result has status `OK`, a finite non-negative travel time in seconds, a finite non-negative distance in metres, and a directed path. R13 minimizes free-flow travel time and reports distance for that selected path; distance is not the R20 objective.
- Routing is directed. Reverse edges are not invented, and the artifacts preserve asymmetry. In the accepted v18 fixture all 132 directed non-self pairs are reachable; all 66 reverse-pair comparisons have unequal travel times, and no zero-time pair occurs.
- R13 can mathematically return zero distance and zero time for two distinct endpoint IDs at the same offset on the same directed edge. R12 permits non-negative values and states that zero is not an unreachable sentinel, but the R13 result validator flags a reachable non-self `(distance,time)=(0,0)` as anomalous and R14 requires reachable distance and time to be strictly positive.

`ROUTING_BASELINE_SPEC_CONFLICT`: the accepted meaning of a reachable non-self zero-time edge is not consistent across R12, R13, and R14. The current real artifact does not resolve the conflict because it contains no such edge. R20 MUST stop on such an input; it MUST NOT reinterpret zero as unreachable or silently accept/reject it until the Routing Baseline authority resolves the policy.

### 16.2.2 Edge classifications

For an R20-selected node set `V={depot} union customers`, every non-self directed pair has exactly one REACHABLE/UNREACHABLE classification; a diagonal, if encountered, is classified separately as SELF_LOOP:

| Classification | Contract | R20 meaning |
|---|---|---|
| `REACHABLE` | `i != j`, `reachable=true`, status `OK`, finite formal `travel_time_s`, and valid source/path provenance | The directed edge may be used. Its travel time is the only formal objective cost; optional distance remains auxiliary. |
| `UNREACHABLE` | `i != j`, `reachable=false`, status `LEGITIMATE_UNREACHABLE`, `travel_time_s=null`, and `distance_m=null` | No formal numeric cost exists and the directed transition is forbidden. R20 does not estimate, impute, or assign a large cost. |
| `SELF_LOOP` | `i == j` | Not a formal edge and not required in the artifact. If present, it is ignored only after identity validation; it never supplies a QUBO travel coefficient. |
| `INVALID_OR_MALFORMED` | Any record violating the above relation, including unknown IDs or failure statuses | Reject the instance before exact/QUBO processing. |

Reachability determination and travel-time availability are separate stages:

`routing search -> reachable -> formal travel_time_s available`

`routing search -> no path -> UNREACHABLE -> no formal numeric travel-time cost`

The R20 layer MUST consume the Routing Baseline reachability decision. It MUST NOT infer reachability from a number, `null`, zero, matrix position, or missing record.

Malformed conditions include `reachable=true` with null/non-numeric/NaN/infinite/negative travel time, `reachable=false` with a numeric formal travel time or distance, a non-`OK` reachable status, a false status other than `LEGITIMATE_UNREACHABLE`, unknown location IDs, duplicate or inconsistent directed records, silent missing directed pairs, and any ambiguous boolean/null serialization. `ROUTING_ENGINE_FAILURE`, `INVALID_ENDPOINT`, and `MISSING_OD` stop the adapter.

### 16.2.3 R20 reduced route-ordering input schema

The adapter output is a versioned, machine-readable object with at least:

```text
problem:
  schema_version
  instance_id
  depot_id
  customer_ids[]                 # ordered, unique, depot excluded
  n_customers
  source_routing_artifact
  source_routing_schema_version
  source_routing_artifact_sha256
  source_network_hash
  routing_objective              # travel_time_minimizing
  travel_time_unit               # s
  distance_unit                  # m, auxiliary only
edges[]:                          # exactly one record per selected directed i!=j pair
  origin_id
  destination_id
  classification                 # REACHABLE or UNREACHABLE
  reachable
  travel_time_s                  # finite number iff REACHABLE; otherwise null
  distance_m                     # optional auxiliary number iff REACHABLE; otherwise null
  source_status
  source_path_reference          # optional but provenance-preserving
normalization:
  applied
  rule                           # reachable_nonself_travel_time_divided_by_tau_max
  tau_max_s                      # null when not applied
  normalized_travel_times        # separate output; raw input is immutable
  normalized_edge_set_hash
reachability:
  reachable_directed_pairs[]
  unreachable_directed_pairs[]
validation:
  selected_pair_count
  expected_pair_count            # (n+1)n
  input_hash
  adapter_version
  validation_status
  failure_reasons[]
```

The selected-node completeness requirement is strict: all `(n+1)n` directed non-self pairs over the depot and `n` customers MUST be explicitly represented as either REACHABLE or UNREACHABLE. A missing row is not equivalent to UNREACHABLE. Customer IDs and the depot ID MUST be unique; the depot MUST NOT appear in `customer_ids`; all IDs MUST resolve to the source endpoint manifest. Duplicate directed records are rejected rather than resolved by row order.

The schema preserves `tau[i,j] != tau[j,i]`. The adapter and QUBO layer MUST NOT average, mirror, fill, or otherwise symmetrize the two directions. Diagonal records and `tau[i,i]` are not required. An internal dense-array zero on the diagonal may be used only as a documented non-edge placeholder and MUST NOT enter `tau_max`, route cost, or a travel coefficient.

### 16.2.4 Zero-time and normalization policy

For `i != j`, zero MUST NOT encode UNREACHABLE. Because the Routing Baseline authorities conflict on whether a reachable zero-time edge is valid, such an edge is currently a stop condition labelled `ROUTING_BASELINE_SPEC_CONFLICT`. The accepted artifacts have strictly positive travel times, so this stop rule does not alter their observed values.

If normalization is requested, define

`A_R = {(i,j): i != j and edge(i,j) is validated REACHABLE}`

and

`τ_max = max{travel_time_s(i,j): (i,j) in A_R}`.

Only validated REACHABLE non-self edges participate. Null unreachable edges, missing diagonals, NaN, infinity, negative values, zero edges pending conflict resolution, and malformed records are excluded by rejection rather than filtering. Normalization is impossible if `A_R` is empty or `tau_max` is non-finite or not strictly positive. Raw values remain immutable and normalized values are stored separately. Division by one positive common scalar preserves every reachable route's ordering and ties and preserves directed asymmetry; this property MUST be checked on each very-small real-data-derived instance.

### 16.2.5 Unreachable-transition treatment

Option A, omission of an unreachable travel coefficient, is not sufficient to prohibit that transition. For a structurally valid permutation assignment, `P_customer=P_position=0`. If `(i,j)` at positions `t,t+1` is unreachable and its travel coefficient is merely absent, its contribution is zero:

`H_QUBO = H_other_reachable_legs + 0`,

so it can be cheaper than a positive reachable transition. The same defect applies to omission of an unreachable depot departure or return linear term. Therefore:

`UNREACHABLE_TRANSITION_CONSTRAINT_REQUIRED`

Option C, an arbitrary large artificial travel time, is rejected: it invents a formal travel cost and hides reachability semantics.

Option B is the valid formulation direction if inputs containing unreachable pairs are to be supported. Candidate prohibition supports are:

- unreachable depot departure `(0,j)`: prohibit `x_(j,1)=1`;
- unreachable customer transition `(i,j)`: prohibit `x_(i,t)x_(j,t+1)=1` for every `t=1,...,n-1`;
- unreachable depot return `(i,0)`: prohibit `x_(i,n)=1`.

A QUBO representation could add positive linear/quadratic hard-constraint penalties on these supports, but its coefficient, dominance proof, and interaction with lambda are not adopted here.

Adopted initial R20 policy: accept only a selected set `V={depot} union customers` satisfying `for all i,j in V, i!=j: reachable(i,j)=true`. Any missing, unreachable, or malformed required pair is rejected before QUBO construction. No unreachable-transition penalty is added, no coefficient is omitted as if it were a zero-cost usable edge, and no artificial large cost is introduced. Hard prohibition is deferred to a future extension and would require a new research decision and proof.

### 16.2.6 Adapter boundary and failure behavior

The non-production adapter contract is:

1. Load an immutable Routing Baseline artifact, schema/config, endpoint manifest, and hashes. Fail on unsupported version, hash mismatch, or non-time-minimizing objective.
2. Select exactly one depot and an ordered customer subset. Fail on duplicate IDs, depot/customer overlap, missing IDs, or unsupported endpoint role.
3. Form the expected `(n+1)n` directed non-self pair set. Fail on silent missing, extra selected-pair ambiguity, or duplicate records.
4. Parse booleans/nulls/status explicitly and classify each pair. Fail on malformed semantics or Routing Baseline execution-failure status.
5. Preserve REACHABLE and UNREACHABLE sets separately; never impute unreachable costs. Preserve direction and optional distance separately from travel time.
6. Check route-level reachability. A cheap necessary graph test may run first; exact permutation reachability for very-small `n` is the authoritative pre-QUBO check. Fail if no reachable depot-rooted Hamiltonian cycle exists.
7. Enforce the adopted initial complete-reachability rule and fail if any selected directed pair is absent, UNREACHABLE, or malformed. A future separately approved hard-constraint extension may replace this scope restriction.
8. If requested, normalize a copy over the validated reachable non-self set and record `tau_max`, units, source/edge-set hashes, and raw-versus-normalized identity.
9. Emit the validated R20 input plus a machine-readable validation report. Only a PASS object may reach the original-route exact reference or QUBO builder.

The following always stop processing: requested location missing; ambiguous edge semantics; reachable with missing/non-finite/negative cost; false reachability with numeric formal cost; silent missing directed pair; inconsistent duplicate; unknown/failure status; unresolved zero-time edge; impossible normalization; no reachable depot-rooted Hamiltonian cycle; or an unreachable pair presented to the current QUBO implementation.

Detecting absence of a Hamiltonian cycle at input time prevents an undefined original-route optimum. For general `n` this decision is combinatorial; the adapter may use necessary graph checks, but a negative result must be sound. For very-small validation, exhaustive permutation checking is exact. A scalable exact/decision method is an `IMPLEMENTATION_TASK`; no formal production-size method is selected here.

### 16.2.7 Very-small real-data-derived validation design

Before formal Routing Baseline integration, create evidence-only subsets containing depot plus two and depot plus three customers from a versioned accepted artifact. Selection MUST be deterministic and recorded; it MUST include an asymmetric reverse pair, and a later dedicated fixture must include an explicit legitimate unreachable pair once the prohibition policy exists.

For each subset, validate all IDs, exact directed-pair completeness, statuses/nulls, units, hashes, asymmetry preservation, and the raw/normalized edge sets. Enumerate every customer permutation, discard routes containing an unreachable leg, and record whether at least one reachable closed route exists. Compare raw and normalized optimal route sets, original permutation optimum, best feasible QUBO route, and direct-versus-expanded energy using the existing synthetic harness only after the adapter has produced a PASS input. An unreachable test MUST demonstrate that omission alone is rejected and, after separate adoption, that the explicit prohibition prevents the transition. No QAOA execution is part of this validation.

### 16.2.8 Remaining decisions and tasks

- Initial complete-reachability subset rejection is adopted. It is a study-scope restriction, not a full-EVRP requirement, a road-network connectivity claim, a quantum requirement, a future-QPU limit, or a formal maximum problem size.
- A future unreachable-transition hard constraint remains a `USER_RESEARCH_DECISION`; it is not implemented or assigned a coefficient here.
- `ROUTING_BASELINE_SPEC_CONFLICT`: reconcile the R12/R13/R14 reachable non-self zero-time rules.
- `IMPLEMENTATION_TASK`: a future explicit-unreachable QUBO formulation, dominance proof, and scalable Hamiltonian-cycle handling remain unimplemented.
- `UNREACHABLE_TRANSITION_CONSTRAINT_REQUIRED`: deferred future-extension requirement; it is inactive for accepted initial instances because complete reachability is mandatory.

## 16.3 Routing Baseline adapter and real-data-derived evidence record

- adapter: `05_src/traffic_simulation/r20_route_ordering/routing_adapter.py`
- adapter version/schema: `1.0.0` / `r20-route-ordering-input-v1`
- evidence runner: `05_src/traffic_simulation/r20_route_ordering/run_real_data_validation.py`
- tests: `05_src/traffic_simulation/validation/test_r20_routing_adapter.py`
- source: accepted R13 v18 geometry-reaccepted artifact, schema `evrp_routing_arc_v1`, routing CSV SHA-256 `29c1a68a71838bb44629cbf4bf7230a0492e9484c0a97d0c2fb2e370f2ca2ec1`
- selection: first two and first three customer endpoints in source endpoint-manifest order; no optimum-based selection and no random selection
- accepted pairs: n=2 has 6/6 and n=3 has 12/12 reachable directed non-self pairs; diagonal records are absent and not required; every unordered pair in both subsets demonstrates directed asymmetry
- original exact reference: 2 and 6 permutations respectively; unique raw optima are 1383.6383890225638 seconds and 1509.7195358760296 seconds
- QUBO enumeration: 16 and 512 states per lambda candidate; direct-versus-expanded mismatch count is zero for every state and lambda
- normalization: both raw and normalized optimal-route sets are identical; tau_max is 600.8883871408055 seconds for both selected subsets
- lambda result interpretation: candidate values 0 through 8 are validation probes only. Some low candidates have infeasible global minima; candidate 1 and above separate these two instances, but no formal numerical lambda is adopted. The general bound is theorem-backed and is recorded separately from these empirical probes.
- evidence artifact: `reproducibility/outputs/traffic_simulation/r20_real_data_validation/20260910_complete_reachability_v10/`
- evidence status: `PASS_FORMULATION_EVIDENCE_ONLY`; this is not FORMULATION_VERIFIED PASS and does not authorize QAOA.

## 16.4 Lambda-bound analysis record

- analysis utility: `05_src/traffic_simulation/r20_route_ordering/analyze_lambda_bound.py`
- analysis artifact: `reproducibility/outputs/traffic_simulation/r20_lambda_bound_analysis/20260910_adversarial_v8/lambda_bound_analysis.json`
- authoritative result: `THEORETICAL_BOUND_PROVED` for the current complete-reachability, normalized, non-negative formulation
- minimum positive assignment penalty: `P_min=2`, proved from integer row/column deviations and attained by deleting one 1 from a permutation matrix
- arbitrary-state travel range: `0 <= H_travel <= n((n-1)^2+2)`; the upper count includes n departure terms, n return terms, and `(n-1)n(n-1)` adjacent i!=j terms
- universal conservative sufficient policy: `lambda>(n+1)/2`; proof uses `H_travel>=0`, `P>=2`, and `f_route*<=n+1`
- instance-aware conservative sufficient policy: `lambda>U_feasible/2`, where U_feasible is the normalized cost of any independently verified feasible route
- exact finite-domain threshold: `B_exact=max_(x not in F)(f_route*-H_travel(x))/P(x)`; `lambda>B_exact` is necessary and sufficient for the fixed finite instance but requires exact enumeration
- adversarial evidence: all 12 deterministic n=2, n=3, and n=4 fixtures passed the bound check; n=4 used all 65,536 binary states per fixture
- evidence classification: theorem-backed supporting evidence, not a numerical lambda adoption and not a QAOA experiment

## 17. Final status

- Modified file: 05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md
- Modified existing status/decision/execution files: none
- Adopted formal subproblem: Single-Vehicle Route Ordering Problem
- Adopted encoding: fixed-depot, customer-only position-based encoding with x_(i,t), N_logical=n²
- Adopted formal objective: normalized static road-network-based total travel time
- Adopted constraints: customer-once and position-once squared penalties with common λ
- Adopted invalid-bitstring policy: discard; no repair in initial study
- Exact validation: corrected synthetic evidence generated; no formal QAOA performed; scoped gate transition is recorded in Section 15.1
- SPECIFICATION_CONFLICT: RESOLVED_FOR_DIRECT_VS_EXPANDED_FORMULATION
- Routing Baseline input contract and validation adapter: implemented for initial complete-reachability subsets; production integration not performed
- Real-data-derived exact validation: PASS_FORMULATION_EVIDENCE_ONLY for deterministic n=2 and n=3 subsets
- Resolved label: THEORETICAL_BOUND_PROVED for the current complete-reachability formulation
- Unresolved labels: ROUTING_BASELINE_SPEC_CONFLICT for non-self zero time; future unreachable-transition hard constraint and formal numerical λ adoption remain
- FORMULATION_VERIFIED: PASS (scope: INITIAL_R20_REDUCED_ROUTE_ORDERING_SCOPE_ONLY)
- R20 Status: BLOCKED
- Reduced downstream state: R21 PASS; R22 PASS; R23 ACCEPTED_WITH_LIMITATIONS
- Prohibited actions: none performed

本書はfull EVRPを解いたことやformal QAOA performanceを示さない。R21/R22の実行可否と結果は`EVRP_EXECUTION_PLAN.md`の別gate recordがauthorityであり、現在は同じreduced scopeについてR21/R22 PASS、R23 ACCEPTED_WITH_LIMITATIONSである。採択済みsubproblem formulationと、未採択のformal numerical λ policy、unreachable-transition extension、full-EVRP constraintsを分離して扱う。
