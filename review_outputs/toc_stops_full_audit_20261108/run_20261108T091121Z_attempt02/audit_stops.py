"""Full read-only source audit. Outputs are exclusive creates in --output only.

No simulator, optimizer, demand generation, source mutation, or shortest paths.
Run with python -B. A new output directory with a protocol/before snapshot is required.
"""
import argparse
import collections
import datetime
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from zipfile import ZipFile

import geopandas as gpd
from lxml import etree as ET
import numpy as np
import pandas as pd
import pyproj
import shapely
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import transform, unary_union
import sumolib

ROOT = Path('/home/takuma/kmd-analysis')
R = Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated')
H = ROOT/'03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1'
BASE = R/'01_research_design/scenario_evaluation'
MD = BASE/'sumo_delivery_point_mapping_20260930'
NET = ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml'
ZIP = ROOT/'03_data/raw/external_statistics/plateau_ota_2025/13111_ota-ku_pref_2025_citygml_1_op.zip'
WARD = ROOT/'03_data/raw/traffic_simulation/boundaries/N03-20260101_13_GML/N03-20260101_13.shp'
TOWN = ROOT/'03_data/raw/external_statistics/census_2020_town_boundary/r2ka13.shp'
NS = {'b':'http://www.opengis.net/citygml/building/2.0','g':'http://www.opengis.net/gml','u':'https://www.geospatial.jp/iur/uro/3.2'}
SEVERITY = {'PASS':0,'CONDITIONAL':1,'HOLD':2,'FAIL':3}

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def read(p):
    return pd.read_csv(p,dtype=str,keep_default_na=False,encoding='utf-8-sig')

def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)

def csvout(p,df):
    with p.open('x',encoding='utf-8',newline='') as f:
        df.to_csv(f,index=False)

def counts(s):
    return {str(k):int(v) for k,v in pd.Series(s).value_counts(dropna=False).items()}

