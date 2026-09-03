from pathlib import Path
import importlib.util, json, yaml

ROOT=Path(__file__).resolve().parents[3]
MAP=ROOT/'reproducibility/config/research_portal/research_map_v1.yml'

def main():
    m=yaml.safe_load(MAP.read_text()); ids={n['id'] for n in m['implementation_nodes']}
    assert m['current_position']['current_stage']=='routing_baseline'
    assert m['current_position']['current_milestone']=='M1 Network Ready'
    assert m['current_position']['milestone_status']=='DONE'
    assert m['current_position']['immediate_next_task']=='Define routing scope for delivery instances'
    assert all(e['from'] in ids and e['to'] in ids for e in m['implementation_edges'])
    assert {'produces','depends on','parameterizes','validates','feeds into','compares with','interprets'} <= {e['relation'] for e in m['implementation_edges']+m['conceptual_edges']}
    spec=importlib.util.spec_from_file_location('portal',ROOT/'research_portal/serve.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); s=mod.summary()
    by_id={n['id']:n for n in s['maps']['implementation']['nodes']}
    assert s['formal']['accepted'] is True and s['formal']['blocker']==0
    assert s['accepted_network']['network_sha256']=='4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f'
    assert all(by_id[x]['status']=='COMPLETE' for x in ['baseline_demand','requests','stops','structural_network','formal_completion','sumo_materialization','network_validation','stop_mapping','routeability','formal_network_acceptance'])
    assert by_id['routing_baseline']['status']=='NEXT' and by_id['classical_optimization']['status']=='FUTURE'
    assert all(by_id[x]['status']=='FUTURE' for x in ['future_demand_parameterization','common_instance','qubo_formulation','qubo_validation','qaoa','quantum_comparison','delivery_simulation','fulfillment_evaluation','planning_business_interpretation','future_society_interpretation','sensitivity_robustness','reproducibility_freeze'])
    assert s['validation']['routeability_gate']['routeable']==100 and s['mapping']['mapping_rate']==1.0
    print(json.dumps({'research_map':'passed','nodes':len(ids),'current_stage':'Routing Baseline','formal_network_accepted':True},sort_keys=True))

if __name__=='__main__': main()
