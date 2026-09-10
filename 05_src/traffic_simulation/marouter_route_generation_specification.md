# marouter route-generation specification and diagnosis

Date: 2026-08-28  
Research stage: baseline traffic model, Step 4 (routing)  
Status: diagnostic; route-generation configuration is not frozen

## Scope

This stage decides whether SUMO 1.24.0 `marouter` can generate a plausible
route set from the frozen network, TAZ definitions, and Tokyo PT OD demand.
Observed Road Census values are not used for route construction. The six
canonical detector edges are used only as structural support checks.

The reproducible diagnostic is implemented in
`calibration/diagnose_marouter_route_generation.py`. The Route2 DOWN fixed
endpoint grid is defined by
`reproducibility/config/traffic_simulation/route_generation/route2_down_fixed_endpoint_probe_v1.json`.

## SUMO 1.24.0 implementation contract

The official documentation describes `--paths` as repeated shortest-path
search with a penalty added to every edge of the previously returned path.
This is not a loopless k-shortest-path algorithm.

The 1.24.0 source gives the precise behavior:

1. `getKPaths(k, penalty)` clears penalties for each OD cell, calls
   `computePath` up to `k` times, and adds `penalty` seconds to every edge in
   each newly returned route.
2. A duplicate path is not appended. Because an empty edge list is returned
   for a duplicate, that iteration adds no further penalty; repeated searches
   can therefore stop discovering distinct candidates before `paths` is
   reached.
3. `max-alternatives` is a hard size gate in `computePath`. Once the route
   vector reaches it, no further shortest-path search is performed.
4. SUE first calls `getKPaths`, then updates route costs, probabilities, flows,
   and capacity-constrained travel times. Each outer iteration can add a new
   shortest route only while the vector remains below `max-alternatives`.
5. Therefore `max-alternatives == paths` can consume all capacity before SUE
   can add a congestion-derived route. In that configuration,
   `max-iterations=20` does not imply twenty further candidate searches.
6. At the size gate, SUMO 1.24.0 calls `recomputeCosts(edges, ...)` with the
   local empty `edges` vector rather than the iterated stored route. This code
   is also present on the current upstream main branch. It is relevant to
   probability accumulation at the cap and is another reason not to infer
   route-set semantics from option names alone.

Primary references:

- <https://sumo.dlr.de/docs/marouter.html>
- <https://github.com/eclipse-sumo/sumo/blob/v1_24_0/src/marouter/ROMAAssignments.cpp>
- <https://github.com/eclipse-sumo/sumo/blob/v1_24_0/src/marouter/marouter_main.cpp>
- <https://github.com/eclipse-sumo/sumo/blob/v1_24_0/src/marouter/ROMAFrame.cpp>

## Fixed-endpoint result

Probe:

- OD relation: `PT_SZ_02432 -> PT_SZ_01320`
- fixed edges: `1138319664#9 -> 828705048#5`
- Route2 DOWN target: `309829214#19`
- seed: `230823`
- network SHA-256:
  `a78a020eda81c3ceda9310d23420c5f4836a6cef0a9a99c9b9f5c42c0383fd91`

`duarouter` with the target as a mandatory `via` produces a legal 222-edge
route with a free-flow cost of 446.406454 seconds. This establishes legality
independently of candidate generation.

| paths | penalty | target routes | best target cost | ratio to forced-via |
|---:|---:|---:|---:|---:|
| 20 | 1.0 | 0 | - | - |
| 50 | 1.0 | 1 | 671.00 | 1.503 |
| 100 | 1.0 | 2 | 569.73 | 1.276 |
| 200 | 1.0 | 4 | 569.74 | 1.276 |
| 50 | 0.25 | 0 | - | - |
| 50 | 0.5 | 0 | - | - |
| 50 | 2.0 | 1 | 587.95 | 1.317 |
| 50 | 4.0 | 1 | 583.66 | 1.307 |
| 100 | 0.5 | 1 | 523.69 | 1.173 |

The best tested inclusion requires 100 penalty searches and is still 17.3%
slower than the independently generated forced-via path. Raising `paths`
alone does not converge toward that path: the default-penalty result is
effectively unchanged between 100 and 200.

## Canonical six-direction quality gate

Route support is not defined as edge presence alone. A clean supporting route
must:

1. contain the canonical direction edge;
2. not contain the opposite canonical direction edge for the same section;
3. contain no adjacent `edge -> reverse(edge)` pair.

The existing `paths=20, max-alternatives=20` output has raw support in five of
six directions, but Route1 UP and DOWN are supported by the same 444 routes.
Every one contains the sequence
`261270870#15 -> -261270870#15`. Thus Route1 support is entirely a boundary
turnaround artifact. With the clean definition, the existing output supports
only Route2 UP and both Route316 directions (3/6); Route2 DOWN is absent and
both Route1 directions are pathological-only.

Three full-OD cases are defined in
`reproducibility/config/traffic_simulation/route_generation/marouter_candidate_experiments_v1.json`:

- `SUE_P1_A5`: minimum screening case with one initial shortest path and at
  most four congestion-derived candidates;
- `SUE_P20_A40`: retains 20 penalty candidates but leaves room for 20
  congestion-derived candidates;
- `SUE_P1_A20`: starts from one unpenalized shortest path and lets SUE add
  congestion-derived candidates, avoiding penalty-enumeration artifacts.

The route-generation setting must not be frozen unless all six directions
have clean support, pathological assigned-weight fractions are at most 5%,
the best supporting detour factor is at most 1.5, and the marouter error log is
empty. The audit also requires every aggregate OD relation to appear in the
route output, total output flow to equal input demand, and the sum of assigned
route weights to equal output flow. This prevents an apparently clean network
variant from passing after silently dropping an unreachable TAZ relation.

The v1 cases all fail the gate. In particular, opening `max-alternatives`
from 20 to 40 does not add a Route2 DOWN candidate: `SUE_P20_A40` retains zero
support on `309829214#19`. The smallest fixed-endpoint setting that includes
that edge (`paths=50`, `paths.penalty=2`) is therefore promoted to a full-OD,
one-iteration screening case in
`marouter_candidate_experiments_v2.json`. Keeping this in a new configuration
file preserves the v1 configuration hash recorded by completed runs.

## Reproduction

```bash
PYTHONPATH=05_src .conda/bin/python \
  05_src/traffic_simulation/calibration/diagnose_marouter_route_generation.py \
  fixed-endpoint \
  --config reproducibility/config/traffic_simulation/route_generation/route2_down_fixed_endpoint_probe_v1.json \
  --output reproducibility/outputs/traffic_simulation/routing/20260828_route2_down_fixed_endpoint_probe_v1

PYTHONPATH=05_src .conda/bin/python \
  05_src/traffic_simulation/calibration/diagnose_marouter_route_generation.py \
  run-case \
  --experiment-config reproducibility/config/traffic_simulation/route_generation/marouter_candidate_experiments_v1.json \
  --case-id SUE_P20_A40
```

SUMO embeds a generation timestamp in output comments, so raw file SHA-256
changes across runs. The diagnostic additionally records a semantic XML hash
that excludes comments, formatting whitespace, and attribute order. A separate
replay of the 20-path case reproduced the same semantic hash
`ba5e24c912908911cf4c399c896be2b263025c1aa44ce24190392c7e67d7b6e6`.
