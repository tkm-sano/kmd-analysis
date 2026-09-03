from __future__ import annotations
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / 'reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml'
MAP = ROOT / 'reproducibility/config/research_portal/research_map_v1.yml'

def load(path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))

def summary():
    authority, research_map = load(AUTH), load(MAP)
    a = authority['accepted_run']
    acceptance = json.loads((ROOT / a['acceptance_artifact']).read_text())
    quality = json.loads((ROOT / a['provenance_accounting']).read_text())
    complete = {'external_data','baseline_demand','requests','stops','structural_network','formal_completion','sumo_materialization','network_validation','stop_mapping','routeability','formal_network_acceptance'}
    network_trace = {
        'decision': authority['decision']['path'],
        'specification': authority['specification']['path'],
        'registry_schema': [authority['registry']['path'], authority['schema']['policy_path'], authority['schema']['record_path']],
        'implementation': '05_src/traffic_simulation/network/execute_three_tier_completion_streaming.py',
        'validation': a['acceptance_artifact'],
        'canonical_artifact': a['network_file'],
        'result': 'FORMAL_NETWORK_ACCEPTED = true',
        'known_limitations': acceptance['known_limitations'],
        'next_dependency': 'routing_baseline'
    }
    nodes=[]
    for node in research_map['implementation_nodes']:
        item=dict(node)
        item['status']='COMPLETE' if item['id'] in complete else 'NEXT' if item['id']=='routing_baseline' else 'CURRENT' if item['id']=='research_question' else 'FUTURE'
        item['detail']=network_trace if item['id'] in {'formal_completion','sumo_materialization','network_validation','stop_mapping','routeability','formal_network_acceptance'} else {'next_dependency': next((e['to'] for e in research_map['implementation_edges'] if e['from']==item['id']), None)}
        nodes.append(item)
    conceptual=[]
    for node in research_map['conceptual_nodes']:
        item=dict(node); item['status']='CURRENT' if item['id'] in {'quantum','mobility'} else 'FUTURE'; conceptual.append(item)
    return {
        'research_question': research_map['research_question'],
        'current_position': {'current_stage':'Routing Baseline','previous_milestone':'M1 Network Ready — DONE','next_major_milestone':'M2 Routing Ready'},
        'maps': {'conceptual':{'nodes':conceptual,'edges':research_map['conceptual_edges']},'implementation':{'nodes':nodes,'edges':research_map['implementation_edges']}},
        'accepted_network': {'network_id':a['network_id'],'run_id':a['run_id'],'network_sha256':a['network_sha256'],'sumo_version':acceptance['sumo_version'],'decision_id':authority['decision']['id']},
        'formal': {'status':'COMPLETE','blocker':acceptance['three_tier_population']['unresolved'],'accepted':acceptance['FORMAL_NETWORK_ACCEPTED']},
        'validation': acceptance['validation'], 'mapping': acceptance['mapping'], 'tiers': acceptance['three_tier_population'], 'confidence': quality.get('confidence',{}),
        'historical': {'strict_v17_blockers':115935,'run_ids':['run_4','run_5','run_6'],'status':'HISTORICAL'}, 'superseded':authority['superseded_decision'],
        'limitations': acceptance['known_limitations'], 'sources':authority
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/state': self.send_json(summary()); return
        path = ROOT/'research_portal'/'index.html' if self.path == '/' else ROOT/'research_portal'/self.path.lstrip('/')
        if path.is_file():
            data=path.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8' if path.suffix=='.html' else 'text/css' if path.suffix=='.css' else 'text/javascript'); self.end_headers(); self.wfile.write(data); return
        self.send_error(404)
    def send_json(self,value):
        data=json.dumps(value,ensure_ascii=False).encode(); self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(data)

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1',int(os.getenv('PORT','8876'))),Handler).serve_forever()
