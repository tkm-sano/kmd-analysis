from __future__ import annotations
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'reproducibility/config/research_portal/registry.yml'
STAGE=ROOT/'reproducibility/config/traffic_simulation/research_stage.yml'
OUT=ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260902_profile_difference_v1_2/runs'

def load(path): return yaml.safe_load(path.read_text(encoding='utf-8'))
def latest_run():
    runs=sorted((p for p in OUT.glob('run_*/successor_run_manifest.json')), key=lambda p:p.stat().st_mtime, reverse=True)
    return runs[0] if runs else None
def summary():
    manifest_path=latest_run(); manifest=json.loads(manifest_path.read_text()) if manifest_path else {}
    root=manifest_path.parent if manifest_path else OUT/'run_5'
    inventory=json.loads((root/'formal/blocker_inventory.json').read_text())
    entries=inventory.get('entries',[])
    def group(key):
        result={}
        for item in entries: result[item.get(key) or 'unclassified']=result.get(item.get(key) or 'unclassified',0)+1
        return dict(sorted(result.items(), key=lambda x:(-x[1],x[0])))
    lanes=[x for x in entries if x.get('attribute_name')=='directional_lanes']
    lane_stops=group('stop_code')
    return {'registry':load(REG),'research_stage':load(STAGE),'run':manifest,'blockers':{'total':inventory.get('counts',{}).get('total',len(entries)),'attribute':group('attribute_name'),'evidence':group('root_cause_category'),'root':group('root_cause_category'),'directional_lanes':len(lanes),'lane_stop_codes':{k:v for k,v in lane_stops.items() if k.startswith('LANE_')},'speed':sum(x.get('attribute_name')=='speed' for x in entries),'permission':sum(x.get('attribute_name')=='final_permission' for x in entries),'relation':sum(x.get('attribute_name')=='relation' for x in entries)},'sources':{'manifest':str(manifest_path.relative_to(ROOT)) if manifest_path else None,'blocker_inventory':str((root/'formal/blocker_inventory.json').relative_to(ROOT)),'baseline':'run_4','lane_review':'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260902_profile_difference_v1_2/runs/run_4/directional_lane_review/directional_lane_review.md'}}
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
