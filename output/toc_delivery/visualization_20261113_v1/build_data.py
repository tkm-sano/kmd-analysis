"""Build visualization data and independent checks from saved experiments only."""
import csv
import gzip
import hashlib
import json
import math
import resource
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from pyproj import Transformer
from data_access import ROOT,REPO,SOURCE,SavedRoads,read_json

MANIFEST={}


def register(p,role):
    p=Path(p); key=str(p.relative_to(REPO))
    if key not in MANIFEST:MANIFEST[key]={'role':role,'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()}


def save_json(p,data):Path(p).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')


def save_csv(name,rows):
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def describe(a,scale=1):
    q=np.quantile(a,[0,.25,.5,.75,1])/scale
    counts,edges=np.histogram(a/scale,bins=80)
    return {'n':int(a.size),'min':float(q[0]),'q25':float(q[1]),'median':float(q[2]),'q75':float(q[3]),'max':float(q[4]),
            'mean':float(a.mean()/scale),'hist':{'counts':counts.tolist(),'edges':edges.tolist()}}


def boundary():
    p=REPO/'03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML/N03-20260101_13.geojson';register(p,'retained MLIT N03 administrative boundary, source EPSG:6668')
    raw=read_json(p);features=[x for x in raw['features'] if x['properties'].get('N03_007')=='13111']
    transform=Transformer.from_crs(6668,4326,always_xy=True)
    def convert(a):
        if isinstance(a[0],(float,int)):
            x,y=transform.transform(a[0],a[1]);return [x,y]
        return [convert(x) for x in a]
    for f in features:f['geometry']['coordinates']=convert(f['geometry']['coordinates'])
    result={'type':'FeatureCollection','features':features,'source_crs':'EPSG:6668','display_crs':'EPSG:4326',
            'transformation':transform.description,'source':str(p.relative_to(REPO))}
    save_json(ROOT/'data/boundary.geojson',result);return result


def main():
    begin=time.perf_counter();roads=SavedRoads();odrows=[];scenarios={};stats={};arcrows=[];triprows=[]
    for case,n in [('S1',1000),('S2',2000),('S3',4000)]:
        inp=roads.inputs[case];base=SOURCE/'roads/inputs'/case;manifest=read_json(base/'od/manifest.json')
        for p in [base/'input.json',*list((base/'od').glob('*'))]:register(p,'adopted Route v2 '+case+' common input/OD')
        for name in ['CONTEXT.json','BLOCK_MANIFEST.json']:register(SOURCE/'roads'/('route_'+case)/name,'retained Route cache context/hash manifest for lazy geometry access')
        d,t,r=(roads.ods[case][k] for k in ['distance_m','duration_s','reachable']);m=len(d)
        mask=~np.eye(m,dtype=bool)
        dstats=describe(d[mask],1000);tstats=describe(t[mask],60)
        upper=np.triu_indices(m,k=1);delta=d[upper]-d.T[upper];astats=describe(delta,1000)
        # Deterministic evenly spaced row-major OFF-diagonal pairs, no RNG.
        sample_flat=np.linspace(0,m*(m-1)-1,2500,dtype=np.int64);ii=sample_flat//(m-1);jj=sample_flat%(m-1);jj=jj+(jj>=ii)
        sample=np.column_stack((np.asarray(d[ii,jj])/1000,np.asarray(t[ii,jj])/60)).tolist()
        asym_count=int(np.count_nonzero(d!=d.T));time_asym=int(np.count_nonzero(t!=t.T))
        metadata=manifest.get('metadata',{})
        quality={'case':case,'N':n,'points_including_depot':m,'total_pairs':m*m,'off_diagonal_pairs':m*(m-1),
            'distance_nonfinite':int((~np.isfinite(d)).sum()),'time_nonfinite':int((~np.isfinite(t)).sum()),
            'negative_distance':int((d<0).sum()),'negative_time':int((t<0).sum()),'unreachable_pairs':int((~r).sum()),
            'unreachable_origin_points':int((~r).any(axis=1).sum()),'diagonal_nonzero_distance':int(np.count_nonzero(d.diagonal())),
            'diagonal_nonzero_time':int(np.count_nonzero(t.diagonal())),'asymmetric_distance_cells':asym_count,'asymmetric_time_cells':time_asym,
            'OD_hash':inp['od_hash'],'route_service':metadata.get('matrix_service'),
            'table_distances_used':metadata.get('table_distances_used'),'shape_ok':d.shape==t.shape==r.shape==(n+1,n+1)}
        quality['passed']=bool(quality['shape_ok'] and not any(quality[k] for k in ['distance_nonfinite','time_nonfinite','negative_distance','negative_time','unreachable_pairs','diagonal_nonzero_distance','diagonal_nonzero_time']) and metadata.get('table_distances_used') is False and 'Route' in metadata.get('matrix_service',''))
        odrows.append(quality);stats[case]={'quality':quality,'distance_km':dstats,'duration_min':tstats,'signed_asymmetry_km':astats,
            'scatter':sample,'scatter_sample_rule':'2500 evenly spaced row-major off-diagonal indices; all histograms/quantiles use ALL off-diagonal pairs'}
        points=[]
        for index,x in enumerate([inp['depot'],*inp['stops']]):
            s=x['snap'];points.append({'id':x.get('stop_id',x.get('depot_id')),'index':index,'lon':x['longitude'],'lat':x['latitude'],
                'demand':x.get('demand',0),'snap_lon':s['longitude'],'snap_lat':s['latitude'],'snap_distance_m':s['distance_m'],
                'node_ids':s['node_ids'],'node_coordinates':[roads.node_coordinates([nid])[0].tolist() if nid else None for nid in s['node_ids']],
                'node_coordinate_note':'0 is an unspecified endpoint ID in the saved snap; no fabricated coordinate' if 0 in s['node_ids'] else '',
                'graph_id':s['graph_id']})
        scenarios[case]={'N':n,'V':len(inp['vehicles']),'B':len(inp['berths']),'points':points,'OD_hash':inp['od_hash'],
            'input_hash':inp['problem_hash'],'road_version':metadata.get('road_version'),'has_delivery_plans':case=='S1'}
        print('OD statistics',case,m*m,'pairs, passed',quality['passed'],flush=True)
    geo=boundary();plans={};stage=[];positions={x['id']:i for i,x in enumerate(scenarios['S1']['points'])};d=roads.ods['S1']['distance_m'];t=roads.ods['S1']['duration_s']
    inp=roads.inputs['S1'];demand={s['stop_id']:s['demand'] for s in inp['stops']};vehicles={v['vehicle_id']:v for v in inp['vehicles']}
    for method in ['B','C','D']:
        condition=method+'_primaryD_epsW_1';result_path=SOURCE/'experiments/S1'/condition/'result.json';result=read_json(result_path);register(result_path,'S1 '+method+' saved result')
        register(result_path.with_name('plan.json'),'S1 '+method+' saved plan');plan=result['plan'];by_vehicle={};visits_all=[];items=[];checks=[]
        for trip in plan['trips']:
            path=SOURCE/'FULL_TOUR_ROUTE_AUDIT'/f"{condition}_{trip['vehicle_id']}_{trip['trip_no']}.json.gz";register(path,'retained full-tour Route path annotation')
            raw=json.loads(gzip.decompress(path.read_bytes()));nodes=[0,*[positions[v['stop_id']] for v in trip['visits']],0]
            length=Decimal(0);clock=trip['departure_s'];geom=[];max_geo=0.;max_dm=0.;max_dt=0.;trip_checks=[]
            if len(raw['routes'][0]['legs'])!=len(nodes)-1:raise ValueError('LEG_COUNT')
            for k,(i,j,leg) in enumerate(zip(nodes,nodes[1:],raw['routes'][0]['legs'])):
                length+=Decimal(str(float(d[i,j])));dm=leg['distance']-float(d[i,j]);dt=leg['duration']-float(t[i,j]);max_dm=max(max_dm,abs(dm));max_dt=max(max_dt,abs(dt))
                coords,gcheck=roads.shape(leg['annotation']['nodes'],raw['waypoints'][k]['location'],raw['waypoints'][k+1]['location'],leg['distance'])
                max_geo=max(max_geo,abs(gcheck['delta_m']));geom.extend(coords if not geom else coords[1:] if coords[0]==geom[-1] else coords)
                arcrows.append({'method':method,'vehicle_id':trip['vehicle_id'],'trip_no':trip['trip_no'],'leg':k,'from_index':i,'to_index':j,
                    'OD_distance_m':float(d[i,j]),'Route_distance_m':leg['distance'],'delta_distance_m':dm,'delta_duration_s':dt,
                    'geometry_length_m':gcheck['length_m'],'geometry_delta_m':gcheck['delta_m'],'node_count':len(leg['annotation']['nodes']),
                    'geometry_passed':gcheck['passed'],'OD_passed':abs(dm)<=.25 and abs(dt)<=.25})
                trip_checks.append(gcheck['passed'] and abs(dm)<=.25 and abs(dt)<=.25)
                clock+=math.ceil(float(t[i,j]))
                if k<len(trip['visits']):
                    v=trip['visits'][k]
                    if (v['arrival_s'],v['service_start_s'],v['service_end_s'])!=(clock,clock,clock+120):checks.append('VISIT_TIME')
                    clock+=120
            ids=[v['stop_id'] for v in trip['visits']];visits_all.extend(ids);quantity=sum(demand[x] for x in ids)
            expected_ready=vehicles[trip['vehicle_id']]['first_ready_s'] if trip['trip_no']==1 else by_vehicle[trip['vehicle_id']][-1]['return_s']
            if trip['ready_s']!=expected_ready:checks.append('READY')
            if trip['load_start_s']<trip['ready_s']:checks.append('NEGATIVE_WAIT')
            if trip['load_end_s']-trip['load_start_s']!=1800 or trip['departure_s']<trip['load_end_s']:checks.append('LOAD')
            if clock!=trip['return_s'] or clock>72000:checks.append('RETURN')
            if quantity>60:checks.append('CAPACITY')
            item={**trip,'stop_indices':[positions[x] for x in ids],'stop_count':len(ids),'load_units':quantity,
                  'geometry':geom if all(trip_checks) else None,'geometry_status':'GO' if all(trip_checks) else 'HOLD',
                  'D_km_recomputed':float(length/1000),'W_min_recomputed':(trip['load_start_s']-trip['ready_s'])/60,
                  'geometry_length_max_arc_delta_m':max_geo}
            by_vehicle.setdefault(trip['vehicle_id'],[]).append(item);items.append(item)
            triprows.append({'method':method,'vehicle_id':trip['vehicle_id'],'trip_no':trip['trip_no'],'stop_count':len(ids),'load_units':quantity,
                'OD_D_km':float(length/1000),'saved_D_km':trip['distance_m']/1000,'D_delta_m':float(length)-trip['distance_m'],
                'W_min':item['W_min_recomputed'],'max_Route_OD_delta_m':max_dm,'max_Route_OD_delta_s':max_dt,
                'max_geometry_delta_m':max_geo,'geometry_status':item['geometry_status'],'constraints_passed':not checks,
                'all_arc_checks_passed':all(trip_checks)})
        if Counter(visits_all)!=Counter(demand):checks.append('COVERAGE')
        if any(len(v)>2 for v in by_vehicle.values()):checks.append('TRIP_COUNT')
        for berth in inp['berths']:
            windows=sorted((x['load_start_s'],x['load_end_s']) for x in items if x['berth_id']==berth['berth_id'])
            if any(b[0]<a[1] for a,b in zip(windows,windows[1:])):checks.append('BERTH_OVERLAP')
        Dsum=float(sum((Decimal(str(x['distance_m'])) for x in items),Decimal(0))/1000)
        Dind=sum(x['D_km_recomputed'] for x in items);Wind=sum((x['load_start_s']-x['ready_s']) for x in items)/60
        if abs(Dind-result['D_km'])>1e-8 or abs(Dsum-result['D_km'])>1e-8 or abs(Wind-result['W_min'])>1e-8:checks.append('TOTAL_METRIC')
        meta=plan['method_settings'];events=result['timing_events']
        plan_info={'method':method,'trips':items,'D_km':result['D_km'],'W_min':result['W_min'],'T_program_s':result['T_program_s'],
                   'D_recomputed_km':Dind,'W_recomputed_min':Wind,'violations':sorted(set(checks)),'feasible':not checks,
                   'geometry_all_passed':all(x['geometry_status']=='GO' for x in items),'timing_events':events,
                   'vehicles':[{'vehicle_id':key,'D_km':sum(x['D_km_recomputed'] for x in value),'W_min':sum(x['W_min_recomputed'] for x in value),'trips':len(value),'stops':sum(x['stop_count'] for x in value)} for key,value in sorted(by_vehicle.items())],
                   'other_limit':result['other_limit'],'input_hash':result['input_hash'],'OD_hash':result['OD_hash']}
        stages=[]
        if method in ['B','C']:
            stages=[{'name':'有向Clarke–Wright候補','routes':meta['initial_CW_routes'],'D_km':meta['route_generation_D_km'],'W_min':None,'geometry_saved':False},
                    {'name':'OR-Tools生成' if method=='C' else '共通完成器への入力','routes':meta.get('OR_Routing_generated_routes',meta['post_completion_route_count']),
                     'D_km':meta['OR_Routing_objective_decimeter']/10000 if method=='C' else meta['route_generation_D_km'],'W_min':None,'geometry_saved':False},
                    {'name':'共通完成器（候補プール）','routes':meta['pool_routes'],'D_km':None,'W_min':None,'geometry_saved':False}]
        else:
            q=meta['quantum'];seed={tuple(x) for x in meta['seed_routes']};sampled={tuple(r) for x in q for r in x['full_route_obtained']}
            selected_new=sum(tuple(t['stop_indices']) in (sampled-seed) for t in items)
            stages=[{'name':'保存された古典seed計画','routes':len(seed),'D_km':sum(t['distance_m'] for t in meta['seed_plan']['trips'])/1000,'W_min':sum(t['waiting_s'] for t in meta['seed_plan']['trips'])/60,'geometry_saved':True},
                    {'name':'基底の車両日列','columns':len(meta['base']['LP']['rc']),'D_km':meta['base']['IP']['objective'],'W_min':meta['base']['IP']['secondary_objective'],'geometry_saved':False},
                    {'name':'AOA完全マクロ取得','routes':len(sampled),'domain':meta['macro_full_routes_total'],'new_routes':len(sampled-seed),'final_shots':sum(x['result']['measured_shots'] for x in q),'geometry_saved':False},
                    {'name':'量子＋古典seedの経路プール','routes':len(sampled|seed),'classical_seed_routes':len(seed),'geometry_saved':False},
                    {'name':'古典日列生成・ゼロ面補充','columns':meta['day_columns'],'zero_RC_added':meta['hybrid']['zero_face_added'],'geometry_saved':False},
                    {'name':'最終選択に残った新AOA経路','routes':selected_new,'geometry_saved':False}]
            plan_info['seed_saved_plan']=meta['seed_plan']
        stages.append({'name':'保存された最終計画','routes':len(items),'D_km':result['D_km'],'W_min':result['W_min'],'T_program_s':result['T_program_s'],'geometry_saved':True})
        plan_info['stages']=stages;plans[method]=plan_info;print('plan',method,Dind,Wind,'geometry',plan_info['geometry_all_passed'],'violations',checks,flush=True)
    # Match B/D vehicle labels by maximal overlap, then compare actual records.
    b,dplan=plans['B'],plans['D'];bvs=sorted({x['vehicle_id'] for x in b['trips']});dvs=sorted({x['vehicle_id'] for x in dplan['trips']})
    vehicle_stops=lambda plan,v:{j for x in plan['trips'] if x['vehicle_id']==v for j in x['stop_indices']}
    overlap=np.array([[len(vehicle_stops(b,v)&vehicle_stops(dplan,w)) for w in dvs] for v in bvs]);ri,ci=linear_sum_assignment(-overlap)
    matches=[]
    for i,j in zip(ri,ci):
        bt=sorted([x for x in b['trips'] if x['vehicle_id']==bvs[i]],key=lambda x:x['trip_no']);dt=sorted([x for x in dplan['trips'] if x['vehicle_id']==dvs[j]],key=lambda x:x['trip_no'])
        keys=['ready_s','berth_id','load_start_s','load_end_s','departure_s','return_s']
        matches.append({'B_vehicle':bvs[i],'D_vehicle':dvs[j],'shared_customers':int(overlap[i,j]),
            'B_customers':len(vehicle_stops(b,bvs[i])),'D_customers':len(vehicle_stops(dplan,dvs[j])),
            'same_customer_set':vehicle_stops(b,bvs[i])==vehicle_stops(dplan,dvs[j]),
            'same_ordered_trips': [x['stop_indices'] for x in bt]==[x['stop_indices'] for x in dt],
            **{'same_'+key: [x[key] for x in bt]==[x[key] for x in dt] for key in keys}})
    route_key=lambda x:tuple(x['stop_indices']);bm={route_key(x):x for x in b['trips']};dm={route_key(x):x for x in dplan['trips']}
    comparison={'vehicle_matching':'Hungarian maximum shared-customer count, deterministic saved order',
                'matches':matches,'same_unlabelled_trip_route_set':bm.keys()==dm.keys(),
                'same_road_shapes_by_trip_route':bm.keys()==dm.keys() and all(bm[k]['geometry']==dm[k]['geometry'] for k in bm),
                'same_vehicle_days_up_to_relabelling':all(x['same_customer_set'] and x['same_ordered_trips'] for x in matches),
                'same_all_schedules_after_matching':all(all(x['same_'+key] for key in keys) for x in matches),
                'same_totals':b['D_km']==dplan['D_km'] and b['W_min']==dplan['W_min']}
    save_json(ROOT/'B_D_COMPARISON.json',comparison)
    defaults={}
    for case in scenarios:
        for i,j in [(0,1),(1,0),(0,len(scenarios[case]['points'])-1)]:
            value=roads.pair(case,i,j);defaults[f'{case}:{i}:{j}']=value
    for path,digest in roads.used_blocks.items():register(REPO/path,'saved OD path block (hash verified), including ancestor')
    extraction=read_json(ROOT/'ROAD_EXTRACTION.json');register(REPO/extraction['source'],'pinned OSM PBF')
    for name in ['ROAD_METADATA.json','COMMON_BUNDLES.json']:register(SOURCE/'roads'/name,'common road version and input correspondence')
    register(SOURCE/'DEPOT_ENTRANCE_DECISION.json','adopted depot entrance evidence')
    for p in (REPO/'03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1').glob('*'):
        if p.is_file():register(p,'frozen demand artifact (unchanged)')
    data={'version':'toc-visualization-20261113-v1','scenarios':scenarios,'stats':stats,'plans':plans,'BD_comparison':comparison,
          'roads':read_json(ROOT/'data/roads.json'),'boundary':geo,'default_OD_routes':defaults,'conditions':{'capacity':60,'loading_s':1800,'customer_service_s':120,'return_preparation_s':0,'max_trips':2,'shift_start_s':28800,'shift_end_s':72000},
          'provenance':{'road_version':scenarios['S1']['road_version'],'OSM_timestamp':'2026-07-16T20:21:30Z','geometry':'retained OSRM annotated nodes + pinned OSM coordinates + saved phantom snaps','network_display':'bounded OSM motor-road context; access not inferred','copyright':'© OpenStreetMap contributors / ODbL; boundary: 国土交通省 国土数値情報N03',
                        'S2_S3_plans':'未実行・表示しない','intermediate_missing':'B/Cの候補の全訪問順・完成器前の全時刻は記録なし','T_definition':'入力読込開始〜共通検査終了の保存wall秒。第二再計算・出力は保存Tの外'}}
    save_json(ROOT/'data/dashboard.json',data)
    (ROOT/'data/data.js').write_text('window.DASHBOARD_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    save_csv('OD_VALIDATION.csv',odrows);save_csv('ROUTE_VALIDATION.csv',triprows);save_csv('ARC_VALIDATION.csv',arcrows)
    save_json(ROOT/'DATA_MANIFEST.json',{'inputs':MANIFEST,'conditions_version':'AD-common-20261111-v1.1','road_version':scenarios['S1']['road_version'],'OD_hashes':{s:x['OD_hash'] for s,x in scenarios.items()},'boundary_crs':{'source':'EPSG:6668','display':'EPSG:4326'},'route_geometry_tolerance_m':.35,'Route_OD_tolerance_m_s':.25,'geometries_simplified':False})
    summary={'OD_all_passed':all(x['passed'] for x in odrows),'plans_all_feasible':all(x['feasible'] for x in plans.values()),
             'geometry_all_passed':all(x['geometry_all_passed'] for x in plans.values()),'arcs':len(arcrows),'trips':len(triprows),
             'geometry_failed_arcs':sum(not x['geometry_passed'] for x in arcrows),'max_geometry_delta_m':max(abs(x['geometry_delta_m']) for x in arcrows),
             'elapsed_s':time.perf_counter()-begin,'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             'display_data_bytes':(ROOT/'data/data.js').stat().st_size,'BD':comparison}
    save_json(ROOT/'BUILD_SUMMARY.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='BD'},indent=2),flush=True)


if __name__=='__main__':main()
