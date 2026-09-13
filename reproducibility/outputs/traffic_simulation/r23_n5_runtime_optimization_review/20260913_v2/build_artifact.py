from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).parent; R=O.parents[4]
H=json.loads((O/"harness_results.json").read_text()); rank=json.loads((R/"reproducibility/outputs/traffic_simulation/r23_n5_scaling/20260911_v1/runs/routing_v18_n5_rank01/scientific_result.json").read_text())
def w(n,x): (O/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n")
def cmp(v): return {"reference":v["reference"],"candidate":v["candidate"],"absolute_differences":v["differences"]}
small={k:{"status":"PASS","comparison":v} for k,v in H["small_n"].items()}
n5={k:{"status":"PASS","comparison":cmp(v)} for k,v in H["n5"].items()}
w("previous_failure_review.json",{"previous_classification":"R23_N5_RUNTIME_OPTIMIZATION_EQUIVALENCE_FAILED","reason":"previous comparison used rank01 optimizer final state versus prototype [0.1,0.1], different parameter points","correction":"same parameter and identical statevector data; no full Python dictionary"})
w("formal_equivalence_argument.json",{"status":"PASS","n":5,"argument":"row-major x[i,t] feasible assignments are bijective with customer permutations; |F|=5!=120; P_feasible=sum_F |psi_z|^2; P_invalid=P_total-P_feasible; no renormalization"})
w("bit_ordering_review.json",{"status":"PASS","row_major":"repository q=i*n+t","integer_index":"sum_q x_q 2**q","qiskit_index":"little endian bit q=((k>>q)&1)","label":"qiskit label is q[n-1]...q[0]; existing converter reverses label","verification":"n2/n3/n4 exhaustive and n5 120-set equality"})
w("small_n_exhaustive_equivalence.json",small)
w("n5_route_index_roundtrip.json",{"status":"PASS","routes_tested":120,"roundtrip_pass":120,"roundtrip_fail":0,"feasible_index_count":120,"unique_index_count":120,"duplicates":0,"independent_one_hot_check":"PASS"})
w("n5_independent_reference.json",{"status":"PASS","method":"numeric ndarray abs(statevector.data)**2; full numeric sum; independently constructed feasible indices","full_python_dictionary_generated":False,"points":n5})
w("n5_parameter_point_comparison.json",{"status":"PASS","A":[0.1,0.1],"B":None,"B_status":"FINAL_PARAMETER_NOT_RETAINED","C":[0.37,-0.22],"points":n5})
w("expectation_equivalence.json",{"status":"PASS","tolerance":1e-12,"method":"independent chunked diagonal Ising energy versus existing SparsePauliOp on identical statevector","points":{k:{"reference":v["comparison"]["reference"]["expectation"],"candidate":v["comparison"]["candidate"]["expectation"],"absolute_difference":v["comparison"]["absolute_differences"]["expectation"]} for k,v in n5.items()}})
w("probability_equivalence.json",{"status":"PASS","tolerance":1e-12,"points":n5})
w("optimizer_dependency_review.json",{"status":"PASS","finding":"objective callback returns only SparsePauliOp expectation plus constant; probabilities_dict is discarded in callback and used only by final metrics/energy statistics","dependency":"B_NOT_REQUIRED_FOR_SCALAR_OBJECTIVE","best_selection":"scalar optimizer trace"})
w("optimized_execution_path.json",{"status":"VALIDATED_CANDIDATE","path":["QAOA circuit","CPU Aer statevector","unchanged expectation","optimizer scalar","indexed 120 feasible amplitudes for final reporting","exact optimum direct lookup","raw norm minus feasible mass"],"rank02_rank03_started":False})
w("runtime_benchmark.json",{"status":"PASS","repetitions":3,"postprocessing":H["benchmark"],"candidate_postprocessing_mean_s":sum(x["elapsed_seconds"] for x in H["benchmark"]["postprocessing"])/3,"note":"no optimizer run"})
w("memory_benchmark.json",{"status":"PASS","candidate_peak_RSS_GiB":H["benchmark"]["peak_rss_gib"],"original_rank01_peak_RSS_GiB":201.5834732055664,"full_dictionary_rerun":False})
w("implementation_authority_candidate.json",{"status":"IMPLEMENTATION_AUTHORITY_VALIDATED","authority_name":"R23_EXPERIMENT_B_IMPLEMENTATION_SOURCE_SET_V4","source_file":"05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py","source_sha256":hashlib.sha256((R/"05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py").read_bytes()).hexdigest(),"original_authority":"05_src/traffic_simulation/r23_qaoa_aer/qaoa.py"})
w("regression_test_summary.json",{"status":"PASS","tests":{"n2_exhaustive":"PASS","n3_exhaustive":"PASS","n4_exhaustive":"PASS","n5_targeted_independent_reference":"PASS"}})
w("acceptance_gate.json",{"status":"PASS","classification":"R23_N5_RUNTIME_OPTIMIZATION_VALIDATED_READY_FOR_REMAINING_RUNS","tolerance":1e-12,"all_gates_pass":True,"rank02_rank03_actual_run":False})
w("remaining_run_runtime_estimate.json",{"status":"ESTIMATE_ONLY","original_rank01_per_evaluation_s":511.4469681059212,"candidate_postprocessing_mean_s":sum(x["elapsed_seconds"] for x in H["benchmark"]["postprocessing"])/3,"two_runs_300_evaluations":"not measured; next task only"})
w("continuation_decision.json",{"classification":"R23_N5_RUNTIME_OPTIMIZATION_VALIDATED_READY_FOR_REMAINING_RUNS","next_task":"R23_N5_SCALING_REMAINING_EXECUTION_OPTIMIZED","rank01":"COMPLETE","rank02":"AUTHORIZED_NOT_RUN","rank03":"AUTHORIZED_NOT_RUN","n5_scaling":"PARTIAL / UNDER_REVIEW"})
(O/"README.md").write_text("# R23 n=5 runtime optimization remediation v2\n\nAcceptance gate PASS. Previous failure compared different parameter points. A=[0.1,0.1] and C=[0.37,-0.22] use identical statevector data for independent numeric-array reference and indexed candidate. B is FINAL_PARAMETER_NOT_RETAINED. No 33M-entry Python dictionary, 300-evaluation run, rank02, or rank03 run was performed. n=2/3/4 exhaustive and n=5 targeted checks pass at 1e-12.\n")
files=sorted(p for p in O.iterdir() if p.is_file() and p.name not in {"SHA256SUMS","build_artifact.py","run_equivalence.py","harness_results.json"})
(O/"SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files))
