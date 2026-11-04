"""Record measured batch evidence before authorizing arithmetic expansion."""
from common import *
def main():
 v=js(O/'VERIFY_BATCH_RUN.json');check('independent batch failures',0,v['failures']);runs={s:js(O/(s+'_BATCH_RUN.json')) for s in ['A','B','C']};projection={}
 for s,r in runs.items():
  check(s+' batch computation failures',0,r['failures'])
  ratio=(2808+9216)/(r['policy_rows']+r['mechanism_arm_rows']) if s=='A' else 36800/r['references'] if s=='B' else (4464+25760+183)/(r['T08_rows']+r['T09_rows']+r['bridge_rows'])
  projection[s]={'measured_wall_s':r['metrics']['wall_s'],'measured_max_RSS_bytes':r['metrics']['max_RSS_bytes'],'linear_row_projection_s':r['metrics']['wall_s']*ratio,'projection_basis':'batch overhead included; workload-dependent estimate, not full-run measurement','conservative_RSS_screen_bytes':4*r['metrics']['max_RSS_bytes']}
 p=js(O/'FROZEN_PROTOCOL.json');estimate=sum(x['linear_row_projection_s'] for x in projection.values());memory=max(x['conservative_RSS_screen_bytes'] for x in projection.values());go=estimate<p['batch_ceiling']['max_projected_full_wall_s'] and memory<p['batch_ceiling']['max_process_RSS_bytes'];files=[]
 for f in sorted((O/'batch').glob('*')):files.append({'path':str(f.relative_to(O)),'sha256':sha(f),'bytes':f.stat().st_size})
 dump('BATCH_ARTIFACT_HASHES.json',files);gate={'full_execution_GO':go,'series_PASS':['A','B','C'] if go else [],'batch_independent_checks':v['checks'],'batch_independent_failures':v['failures'],'projection':projection,'projected_total_wall_s':estimate,'screen_RSS_bytes':memory,'protocol_sha256':sha(O/'FROZEN_PROTOCOL.json'),'primary_code_hashes':{n:sha(O/n) for n in ['common.py','run_a.py','run_b.py','run_c.py','verify_independent.py']},'status':'GO_CONDITIONAL_NUMERIC_ANALYSIS_ONLY' if go else 'STOP_RESOURCE_GATE'};dump('BATCH_GATE.json',gate);print(json.dumps(gate,ensure_ascii=False))
 if not go:raise RuntimeError('Resource gate stop')
if __name__=='__main__':main()
