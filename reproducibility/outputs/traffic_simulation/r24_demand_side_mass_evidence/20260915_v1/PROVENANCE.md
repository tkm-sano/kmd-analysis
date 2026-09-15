# Provenance and execution boundary

Date: 2026-09-15 JST  
Branch: `main`  
Start SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b`  
End SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b` (no commit)

## Repository authority inspected

- `r24_gate_c_capacity_dimension/20260915_v1/R24_GATE_C_CAPACITY_DIMENSION_DECISION.md`
- `r24_gate_c_capacity_dimension/20260915_v1/GATE_D_HANDOFF.md`
- `r24_gate_b_vehicle_class/20260915_v1/R24_GATE_B_VEHICLE_CLASS_DECISION.md`
- `r24_gate_b_vehicle_class/20260915_v1/GATE_C_HANDOFF.md`
- `r24_gate_a_minimal_benchmark_abstraction/20260915_v1/`
- `r24_planning_horizon_decision/20260915_v1/R24_PLANNING_HORIZON_DECISION.md`
- `end_to_end_workflow_feasibility_audit/20260914_v2/END_TO_END_WORKFLOW_AUTHORITY.md`
- existing parcel-weight authority reviews/registers found under `reproducibility/outputs/traffic_simulation/`
- frozen demand snapshot metadata and building aggregate evidence referenced by Gate C

## External sources reviewed

Japanese government/public statistics:

- MLIT Logistics Census overview: https://www.mlit.go.jp/statistics/details/t-other-2_tk_000197.html
- MLIT 11th Logistics Census result release: https://www.mlit.go.jp/report/press/tokatsu01_hh_000697.html
- e-Stat Logistics Census tables: https://www.e-stat.go.jp/stat-search/files?toukei=00600620
- e-Stat secondary-use process: https://www.e-stat.go.jp/microdata/data-use
- MLIT Domestic Air Cargo Flow Survey overview/results/reference: https://www.mlit.go.jp/statistics/details/t-other-2_tk_000278.html ; https://www.mlit.go.jp/statistics/details/t-other-2_tk_000284.html ; https://www.mlit.go.jp/statistics/details/t-other-2_tk_000281.html
- FY2024 air-cargo report/summary: https://www.mlit.go.jp/koku/content/001896775.pdf
- FY2020 and FY2007 air-cargo reports: https://www.mlit.go.jp/statistics/details/content/001874283.pdf ; https://www.mlit.go.jp/statistics/details/content/001874296.pdf
- MLIT Ogawa demonstration: https://www.mlit.go.jp/common/001133514.pdf
- MLIT parcel-volume statistics: https://www.mlit.go.jp/report/press/jidosha04_hh_000341.html

Carrier/public sources:

- Yamato Transport: https://www.kuronekoyamato.co.jp/ytc/customer/send/services/takkyubin/
- Sagawa Express: https://www.sagawa-exp.co.jp/service/takuhai/
- Japan Post: https://www.post.japanpost.jp/service/you_pack/ ; https://www.post.japanpost.jp/service/send/domestic/delivery/yu-packet/

Research sources:

- Roll-box-pallet study: https://www.jstage.jst.go.jp/article/josh/19/1/19_JOSH-2025-0010-CHO/_html/-char/ja
- SIP-adus report: https://www.sip-adus.go.jp/rd/rddata/rd04/213.pdf
- parcel shock study: https://www.jstage.jst.go.jp/article/spstj/7/1/7_23/_article/-char/ja
- IPC cross-border survey entry: https://www.ipc.be/services/markets-and-regulations/cross-border-shopper-survey

## Search and inference boundary

A bounded targeted search was conducted across MLIT/e-Stat, the three major carriers' official sites, J-STAGE and general scholarly web indexing. Search terms combined 宅配便/EC/home delivery/parcel with 重量/分布/個票/実測. No accessible source meeting all acceptance criteria was found. This is evidence insufficiency for the reviewed authority set, not proof that no confidential, licensed or future dataset exists.

Numerical ratios described as implied values are arithmetic summaries of source aggregates, not source-provided parcel distributions. No value was adopted into the model.

## Execution record

- tracked changes at start: `NONE`
- tracked changes at end: `NONE` (output path is ignored and uncommitted)
- scientific/data mutation: `NONE`
- demand generation/model revision: `NONE`
- parcel mass generation: `NONE`
- `q_i/Q/m` definition or freeze: `NONE`
- eligible-population generation: `NONE`
- routing revalidation: `NONE`
- instance generation: `NONE`
- MILP/QUBO/QAOA/Aer/optimization: `NONE`
- output hashes: `SHA256SUMS.txt` (manifest excludes itself)
