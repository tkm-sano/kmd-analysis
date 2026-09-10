# R20 QAOA Subproblem Specification

- Document ID: R20-QAOA-SUBPROBLEM-SPEC
- Status: DESIGN_PROPOSAL_ONLY
- Scope: quantum subproblem and QUBO formulation design before formal QAOA implementation or simulation
- Current R20 Status: BLOCKED
- Current Next Allowed Stage: NONE
- Formal adoption: SUBPROBLEM_FORMULATION_ADOPTED; FORMULATION_VERIFIED remains NOT_PASS
- Authority rule: This document does not supersede the current R20 formal artifacts, R15/R16/R19 authority, or the execution plan.

## 1. Purpose

本仕様書は、formal QAOA simulationを開始する前段階として、最初の量子サブ問題候補、QUBO formulation候補、exact validation method、bitstring decodeおよびvalidation ruleを設計・固定するための文書である。

今回の設計対象は、Single-Vehicle Route Ordering Problemである。ただし、この文書はR20の正式なQUBO採択、reduced problemの正式採択、Ising変換、QAOA実装、QAOA simulation開始を意味しない。

本仕様書の作成自体では、R20 BLOCKEDを解除しない。未決定の研究判断はUSER_RESEARCH_DECISIONとして保持する。

## 2. Current repository state and authority

### 2.1 Confirmed current state

- R20 Status: BLOCKED
- Next Allowed Stage: NONE
- 既存R20はfull EVRPを対象とするposition-indexed formulation候補、variable registry、HC mapping、penalty framework、Rosenberg auxiliary registry、resource estimateを持つ。
- full-EVRP R20には、実装済みのcomplete coefficient builder、reproducible sparse QUBO matrix、completed numeric penalty certificate、QUBO decoder、R21 independent validatorがない。本仕様のreduced route-orderingについては、exact reference・exact enumeration・独立validator/decoderを別packageとして実装済みだが、これらはFORMULATION_VERIFIEDを自動的にPASSしない。
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

既存R20のformal artifactはfull-EVRP全13制約を表現する方向の設計であり、本書のSingle-Vehicle Route Ordering Problemは、その代替として自動採択するものではない。本書は、R20の未解決なreduced quantum subproblem decisionを具体化するための別設計案である。既存R20のauthority、status、execution planは変更しない。

## 3. Proposed formal subproblem definition

### 3.1 Names and sets

- Depot: 0
- Customer set: C = {1, ..., n}
- Customer count: n = |C|
- Position set: T = {1, ..., n}
- Node set for the subproblem: V = {0} ∪ C
- Input travel-time matrix: τ = (τ_ij) for i,j in V, i != j; static and road-network-based by Routing Baseline design
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

### 3.4 Feasible route

A route is feasible for this subproblem if and only if:

1. π_t ∈ C for every t ∈ T;
2. π_t != π_u whenever t != u;
3. {π_1, ..., π_n} = C;
4. the route starts at depot 0 and returns to depot 0.

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

Reachability and full EVRP feasibility are re-evaluated later by Hayate and the independent validator. Excluding a constraint from this candidate QUBO does not delete or weaken that constraint in the formal EVRP model.

## 5. Candidate QUBO encoding

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

A quadratic penalty candidate is:

P_customer(x) =
Σ_(i∈C) (Σ_(t∈T) x_(i,t) - 1)²

### 5.3 Position exactly-once constraint

For each position t:

Σ_(i∈C) x_(i,t) = 1

A quadratic penalty candidate is:

P_position(x) =
Σ_(t∈T) (Σ_(i∈C) x_(i,t) - 1)²

### 5.4 Normalized travel-time objective

Before QUBO construction, use the normalized static travel time

τ̃_ij = τ_ij / τ_max, with 0 ≤ τ̃_ij ≤ 1.

The definition of τ_max, zero edges, unreachable edges, and asymmetric entries MUST be consistent with the existing Routing Baseline. Any conflict is an UNRESOLVED_RESEARCH_DECISION and MUST be reported, not silently resolved.

The QUBO travel term is:

H_travel(x) =
Σ_(i∈C) τ̃_(0,i) x_(i,1)
+ Σ_(t=1)^(n-1) Σ_(i∈C) Σ_(j∈C) τ̃_(i,j) x_(i,t) x_(j,t+1)
+ Σ_(i∈C) τ̃_(i,0) x_(i,n)

The i=j terms MUST be explicitly handled by the coefficient builder. Their inclusion or exclusion is a USER_RESEARCH_DECISION governed by Routing Baseline semantics; it must be recorded and tested.