def number(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except (ValueError,TypeError):
        return None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    O=args.output.resolve()
    assert O.is_relative_to(ROOT/'review_outputs/toc_stops_full_audit_20261108')
    assert (O/'AUDIT_PROTOCOL.json').exists() and (O/'REPOSITORY_BEFORE.json').exists()
    started=time.perf_counter()
    protocol=json.loads((O/'AUDIT_PROTOCOL.json').read_text())
    env={'python':sys.version,'executable':sys.executable,'platform':sys.platform,'libraries':{},'sumolib_file':sumolib.__file__,'proj_version':pyproj.proj_version_str}
    for name in ['pandas','numpy','geopandas','shapely','pyproj','pyarrow','lxml','pyogrio']:
        env['libraries'][name]=importlib.metadata.version(name)
    dump(O/'ENVIRONMENT.json',env)

    inputs=[H/n for n in ['building_delivery_stops_scoped.csv','plateau_residential_building_candidates.csv','synthetic_households.csv','household_building_assignment_scoped.csv','daily_requests.csv','stop_generation_run_summary.json','pipeline_run_summary.json']]
    inputs += [ZIP,NET,MD/'DELIVERY_POINT_SUMO_MAPPING_39956.csv',MD/'DELIVERY_POINT_INPUT_FREEZE_MANIFEST.json',MD/'DELIVERY_MAPPING_PROTOCOL.md',MD/'SUMO_DELIVERY_POINT_MAPPING_VALIDATION.json',BASE/'sumo_facility_routing_baseline_20260930/DEPOT_ROUTING_DEFINITION.json',BASE/'sumo_facility_routing_baseline_20260930/SUMO_FACILITY_MAPPING_FREEZE_MANIFEST.json',BASE/'sumo_delivery_point_mapping_20260930/map_points.py',ROOT/'docs/QUANTITATIVE_GUIDE.md',ROOT/'reproducibility/outputs/traffic_simulation/r24_problem_data_spec_freeze_review/20260914_v1/DEPOT_SPEC.md',ROOT/'reproducibility/outputs/traffic_simulation/pipeline_authority_and_r24_capacity_plan/20260914_v1/CURRENT_PIPELINE_STAGES.csv',ROOT/'reproducibility/outputs/traffic_simulation/r24_demand_capacity_authority/20260914_v2/demand_source_registry.csv']
    for base in [WARD,TOWN]:
        inputs += [p for ext in ['.shp','.shx','.dbf','.prj','.cpg'] if (p:=base.with_suffix(ext)).exists()]
    manifest=[]
    for p in inputs:
        manifest.append({'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None,'sha256':sha(p) if p.exists() else None})
    dump(O/'INPUT_MANIFEST.json',manifest)
    print('Input manifest complete',flush=True)

    stops=read(H/'building_delivery_stops_scoped.csv')
    cand=read(H/'plateau_residential_building_candidates.csv')
    hh=read(H/'synthetic_households.csv')
    assignment=read(H/'household_building_assignment_scoped.csv')
    requests=read(H/'daily_requests.csv')
    mapping=read(MD/'DELIVERY_POINT_SUMO_MAPPING_39956.csv')
    saved=json.loads((H/'stop_generation_run_summary.json').read_text())
    frozen=json.loads((MD/'DELIVERY_POINT_INPUT_FREEZE_MANIFEST.json').read_text())
    n=len(stops)
    assert n==39956, 'Unexpected source count: retain source and investigate before adapting expectations'
    a=stops[['stop_id','building_id','chocho_code']].copy()
    a.insert(0,'audit_row_id',np.arange(1,n+1))
    a['source_csv_line']=np.arange(2,n+2)
    domains=['structure','source_lineage','building_join','residential_use','coordinates','ward_boundary','town_boundary','building_geometry','road_mapping','road_reachability']
    for d in domains:a[d+'_status']='PASS'
    reasons=[[] for _ in range(n)]
    issues=[]
    def mark(indices,domain,status,reason,detail=''):
        ix=list(indices)
        for i in ix:
            old=a.at[i,domain+'_status']
            if SEVERITY[status]>SEVERITY[old]:a.at[i,domain+'_status']=status
            if reason not in reasons[i]:reasons[i].append(reason)
            issues.append({'audit_row_id':int(i+1),'stop_id':stops.at[i,'stop_id'],'building_id':stops.at[i,'building_id'],'chocho_code':stops.at[i,'chocho_code'],'domain':domain,'severity':status,'reason_code':reason,'detail':str(detail)})
    def where(mask,domain,status,reason,detail=''):
        mark(np.flatnonzero(np.asarray(mask,dtype=bool)),domain,status,reason,detail)

    profile={}
    for c in stops:
        s=stops[c]
        blank=s.str.strip().eq('')
        profile[c]={'storage_type':'CSV text','pandas_dtype':str(s.dtype),'missing_count':int(blank.sum()),'missing_rate':float(blank.mean()),'unique_count':int(s.nunique()),'min_string_length':int(s.str.len().min()),'max_string_length':int(s.str.len().max()),'leading_trailing_space':int(s.ne(s.str.strip()).sum()),'control_character_rows':int(s.str.contains(r'[\x00-\x1f\x7f]',regex=True).sum())}
        if c in ['request_count','household_count','parcel_equivalent']:
            nums=pd.to_numeric(s,errors='coerce')
            good=nums.notna() & np.isfinite(nums) & nums.ge(1) & nums.eq(np.floor(nums))
            where(~good,'structure','FAIL','INVALID_POSITIVE_INTEGER_'+c.upper())
            profile[c].update({'semantic_type':'positive integer; historical units retained','numeric_min':float(nums.min()),'numeric_max':float(nums.max()),'invalid_count':int((~good).sum())})
        if blank.any():where(blank,'structure','HOLD','MISSING_'+c.upper())
        where(s.ne(s.str.strip())|s.str.contains(r'[\x00-\x1f\x7f]',regex=True),'structure','CONDITIONAL','ABNORMAL_TEXT_'+c.upper())
    for c in ['stop_id','building_id']:
        where(stops[c].duplicated(False),'structure','FAIL','DUPLICATE_'+c.upper())
    where(~stops.chocho_code.str.fullmatch(r'\d{6}'),'structure','FAIL','INVALID_CHOCHO_CODE_FORMAT')
    dates=pd.to_datetime(stops.evaluation_date,format='%Y-%m-%d',errors='coerce')
    where(dates.isna(),'structure','FAIL','INVALID_EVALUATION_DATE')
    expected_version='household-parcel-stop-v1-scoped-accepted-mapping'
    where(stops.stop_generation_version.ne(expected_version),'structure','HOLD','UNEXPECTED_GENERATION_VERSION')
    where(stops.stop_id.ne(stops.evaluation_date+'-'+stops.building_id),'structure','FAIL','STOP_ID_BUILDING_DATE_MISMATCH')
    dump(O/'COLUMN_PROFILE.json',profile)

    # Reconstruct every saved aggregation from source IDs, with no demand generation.
    req_by=collections.defaultdict(list)
    ass_by=collections.defaultdict(list)
    for row in requests.itertuples(index=False):req_by[row.request_id].append(row)
    for row in assignment.itertuples(index=False):ass_by[row.household_id].append(row)
    hh_ids=set(hh.household_id)
    used=collections.Counter()
    lineage_totals=collections.Counter()
    for i,r in stops.iterrows():
        ids=r.request_ids.split(';')
        if len(ids)!=len(set(ids)):mark([i],'source_lineage','FAIL','DUPLICATE_REQUEST_REFERENCE')
        if len(ids)!=int(r.request_count):mark([i],'source_lineage','FAIL','REQUEST_COUNT_MISMATCH')
        got=[]; households=[]
        for rid in ids:
            used[rid]+=1
            if rid not in req_by:
                mark([i],'source_lineage','HOLD','REQUEST_REFERENCE_MISSING',rid);continue
            rg=req_by[rid]
            if len(rg)!=1:
                mark([i],'source_lineage','FAIL','DUPLICATE_SOURCE_REQUEST_ID',rid);continue
            rr=rg[0];hid=rr.household_id;households.append(hid)
            if hid not in hh_ids:mark([i],'source_lineage','FAIL','SOURCE_HOUSEHOLD_MISSING',hid)
            if hid not in ass_by:
                mark([i],'source_lineage','HOLD','HOUSEHOLD_ASSIGNMENT_MISSING',hid);continue
            ar=ass_by[hid]
            if len(ar)!=1:
                mark([i],'source_lineage','FAIL','DUPLICATE_HOUSEHOLD_ASSIGNMENT',hid);continue
            ar=ar[0]
            if ar.building_id!=r.building_id:mark([i],'source_lineage','FAIL','REQUEST_BUILDING_MISMATCH',rid)
            if ar.chocho_code!=r.chocho_code:mark([i],'source_lineage','FAIL','SOURCE_CHOCHO_MISMATCH',rid)
            if ar.assignment_status!='assigned':mark([i],'source_lineage','HOLD','ASSIGNMENT_STATUS_UNEXPECTED',ar.assignment_status)
            if rr.evaluation_date!=r.evaluation_date:mark([i],'source_lineage','FAIL','REQUEST_DATE_MISMATCH',rid)
            got.append(int(rr.parcel_equivalent))
        if len(set(households))!=int(r.household_count):mark([i],'source_lineage','FAIL','HOUSEHOLD_COUNT_MISMATCH')
        if len(got)==len(ids) and sum(got)!=int(r.parcel_equivalent):mark([i],'source_lineage','FAIL','HISTORICAL_AMOUNT_CONSERVATION_FAIL')
    multiply_used={k for k,v in used.items() if v!=1}
    if multiply_used:
        for i,r in stops.iterrows():
            if set(r.request_ids.split(';')) & multiply_used:mark([i],'source_lineage','FAIL','REQUEST_USED_BY_MULTIPLE_STOPS')
    req_pos=pd.to_numeric(requests.parcel_equivalent,errors='coerce').gt(0)
    positive_households=set(requests.loc[req_pos,'household_id'])
    mapped_ass=assignment[assignment.household_id.isin(positive_households) & assignment.building_id.ne('') & assignment.assignment_status.eq('assigned')]
    active_buildings=set(mapped_ass.building_id)
    missing_stop_buildings=active_buildings-set(stops.building_id)
    extra_stop_buildings=set(stops.building_id)-active_buildings
    where(stops.building_id.isin(extra_stop_buildings),'source_lineage','FAIL','STOP_WITHOUT_POSITIVE_MAPPED_HOUSEHOLD')
    lineage={'synthetic_household_rows':len(hh),'unique_household_ids':hh.household_id.nunique(),'positive_request_rows':int(req_pos.sum()),'unique_positive_households':len(positive_households),'mapped_positive_request_references':len(used),'mapped_positive_households':mapped_ass.household_id.nunique(),'positive_mapped_buildings':len(active_buildings),'stops':n,'missing_stop_buildings':sorted(missing_stop_buildings),'extra_stop_buildings':sorted(extra_stop_buildings),'duplicate_request_ids':int(requests.request_id.duplicated().sum()),'duplicate_assignment_households':int(assignment.household_id.duplicated().sum()),'unmapped_request_rows':len(requests)-len(used),'historical_amount_request_total':int(pd.to_numeric(requests.parcel_equivalent).sum()),'historical_amount_stop_total':int(pd.to_numeric(stops.parcel_equivalent).sum()),'historical_amount_is_not_new_parcel_count':True,'generation_seeds':counts(requests.generation_seed),'generation_models':counts(requests.generation_model_version),'distribution':counts(requests.distribution),'evaluation_dates':counts(requests.evaluation_date),'assignment_seeds':counts(assignment.assignment_seed),'saved_summary':saved,'full_original_regeneration':'NOT_PERFORMED_OR_PROVEN; original household/building generator unrecovered'}
    checks={'households_384353':len(hh)==384353,'positive_requests_73547':int(req_pos.sum())==73547,'mapped_positive_73200':len(used)==73200,'stops_39956':n==39956,'all_positive_mapped_buildings_present':not missing_stop_buildings and not extra_stop_buildings,'saved_summary_counts':len(hh)==saved['synthetic_households'] and len(requests)==saved['active_requests'] and len(used)==saved['mapped_requests'] and n==saved['stop_count']}
    lineage['checks']=checks
    dump(O/'SOURCE_LINEAGE_CHECK.json',lineage)
    del req_by,ass_by
    print('Source lineage all-row checks complete',checks,flush=True)

    # Preserve all candidate matches; avoid one-to-many merges inflating stops.
    cb=cand.groupby('building_id',sort=False).indices
    raw_targets=set(stops.building_id)
    candidate_records={}
    for i,r in stops.iterrows():
        indices=cb.get(r.building_id)
        g=None if indices is None else cand.iloc[indices]
        a.at[i,'candidate_match_count']=0 if g is None else len(g)
        if g is None:
            mark([i],'building_join','HOLD','SOURCE_JOIN_MISSING');continue
        unique=g.drop_duplicates()
        candidate_records[r.building_id]=unique.to_dict('records')
        if len(g)>1:
            mark([i],'building_join','CONDITIONAL' if len(unique)==1 else 'HOLD','DUPLICATE_BUILDING_ATTRIBUTE_ROWS' if len(unique)==1 else 'CONFLICTING_BUILDING_ATTRIBUTE_ROWS')
        a.at[i,'candidate_usage_codes']=';'.join(sorted(set(g.building_usage)))
        a.at[i,'housing_type_compatibility']=';'.join(sorted(set(g.housing_type_compatibility)))
        a.at[i,'candidate_status_values']=';'.join(sorted(set(g.status)))
        a.at[i,'candidate_geometry_refs']=';'.join(sorted(set(g.geometry_ref)))
        a.at[i,'candidate_source_feature_ids']=';'.join(sorted(set(g.source_feature_id)))
    del cb

    # WKT and explicit historical CRS binding (not inferred from numeric appearance).
    master_hash=sha(H/'building_delivery_stops_scoped.csv')
    declared_crs_ok=(master_hash==frozen['source_files'][0]['sha256'] and frozen.get('coordinate_crs')=='EPSG:4326')
    points=[]
    for i,s in enumerate(stops.building_representative_point):
        try:
            p=shapely.from_wkt(s)
            if p is None or p.is_empty or p.geom_type!='Point' or not p.is_valid or not(math.isfinite(p.x) and math.isfinite(p.y)) or not(-180<=p.x<=180 and -90<=p.y<=90):raise ValueError('Not finite valid lon/lat point')
            points.append(p);a.at[i,'longitude']=p.x;a.at[i,'latitude']=p.y
        except Exception as exc:
            points.append(None);mark([i],'coordinates','FAIL','INVALID_GEOMETRY',str(exc))
    a['coordinate_crs']='EPSG:4326' if declared_crs_ok else 'UNVERIFIED'
    if not declared_crs_ok:mark(range(n),'coordinates','HOLD','CRS_UNVERIFIED')
    valid_points=np.array([p is not None for p in points])
    coords=[(p.x,p.y) if p is not None else None for p in points]
    dupcoords=pd.Series(coords).duplicated(False).to_numpy() & valid_points
    where(dupcoords,'coordinates','CONDITIONAL','DUPLICATE_COORDINATE_DIFFERENT_BUILDING')
    pg=gpd.GeoSeries(points,crs='EPSG:4326')
    metric=pg.to_crs(6677)
    # Administrative geometries are never repaired in this audit.
    ward=gpd.read_file(WARD);ward=ward[ward.N03_007.eq('13111')]
    ward_bad=int((~ward.geometry.is_valid).sum())
    assert ward_bad==0,'Invalid administrative boundary requires explicit review'
    wardm=ward.to_crs(6677).geometry.union_all()
    towns=gpd.read_file(TOWN);towns=towns[towns.PREF.eq('13') & towns.CITY.eq('111')].copy()
    towns['chocho_code']=towns.KEY_CODE.str[-6:]
    towns_m=towns.to_crs(6677)
    town_by={k:g.geometry.union_all() for k,g in towns_m.groupby('chocho_code')}
    town_codes=set(town_by)
    geometries=list(town_by.values());codes=list(town_by);tree=shapely.STRtree(geometries)
    for i,p in enumerate(metric):
        if p is None:continue
        inside=wardm.contains(p);covered=wardm.covers(p);dist=p.distance(wardm.boundary)
        a.at[i,'ward_relation']='INSIDE' if inside else 'ON_BOUNDARY' if covered else 'OUTSIDE'
        a.at[i,'ward_boundary_distance_m']=dist
        if dist<=2:mark([i],'ward_boundary','CONDITIONAL','NEAR_OTA_BOUNDARY','within 2m audit screening distance')
        elif not covered:mark([i],'ward_boundary','FAIL','OUTSIDE_OTA_BOUNDARY')
        stored=stops.at[i,'chocho_code']
        hits=tree.query(p,predicate='intersects');spatial=sorted({codes[int(j)] for j in hits})
        a.at[i,'spatial_chocho_codes']=';'.join(spatial)
        if stored not in town_codes:
            mark([i],'town_boundary','HOLD','CHOCHO_CODE_NOT_IN_BOUNDARY');continue
        own=town_by[stored];td=p.distance(own);bd=p.distance(own.boundary)
        a.at[i,'stored_town_distance_m']=td;a.at[i,'stored_town_boundary_distance_m']=bd
        if own.covers(p):
            a.at[i,'town_relation']='MATCH'
            if bd<=2:mark([i],'town_boundary','CONDITIONAL','NEAR_CHOCHO_BOUNDARY')
        elif td<=2:
            a.at[i,'town_relation']='NEAR_MISMATCH';mark([i],'town_boundary','CONDITIONAL','CHOCHO_BOUNDARY_NEAR_MISMATCH')
        else:
            a.at[i,'town_relation']='MISMATCH';mark([i],'town_boundary','FAIL','CHOCHO_COORDINATE_MISMATCH')
    boundary_meta={'ward_path':str(WARD),'ward_year':2026,'ward_source_url':'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html','ward_crs':str(ward.crs),'ward_features':len(ward),'town_path':str(TOWN),'town_year':2020,'town_crs':str(towns.crs),'town_source_url':'https://www.e-stat.go.jp/gis/statmap-search?page=1&type=2&aggregateUnit=2&statsId=00200521&serveyId=B002005212020&prefCode=13','town_features':len(towns),'town_distinct_codes':len(town_by),'invalid_town_geometries':int((~towns.geometry.is_valid).sum()),'metric_crs':'EPSG:6677','screening_distance_m':2,'point_crs_evidence_hash_matches':declared_crs_ok,'datum_note':'historical WKT explicitly declared EPSG:4326; native PLATEAU is EPSG:6697 with lat/lon/height, horizontal EPSG:6668. Datum/year and 2m near-boundary ambiguity are not silently corrected.'}
    dump(O/'BOUNDARY_METADATA.json',boundary_meta)
    print('Boundary all-row joins complete',counts(a.ward_relation),counts(a.town_relation),flush=True)

    # Full original CityGML streaming read; no extracted source files or fixes.
    raw=collections.defaultdict(list);raw_count=0;raw_ids=collections.Counter();raw_members=[]
    tf=pyproj.Transformer.from_crs(6668,6677,always_xy=True).transform
    raw_errors=[]
    with ZipFile(ZIP) as z:
        code_xml=ET.fromstring(z.read('codelists/Building_usage.xml'))
        usage_dict={d.findtext('g:name',namespaces=NS):d.findtext('g:description',namespaces=NS) for d in code_xml.findall('.//g:Definition',NS)}
        dump(O/'BUILDING_USAGE_CODES.json',{'zip_member':'codelists/Building_usage.xml','definitions':usage_dict,'official_reference':'https://www.mlit.go.jp/plateaudocument01-01/Contents/コードリスト/Building_usage.html'})
        names=sorted(nm for nm in z.namelist() if '/bldg/' in nm and nm.endswith('.gml'))
        for mi,nm in enumerate(names):
            member_stat={'member':nm,'bytes':z.getinfo(nm).file_size,'crc32':z.getinfo(nm).CRC,'buildings':0,'matched_target_occurrences':0}
            with z.open(nm) as header_stream:
                header=header_stream.read(6000).decode('utf-8-sig')
            srs_match=re.search(r'<gml:Envelope[^>]*srsName="([^"]+)"',header)
            member_stat['declared_srs']=srs_match.group(1) if srs_match else None
            member_crs_ok=bool(srs_match and srs_match.group(1).endswith('/6697'))
            with z.open(nm) as f:
                for _,el in ET.iterparse(f,events=('end',),tag='{'+NS['b']+'}Building',huge_tree=True):
                    raw_count+=1;member_stat['buildings']+=1
                    ids=el.findall('.//u:BuildingIDAttribute/u:buildingID',NS)
                    bid=ids[0].text.strip() if ids and ids[0].text else ''
                    raw_ids[bid]+=1
                    if bid in raw_targets:
                        member_stat['matched_target_occurrences']+=1
                        rec={'building_id':bid,'member':nm,'gml_id':el.get('{'+NS['g']+'}id'),'usage':el.findtext('b:usage',namespaces=NS),'source_crs':'EPSG:6697','geometry_kind':None,'geometry':None,'geometry_valid':False,'error':''}
                        try:
                            areas=[]
                            for kind in ['lod0FootPrint','lod0RoofEdge']:
                                nodes=el.findall('b:'+kind,NS)
                                for node in nodes:
                                    for poly in node.findall('.//g:Polygon',NS):
                                        ext=poly.find('g:exterior/g:LinearRing/g:posList',NS)
                                        if ext is None or not ext.text:continue
                                        vals=np.fromstring(ext.text,sep=' ')
                                        dim=int(ext.get('srsDimension','3'))
                                        arr=vals.reshape(-1,dim)
                                        shell=[(float(v[1]),float(v[0])) for v in arr]
                                        holes=[]
                                        for interior in poly.findall('g:interior/g:LinearRing/g:posList',NS):
                                            av=np.fromstring(interior.text,sep=' ').reshape(-1,int(interior.get('srsDimension','3')))
                                            holes.append([(float(v[1]),float(v[0])) for v in av])
                                        pp=transform(tf,Polygon(shell,holes))
                                        areas.append(pp)
                                if areas:rec['geometry_kind']=kind;break
                            if not member_crs_ok:
                                rec['error']='RAW_CRS_UNVERIFIED'
                            elif areas:
                                if not all(p.is_valid for p in areas):rec['error']='INVALID_RAW_POLYGON'
                                else:
                                    geom=unary_union(areas)
                                    rec['geometry']=geom;rec['geometry_valid']=bool(geom.is_valid and not geom.is_empty)
                            else:rec['error']='NO_LOD0_ROOF_OR_FOOTPRINT'
                        except Exception as exc:rec['error']=type(exc).__name__+':'+str(exc)
                        raw[bid].append(rec)
                    el.clear()
                    while el.getprevious() is not None:del el.getparent()[0]
            raw_members.append(member_stat)
            if mi%10==0 or mi==len(names)-1:print('CityGML',mi+1,'/',len(names),'matched',sum(len(v) for v in raw.values()),flush=True)
    csv_raw=[]
    residential={'411','412','413','414','415'}
    nonres=set(usage_dict)-residential-{'461'}
    for i,r in stops.iterrows():
        recs=raw.get(r.building_id,[]);a.at[i,'raw_building_match_count']=len(recs)
        if not recs:
            mark([i],'building_join','HOLD','RAW_BUILDING_ID_NOT_FOUND');mark([i],'building_geometry','HOLD','RAW_GEOMETRY_MISSING');mark([i],'residential_use','HOLD','RESIDENTIAL_USE_UNVERIFIED');continue
        usages={x['usage'] for x in recs};a.at[i,'raw_usage_codes']=';'.join(sorted(str(x) for x in usages))
        a.at[i,'raw_gml_ids']=';'.join(sorted(str(x['gml_id']) for x in recs))
        if len(recs)>1:mark([i],'building_join','HOLD','RAW_BUILDING_ID_MULTIPLE_FEATURES')
        if usages <= residential:
            a.at[i,'residential_class']='RESIDENTIAL_OR_MIXED_RESIDENTIAL'
        elif usages and usages <= nonres:
            a.at[i,'residential_class']='CONFIRMED_NON_RESIDENTIAL';mark([i],'residential_use','FAIL','NON_RESIDENTIAL_CONFIRMED')
        else:
            a.at[i,'residential_class']='UNVERIFIED';mark([i],'residential_use','HOLD','RESIDENTIAL_USE_UNVERIFIED')
        for cr in candidate_records.get(r.building_id,[]):
            if cr['building_usage'] not in usages:mark([i],'building_join','FAIL','CANDIDATE_RAW_USAGE_MISMATCH')
            if not any(cr['geometry_ref']==x['member'] and cr['source_file']==x['member'] for x in recs):mark([i],'building_join','FAIL','CANDIDATE_GEOMETRY_REFERENCE_MISMATCH')
            # source_feature_id in this historical table is uro:buildingID, not gml:id.
            if cr['source_feature_id']!=r.building_id:mark([i],'building_join','FAIL','CANDIDATE_SOURCE_FEATURE_ID_MISMATCH')
        good=[x for x in recs if x['geometry_valid']]
        p=metric.iloc[i]
        if not good or p is None:
            mark([i],'building_geometry','HOLD','RAW_FOOTPRINT_UNVERIFIED',';'.join(x['error'] for x in recs));continue
        inside=any(x['geometry'].covers(p) for x in good)
        dist=min(p.distance(x['geometry']) for x in good)
        a.at[i,'raw_building_point_relation']='COVERED' if inside else 'OUTSIDE'
        a.at[i,'raw_building_distance_m']=dist
        if not inside:
            mark([i],'building_geometry','FAIL' if dist>50 else 'CONDITIONAL','BUILDING_GEOMETRY_MISMATCH' if dist>50 else 'REPRESENTATIVE_OUTSIDE_FOOTPRINT',f'{dist:.6f} m')
        for x in recs:
            csv_raw.append({k:v for k,v in x.items() if k!='geometry'}|{'audit_row_id':i+1,'point_covered':bool(x['geometry'].covers(p)) if x['geometry_valid'] else None,'point_distance_m':float(p.distance(x['geometry'])) if x['geometry_valid'] else None})
    csvout(O/'GEOMETRY_RAW_CHECK.csv',pd.DataFrame(csv_raw))
    dump(O/'CITYGML_SCAN.json',{'zip':str(ZIP),'members':raw_members,'raw_building_features':raw_count,'unique_uro_building_ids':len(raw_ids),'duplicate_uro_building_ids':sum(v>1 for v in raw_ids.values()),'target_ids_matched':len(raw),'target_ids_missing':len(raw_targets-set(raw)),'axis_rule':'EPSG:6697 gml posList lat,lon,height; use lon,lat in EPSG:6668 for horizontal comparison; no geometry repair','source_feature_id_note':'historical CSV source_feature_id stores uro:buildingID, not gml:id','original_generator':'UNRECOVERED; this audit reads original published CityGML independently'} )
    print('Raw building all-target comparison complete',counts(a.raw_usage_codes),flush=True)

    # Independently validate every selected road endpoint and two graph traversals.
    # This is topology verification, not all-pairs OD or a simulator invocation.
    net_hash=sha(NET);net_hash_ok=net_hash==frozen['network_sha256']
    net=sumolib.net.readNet(str(NET),withInternal=True)
    lanes={l.getID():l for e in net.getEdges(withInternal=True) for l in e.getLanes()}
    restrictions={}
    for _,el in ET.iterparse(str(NET),events=('end',),tag='lane',huge_tree=True):
        if el.get('changeLeft') is not None or el.get('changeRight') is not None:restrictions[el.get('id')]={k:el.get(k) for k in ['changeLeft','changeRight'] if el.get(k) is not None}
        el.clear()
        while el.getprevious() is not None:del el.getparent()[0]
    allowed={k for k,l in lanes.items() if l.allows('delivery')}
    adj={k:set() for k in allowed};rev={k:set() for k in allowed}
    lateral=0
    for lid in allowed:
        l=lanes[lid]
        for co in l.getOutgoing():
            dst=co.getViaLaneID() or co.getToLane().getID()
            if dst in allowed and co.getToLane().allows('delivery'):adj[lid].add(dst)
        if l.getEdge().getFunction()=='':
            ll=l.getEdge().getLanes();idx=l.getIndex()
            for off,key in [(1,'changeLeft'),(-1,'changeRight')]:
                if 0<=idx+off<len(ll):
                    dst=ll[idx+off].getID();rule=restrictions.get(lid,{}).get(key)
                    if dst in allowed and (rule is None or 'delivery' in rule.split() or rule=='all'):adj[lid].add(dst);lateral+=1
    for src,targets in adj.items():
        for dst in targets:rev[dst].add(src)
    depot=json.loads((BASE/'sumo_facility_routing_baseline_20260930/DEPOT_ROUTING_DEFINITION.json').read_text())
    depot_lane=depot['lane_id']
    def bfs(graph,start):
        seen={start};queue=collections.deque([start])
        while queue:
            for nxt in graph[queue.popleft()]:
                if nxt not in seen:seen.add(nxt);queue.append(nxt)
        return seen
    assert depot_lane in allowed
    forward=bfs(adj,depot_lane);backward=bfs(rev,depot_lane)
    mb={k:g for k,g in mapping.groupby('delivery_point_id',sort=False)}
    for i,r in stops.iterrows():
        g=mb.get(r.stop_id)
        if g is None:
            mark([i],'road_mapping','HOLD','ROAD_MAPPING_MISSING');mark([i],'road_reachability','HOLD','ROAD_REACHABILITY_UNVERIFIED');continue
        if len(g)!=1:
            mark([i],'road_mapping','FAIL','DUPLICATE_ROAD_MAPPING_ID');continue
        m=g.iloc[0];lid=m.selected_lane_id
        for col in ['selected_edge_id','selected_lane_id','lane_position','mapping_status','mapping_basis','projection_distance_m','quality_flags','real_world_gate_confirmed']:
            a.at[i,('road_historical_mapping_status' if col=='mapping_status' else 'road_'+col)]=m[col]
        if not net_hash_ok:mark([i],'road_mapping','HOLD','NETWORK_HASH_MISMATCH')
        if lid not in lanes:
            mark([i],'road_mapping','FAIL','ROAD_LANE_MISSING');mark([i],'road_reachability','HOLD','ROAD_REACHABILITY_UNVERIFIED');continue
        l=lanes[lid]
        if l.getEdge().getID()!=m.selected_edge_id:mark([i],'road_mapping','FAIL','ROAD_EDGE_LANE_MISMATCH')
        if not l.allows('delivery'):mark([i],'road_mapping','FAIL','ROAD_PERMISSION_INCONSISTENT')
        pos=number(m.lane_position)
        if pos is None or not(0<=pos<=l.getLength()):mark([i],'road_mapping','FAIL','ROAD_POSITION_OUT_OF_RANGE')
        p=points[i]
        if p is not None:
            xy=net.convertLonLat2XY(p.x,p.y)
            if abs(float(m.longitude)-p.x)>1e-10 or abs(float(m.latitude)-p.y)>1e-10:mark([i],'road_mapping','FAIL','ROAD_SOURCE_COORDINATE_MISMATCH')
            xyerr=math.dist(xy,[float(m.sumo_x),float(m.sumo_y)])
            a.at[i,'road_source_xy_error_m']=xyerr
            if xyerr>0.02:mark([i],'road_mapping','FAIL','ROAD_PROJECTED_COORDINATE_MISMATCH')
            line=LineString(l.getShape())
            pointdistance=line.distance(Point(xy))
            a.at[i,'road_recomputed_distance_m']=pointdistance
            if abs(pointdistance-float(m.projection_distance_m))>0.02:mark([i],'road_mapping','FAIL','ROAD_MAPPING_DISTANCE_MISMATCH')
            if pos is not None:
                savedproj=Point(float(m.projected_x),float(m.projected_y))
                ppos=line.interpolate(pos/l.getLength(),normalized=True)
                if savedproj.distance(ppos)>0.02:mark([i],'road_mapping','FAIL','ROAD_POSITION_PROJECTION_MISMATCH')
        if m.source_row_index!=str(i):mark([i],'road_mapping','FAIL','ROAD_SOURCE_ROW_MISMATCH')
        reachable=lid in forward and lid in backward
        a.at[i,'road_graph_inbound']=lid in forward;a.at[i,'road_graph_outbound']=lid in backward
        a.at[i,'road_reachability_evidence']='CURRENT_FROZEN_LANE_GRAPH_TWO_TRAVERSALS'
        if not reachable:mark([i],'road_reachability','FAIL','NOT_REACHABLE_IN_FROZEN_MODEL_GRAPH')
        if (m.inbound_reachable=='True')!=(lid in forward) or (m.outbound_reachable=='True')!=(lid in backward):mark([i],'road_reachability','FAIL','SAVED_GRAPH_REACHABILITY_MISMATCH')
        flags=set(m.quality_flags.split(';'))
        for flag in protocol['road_review_flags']:
            if flag in flags:mark([i],'road_mapping','CONDITIONAL','ROAD_'+flag)
        a.at[i,'real_access_status']='UNVERIFIED_MODEL_SERVICE_POINT'
    graph_meta={'network_path':str(NET),'network_sha256':net_hash,'frozen_hash_matches':net_hash_ok,'nodes':len(allowed),'arcs':sum(map(len,adj.values())),'lateral_transition_attempts':lateral,'depot':depot,'depot_lane_length_m':lanes[depot_lane].getLength(),'depot_offset_in_range':0<=depot['departure_position']<=lanes[depot_lane].getLength(),'forward_lanes':len(forward),'reverse_lanes':len(backward),'projection':net.getGeoProj().srs,'netOffset':list(net.getLocationOffset()),'semantics':'delivery lane graph including explicit via/internal connections and permitted adjacent lane transitions; zero-time lane changes are topology approximation, not dynamic feasibility','all_pairs_od_generated':False,'simulator_run':False,'real_entrance_or_stopping_verified':False,'new_study_network_adoption':'HOLD; historical topology consistency is not acceptance of all road geometry/access assumptions'}
    dump(O/'ROAD_GRAPH_CHECK.json',graph_meta)
    print('Road endpoint and directed graph all-row checks complete',flush=True)

    # Per-row separate spatial and road verdicts, then total. No dropped source rows.
    location_domains=domains[:8]
    def worst(row,ds):return max((row[d+'_status'] for d in ds),key=SEVERITY.get)
    a['location_status']=a.apply(lambda r:worst(r,location_domains),axis=1)
    a['road_status']=a.apply(lambda r:worst(r,['road_mapping','road_reachability']),axis=1)
    a['overall_status']=a.apply(lambda r:worst(r,domains),axis=1)
    a['reason_codes']=[';'.join(sorted(x)) for x in reasons]
    a['evidence_refs']='INPUT_MANIFEST.json;SOURCE_LINEAGE_CHECK.json;GEOMETRY_RAW_CHECK.csv;BOUNDARY_METADATA.json;ROAD_GRAPH_CHECK.json'
    a['additional_work']=a.reason_codes.map(lambda s:'NONE_FOR_AUDITED_MODEL_SCOPE' if not s else 'REVIEW_REASONS; do not auto-correct or delete')
    a['new_study_road_adoption']='HOLD'
    a['source_master_sha256']=master_hash
    assert len(a)==n and a.audit_row_id.is_unique and a.source_csv_line.is_unique
    assert sum(counts(a.overall_status).values())==n
    csvout(O/'ALL_STOPS_AUDIT.csv',a)
    exceptions=pd.DataFrame(issues,columns=['audit_row_id','stop_id','building_id','chocho_code','domain','severity','reason_code','detail'])
    csvout(O/'AUDIT_EXCEPTIONS.csv',exceptions)
    regional=[]
    total_pass=int(a.overall_status.eq('PASS').sum())
    total_usable=int(a.overall_status.isin(['PASS','CONDITIONAL']).sum())
    for code,g in a.groupby('chocho_code',dropna=False):
        pc=int(g.overall_status.eq('PASS').sum());cc=int(g.overall_status.eq('CONDITIONAL').sum())
        regional.append({'chocho_code':code,'original_count':len(g),'PASS':pc,'CONDITIONAL':cc,'HOLD':int(g.overall_status.eq('HOLD').sum()),'FAIL':int(g.overall_status.eq('FAIL').sum()),'location_PASS':int(g.location_status.eq('PASS').sum()),'original_share':len(g)/n,'pass_share':pc/total_pass if total_pass else None,'pass_conditional_share':(pc+cc)/total_usable if total_usable else None,'pass_share_change':pc/total_pass-len(g)/n if total_pass else None,'pass_conditional_share_change':(pc+cc)/total_usable-len(g)/n if total_usable else None})
    region=pd.DataFrame(regional)
    csvout(O/'REGIONAL_COVERAGE.csv',region)
    # Quotas only: no selected stop IDs or new demand sets are generated.
    quota_rows=[];scale_checks={}
    for size in [1000,2000,4000]:
        sc={}
        for policy,col in [('PASS_ONLY','PASS'),('PASS_PLUS_CONDITIONAL',None)]:
            capacities=region.PASS.to_numpy() if col else (region.PASS+region.CONDITIONAL).to_numpy()
            original=region.original_count.to_numpy();floor=(size*original)//n
            rem=(size*original)%n;order=sorted(range(len(region)),key=lambda j:(-int(rem[j]),str(region.iloc[j].chocho_code)))
            quotas=floor.copy()
            for j in order[:int(size-floor.sum())]:quotas[j]+=1
            shortages=np.maximum(0,quotas-capacities)
            for j,r in region.iterrows():quota_rows.append({'N':size,'policy':policy,'chocho_code':r.chocho_code,'quota_preserving_original_share':int(quotas[j]),'available_count':int(capacities[j]),'shortage':int(shortages[j])})
            sc[policy]={'available':int(capacities.sum()),'enough_total':int(capacities.sum())>=size,'original_distribution_quota_feasible':bool(not shortages.any()),'shortage_regions':int((shortages>0).sum()),'shortage_total':int(shortages.sum()),'feasible_with_rebased_eligible_distribution':bool(int(capacities.sum())>=size),'vrp_feasibility':'NOT_ASSESSED','od_completeness':'NOT_PROVEN','road_network_adoption':'HOLD'}
        scale_checks['S'+str([1000,2000,4000].index(size)+1)]=sc
    csvout(O/'STRATIFIED_QUOTA_CHECK.csv',pd.DataFrame(quota_rows))
    # Read outputs again; aggregate from serialized all-row ledger, not source constants.
    back=read(O/'ALL_STOPS_AUDIT.csv')
    assert len(back)==n and back.audit_row_id.nunique()==n
    status_counts=counts(back.overall_status)
    assert sum(status_counts.values())==n
    exception_counts=counts(exceptions.reason_code) if len(exceptions) else {}
    summary={'audit_version':protocol['version'],'target_count':n,'status_counts':status_counts,'location_status_counts':counts(back.location_status),'road_status_counts':counts(back.road_status),'per_domain_counts':{d:counts(back[d+'_status']) for d in domains},'reason_counts':exception_counts,'unique_stops_with_issues':int(exceptions.audit_row_id.nunique()),'source_stats':{'unique_stop_id':stops.stop_id.nunique(),'unique_building_id':stops.building_id.nunique(),'unique_chocho_code':stops.chocho_code.nunique(),'duplicate_stop_rows':int(stops.stop_id.duplicated(False).sum()),'duplicate_building_rows':int(stops.building_id.duplicated(False).sum()),'exact_duplicate_excess_rows':int(stops.duplicated().sum()),'rows_with_missing_fields':int(stops.apply(lambda s:s.str.strip().eq('')).any(axis=1).sum()),'rows_with_duplicate_coordinates':int(dupcoords.sum())},'residential_usage_counts':counts(back.raw_usage_codes),'ward_relation_counts':counts(back.ward_relation),'town_relation_counts':counts(back.town_relation),'source_lineage_checks':checks,'road_historical_mapping_classes':counts(back.road_historical_mapping_status),'real_access':'not verified; model service points, not observed gates','S1_S3':scale_checks,'region_count':len(region),'regional_total_variation_from_original':{'PASS_ONLY':float(region.pass_share_change.abs().sum()/2) if total_pass else None,'PASS_PLUS_CONDITIONAL':float(region.pass_conditional_share_change.abs().sum()/2) if total_usable else None},'unperformed':['complete regeneration from original statistics','dynamic simulation','route optimization','new OD calculations','new demand sampling','physical capacity or shift/berth feasibility','new-study road acceptance'],'all_source_rows_retained':True,'total_equals_status_sum':True,'elapsed_seconds':time.perf_counter()-started,'source_master_sha256':master_hash,'output_ledger_sha256':sha(O/'ALL_STOPS_AUDIT.csv'),'audit_code_sha256':sha(Path(__file__))}
    dump(O/'AUDIT_SUMMARY.json',summary)
    # Verify every consumed input, all tracked bytes, and all existing status entries.
    before=json.loads((O/'REPOSITORY_BEFORE.json').read_text())
    changed_inputs=[m['path'] for m in manifest if m['exists'] and sha(m['path'])!=m['sha256']]
    changed_tracked=[p for p,h in before['tracked_sha256'].items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    after_status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=ROOT).decode()
    old_status=set(filter(None,before['status_porcelain_z'].split('\0')))
    new_status=set(filter(None,after_status.split('\0')))
    output_relative=str(O.relative_to(ROOT))
    unexpected_status=[x for x in new_status-old_status if not x[3:].startswith('review_outputs/toc_stops_full_audit_20261108')]
    protection={'changed_consumed_inputs':changed_inputs,'changed_tracked_files':changed_tracked,'preexisting_status_entries_removed':sorted(old_status-new_status),'unexpected_new_status_entries':unexpected_status,'new_output_directory':str(O),'all_checks_pass':not(changed_inputs or changed_tracked or old_status-new_status or unexpected_status),'head_before':before['head'],'head_after':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'note':'hashes cover all consumed source files and all tracked files; preexisting untracked status entries retained; unrelated untracked bytes not exhaustively hashed'}
    dump(O/'PROTECTION_CHECK.json',protection)
    assert protection['all_checks_pass']
    print(json.dumps({'statuses':status_counts,'locations':summary['location_status_counts'],'reasons':exception_counts,'scale_checks':scale_checks,'protection':protection['all_checks_pass']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
