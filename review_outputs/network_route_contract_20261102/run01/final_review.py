"""Separate readback of outputs, fixed references and source preservation, no solver."""
from evidence import *
import collections,difflib,xml.etree.ElementTree as ET
def main():
 start=time.monotonic();checks=[]
 def ck(label,expected,actual):checks.append({'check':label,'expected':canon(expected),'actual':canon(actual),'status':'PASS' if expected==actual else 'FAIL'})
 rr=rows(O/'B_FINAL_RECOVERY_CLASSIFICATION.csv');links=rows(P2/'B_PLAN_RUN_LINKS.csv');by={x['candidate_id']:x for x in rr}
 ck('candidate PK and count',4987,len(by));ck('plan references',36800,len(links));ck('unlinked references',0,sum(x['candidate_id'] not in by for x in links))
 counts=collections.Counter(x['recovery_class'] for x in rr);ck('exclusive classification',{'ORIGINAL_RECOVERED':2323,'ALTERNATIVE_RECONSTRUCTED':2,'PARTIAL':2662},dict(counts))
 ck('strict original coverage',24333,sum(by[x['candidate_id']]['recovery_class']=='ORIGINAL_RECOVERED' for x in links));ck('physical input coverage',24493,sum(bool(by[x['candidate_id']]['available_physical_input_id']) for x in links))
 ck('no incomplete input ID',0,sum(bool(x['complete_input_id'] or x['available_physical_input_id']) for x in rr if x['recovery_class']=='PARTIAL'))
 ck('all network blocked',4987,sum(x['network_status']=='BLOCKED_BY_NETWORK' for x in rr))
 data=[]
 with use(O/'RECOVERED_RUN_INPUTS.jsonl').open() as f:
  for line in f:data.append(json.loads(line))
 ck('complete payload count',2323,len(data));ck('all payload digests correct',2323,sum(x['complete_input_id']=='RECOVERY-RUN-'+hashlib.sha256(json.dumps(x['payload'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() for x in data));ck('unique complete payload IDs',2323,len({x['complete_input_id'] for x in data}))
 ck('no complete payload marked prior native execution',0,sum(x['whole_B_run_previously_executed'] for x in data))
 end=read(P2/'ENDPOINTS_USED.json');diff=0
 for k,a in end.items():
  if k.endswith('|ORIGIN') and k[:-7]+'|DESTINATION' in end:
   b=end[k[:-7]+'|DESTINATION'];diff+=tuple(a.get(x) for x in ['edge','lane','position'])!=tuple(b.get(x) for x in ['edge','lane','position'])
 ck('origin/destination endpoint identity for stop stitching',0,diff)
 # Independent edge-adjacency and monotone stop-order screening (not native lane feasibility).
 needed={tuple(v) for x in data for v in zip(x['payload']['road_edges'],x['payload']['road_edges'][1:])};wanted={e for pair in needed for e in pair};edges={};pairs=set()
 for _,e in ET.iterparse(use(NET),events=['end']):
  if e.tag=='edge':
   if e.get('id') in wanted:
    lanes=[]
    for z in e.findall('lane'):
     allow=set(z.get('allow','').split());deny=set(z.get('disallow','').split())
     if (not allow or 'delivery' in allow or 'all' in allow) and 'delivery' not in deny and 'all' not in deny:lanes.append(z.get('id'))
    edges[e.get('id')]=lanes
   e.clear()
  elif e.tag=='connection':
   key=(e.get('from'),e.get('to'))
   if key in needed:pairs.add(key)
   e.clear()
  elif e.tag in ['junction','tlLogic']:e.clear()
 ck('missing directed external adjacency',0,len(needed-pairs));ck('edges without delivery-permitted lane',0,sum(not edges.get(e) for e in wanted))
 stopbad=[]
 for x in data:
  p=x['payload'];path=p['road_edges'];ix=0;lastpos=float(p['vehicle']['departPos'])
  for stop in p['stops']:
   edge=stop['lane'].rsplit('_',1)[0];pos=float(stop['endPos'])
   while ix<len(path) and (path[ix]!=edge or pos<lastpos):ix+=1;lastpos=-float('inf')
   if ix==len(path) or stop['lane'] not in edges.get(edge,[]):stopbad.append(x['candidate_id']);break
   lastpos=pos
 ck('stop edge/lane/order screen failures',0,len(stopbad))
 known=rows(O/'KNOWN37_IDENTITY_COMPARISON.csv');ck('retained prior known controls',37,len(known));dist=rows(O/'KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.csv');ck('raw native control denominator',134,len(dist));ck('raw native retained explicit HOLD',1,sum(x['status'].startswith('HOLD') for x in dist));ck('raw native distance failures',0,sum(x['status']=='FAIL' for x in dist))
 tests=rows(O/'MEASUREMENT_TEST_CASES.csv');ck('new unit fixture count',35,len(tests));ck('new unit fixture failures',0,sum(x['status']!='PASS' for x in tests));sat=rows(O/'COLLISION_BODY_OVERLAP_INDEPENDENT.csv');ck('collision overlap evidence rows',183,len(sat))
 # Check all recorded sources again, including independently pinned prior artifacts.
 sources_all={}
 for p in sorted(O.glob('*SOURCES.json')):
  for x in json.loads(p.read_text()):
   if not Path(x['path']).is_relative_to(O):sources_all[x['path']]=x['sha256']
 for root,name in [(P1,'REVIEW_ARTIFACT_MANIFEST.json'),(P2,'ARTIFACT_MANIFEST.json')]:
  for x in json.loads((root/name).read_text()):sources_all[str(root/x['path'])]=x['sha256']
 preserved=[]
 for path,h in sorted(sources_all.items()):
  p=Path(path);actual=sha(p) if p.is_file() else None;preserved.append({'path':path,'before_sha256':h,'after_sha256':actual,'status':'PASS' if actual==h else 'FAIL'})
 table('FINAL_SOURCE_HASH_CHECK.csv',preserved);ck('preservation hash failures',0,sum(x['status']!='PASS' for x in preserved))
 diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True);(O/'GIT_DIFF_FINAL.patch').write_text(diff);ck('tracked git diff empty','',diff)
 (O/'GIT_STATUS_FINAL.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=R,text=True))
 rev=O/'revisions'
 for old,new,dest in [(rev/'review_recovery_before_missing_control.py',O/'review_recovery.py','review_recovery.diff'),(rev/'KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.before.csv',O/'KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.csv','control_ledger.diff')]:
  (rev/dest).write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new))))
 table('FINAL_REVIEW_CHECKS.csv',checks);summary={'checks':len(checks),'passed':sum(x['status']=='PASS' for x in checks),'failed':[x['check'] for x in checks if x['status']=='FAIL'],'source_files_rehashed':len(preserved),'source_hash_failures':sum(x['status']!='PASS' for x in preserved),'tracked_diff_bytes':len(diff.encode()),'new_native_executions':0,'metrics':metrics(start)};write('FINAL_REVIEW.json',summary);print(canon(summary))
 if summary['failed']:raise RuntimeError('Final independent review failure; retain evidence')
if __name__=='__main__':main()
