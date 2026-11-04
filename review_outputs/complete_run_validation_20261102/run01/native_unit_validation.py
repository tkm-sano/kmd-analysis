"""Tiny synthetic native unit tests only. Regional gates are never bypassed."""
import os,time,json,xml.etree.ElementTree as ET,collections
from common import *
from contracts import delivery_event,scalar_dc,validate_trace

def timed(cmd,where,timeout=30):
 import subprocess
 where.mkdir(parents=True,exist_ok=True);start=time.monotonic();killed=False
 with (where/'stdout.log').open('w') as out,(where/'stderr.log').open('w') as err:
  p=subprocess.Popen(cmd,cwd=where,stdout=out,stderr=err,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  while True:
   pid,status,ru=os.wait4(p.pid,os.WNOHANG)
   if pid:break
   if time.monotonic()-start>timeout:p.kill();pid,status,ru=os.wait4(p.pid,0);killed=True;break
   time.sleep(.01)
  p.returncode=os.waitstatus_to_exitcode(status)
 result={'argv':cmd,'returncode':p.returncode,'wall_s':time.monotonic()-start,'CPU_s':ru.ru_utime+ru.ru_stime,'max_RSS_bytes':ru.ru_maxrss*1024,'timeout':killed,'scope':'SYNTHETIC_UNIT_PROCESS_NOT_REGIONAL_PILOT'}
 (where/'process.json').write_text(json.dumps(result,indent=2)+'\n');return result
def main():
 protect_previous();unit=O/'NATIVE_UNIT';unit.mkdir(exist_ok=True)
 netconvert=use(R/'.local/sumo-1.24.0/bin/netconvert');sumo=use(R/'.local/sumo-1.24.0/bin/sumo')
 (unit/'nodes.xml').write_text('<nodes><node id="a" x="0" y="0" type="dead_end"/><node id="b" x="1000" y="0" type="dead_end"/></nodes>\n')
 (unit/'edges.xml').write_text('<edges><edge id="e" from="a" to="b" numLanes="1" speed="10"/></edges>\n')
 proc=timed([str(netconvert),'--node-files',str(unit/'nodes.xml'),'--edge-files',str(unit/'edges.xml'),'--output-file',str(unit/'net.xml'),'--no-turnarounds','true'],unit/'netbuild')
 if proc['returncode']!=0:raise RuntimeError('Synthetic netbuild failed')
 # Cases chosen before runs; deadlines fixed independently of measured output.
 specs=[('early',0,120,222,222,20260930),('delayed',120,120,222,222,20260930),('late',240,0,102,222,20260930),('extra_hold',0,120,600,222,20260930),('early_replay',0,120,222,222,20260930),('early_seed1',0,120,222,222,20260931),('early_seed2',0,120,222,222,20260932)]
 records=[];events=[];assertions=[];traces={}
 for label,depart,ready,until,deadline,seed in specs:
  d=unit/label;d.mkdir(exist_ok=True)
  # Same vClass/default distribution as old runs; this is a standalone harness, not fork equivalence.
  (d/'routes.xml').write_text('<routes><vType id="delivery" vClass="delivery"/><vehicle id="unit" type="delivery" depart="'+str(depart)+'" departLane="0" departPos="0" arrivalPos="999" arrivalSpeed="0"><route edges="e"/><stop lane="e_0" endPos="500" duration="102" until="'+str(until)+'" actType="task"/></vehicle></routes>\n')
  cmd=[str(sumo),'-n',str(unit/'net.xml'),'-r',str(d/'routes.xml'),'--step-length','1','--seed',str(seed),'--fcd-output',str(d/'fcd.xml'),'--stop-output',str(d/'stops.xml'),'--tripinfo-output',str(d/'tripinfo.xml'),'--tripinfo-output.write-unfinished','true','--tripinfo-output.write-undeparted','true','--collision-output',str(d/'collisions.xml'),'--time-to-teleport','-1','--precision','9','--end','1000','--no-step-log','true']
  met=timed(cmd,d);trip=ET.parse(d/'tripinfo.xml').getroot().find('tripinfo') if (d/'tripinfo.xml').exists() else None;ss=ET.parse(d/'stops.xml').getroot().find('stopinfo') if (d/'stops.xml').exists() else None
  if trip is None or ss is None:raise RuntimeError('Missing native output '+label)
  tv=[];xy=[]
  for e in ET.parse(d/'fcd.xml').getroot().findall('timestep'):
   v=e.find('vehicle')
   if v is not None:tv.append((float(e.get('time')),float(v.get('speed'))));xy.append(float(v.get('x')))
  vdict=[float(x[1]) for x in tv];t=[x[0] for x in tv];validate_trace(t,vdict,1200,4.5,arrival=float(trip.get('arrival')))
  end=float(ss.get('ended'));resume=next((time for (time,speed) in tv if time>=end and speed>0),None)
  ev=delivery_event(stop_start=float(ss.get('started')),stop_end=end,ready=ready,service=102,deadline=deadline,resume=resume)
  energy=scalar_dc(t,vdict,1200,4.5,arrival=float(trip.get('arrival')))
  stderr=(d/'stderr.log').read_text();collisions=len(ET.parse(d/'collisions.xml').getroot().findall('collision')) if (d/'collisions.xml').exists() else None
  semantic_digest=digest(tv);traces[label]=semantic_digest
  met.update(case=label,series='SYNTHETIC_UNIT',seed=seed,requested_departure_s=depart,observed_departure_s=float(trip.get('depart')),return_s=float(trip.get('arrival')),teleport_warning='teleport' in stderr.lower(),collisions=collisions,routing_failure='no route' in stderr.lower(),missing_intervals=False,trajectory_semantic_sha256=semantic_digest,trajectory_file_sha256=sha(d/'fcd.xml'),net_sha256=sha(unit/'net.xml'),input_sha256=digest({'net':sha(unit/'net.xml'),'routes':sha(d/'routes.xml'),'sumo':sha(sumo),'seed':seed,'step':1,'end':1000}),dc_Wh=energy['DC_Wh'],DC_mass_kg=1200,dc_terminal_gap_s=energy['terminal_gap_s'],dc_terminal_gap_Wh=None,acceptance='UNIT_ONLY_NOT_RESEARCH_DELIVERY_RATE')
  records.append(met);events.append(dict(case=label,**ev,return_s=float(trip.get('arrival'))))
  assertions.append({'case':label,'name':'native_stop_hold_and_departure','passed':met['returncode']==0 and met['observed_departure_s']==depart and met['collisions']==0 and not met['teleport_warning'] and end>=float(ss.get('started'))+102})
 assertions.extend([{'case':'early','name':'early_wait_model_on_time','passed':events[0]['outcome']=='ON_TIME' and events[0]['work_complete_model_s']==222},{'case':'extra_hold','name':'native_end_distinct_from_work','passed':events[3]['stop_end_s']>events[3]['work_complete_model_s']},{'case':'late','name':'late_completion','passed':events[2]['outcome']=='LATE'},{'case':'early_replay','name':'same_seed_same_speed','passed':traces['early']==traces['early_replay']}])
 write('NATIVE_UNIT_PROCESS_RESULTS.json',records);table('NATIVE_UNIT_EVENTS.csv',events);write('NATIVE_UNIT_ASSERTIONS.json',assertions)
 seedvar=len({traces[x] for x in ['early','early_seed1','early_seed2']})
 write('NATIVE_UNIT_SUMMARY.json',{'cases':len(records),'assertions':len(assertions),'failed_assertions':[x for x in assertions if not x['passed']],'same_seed_same_speed':traces['early']==traces['early_replay'],'different_seed_distinct_speed_traces':seedvar,'seed_scope':'Synthetic single-edge default delivery only; no regional replication count inferred','failure_rate_unit_process':sum(x['returncode']!=0 for x in records)/len(records),'regional_representative_runs':0,'regional_wall_CPU_RSS_failure_rate':None})
 save_sources('NATIVE_UNIT_SOURCE_FILES.json');print('native unit',len(records),'cases',seedvar,'distinct seed traces','failed',sum(not x['passed'] for x in assertions))
 if any(not x['passed'] for x in assertions):raise RuntimeError('Native unit contract failures')
if __name__=='__main__':main()
