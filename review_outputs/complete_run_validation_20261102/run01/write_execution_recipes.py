"""Concrete per-run files for review. This program never launches SUMO."""
from common import *
import json
def main():
 gate=read(O/'ROAD_AND_EXECUTION_GATE.json');env=read(O/'ENVIRONMENT.json');types=use(L/SC/'matched_classical_trajectories_20261007/types.xml');(O/'types.xml').write_bytes(types.read_bytes());recipes=[]
 with (O/'RUN_INPUTS.jsonl').open() as h:
  for line in h:
   x=json.loads(line)
   if not x['run_id']:continue
   cid=x['candidate_id'];p=x['payload'];directory=O/('A_MECHANISM_INPUTS' if cid.startswith('AMECH') else 'A_INPUTS' if cid.startswith('D12') else 'B_INPUTS')/cid
   assert sha(O/'types.xml')==p['vtype_sha256']
   tsv=directory/'one_run.tsv';tsv.write_text(str(directory)+' '+str(p['simulation']['end_s'])+'\n')
   argv=[str(resolve(L/SC/'canonical_delivery_trajectories_20261006/canonical_sumo_fork')),str(NET),str(O/'types.xml'),str(tsv),'1']
   recipes.append({'candidate_id':cid,'run_id':x['run_id'],'vehicle_xml':str(directory/'vehicle.xml'),'vehicle_xml_sha256':sha(directory/'vehicle.xml'),'single_run_list':str(tsv),'single_run_list_sha256':sha(tsv),'argv_candidate':argv,'environment_sha256':env['fingerprint'],'allow_execution':False,'gate':gate['representative_regional_execution'],'expected_outputs':['fcd.xml.gz','stops.xml','tripinfo.xml','execution.json','stderr.log'],'scope':'INPUT_REVIEW_ONLY_NO_PROCESS_STARTED','warnings':['Dedicated fork hardcodes parent /tmp outputs; cold build/ABI and isolated output handling must be accepted before execution','Current output path is unique to this review; never point runner to saved originals','Real work-start/completion event instrumentation remains HOLD']})
 write('EXECUTION_RECIPES.json',recipes);save_sources('RECIPE_SOURCE_FILES.json');print('Prepared',len(recipes),'single-run recipes, executed 0')
if __name__=='__main__':main()
