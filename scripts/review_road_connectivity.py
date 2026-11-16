"""One-time forensic recovery of the retained initial disconnected OD.

Normal reproduction uses the reviewed snap evidence and build_common_road_od.
Refuse to overwrite a completed connectivity review.
"""
import json, numpy as np
from pathlib import Path
from urllib.parse import urlencode
from kmd_toc.pipeline.roads import get,dump
p=Path('output/toc_delivery/ad_pipeline_20261112/roads')
if (p/'CONNECTIVITY_REVIEW.json').exists():raise FileExistsError('preserve existing review')
records=json.loads((p/'SNAP_REVIEW.json').read_text())['records'];r=np.load(p/'full_S3/reachable.npy',mmap_mode='r');bad=sorted(set(np.where(~r[0])[0])|set(np.where(~r[:,0])[0]));depot=records[0]
log={'allowed_hints':{},'records':[],'scope':'bidirectional depot connectivity, no demand or 100m threshold change'}
for i in bad:
 a=records[i];sid=a['id'];lon,lat=a['original'];raw=get(f'http://127.0.0.1:5000/nearest/v1/driving/{lon},{lat}?number=100');dump(p/'nearest'/(sid+'.expanded.json'),raw);allowed=[];checks=[]
 for c in raw['waypoints']:
  if c['distance']>100:continue
  opts=[depot['selected'],c];coords=';'.join(','.join(map(str,x['original'])) for x in [depot,a]);u=f'http://127.0.0.1:5000/table/v1/driving/{coords}?'+urlencode({'hints':';'.join(x['hint'] for x in opts),'annotations':'distance,duration'})
  q=get(u);ok=q.get('code')=='Ok' and all(q['distances'][j][1-j] is not None for j in [0,1]);checks.append({'hint':c['hint'],'distance_m':c['distance'],'connected':ok,'response':q})
  if ok:allowed.append(c['hint'])
 log['allowed_hints'][sid]=allowed;log['records'].append({'id':sid,'checks':checks});print(sid,'connected candidates',len(allowed),flush=True)
dump(p/'CONNECTIVITY_REVIEW.json',log)
for name in ['SNAP_REVIEW.json','SNAP_ROAD_WAYS.json']:
 (p/name).rename(p/(name+'.before_connectivity'))