### 5.5 Complete QUBO objective and full expansion

The adopted scalar form is:

H_QUBO(x) = H_travel(x) + λ(P_customer(x) + P_position(x))

Using x_(i,t)^2 = x_(i,t), the fully expanded form is:

H_QUBO(x) = 2λn
- λ Σ_i Σ_t x_(i,t)
- 2λ Σ_i Σ_(1≤t<u≤n) x_(i,t)x_(i,u)
- 2λ Σ_t Σ_(1≤i<j≤n) x_(i,t)x_(j,t)
+ Σ_i τ̃_(0,i)x_(i,1)
+ Σ_(t=1)^(n-1) Σ_i Σ_j τ̃_(i,j)x_(i,t)x_(j,t+1)
+ Σ_i τ̃_(i,0)x_(i,n).

Thus the constant offset is 2λ; the penalty linear coefficient is -λ per variable, plus the applicable first-leg and/or final-leg travel coefficient. For n≥2, linear coefficients lie in [-λ, 1-λ]; for n=1, where both depot legs hit the same variable, they lie in [-λ, 2-λ]. Penalty quadratic coefficients are -2λ for same-customer/different-position pairs and -2λ for same-position/different-customer pairs. Travel quadratic coefficients lie in [0,1]. Where a retained diagonal adjacent travel term overlaps a same-customer penalty pair, the aggregated quadratic coefficient lies in [-2λ, 1-2λ]; otherwise each applicable support is in {-2λ} or [0,1]. If an implementation stores H_QUBO=Σ_a q_a x_a + Σ_{a<b} q_ab x_ax_b + const, these are the coefficients. A symmetric matrix convention MUST document the corresponding factor-of-two mapping.

This scalar form is the adopted formulation. The numerical λ value remains unresolved by policy; a hierarchical or lexicographic alternative is not permitted without a new USER_RESEARCH_DECISION.

### 5.6 Logical indexing, couplers, and density

Use row-major indexing:

index(i,t) = (i-1)n + (t-1), for i,t ∈ {1,...,n}; index values are 0,...,n²-1. The serialized order is x_(1,1),...,x_(1,n),x_(2,1),...,x_(n,n).

For a dense coefficient map, the exact count MUST be obtained after aggregation and removal of numerically zero coefficients. Before aggregation, the possible quadratic supports are:

- customer-row pairs: n·C(n,2);
- position-column pairs: n·C(n,2);
- adjacent-position travel pairs: (n-1)n².

If all τ̃_(i,j), including i=j, are retained and nonzero, the i=j adjacent travel pairs overlap the customer-row pairs for adjacent positions. Therefore the distinct-support upper count before accidental numeric cancellation is

M_possible = 2nC(n,2) + (n-1)n² - n(n-1) = (n-1)(2n²-n).

If diagonal travel terms are excluded, the generic dense count is 2nC(n,2)+(n-1)n(n-1), subject to any other overlap or zero coefficient. The authoritative method is to construct a canonical unordered pair key (min(index_a,index_b), max(index_a,index_b)), sum all contributions, remove zero coefficients under the declared tolerance, and count keys.

The exact number of nonzero quadratic terms/couplers MUST be generated from the final coefficient map after duplicate-term aggregation and zero removal. It MUST NOT be inferred only from n².

QUBO density MUST specify its denominator convention, for example:

density = M_nonzero / [N_logical(N_logical - 1)/2]

For this basic formulation N_logical=n² and N_auxiliary=0. If auxiliaries are later introduced, the denominator uses N_total and that change is separately recorded.

The exact count depends on whether the travel-time matrix is dense, sparse, symmetric, directed, and whether zero coefficients are removed. Density MUST use the same finalized coefficient map as coupler count.

## 6. Penalty design

### 6.1 No arbitrary coefficient

No fixed arbitrary penalty such as 1,000 or 1,000,000 is adopted without a coefficient-bound certificate. λ is a QUBO formulation parameter, not a QAOA tuning parameter, and MUST be verified and fixed before QAOA experiments.

With 0≤τ̃≤1, every valid route objective lies in [0,n+1]. Raw travel coefficients lie in [0,1]; complete aggregated coefficient ranges remain λ-dependent and depend on diagonal-edge handling and matrix sparsity. The constant offset is 2λ.

### 6.2 Feasibility-dominance condition

Let:

- C_valid_min and C_valid_max be proven lower and upper bounds for the route-cost objective over the considered binary domain or valid-route domain;
- ΔP_min be the smallest positive penalty increase caused by a constraint violation under the selected penalty expression;
- λ be the associated penalty coefficient.

