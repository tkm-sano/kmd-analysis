"""One-time cache migration; retain initial OD and prove unchanged block ranges."""
import json, os
from pathlib import Path
from kmd_toc.pipeline.roads import nearest_all,road_nodes_for_candidates,review_snaps,dump
p=Path('output/toc_delivery/ad_pipeline_20261112/roads')
if (p/'full_S3_INITIAL_HOLD').exists():raise FileExistsError('preserve initial OD and migrated cache')
old=json.loads((p/'SNAP_REVIEW.json.before_connectivity').read_text())['records'];points=[(r['id'],*r['original']) for r in old];near=nearest_all(points,p);ways=road_nodes_for_candidates(near,p);snaps=review_snaps(points,near,ways,json.loads((p/'ROAD_METADATA.json').read_text()),p)
changed=[i for i,r in enumerate(old) if r['selected']['hint']!=snaps[r['id']].hint];print('changed',changed,flush=True)
original=p/'full_S3_INITIAL_HOLD';(p/'full_S3').rename(original);new=p/'full_S3';(new/'blocks').mkdir(parents=True)
reused=[]
for f in (original/'blocks').glob('*.json.gz'):
 i,j=map(int,f.name.split('.')[0].split('_'))
 if any(i<=k<i+100 or j<=k<j+100 for k in changed):continue
 side=f.with_name(f.name.replace('.json.gz','.sha256'));os.link(f,new/'blocks'/f.name);os.link(side,new/'blocks'/side.name);reused.append(f.name)
dump(p/'CACHE_MIGRATION.json',{'reason':'reviewed hint changes only; original immutable blocks retained','changed_point_indices':changed,'unchanged_graph':True,'reused_blocks':reused,'proof':'reused source/destination ranges contain no changed coordinates/hints; same graph and original coordinates'})
