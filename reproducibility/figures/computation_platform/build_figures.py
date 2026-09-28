"""Read saved artifacts and render documentation only; no routing/solver/backend calls."""
from pathlib import Path
import json,csv,hashlib,xml.etree.ElementTree as ET,math
from fractions import Fraction
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch
R=Path(__file__).resolve().parents[3]; P=R/'reproducibility/outputs/traffic_simulation'; O=Path(__file__).parent
sources={}
def load(path):
 p=R/path if not isinstance(path,Path) else path
 sources[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
pre=P/'r24_first_meaningful_multi_vehicle_preflight/20260927_v1'; inst=load(pre/'SELECTED_INSTANCE.json'); fleets=load(pre/'EXACT_PHYSICAL_FLEETS.json')['all_fleets']; selected=load(pre/'SELECTED_MULTI_VEHICLE_CANDIDATE.json')
base=P/'r24_benchmark_instance_suite/20260915_v1/instances/R24-RND-N002-R01'; meta=load(base/'base_instance.json')
net=P/'attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml'; accepted=load(net.parent/'network_acceptance.json');assert accepted['network_semantic_sha256']==meta['graph_sha256']
sources[str(net.relative_to(R))]=hashlib.sha256(net.read_bytes()).hexdigest()
odpath=base/'od_manifest.csv';sources[str(odpath.relative_to(R))]=hashlib.sha256(odpath.read_bytes()).hexdigest();ods=list(csv.DictReader(odpath.open()));od={(x['origin_id'],x['destination_id']):x for x in ods}
for x in inst['travel']:
 row=od[x['origin'],x['destination']];assert row['validation_status']=='PASS' and row['reachable']=='True';assert Fraction(row['travel_time_s'])==Fraction(x['travel_time_seconds']);assert Fraction(row['distance_m'])==Fraction(x['travel_distance'])
plt.rcParams.update({'font.size':12,'font.family':'DejaVu Sans','svg.fonttype':'none','savefig.facecolor':'white'})
def save(fig,name):
 fig.savefig(O/(name+'.svg'),bbox_inches='tight');fig.savefig(O/(name+'.png'),bbox_inches='tight',dpi=130);plt.close(fig)
 svg=O/(name+'.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
def box(ax,x,y,text,w=.7,h=.065,color='#e8f1f8'):
 ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.009',fc=color,ec='#456174',lw=1.2));ax.text(x,y,text,ha='center',va='center',fontsize=12)
def arrow(ax,x,y,x2,y2):ax.annotate('',(x2,y2),(x,y),arrowprops={'arrowstyle':'->','lw':1.5,'color':'#456174'})
fig,ax=plt.subplots(figsize=(12,12));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');ax.set_title('Computation platform | validated scope and research extensions',fontsize=17,pad=18)
for y,t in [( .94,'Geographic source data / mapped delivery proxies'),(.84,'Accepted directed road network'),(.74,'Saved OD: distance, travel time, reachability'),(.64,'Delivery model: VRPTW / EVRP constraints')]:box(ax,.5,y,t)
for y in [.94,.84,.74]:arrow(ax,.5,y-.037,.5,y-.063)
box(ax,.23,.52,'Classical reference',w=.36);box(ax,.76,.52,'QUBO → fixed QAOA circuit',w=.40);arrow(ax,.4,.605,.23,.56);arrow(ax,.6,.605,.76,.56)
box(ax,.76,.41,'Dense / MPS simulators',w=.40);arrow(ax,.76,.48,.76,.45)
box(ax,.76,.30,'64-shot sampling → decoder',w=.40);arrow(ax,.76,.37,.76,.34)
box(ax,.5,.19,'Independent physical validator');arrow(ax,.23,.48,.23,.23);arrow(ax,.23,.23,.38,.225);arrow(ax,.76,.26,.62,.225)
box(ax,.5,.09,'Routes / time / vehicles → EV operating energy*',color='#fff1d5');arrow(ax,.5,.15,.5,.13)
ax.text(.5,.005,'* EV-energy evaluation is a separate research stage; this smoke test does not establish energy savings.',ha='center',fontsize=10)
save(fig,'computation_platform_overview')
fig,ax=plt.subplots(figsize=(11,13));ax.axis('off');ax.set(xlim=(0,1),ylim=(0,1));ax.set_title('Quantum-circuit branch | N002 / M2 / TW-MODERATE',fontsize=17)
steps=['Delivery problem → variables and physical constraints','QUBO: 20 variables / 72 couplers','Initial state: H on every qubit','Fixed QAOA circuit: p=1 / CX=144 / logical depth=60','Dense statevector  |  Matrix product state (MPS)','State-level validation: Protocol v2 four layers','Separate finite-shot runs: Dense64 + MPS64, seed 20260927','20-bit raw counts → decoder (no repair / no filtering)','Independent physical validator → integrity verdict / STOP']
for i,t in enumerate(steps):
 y=.94-i*.10;box(ax,.5,y,t,w=.94,h=.06)
 if i:arrow(ax,.5,y+.064,.5,y+.033)
ax.text(.5,.035,'Dense and MPS are TWO CLASSICAL SIMULATORS of the same quantum circuit.\nState validation and sampling are separate runs; no state export in sampling.',ha='center',va='center',fontsize=12,color='#943b24')
save(fig,'quantum_computation_pipeline')
# Read stored geometry only. Lane 0 polylines: no shortest-path recomputation.
edges={}
for event,e in ET.iterparse(net,events=('end',)):
 if e.tag=='edge':
  lanes=e.findall('lane')
  if lanes and not e.get('function'):
   lane=min(lanes,key=lambda l:int(l.get('index','0')));shape=lane.get('shape');
   if shape:edges[e.get('id')]=([tuple(map(float,p.split(','))) for p in shape.split()],float(lane.get('length')))
  e.clear()
D=inst['depot']['depot_id']; C=[x['customer_id'] for x in inst['customers']]
def cut(points,start,end,length):
 dist=[0.]
 for a,b in zip(points,points[1:]):dist.append(dist[-1]+math.dist(a,b))
 start=start/length*dist[-1];end=end/length*dist[-1]
 def at(t):
  for i in range(1,len(dist)):
   if dist[i]>=t:
    f=(t-dist[i-1])/(dist[i]-dist[i-1]) if dist[i]>dist[i-1] else 0
    return tuple(points[i-1][j]+f*(points[i][j]-points[i-1][j]) for j in (0,1))
  return points[-1]
 return [at(start)]+[p for p,d in zip(points,dist) if start<d<end]+[at(end)]
route_data=[];allpts=[];stops={}
for customer in C:
 legs=[]
 for pair in [(D,customer),(customer,D)]:
  row=od[pair];seq=json.loads(row['edge_sequence']);assert all(x in edges for x in seq);assert hashlib.sha256((json.dumps(seq,separators=(',',':'))+'\n').encode()).hexdigest()==row['edge_sequence_sha256']
  lines=[]
  for i,eid in enumerate(seq):
   shape,L=edges[eid];line=cut(shape,float(row['origin_offset_m']) if i==0 else 0,float(row['destination_offset_m']) if i==len(seq)-1 else L,L);lines.append(line);allpts+=line
  stops[pair[0]]=lines[0][0];stops[pair[1]]=lines[-1][-1];legs.append(lines)
 route_data.append(legs)
xs,ys=zip(*allpts);bounds=(min(xs)-250,max(xs)+250,min(ys)-250,max(ys)+250)
bg=[pts for pts,L in edges.values() if any(bounds[0]<=x<=bounds[1] and bounds[2]<=y<=bounds[3] for x,y in pts)]
fig,axs=plt.subplots(1,2,figsize=(15,10),sharex=True,sharey=True)
for i,ax in enumerate(axs):
 ax.add_collection(LineCollection(bg,colors='#d6dbe0',linewidths=.45,rasterized=False))
 for j,lines in enumerate(route_data[i]):
  color=['#006b9a','#d45e00'][j];ax.add_collection(LineCollection(lines,colors=color,linewidths=2,label=['Outbound','Return'][j]))
  flat=[(a,b) for line in lines for a,b in zip(line,line[1:]) if math.dist(a,b)>8]
  for a,b in flat[::max(1,len(flat)//12)]:ax.annotate('',b,a,arrowprops={'arrowstyle':'->','color':color,'lw':1.5})
 for k,label in [(D,'Depot'),(C[0],'C1'),(C[1],'C2')]:
  x,y=stops[k];ax.scatter(x,y,s=65,c='black',marker='s' if k==D else 'o',zorder=5);ax.annotate(label,(x,y),xytext=(8,8),textcoords='offset points',fontsize=13,bbox=dict(fc='white',alpha=.85,ec='none'))
 ax.set(xlim=bounds[:2],ylim=bounds[2:],aspect='equal',xlabel='SUMO network x (m)',ylabel='SUMO network y (m)');ax.set_title(f'Vehicle {i+1}: Depot → C{i+1} → Depot');ax.legend(loc='lower left')
fig.suptitle('Saved classical feasible reference — actual directed road geometry',fontsize=18)
fig.text(.5,.015,'C1: bldg-43666 | C2: bldg-67228 | depot: DEP_006\nMapped road access points; gray = network crop. Not a route observed in the 64-shot samples.',ha='center',fontsize=12)
save(fig,'n002_m2_tw_moderate_routes')
# Timeline reads exact saved physical fleet events/returns; no optimization.
valid=next(f for f in fleets if f['feasible']);one=[]
for order in [C,C[::-1]]:one.append(next(f for f in fleets if order in f['routes'] and f['m_used']==1))
fig,ax=plt.subplots(figsize=(15,8));rows=[('Vehicle 1',valid['vehicles'][0]),('Vehicle 2',valid['vehicles'][1])]+[(f'One vehicle: C{1+i} → C{2-i}',next(v for v in f['vehicles'] if v['used'])) for i,f in enumerate(one)]
for idx,(label,v) in enumerate(rows):
 y=3-idx;previous=0
 for ev in v['events']:
  c=next(c for c in inst['customers'] if c['customer_id']==ev['customer']);start=float(Fraction(ev['service_start']));dur=float(c['service_duration']);lo=float(c['earliest_service_time']);hi=float(c['latest_service_time']);ci=C.index(c['customer_id'])+1
  ax.broken_barh([(lo,hi-lo)],(y+.18,.15),facecolors='#a5d6a7');ax.text((lo+hi)/2,y+.38,f'C{ci} TW',ha='center',fontsize=10)
  ax.broken_barh([(previous,start-previous)],(y-.13,.23),facecolors='#70a4ce');ax.broken_barh([(start,dur)],(y-.13,.23),facecolors='#f3bb53');ax.plot(start,y,'o',color='black' if ev['TW'] else '#c62828')
  ax.text(start,y-.32,f'C{ci}: {start:.3f}s'+(' > deadline' if not ev['TW'] else ''),fontsize=10,color='black' if ev['TW'] else '#c62828');previous=start+dur
 ret=float(Fraction(v['return_time']));ax.broken_barh([(previous,ret-previous)],(y-.13,.23),facecolors='#70a4ce');ax.plot(ret,y,'s',color='#334455');ax.text(ret+10,y,f'{ret:.3f}s',va='center',fontsize=10)
 ax.plot(0,y,'>',color='black')
ax.set(yticks=[3,2,1,0],yticklabels=[x[0] for x in rows],xlabel='Elapsed seconds from depot opening / departure t=0',xlim=(-20,1450),ylim=(-.65,3.7));ax.grid(axis='x',alpha=.2);ax.set_title('Two vehicles are required by the frozen service-start time windows',fontsize=17,pad=20)
fig.text(.5,.01,'Blue: road travel | gold: service | green: allowed service-start window | square: depot return\nBoth one-vehicle orders miss the SECOND customer deadline. AT_MOST_M is unchanged.',ha='center',fontsize=12)
save(fig,'n002_m2_tw_moderate_timeline')
(O/'FIGURE_DATA_PROVENANCE.json').write_text(json.dumps({'sources':sources,'geometry':'saved OD edge sequence; lane 0 shape clipped at saved offsets, scaled by declared lane length; no routing computation','route_status':'PASS','time_status':'PASS','background_edges_in_crop':len(bg),'figure_routes':'classical feasible reference, not sampled quantum solutions','science_calls':0,'shots':0},indent=2)+'\n')
print('4 SVG + 4 PNG generated; route and timeline sources verified')