A sufficient candidate condition is:

λ × ΔP_min > C_valid_max - C_valid_min

For this formulation P_customer+P_position is integer-valued and any infeasible assignment has a positive penalty. A global sufficient λ bound nevertheless requires a proven bound on the largest possible travel-cost advantage of every infeasible assignment relative to a feasible assignment, including the exact treatment of unreachable and zero edges. The proof must establish argmin H_QUBO ⊆ F.

If a hierarchical objective is used, a separate proof is required for each priority level. The proof must include cross-term and auxiliary-product contributions.

### 6.3 Theoretical-bound method

The theoretical method should:

1. define the domain of every binary variable;
2. bound the maximum possible objective improvement from violating a constraint;
3. identify the minimum nonzero penalty contribution;
4. bound all linear, quadratic, auxiliary, and cross terms;
5. prove that every violating assignment is dominated by the intended valid assignment class;
6. record coefficient ranges, offsets, and numerical precision.

### 6.4 Formal λ policy and unresolved bound

The policy is size-aware and cost-aware: derive a theoretical safe-bound candidate using n, the normalized travel-time scale, matrix support/directionality, and the precise invalid-state domain; test it by exhaustive enumeration on very-small instances; reject any λ for which an infeasible global minimum exists; and avoid unnecessarily large λ. No single numerical λ is adopted here.

UNRESOLVED_THEORETICAL_BOUND: a general proven safe bound has not yet been established for all allowed Routing Baseline matrices and edge-handling conventions. No guessed value may replace this status.

### 6.5 Empirical-pilot method

An empirical pilot may be used to explore candidate λ ranges on very small instances. It may measure:

- whether exact enumeration finds valid ground states;
- whether invalid assignments occur at the minimum;
- sensitivity to cost scaling;
- sensitivity to coefficient normalization.

An empirical pilot alone does not prove formal penalty validity. Formal acceptance requires a theoretical certificate or another explicitly approved proof method.

No formal penalty coefficient is selected in this document. Pilot results cannot replace the unresolved theoretical proof.

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
2. calculate f_route using the original static travel-time matrix τ (and separately record normalization metadata);
3. record the minimum objective and all tied optimal permutations;
4. record the exact optimum and enumeration metadata.

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
| valid permutation but unreachable transition | route-ordering decode valid; full EVRP validation may reject |

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
| penalty coefficient policy | USER_RESEARCH_DECISION | adopted size-aware/cost-aware policy; numerical λ and proof unresolved |
| invalid sample policy | USER_RESEARCH_DECISION | adopted: discard; no repair in initial study |
| exact classical reference implementation | USER_RESEARCH_DECISION | specified as route enumeration and exact binary QUBO enumeration; implementation not completed |
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

Current gate status:

FORMULATION_VERIFIED = NOT_PASS

Reason:

- formal λ policy still has UNRESOLVED_THEORETICAL_BOUND;
- exact coefficient builder and canonical coefficient convention are not implemented and independently checked;
- exact reference implementation for both enumerators is not completed;
- multiple very-small-instance equivalence validation has not been executed;
- final decode specification has not been independently verified;
- exact reference implementation for this candidate is not completed;
- no formal QAOA implementation or simulation was authorized in this task.

This task MUST NOT set the gate to PASS.

## 16. Strict execution record

The following actions were not performed in this task:

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
- implementation result: tests PASS; validation evidence is not a gate PASS

## 17. Final status

- Modified file: 05_src/traffic_simulation/specifications/R20_QAOA_SUBPROBLEM_SPEC.md
- Modified existing status/decision/execution files: none
- Adopted formal subproblem: Single-Vehicle Route Ordering Problem
- Adopted encoding: fixed-depot, customer-only position-based encoding with x_(i,t), N_logical=n²
- Adopted formal objective: normalized static road-network-based total travel time
- Adopted constraints: customer-once and position-once squared penalties with common λ
- Adopted invalid-bitstring policy: discard; no repair in initial study
- Exact validation: specified only; no formal run performed
- Unresolved labels: UNRESOLVED_THEORETICAL_BOUND; implementation items remain IMPLEMENTATION_TASK
- FORMULATION_VERIFIED: NOT_PASS
- R20 Status: BLOCKED
- Next Allowed Stage: NONE
- Prohibited actions: none performed

本書は、full EVRPを解いたこと、formal QAOA simulationを開始する許可、Ising conversionの許可、またはR21移行を意味しない。採択済みのsubproblem formulationと、未解決のλ理論境界・実装・検証作業を明確に分離して扱う。
