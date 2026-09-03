from __future__ import annotations
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
AUTH=ROOT/'reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml'
PIPE=ROOT/'reproducibility/config/traffic_simulation/network_completion_pipeline_v17.yml'

def load(path): return yaml.safe_load(path.read_text(encoding='utf-8'))
def summary():
    authority=load(AUTH); pipeline=load(PIPE); a=authority['accepted_run']; acceptance=json.loads((ROOT/a['acceptance_artifact']).read_text()); q=json.loads((ROOT/authority['accepted_run']['provenance_accounting']).read_text())
    stages=[{'id':'source','label':'Source Data','status':'completed'},{'id':'structural','label':'Structural Network','status':'completed'},{'id':'formal','label':'Three-tier Formal Completion','status':'completed'},{'id':'sumo','label':'SUMO Materialization','status':'completed'},{'id':'validation','label':'Network Validation','status':'completed'},{'id':'mapping','label':'Stop Mapping','status':'completed'},{'id':'routeability','label':'Routeability Validation','status':'completed'},{'id':'acceptance','label':'Formal Network Acceptance','status':'completed'},{'id':'routing','label':'Routing Baseline','status':'planned'},{'id':'optimization','label':'Optimization','status':'planned'}]
    return {'authority':authority,'accepted_network':{'network_id':a['network_id'],'run_id':a['run_id'],'network_sha256':a['network_sha256'],'sumo_version':acceptance['sumo_version'],'decision_id':authority['decision']['id']},'formal':{'status':'COMPLETE','blocker':acceptance['three_tier_population']['unresolved'],'accepted':acceptance['FORMAL_NETWORK_ACCEPTED']},'validation':acceptance['validation'],'mapping':acceptance['mapping'],'tiers':acceptance['three_tier_population'],'confidence':q.get('confidence',{}),'pipeline':stages,'historical':{'strict_v17_blockers':115935,'run_ids':['run_4','run_5','run_6'],'status':'HISTORICAL'},'superseded':authority['superseded_decision'],'limitations':acceptance['known_limitations'],'next_stage':'Routing Baseline','sources':authority}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/api/state': self.send_json(summary()); return
        path=(ROOT/'research_portal'/'index.html') if self.path=='/' else ROOT/'research_portal'/self.path.lstrip('/')
        if path.is_file():
            data=path.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8' if path.suffix=='.html' else 'text/css' if path.suffix=='.css' else 'text/javascript'); self.end_headers(); self.wfile.write(data); return
        self.send_error(404)
    def send_json(self,value):
        data=json.dumps(value,ensure_ascii=False).encode(); self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(data)
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',int(os.getenv('PORT','8876'))),Handler).serve_forever()
