#!/usr/bin/env python3
"""Read-only source profiling; writes evidence reports only, never scientific data."""
from pathlib import Path
import csv, hashlib, json, re, subprocess, sys
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
P = ROOT / '03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1'
E = ROOT / 'reproducibility/outputs/traffic_simulation'
START = '5bb6829ced63195dcbd3ce5785c8e66331994b6b'
inspected = {}
def rel(p): return str(p.relative_to(ROOT))
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def inspect(p, kind):
    inspected[rel(p)] = {'file':rel(p),'kind':kind,'sha256':sha(p),'bytes':p.stat().st_size}
def table(name, rows, columns=None):
    with (OUT/name).open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=columns or list(rows[0])); w.writeheader(); w.writerows(rows)
def md(name, s): (OUT/name).write_text(s.strip()+'\n',encoding='utf-8')
def role(p):
    s=rel(p)
    if 'receipt_experience_sensitivity' in s: return 'SAVED_SENSITIVITY_VARIANT_NOT_PRIMARY'
    if 'r24_demand_capacity_authority' in s: return 'LEGACY_ASSUMED_LOAD_NOT_R24_AUTHORITY'
    if '/evrp_r' in s: return 'HISTORICAL_FIXTURE_OR_ROUTING_EVIDENCE_CONDITIONAL_REUSE'
    if p.name in {'building_delivery_stops.csv','household_building_assignment.csv','plateau_residential_building_candidates.csv'}: return 'HISTORICAL_UNRESOLVED_NOT_SCOPED_PRIMARY'
    return 'CANDIDATE_SAVED_SYNTHETIC_OR_SOURCE_STATISTIC'
def meaning(n,p):
    exact={
      'request_id':('synthetic household-day demand-record identity; not shipment ID','identifier'),
      'household_id':('synthetic census-expanded household identity; not recipient microdata','identifier'),
      'building_id':('PLATEAU building source identity; not event/access identity','identifier'),
      'stop_id':('historical building-day aggregation identity; not observed service visit','identifier'),
      'request_ids':('serialized child synthetic demand-record identities','identifier-list'),
      'household_ids':('serialized child synthetic household identities','identifier-list'),
      'parcel_equivalent':('realized synthetic content count; not individually identified physical parcels','parcel_equivalent'),
      'expected_parcel_equivalent_per_day':('calibrated household expected daily rate; not realized content','parcel_equivalent/day'),
      'request_count':('count of child household-day demand records','records'),
      'household_count':('household count in source aggregation; geography/statistic depends on file','households'),
      'evaluation_date':('designated synthetic date, not observed release/delivery date','calendar-date'),
      'building_representative_point':('geographic building representative point WKT; not entrance','degrees; EPSG:4326 per R04 config'),
      'sumo_edge_id':('nearest delivery-permitted road-edge routing proxy','identifier'),
      'mapped_edge_id':('routing endpoint mapped directed edge; fixture-scoped','identifier'),
      'edge_from_node':('directed mapped edge start road node, not physical access','identifier'),
      'edge_to_node':('directed mapped edge end road node, not physical access','identifier'),
      'nearest_edge_distance_m':('distance to selected shape vertex at index len(shape)//2, not perpendicular snap','m'),
      'mapping_distance_m':('legacy endpoint projection/mapping distance; method manifest-scoped','m'),
      'edge_offset_m':('endpoint distance along mapped directed edge; fixture-scoped','m'),
      'longitude':('geographic longitude; location proxy rather than observed stop','degrees'),
      'latitude':('geographic latitude; location proxy rather than observed stop','degrees'),
      'w_i':('legacy mesh household-equivalents per candidate; not realized demand','household_equivalents/candidate'),
      'q_i':('legacy fixed customer demand convention, not current R24 load','source q_i_unit; not adopted'),
      'day_code':('source survey weekday category code; no request foreign key','category'),
      'day_label':('source survey weekday label; not request-specific delivery day','category'),
      'hour_code':('source survey hour category code; no request foreign key','category'),
      'hour_label':('source survey receipt hour label; not synthetic request timestamp','hour bucket'),
      'source_row':('upstream table row reference','row index'),
      'geometry_ref':('reference to source building geometry; not saved access geometry','source reference'),
      'geometry':('stored geospatial geometry/WKB; source CRS metadata retained','source CRS'),
      'realized_parcel_equivalent':('saved sensitivity-variant realized household count, not primary request identity','parcel_equivalent'),
      'demand_expected_parcel_equivalent':('macro mesh calibrated expected count for target_days=1; not household realization','parcel_equivalent/day'),
      'demand_parcel_equivalent':('macro mesh largest-remainder integer demand proxy, not realized shipments','parcel_equivalent/day'),
      'census_population_2020':('source census mesh population before boundary apportionment','persons'),
      'area_weighted_population_2020':('census population apportioned by Ota boundary area overlap','persons'),
      'population_2024_expected':('macro population rescaled to Ota2024 total before integer allocation','persons'),
      'population_2024':('macro population proxy after largest-remainder integer allocation','persons'),
      'mesh_area_m2':('mesh geometry area','m2'),
      'boundary_overlap_area_m2':('mesh intersection with Ota boundary area','m2'),
      'boundary_overlap_ratio':('boundary overlap area divided by mesh area','dimensionless'),
      'experience_multiplier':('saved sensitivity receipt-experience adjustment factor','dimensionless'),
      'relative_propensity':('household size receipt frequency relative to common reference','dimensionless'),
      'total_calibration_target':('fixed macro Ota total used for expectation normalization','parcel_equivalent/day'),
      'building_usage':('PLATEAU coded building use; not observed residential recipient occupancy','category'),
      'floors':('PLATEAU above-ground floor attribute; source sentinel values retained','floors'),
      'underground_floors':('PLATEAU underground floor attribute; sentinel values retained','floors'),
      'height_m':('source building height attribute, not parcel dimension','m'),
      'unit':('source measurement unit dictionary, not a load-dimension adoption','unit label'),
      'value':('normalized aggregate source statistical cell; interpreted jointly with unit/category/source_row','source unit column'),
      'raw_value':('original source statistical cell retained before normalization','source unit column'),
    }
    if n in exact: return exact[n]
    if n.endswith('_seed') or n=='seed': return ('recorded historical seed, insufficient to reconstruct RNG stream','seed integer')
    if 'provenance' in n or 'classification' in n: return ('source classification label; does not upgrade synthetic input to observation','category')
    if n.endswith('_id') or n.endswith('_code'): return ('source entity/category identifier; meaning limited to file schema','identifier/category')
    if n.endswith('_m'): return ('source length/distance field; method limited to file provenance','m')
    if n.endswith('_s'): return ('source modeled duration or fixture timing; not observed request time','s')
    if 'version' in n or 'status' in n or 'method' in n or 'source' in n or 'hash' in n or 'sha256' in n: return ('source metadata / reference / state; retain verbatim','metadata')
    if n in {'parcel_count','delivery_count','payload_quantity'}: return ('legacy placeholder; presence of column alone is not evidence of populated physical quantity','NOT_DEFINED unless source unit populated')
    return ('source column '+n+'; detailed operational semantics NOT_ESTABLISHED; no promotion to request/event evidence','source unit column if present; otherwise NOT_ESTABLISHED')

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==START
    roots=[ROOT/'03_data/processed/traffic_simulation/demand',E/'demand',E/'r24_demand_capacity_authority']
    files=sorted({p for r in roots for p in r.rglob('*') if p.is_file()})
    inventory=[]; catalog=[]; schema_rows=[]
    for p in files:
        inspect(p,'data/artifact')
        catalog.append({**inspected[rel(p)],'current_use':role(p),'profile_scope':'FULL_TABULAR' if p.suffix in {'.csv','.parquet'} else 'BYTE_INVENTORY_METADATA'})
        if p.suffix not in {'.csv','.parquet'}: continue
        if p.suffix=='.csv':
            try: f=pd.read_csv(p,dtype='string',keep_default_na=False)
            except pd.errors.EmptyDataError: continue
            storage={n:'CSV UTF-8 text' for n in f.columns}
        else:
            ar=pq.read_table(p); f=ar.to_pandas(); storage={x.name:str(x.type) for x in ar.schema}
            schema_rows.append({'file':rel(p),'arrow_schema':str(ar.schema),'metadata':str(ar.schema.metadata)})
        for n in f.columns:
            s=f[n]
            if storage[n] in {'binary','large_binary'}: s=s.map(lambda x:x.hex() if isinstance(x,bytes) else x)
            null=s.isna() | s.astype('string').str.strip().eq('').fillna(False)
            good=s[~null].astype('string'); distinct=int(good.nunique()); numeric=pd.to_numeric(good,errors='coerce')
            logical='string'
            if len(good) and numeric.notna().all() and not (n.endswith('_id') or n.endswith('_code') or n in {'request_ids','household_ids'}):
                logical='integer' if ((numeric%1)==0).all() else 'float'
            if len(good) and good.isin(['True','False','true','false']).all(): logical='boolean'
            if n=='evaluation_date': logical='ISO date string (day only)'
            sem,unit=meaning(n,p)
            inventory.append({'name':n,'file':rel(p),'schema':';'.join(f.columns),'data_type':storage[n]+'; logical='+logical,'semantic_meaning':sem,'unit':unit,'provenance':role(p)+'; source byte hash in INSPECTED_FILES.csv; no generator reproduction claim','cardinality':len(f),'non_null_distinct':distinct,'null_count':int(null.sum()),'null_rate':float(null.mean()) if len(f) else 'NA_EMPTY_TABLE','uniqueness': 'EMPTY_TABLE' if not len(f) else ('UNIQUE_NON_NULL' if distinct==len(good) else 'NOT_UNIQUE'),'current_use':role(p)})
        del f
    table('DEMAND_RECORD_INVENTORY.csv',inventory)
    table('DATA_FILE_CATALOG.csv',catalog)
    table('PARQUET_SCHEMA_REGISTER.csv',schema_rows)
    # Inspect full authority/script/config bytes without importing or executing scientific code.
    authority=[E/'end_to_end_workflow_feasibility_audit/20260914_v2'/n for n in ['END_TO_END_WORKFLOW_FEASIBILITY_AUDIT.md','END_TO_END_WORKFLOW_AUTHORITY.md','PLANNING_HORIZON_OPTIONS.md','INSTANCE_GENERATION_POLICY.md','ASSET_HASH_VERIFICATION.csv']]
    for dirname in ['r24_data_gate_execution_pipeline/20260914_v1','r24_problem_data_spec_freeze_review/20260914_v1','pipeline_authority_and_r24_capacity_plan/20260914_v1']:
        authority += list((E/dirname).glob('*.md'))
    scripts=list((ROOT/'05_src/traffic_simulation/demand').glob('*.py'))+[ROOT/'05_src/traffic_simulation/evrp_r13_routing/compute_routing.py']
    scripts += [ROOT/'05_src/research_cli/demand.py',ROOT/'05_src/research_cli/core.py',ROOT/'05_src/traffic_simulation/calibration/diagnose_ota_initial_demand_spatial_support.py']
    scripts += [ROOT/'05_src/traffic_simulation/network/accept_three_tier_network_run.py',ROOT/'05_src/traffic_simulation/network/finalize_three_tier_postchecks.py']
    scripts += list((ROOT/'05_src/traffic_simulation/validation').glob('*demand*.py'))
    configs=[p for p in (ROOT/'reproducibility/config/traffic_simulation').rglob('*') if p.is_file() and re.search(r'demand|parcel|delivery|household',p.name,re.I)]
    configs += [ROOT/'reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml']
    for p in authority+scripts+configs:
        p.read_text(encoding='utf-8'); inspect(p,'authority' if p in authority else ('script_NOT_EXECUTED' if p in scripts else 'config_NOT_EXECUTED'))
    # Raw sources are provenance references; normalized statistical tables are fully profiled above.
    rawroots=[ROOT/'03_data/raw/traffic_simulation/demand_proxy',ROOT/'03_data/raw/traffic_simulation/population',ROOT/'03_data/raw/traffic_simulation/boundaries',ROOT/'03_data/raw/external_statistics/census_2020_tokyo_small_area',ROOT/'03_data/raw/external_statistics/housing_land_2023',ROOT/'03_data/raw/external_statistics/plateau_ota_2025',ROOT/'03_data/raw/external_statistics/tokyo_metropolitan_freight_survey_2024_screening']
    raw=[]
    for r in rawroots:
        for p in sorted(r.rglob('*')):
            if p.is_file():
                inspect(p,'raw_source_byte_inventory_NOT_REQUEST_MICRODATA')
                raw.append(inspected[rel(p)])
    table('RAW_SOURCE_CATALOG.csv',raw)
    related_specs=[
      (ROOT/'03_data/metadata/acquisition/20260825_tokyo_metropolitan_goods_movement_delivery_receipt_tables.md','RAW_ACQUISITION_AUTHORITY','aggregate receipt survey provenance; not request microdata'),
      (ROOT/'03_data/processed/traffic_simulation/validation/ota_ward_baseline_demand_2024_500m_quality_summary.json','MACRO_DEMAND_VALIDATION','mesh-level macro expected/count validation; not realized requests'),
      (ROOT/'05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md','CURRENT_NORMATIVE_WITH_STALE_SELECTION_SECTION','macro demand authority; later R24 authority supersedes old weighted sampling'),
      (ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1/request_stop_mapping.json','HISTORICAL_MAPPING_ATTEMPT','0 mapped; blocked run; not current stop evidence'),
      (ROOT/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json','HISTORICAL_MAPPING_SUMMARY','39956 mapped against all network edges; detailed R03 CSV separately filters delivery-permitted edges and remains field evidence'),
      (E/'end_to_end_workflow_feasibility_audit/20260914_v2/REQUEST_READINESS.csv','CURRENT_PARENT_AUDIT_REGISTER','prior request readiness claim checked against source rows'),
      (E/'r24_data_gate_execution_pipeline/20260914_v1/STOP_AND_REMEDIATION_MATRIX.csv','CURRENT_PARENT_STOP_REGISTER','parent STOP definitions; reassessed by scope'),
    ]
    related=[]
    for p,rclass,note in related_specs:
        p.read_bytes(); inspect(p,'related_evidence')
        related.append({**inspected[rel(p)],'classification':rclass,'current_use_or_exclusion':note})
    table('RELATED_EVIDENCE_CATALOG.csv',related)
    d=pd.read_csv(P/'daily_requests.csv',dtype={'request_id':str,'household_id':str})
    a=pd.read_csv(P/'household_building_assignment_scoped.csv',dtype=str,keep_default_na=False)
    rm=pd.read_csv(P/'request_building_mapping.csv',dtype={'request_id':str,'household_id':str,'building_id':str})
    assert set(rm.request_id)==set(d.request_id) and rm.request_id.is_unique
    fullcheck=d.merge(rm[['request_id','household_id','evaluation_date','parcel_equivalent']],on='request_id',validate='one_to_one',suffixes=('_d','_m'))
    assert all((fullcheck[n+'_d']==fullcheck[n+'_m']).all() for n in ['household_id','evaluation_date','parcel_equivalent'])
    rm=rm[rm.assignment_status.eq('assigned')].copy()
    st=pd.read_csv(P/'building_delivery_stops_scoped.csv',dtype={'stop_id':str,'building_id':str})
    edgepath=E/'demand/candidate_validation/20260909_r03_edge_mapping/candidate_delivery_edge_connections.csv'
    edge=pd.read_csv(edgepath,dtype={'stop_id':str,'building_id':str,'sumo_edge_id':str,'edge_from_node':str,'edge_to_node':str})
    # Different schemas/snapshots must not be silently substituted.
    variants=[]
    for name in ['household_building_assignment','request_building_mapping','building_delivery_stops']:
        pp=pq.read_table(P/(name+'.parquet')).to_pandas()
        cp=P/({'household_building_assignment':'household_building_assignment_scoped','request_building_mapping':'request_building_mapping','building_delivery_stops':'building_delivery_stops_scoped'}[name]+'.csv')
        cf=pd.read_csv(cp,dtype='string',keep_default_na=False)
        assert list(cf.columns)==list(pp.columns) and len(cf)==len(pp)
        equal=all(cf[n].fillna('').astype(str).equals(pp[n].map(lambda x:x.hex() if isinstance(x,bytes) else x).fillna('').astype(str)) for n in cf.columns)
        variants.append({'file':rel(P/(name+'.parquet')),'rows':len(pp),'columns':','.join(pp.columns),'comparison':'ROW_VALUE_EQUAL' if equal else 'TYPE_OR_VALUE_DIFFERENCE_RETAIN_SEPARATE; scoped CSV primary'})
    table('SNAPSHOT_VARIANTS.csv',variants)
    assert d.request_id.is_unique and d.household_id.is_unique and a.household_id.is_unique
    mapped=d.merge(a[['household_id','building_id','assignment_status']],on='household_id',validate='one_to_one')
    mapped=mapped[mapped.assignment_status.eq('assigned')]
    assert set(mapped.request_id)==set(rm.request_id)
    assert rm.request_id.is_unique
    check=mapped.merge(rm[['request_id','building_id','parcel_equivalent']],on='request_id',suffixes=('_join','_saved'),validate='one_to_one')
    assert (check.building_id_join==check.building_id_saved).all() and (check.parcel_equivalent_join==check.parcel_equivalent_saved).all()
    assert set(st.stop_id)==set(edge.stop_id) and st.stop_id.is_unique and edge.stop_id.is_unique
    assert set(st.building_id)==set(rm.building_id)
    ep=st[['stop_id','building_id']].merge(edge[['stop_id','building_id']],on='stop_id',suffixes=('_s','_e'),validate='one_to_one')
    assert (ep.building_id_s==ep.building_id_e).all()
    grouped=rm.groupby('building_id').agg(request_count=('request_id','size'),parcel_equivalent=('parcel_equivalent','sum'))
    comp=st.set_index('building_id')[['request_count','parcel_equivalent']].sort_index()
    assert grouped.sort_index().equals(comp)
    assert st.evaluation_date.eq('2026-01-01').all() and rm.evaluation_date.eq('2026-01-01').all()
    assert (st.household_count==st.request_count).all()
    child_ids=[]
    child_by_building=rm.groupby('building_id')['request_id'].agg(set).to_dict()
    for row in st.itertuples():
        ids=str(row.request_ids).split(';')
        if len(ids)!=row.request_count: ids=str(row.request_ids).split('|')
        if len(ids)!=row.request_count: ids=str(row.request_ids).split(',')
        assert len(ids)==row.request_count
        assert set(ids)==child_by_building[row.building_id]
        child_ids.extend(ids)
    assert len(child_ids)==len(set(child_ids))==len(rm)
    # Existing manifest verification only; never run the historical mapper.
    checks=[]
    prior=pd.read_csv(E/'end_to_end_workflow_feasibility_audit/20260914_v2/ASSET_HASH_VERIFICATION.csv',keep_default_na=False)
    for row in prior.to_dict('records'):
        if row['path'] in inspected and re.fullmatch('[0-9a-f]{64}',row['actual_sha256']):
            checks.append({'file':row['path'],'expected_sha256':row['actual_sha256'],'actual_sha256':inspected[row['path']]['sha256'],'status':'MATCH' if row['actual_sha256']==inspected[row['path']]['sha256'] else 'MISMATCH'})
    manifest=json.loads((edgepath.parent/'candidate_validation_manifest.json').read_text())
    for k in ['candidate_population','accepted_network','output']:
        item=manifest[k]; path=ROOT/item['path']; inspect(path,'mapping_manifest_input_or_output_hash_only')
        checks.append({'file':item['path'],'expected_sha256':item['sha256'],'actual_sha256':sha(path),'status':'MATCH' if sha(path)==item['sha256'] else 'MISMATCH'})
    table('INPUT_HASH_VERIFICATION.csv',checks)
    assert all(x['status']=='MATCH' for x in checks)
    stats={'daily_records':len(d),'daily_content':int(d.parcel_equivalent.sum()),'mapped_records':len(rm),'mapped_content':int(rm.parcel_equivalent.sum()),'excluded_records':len(d)-len(rm),'excluded_content':int(d.parcel_equivalent.sum()-rm.parcel_equivalent.sum()),'positive_buildings':len(st),'assigned_households':int(a.assignment_status.eq('assigned').sum()),'assigned_buildings':a.loc[a.assignment_status.eq('assigned'),'building_id'].nunique(),'dates':sorted(d.evaluation_date.unique()),'multi_content_household_day_records':int((d.parcel_equivalent>1).sum()),'multi_record_buildings':int((st.request_count>1).sum()),'max_records_per_building':int(st.request_count.max()),'max_content_per_household_day':int(d.parcel_equivalent.max()),'max_content_per_building':int(st.parcel_equivalent.max()),'unique_r03_edges':edge.sumo_edge_id.nunique(),'shared_r03_edges':int((edge.groupby('sumo_edge_id').size()>1).sum()),'shared_from_nodes':int((edge.groupby('edge_from_node').size()>1).sum()),'shared_to_nodes':int((edge.groupby('edge_to_node').size()>1).sum()),'r03_distance_min_m':float(edge.nearest_edge_distance_m.min()),'r03_distance_median_m':float(edge.nearest_edge_distance_m.median()),'r03_distance_max_m':float(edge.nearest_edge_distance_m.max()),'inventory_fields':len(inventory),'profiled_tables':len({r['file'] for r in inventory})}
    expected=pd.read_csv(P/'household_daily_expected_demand.csv',dtype={'household_id':str})
    assert expected.household_id.is_unique and set(expected.household_id)==set(a.household_id)
    allocated_ids=set(a.loc[a.assignment_status.eq('assigned'),'household_id'])
    stats['all_household_expected_per_day']=float(expected.expected_parcel_equivalent_per_day.sum())
    stats['allocated_household_expected_per_day']=float(expected.loc[expected.household_id.isin(allocated_ids),'expected_parcel_equivalent_per_day'].sum())
    stats['mapped_positive_household_expected_per_day']=float(expected.loc[expected.household_id.isin(set(rm.household_id)),'expected_parcel_equivalent_per_day'].sum())
    (OUT/'EVIDENCE_STATISTICS.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    evidence=[]
    def ev(item,status,source,limitation): evidence.append({'item':item,'status':status,'source':source,'limitation':limitation,'adopted_new_assumption':'NONE'})
    for item,source,lim in [
      ('synthetic request record identity','daily_requests.csv:request_id','household-day aggregate identity only'),('household destination','daily_requests.csv:household_id','synthetic household, not actual recipient'),('saved mapped building destination','request_building_mapping.csv:building_id','73200 mapped records only'),('realized content','daily_requests.csv:parcel_equivalent','parcel-equivalent integer count, not shipment microdata'),('expected daily rate','household_daily_expected_demand.csv:expected_parcel_equivalent_per_day','rate; cannot substitute for realized content'),('synthetic date','daily_requests.csv:evaluation_date','2026-01-01, day-only'),('building-day record identity','building_delivery_stops_scoped.csv:stop_id','AGGREGATED_DELIVERY_DEMAND_RECORD'),('road edge / endpoint nodes','candidate_delivery_edge_connections.csv','historical R03 routing proxy on old run_2 network')]: ev(item,'EXISTS',source,lim)
    for item,source,lim in [('building destination from household','saved scoped assignment join','unassigned 347 positive rows excluded explicitly'),('coordinates for mapped demand','mapped building -> scoped stop -> R03 coordinates','geographic proxy'),('routing node relation for mapped demand','mapped building -> scoped stop -> R03 edge endpoints','edge endpoints are not individual access points'),('same-building child membership','request_building_mapping.csv and stop.request_ids','candidate aggregation, not accepted event'),('weekday of synthetic date','ISO date calendar arithmetic','Thursday; no operational weekday demand pattern')]: ev(item,'DERIVABLE_WITHOUT_NEW_RANDOMNESS',source,lim)
    for item in ['individual parcel ID','individual shipment/delivery ID','observed transaction/request ID','exact request timestamp','request hour','request time bucket','request AM/PM','request release/cutoff','dispatch membership','departure time','wave membership','worker/vehicle shift','mass','volume','parcel class','parcel dimensions','physical entrance/access ID','parking/loading point']:
        ev(item,'NOT_AVAILABLE','primary saved demand and mapping schemas; normalized survey timing has no child request key','legacy fixtures/statistical categories cannot fill primary missing field')
    for item in ['one building-day as one service event','one request-row as one indivisible service event','one synthetic day as operational CVRP horizon','individual count expansion into surrogate parcels','proxy location adopted as service access']:
        ev(item,'DERIVABLE_WITH_MODEL_ASSUMPTION','NEW_ASSUMPTION_REQUIRED','not adopted; no new surrogate identities/events/times generated')
    table('REQUEST_EVIDENCE_REGISTER.csv',evidence)
    temporal=[
      ('synthetic date','synthetic','daily_requests.evaluation_date; mapped records and scoped stops','day','2026-01-01','request/stop linked; not operating day'),
      ('generation date / artifact timestamp','observed','R03 manifest.created_at=2026-09-09T03:45:16.783245+00:00; historical summaries; Git','artifact clock','NOT_DELIVERY_TIME','R03 processing time only; original request generation clock unavailable'),
      ('generation seed date-like value','synthetic','generation_seed=20260829; assignment_seed=20260830','seed','NOT_DATE_EVIDENCE','numeric seeds are not generation timestamps'),
      ('delivery date','absent','primary demand schema','NONE','NOT_AVAILABLE','evaluation_date is synthetic label'),
      ('exact request timestamp','absent','daily_requests schema','NONE','NOT_AVAILABLE','no creation/release/arrival clock'),
      ('request hour / bucket / AM-PM','absent','primary demand schema','NONE','NOT_AVAILABLE','no request-linked timing'),
      ('survey receipt hour and weekday','observed','household_type_delivery_time.csv: day_code/day_label/hour_code/hour_label; source ss530','aggregate weekday/hour categories','EXTERNAL_REFERENCE_ONLY','source-reported aggregate survey; no synthetic request key; cannot allocate hours without new model assumption'),
      ('survey parking/box environment categories','observed','housing_delivery_environment.csv:road_parking_code/yard_parking_code/box_code; normalized additional ss tables','aggregate source categories','SOURCE_STATISTIC_ONLY','parking availability statistics exist; no building-linked physical access/loading point or timing'),
      ('weekday of synthetic date','derived','calendar arithmetic on 2026-01-01','weekday','Thursday','calendar label only; weekend can be derived false; no weekday pattern calibration'),
      ('dispatch time/membership','absent','primary saved demand / mapping','NONE','NOT_AVAILABLE','dispatch not mandatory horizon concept'),
      ('route departure / service windows','synthetic','legacy evrp_r07_time_window customer_time_windows and routing/EV fixtures','fixture seconds','LEGACY_FIXED_MODEL_ASSUMPTION','exists in historical fixtures; not primary request timestamp or observed departure'),
      ('shift / working time','absent','primary saved demand','NONE','NOT_AVAILABLE','legacy runtime schedule cannot establish worker/vehicle shift'),
      ('seasonal calibration','absent','synthetic date; national FY2024 annual calibration','annual source context','NOT_AVAILABLE_REQUEST_SEASONALITY','January/calendar quarter derivable only as label, no seasonal generation factor'),
      ('routing travel time','derived','legacy R13 routing_arcs; Routing Baseline','seconds','FREE_FLOW_MODEL','duration/cost, not request/event timestamp; scope 12 endpoints')]
    table('TEMPORAL_EVIDENCE_REGISTER.csv',[dict(zip(['item','classification','source','resolution','value_or_scope','limitation'],x)) for x in temporal])
    # Exhaustive term screening of textual architecture documents/configs/scripts, including archives.
    hits=[]
    pattern=r'dispatch[ _-]batch|batch[ _-]membership|one[ _-]dispatch|daily building demand|batch demand|service[ _-]event|physical[ _-]stop|batch_id|horizon_days|NEXT_EXECUTABLE_TASK'
    screenroots=[ROOT/'05_src',ROOT/'reproducibility/outputs/traffic_simulation',ROOT/'reproducibility/archive/traffic_simulation',ROOT/'reproducibility/config',ROOT/'RESEARCH_PIPELINE_REFERENCE.md']
    paths=set()
    for r in screenroots:
        paths.update([r] if r.is_file() else [p for p in r.rglob('*') if p.is_file() and p.suffix in {'.md','.yml','.yaml','.py'} and OUT not in p.parents and '__pycache__' not in str(p)])
    for p in sorted(paths):
        contents=p.read_text(encoding='utf-8',errors='replace')
        for ln,line in enumerate(contents.splitlines(),1):
            if not re.search(pattern,line,re.I): continue
            s=rel(p)
            current=('r24_data_gate_execution_pipeline' in s or 'r24_problem_data_spec_freeze_review' in s or 'pipeline_authority_and_r24_capacity_plan' in s)
            old=('r24_demand_capacity_authority' in s or 'representative_instance_schema' in s)
            mandatory=bool(re.search(r'one.dispatch|one_dispatch|horizon_semantics|one batch|batch_id|within.{0,12}batch|A5|batch-specific|batch service|batch event|NEXT_EXECUTABLE_TASK',line,re.I))
            caution=bool(re.search(r'not (?:an? )?(?:actual |observed |automatically )?(?:dispatch|batch)|no .*dispatch|without .*dispatch|dispatch is (?:a )?(?:possible|optional)|does not .*dispatch',line,re.I))
            status='MARK_SUPERSEDED' if old else ('REWRITE' if current and mandatory and not caution else ('KEEP_CURRENT' if current or 'end_to_end_workflow_feasibility_audit' in s else 'KEEP_HISTORICAL'))
            reason='field-scoped horizon/interface amendment proposal; preserve mathematics' if status=='REWRITE' else ('historical design cannot govern R24' if status=='MARK_SUPERSEDED' else 'valid terminology/limitations or historical evidence; no edit')
            hits.append({'file':s,'line':ln,'text':line,'classification':status,'reason':reason})
        if re.search(pattern,contents,re.I): inspect(p,'legacy_term_screen_full_text')
    table('LEGACY_DISPATCH_CONFLICTS.csv',hits)
    md('SEARCH_SCOPE.md',f'''# Inventory and search scope
All files under processed traffic_simulation/demand, outputs/traffic_simulation/demand and r24_demand_capacity_authority were byte-inventoried, including ignored files and sensitivity/repeat/legacy variants. All CSV and Parquet fields in those roots were fully profiled, not sampled: {stats['profiled_tables']} tables / {len(inventory)} fields. Non-tabular artifacts are catalogued separately. Raw demand_proxy, population, boundary, PLATEAU, small-area census, housing-land and freight-screening source files are byte-inventoried; their normalized demand-statistic columns are profiled, not a claim of raw XLSX/PDF/CityGML cell or feature inspection. RELATED_EVIDENCE_CATALOG.csv records connected validation/mapping summaries and source documentation that sit outside the three tabular roots.
Search screened {len(paths)} Markdown/YAML/Python files across 05_src, traffic outputs, traffic archives, config and RESEARCH_PIPELINE_REFERENCE.md. Every matching line is recorded. Excludes this output, .git, .conda, caches, binaries and large CSV request-list text; CSV fields are covered by the inventory. Classification concerns reuse in current R24, not rewriting history. Unknown column semantics explicitly remain NOT_ESTABLISHED.
Null means stored null or empty/whitespace; literal NA/X/- is retained as a source value. Cardinality = all rows; uniqueness considers non-null values; empty tables explicitly marked. CSV storage is text, logical numeric inference is recorded separately; IDs/codes remain strings. Arrow schema and CRS metadata are preserved in PARQUET_SCHEMA_REGISTER.csv. Byte equality establishes snapshot continuity, not original generator reproducibility.
''')
    write_decisions(stats)
    table('INSPECTED_FILES.csv',list(inspected.values()))
    git={'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'start_sha':START,'end_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'tracked_changes':subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines(),'git_status':subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=ROOT,text=True).splitlines(),'scientific_mutation':'NONE; evidence/schema/decision reports only','experiment_execution':'NONE','demand_generation':'NONE','optimization_execution':'NONE','event_generation':'NONE','instance_generation':'NONE','executed_script':'build_evidence.py (profiling/reporting only)','python':sys.version,'pandas':pd.__version__,'pyarrow':__import__('pyarrow').__version__}
    git['output_tracking']='IGNORED_BY_EXISTING_GITIGNORE; not staged or committed'
    git['ignored_output_status']=subprocess.check_output(['git','status','--short','--ignored',str(OUT)],cwd=ROOT,text=True).splitlines()
    (OUT/'GIT_STATUS.json').write_text(json.dumps(git,ensure_ascii=False,indent=2)+'\n')
    validation={'profiled_tables':stats['profiled_tables'],'inventory_fields':len(inventory),'source_hashes_match':True,'request_identity_unique':True,'scoped_request_building_join_equal':True,'saved_child_membership_and_count_conservation':True,'edge_population_ids_equal':True,'historical_generators_executed':False,'tracked_existing_files_unchanged':not git['tracked_changes'],'gate_a_passed':False}
    assert validation['tracked_existing_files_unchanged']
    (OUT/'VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
    print(json.dumps(stats,ensure_ascii=False,indent=2))

def write_decisions(s):
    md('R24_GATE_A_REQUEST_EVENT_TEMPORAL_EVIDENCE.md',f'''# R24 Gate A request/event/temporal evidence decision
Decision ID: R24-GATE-A-EVIDENCE-20260915-v1. Date: 2026-09-15 JST.
Scope: EVIDENCE RECONSTRUCTION / SCHEMA / GATE-A DECISION ONLY.
Verdict: GATE_A_REQUIRES_TARGETED_REMEDIATION.
NEXT_EXECUTABLE_TASK = finalize Planning Horizon

The source chain is supported to synthetic household-day demand records → mapped building-day demand aggregation → historical routing proxies → reproducible synthetic-date membership. It does **not** establish individual shipments, compatible single-visit events, observed access points or operating schedules. No mandatory dispatch is inferred. No event/stop schema is implemented and no horizon/population is frozen.

## Facts and decision boundary
Saved daily_requests contains {s['daily_records']:,} unique synthetic request IDs and unique households, with {s['daily_content']:,} parcel-equivalents on 2026-01-01. {s['multi_content_household_day_records']:,} rows contain multiple parcel-equivalents; maximum {s['max_content_per_household_day']}. These IDs identify aggregated household-day demand, not individual parcel/transaction requests. Individual parcel, shipment and observed transaction IDs are absent.
Expected rates remain separate: all-household expectation {s['all_household_expected_per_day']:.6f}/day; allocated-household expectation {s['allocated_household_expected_per_day']:.6f}/day; mapped-positive-household expectation {s['mapped_positive_household_expected_per_day']:.6f}/day. None is the realized count or a load value. request_building_mapping.csv contains all 73,547 primary rows, including 347 null-building exceptions; 73,200 is its assigned subset, not the total file row count.
Scoped saved assignment supports {s['assigned_households']:,} households / {s['assigned_buildings']:,} buildings. Saved request mapping covers {s['mapped_records']:,} rows / {s['mapped_content']:,} content units. {s['excluded_records']} positive rows / {s['excluded_content']} units remain outside mapped scope; retain exclusion lineage. {s['positive_buildings']:,} positive building-day demand aggregates contain child request IDs. {s['multi_record_buildings']:,} buildings contain multiple request rows, maximum {s['max_records_per_building']}; maximum content per building {s['max_content_per_building']}. Full primary row/join/child/count checks passed; this verifies saved records, not original random generation.

The minimum upstream demand unit is SYNTHETIC_HOUSEHOLD_DAY_DEMAND_RECORD. The downstream building table is AGGREGATED_DELIVERY_DEMAND_RECORD. Existing stop_id is a building-day source ID, not an accepted service_event_id. Same building ≠ same service event. Same routing edge/node ≠ common access or service compatibility.

R03 saved connections cover all {s['positive_buildings']:,} building-day IDs on historical run_2 network: ROUTING_PROXY_STOP only. Routing Baseline's accepted run_3 geometry/edge-offset endpoints cover the old 10-customer fixture plus depot/charger, not an all-population OD matrix. Current-class/reachability compatibility is unaccepted. Physical entrances, access IDs, legal loading/parking and visit compatibility are unavailable in primary sources.

Request-linked temporal resolution is day-only. Source ss530 has aggregate weekday/hour receipt statistics, and manifests/legacy fixtures contain processing clocks and modeled timing; none establishes individual request timestamps, dispatch membership or real shifts. One synthetic day is DATA_SUPPORTED for immutable source membership, and MODEL_ASSUMPTION_REQUIRED as an operational one-tour horizon. Dispatch, wave and shift membership are UNSUPPORTED. Horizon may remain an abstract core concept, but A cannot pass with undefined reproducible benchmark membership and event compatibility.

## Gate decision
Accept evidence claims above and continued **read-only snapshot reconstruction** with incomplete historical generator lineage. Do not yet accept executable source adoption, event aggregation, physical access or concrete CVRP horizon. Full source-use decision for production requires scoped snapshot IDs/hashes, exclusions, request unit, horizon and access/event policy together. Gate A is not globally blocked by generator provenance; bounded remediation can proceed from saved bytes. Gate B remains gated by A passage.
Remaining A work: finalize reproducible horizon/source-use decision and versioned interface amendment; resolve event/access evidence or separately review explicitly labeled proxy assumptions; complete acceptance/conservation/exception contract and gate sign-off. Merely choosing a day does not resolve event/access. Vehicle/capacity remain OPEN; they are not conditions for this evidence audit.
Acceptance reviewer: Codex evidence audit under user-authorized scope. This is a negative/conditional gate decision, **not** approval of new model assumptions; no affirmative final A sign-off.

Next task rationale: horizon membership constrains event compatibility and schema; finalize Planning Horizon is first, using the documented alternatives and keeping event/access dependencies explicit. It is not executed here. Do not advance to B or freeze eligibility yet.

Arbitrariness risk: converting building/day/road-node co-location into a one-visit event or carrier batch. Validity risk: synthetic parcel-equivalents/proxy geometry relabeled observed parcels/physical stops. Compatibility risk: promoting old run_2 all-candidate mappings to accepted run_3/new-class endpoints and costs. Ota statistical/geographic grounding does not establish observed operations or representativeness.
Parent paths/hashes, source files, scripts/configs, Git state and output hashes are in INSPECTED_FILES.csv, PROVENANCE.md, GIT_STATUS.json and SHA256SUMS.txt. R23 closure, frozen R24 mathematics and sequential A→B→C→D remain unchanged. All scientific/experimental/generation/optimization execution = NONE.
''')
    md('REQUEST_SCHEMA_PROPOSAL.md','''# Minimum request/demand schema proposal — not implemented
Primary type: SYNTHETIC_HOUSEHOLD_DAY_DEMAND_RECORD, a count-bearing explicit synthetic demand record, not individual shipment microdata. Never expand counts to invented parcel IDs. Individual Delivery Request identity is NOT_AVAILABLE.

| Proposed field | Existing source / derivation | Null policy / meaning |
|---|---|---|
| request_id | daily_requests.request_id, retain verbatim | unique non-null household-day record identity |
| source_record_id | same existing request_id, no new ID | source identity |
| source_snapshot_sha256 | saved source byte hash | required metadata, deterministic |
| destination_building_id | request_building_mapping.building_id or scoped household join | nullable for 347 unmapped positive rows, reason required |
| household_id | daily_requests.household_id | synthetic household identity |
| realized_count | daily_requests.parcel_equivalent | integer content count, unit parcel_equivalent; not count of shipment IDs |
| content_basis | source is realized count | MODEL_BASED_SYNTHETIC lineage, not physical load |
| synthetic_date | evaluation_date | ISO date, no added timestamp |
| access_id | none | null: NOT_AVAILABLE; no fabricated entrance |
| road_node_id | R03 edge_from_node/edge_to_node relation | do not choose one endpoint arbitrarily; use separate routing reference relation |
| provenance_class | raw provenance_type retained plus authority interpretation | original model_assumed; synthetic with calibrated mean, Poisson family assumed |
| observation_status | source authority | SYNTHETIC, never observed |
| record_type / unit_definition | this dictionary proposal | household-day aggregated demand record |
| transformation_version | future deterministic join contract | not implemented |

Road relation should retain routing_proxy_id=existing stop_id, network_sha256, mapping_rule, mapped_edge_id, edge_from_node, edge_to_node, geometry/CRS and mapping status. No one road node or access identity is selected. Old accepted fixture may supply edge_offset_m only for its existing endpoints; that does not populate all records.

Building-level alternative type: AGGREGATED_DELIVERY_DEMAND_RECORD. Retain source_record_id=stop_id, destination_building_id, child request_ids, request_count (number of household-day rows), realized_count (sum of parcel-equivalents), synthetic_date, geographic point and source hash. Do not set its ID equal to individual request or service-event identity. Expected rate belongs in a separate expectation table with parcel_equivalent/day unit.

Proposed invariants: source IDs stable/unique; one household and day per request row; no split/added child identity; join at most one saved building per household; explicitly preserve unmapped rows; within selected horizon no omission/double membership; request_count and realized_count conserved separately. Event assignment and horizon fields stay OPEN. No q_i/Q/m fields are populated.
''')
    md('SERVICE_EVENT_EVIDENCE.md',f'''# Service event evidence
Definition: request group compatible with one vehicle visit at one access location within a selected Planning Horizon. Dispatch is optional specialization.

| Relation | Evidence | Decision |
|---|---|---|
| multiple demand records at same building | {s['multi_record_buildings']:,} scoped building-day aggregates; child IDs/counts verified | EXISTS building grouping; not service-event identity |
| multiple request rows at same household on selected day | daily household_id is unique | no such multiple rows; {s['multi_content_household_day_records']:,} rows contain multiple content units without child parcel IDs |
| multiple buildings at same access point | no primary access/entrance IDs | NOT_AVAILABLE; access-point evidence needed |
| multiple destinations on same mapped edge | {s['shared_r03_edges']:,} edges shared by multiple building-day records | routing relation EXISTS; not common entrance or one visit |
| multiple destinations on same edge endpoint node | {s['shared_from_nodes']:,} shared from-nodes / {s['shared_to_nodes']:,} shared to-nodes | topology relation EXISTS, not physical service evidence |

Existing evidence supports building-level aggregation **only**. Final one-visit aggregation requires access-point and service/operational compatibility evidence, or a separately accepted controlled proxy rule. Even one household-day row as one indivisible event requires explicit unit/access policy; count-bearing row is not proof of a single operational visit. Shared road locations can support distinct events. No distance-based merging, entrance assumption or event groups/IDs are generated.
NEW_ASSUMPTION_REQUIRED: building-day=single visit; request-row=single visit; shared node=single access; timeless service compatibility. None adopted. Event cardinality is unaccepted; 39,956 is building aggregate count, not known service-event count.
''')
    md('PHYSICAL_STOP_EVIDENCE.md',f'''# Physical stop evidence
Building geometry: plateau_residential_building_candidates has GML geometry_ref/source_feature_id and building attributes; historical chocho join unresolved. Saved scoped stops have building representative WKT points. Missing scoped geospatial Parquet prerequisites in historical summary are not recovered or replaced by historical candidates. Representative point ≠ building entrance ≠ vehicle access.

R03 saved candidate_delivery_edge_connections maps {s['positive_buildings']:,} source building-day IDs to {s['unique_r03_edges']:,} road edges plus from/to node IDs; source/manifest/network hashes verified. Mapping rule nearest_delivery_permitted_edge_midpoint actually chooses shape vertex at index len(shape)//2, as historical script shows. Distance min/median/max: {s['r03_distance_min_m']:.6f}/{s['r03_distance_median_m']:.6f}/{s['r03_distance_max_m']:.6f} m. This is a distance to that proxy vertex, not perpendicular road snap, entrance or parking evidence. No new mapper execution.

The earlier run_2 request_stop_mapping summary reports median/p95/max 16.185094/35.479351/94.628786 m because its code indexes **all** network edges, whereas R03 restricts the candidate set to delivery-permitted edges and reports 16.596829/36.409268/94.628786 m from the detailed CSV. These are distinct mapping policies, not interchangeable measurements. R03 is the field-level routing-proxy evidence used here; neither policy establishes physical access.

Classify as ROUTING_PROXY_STOP, retain source stop ID and old network hash. Generic delivery_permitted=true on old network is not class-specific road/access or depot reachability acceptance. Source summary sumo_mapping_executed=false describes an earlier stage, not absence of later R03 saved mapping.

Accepted Routing Baseline has run_3 network and directed edge-offset endpoints for a scoped old fixture: 10 customers + DEP_006 + charger, 132 directed pairs. These are routing locations with mapping distances, not observed physical loading points. New population/class requires validation; all-39,956 accepted OD does not exist. Building point / edge / endpoint road node / physical access / service event are separate entities. Same node cannot prove common stop or legal access.

Physical access-point IDs, entrance coordinates, parking/loading data, observed service visits: NOT_AVAILABLE in primary linked evidence. Geometry references do not supply them. NEW_ASSUMPTION_REQUIRED for adopting representative point / mapped road location as modeled service access; no such adoption in this audit.
''')
    md('PLANNING_HORIZON_OPTIONS.md',f'''# Planning Horizon options — evidence decision only
Planning Horizon is a finite reproducible service-set membership concept. Clock duration and carrier operations are not implied. No option is frozen here.

| Option | Classification | Reproduction / size | Interpretation and limitation |
|---|---|---|---|
| 1 One synthetic day | DATA_SUPPORTED for date-based demand membership; MODEL_ASSUMPTION_REQUIRED for one-tour operational interpretation | filter evaluation_date=2026-01-01; {s['daily_records']:,} primary demand rows / {s['daily_content']:,} content units; mapped {s['mapped_records']:,} / {s['mapped_content']:,}, {s['positive_buildings']:,} building aggregates | no new randomness needed for source membership; event count, access eligibility and CVRP membership unaccepted |
| 2 One dispatch | UNSUPPORTED as operational horizon | no dispatch IDs/members/departure times or DEP_006 operator source | controlled policy would require NEW_ASSUMPTION_REQUIRED |
| 3 One delivery wave | UNSUPPORTED | no request-linked waves/time buckets; survey aggregate hours do not define waves | do not divide day/2 or assign AM/PM |
| 4 One shift | UNSUPPORTED | no worker/vehicle shifts or working-time source | no R24 duration feasibility guarantee |
| 5 Horizon remains abstract | PARTIALLY_SUPPORTED | frozen finite-set atemporal core; concrete controlled membership policy still missing | valid core concept; cannot close A or produce executable instances with undefined membership/event rule |

Most directly data-supported horizon component: **one designated synthetic day**. Fixed-date filtering is reproducible without an additional temporal model, but mapped-scope exclusion and event/access policy must be documented. synthetic day ≠ real carrier operating day. A controlled benchmark could use the date as source boundary while separately constructing small computational instances; full-day population is not automatically one feasible fleet tour set.

One-day special assessment: reproducibility HIGH from saved snapshot; semantic validity valid as synthetic household-day realization, not physical parcel manifests; operational interpretation unestablished; instance-generation compatibility conditional on eligibility/event/horizon and Routing Baseline acceptance; R24 compatibility conditional on finite required unsplittable events, at most one tour per used vehicle, no reload/re-dispatch, no scheduling claim. No vehicle or capacity is selected. Future VRPTW needs request/window/service/clock evidence or separately labeled models; date/hour survey aggregates alone cannot establish individual windows.

Decision: recommend one synthetic day as the **source-membership candidate**, retain horizon adoption OPEN. Dispatch is not required. Required next review finalizes source-use/horizon policy and field-scoped authority amendment; event/access acceptance remains a separate condition. No artificial timestamps, departure times or demand splits adopted.
''')
    md('ELIGIBLE_STOP_PREREQUISITES.md','''# Eligible stop prerequisites — no population freeze
Required before a stable candidate population: selected reproducible Planning Horizon membership and source snapshot; positive realized demand under a declared content basis; stable unique source/event/proxy IDs; valid coordinate/CRS; saved road mapping with network/method provenance; explicitly accepted physical-stop or routing-proxy interpretation and request/event relation; conservation and unmapped/out-of-scope exceptions. IDs should distinguish event identity from place identity.

Required for executable routing eligibility: directed reachability from/to DEP_006 and compatible routing endpoint/access profile. No new reachability computation here. Preliminary geography population may remain candidate-only before class evidence; final class legality/OD checks must be ratified downstream B/D, without assuming a vehicle now. Existing R03 generic delivery mapping is insufficient for final accepted eligibility.

Optional unless separately adopted scope: observed entrance/parking detail for a controlled proxy population; operating timestamps, windows, shifts, territorial representativeness; descriptive spatial/network strata for structural suites. Operational claims make corresponding operational evidence necessary. Parcel mass/volume and q_i/Q/m are B–D responsibilities, not filled here.

Currently 39,956 mapped positive building-day records are reconstructable candidates, **not frozen eligible service stops**. Candidate construction is technically possible; production freeze/executable stop population is not accepted until A, then required routing checks. No filtering/freeze performed.

Instance interface: Repeated Random Suite needs accepted eligible stop/event IDs, stable population/snapshot, horizon/source-use/event rule, Routing Baseline endpoint compatibility, prespecified SRSWOR/RNG/order/manifest policy; policy can be prepared after A, numeric materialization after D/data freeze. Old R05 PPS is not repeated SRSWOR. Controlled Structural Suite additionally needs coordinates/network positions and prespecified metrics/threshold/cases. Fixed Anchor Suite needs stable IDs and immutable snapshot with all data/authority hashes; R23 anchors reference route-ordering only. All suites also need later compatible vehicle/load/fleet/cost validation before CVRP materialization. No instances or sampling generated.
''')
    md('GATE_A_ACCEPTANCE_CRITERIA.md','''# Versioned Gate A acceptance criteria amendment
Gate sequence A→B→C→D and source-use M3 remain. Dispatch-specific A5 is generalized to Planning Horizon membership, with optional dispatch specialization. No symbolic mathematics changes.

| Criterion | Acceptance test / contract | Current result |
|---|---|---|
| A1 source-use | accept immutable snapshot continuation or recover original generator; source hashes/exclusions/allowed claims/transform lineage | bounded read-only snapshot use accepted; executable source adoption pending linked horizon/event/access policy |
| A2 request semantics | household-day aggregated record vs individual request; realized/expected and count units separate; stable source IDs; no fabricated parcels | evidence dictionary reconstructed; proposal ready, executable contract pending |
| A3 event semantics | compatible one-visit group within selected horizon, child lineage, no duplicate/loss, event≠building≠place; explicit evidence or separately reviewed proxy policy | OPEN; building aggregate is not accepted event |
| A4 stop semantics | physical access or explicitly approved ROUTING_PROXY_STOP; CRS/network/method/endpoint references, missing access reasons; B/D compatibility dependencies declared | proxy evidence reconstructed; access/proxy adoption OPEN |
| A5 temporal/horizon | exact available resolution; reproducible finite membership, source date/scope/exclusions; concrete horizon or accepted abstract-core + controlled benchmark membership policy | day-only supported; operational dispatch/wave/shift absent; adoption OPEN |
| A6 provenance/downstream | snapshot/transform hashes; exception and content/count conservation checks; stable eligible-ID interface; reviewer decision, remaining B–D dependencies | saved checks pass; full executable interface/sign-off pending |

A is accepted only when A1–A6 are satisfied together. A_ACCEPTED_WITH_LIMITATIONS is appropriate only after an explicit controlled proxy/horizon/event policy resolves these bindings without pretending operational evidence exists. Inventory alone and an abstract horizon alone do not pass. Gate B may start after affirmative A passage; vehicle/capacity need not already be resolved for A. Current verdict GATE_A_REQUIRES_TARGETED_REMEDIATION preserves this boundary.

Conservation test specification: primary request IDs unique; exactly one source unit per row; separate row/content counts; mapped plus documented excluded records equals full saved source; each eligible request assigned exactly once within one horizon; group child counts/content conserved; one access/proxy reference per event; no co-location merging without compatible policy. Existing saved building aggregations checked as source facts, not production events. Reachability/class/OD/load feasibility remain explicit later dependencies.
''')
    stop=[
      ('STOP_DEMAND_GENERATOR_PROVENANCE_INCOMPLETE','BLOCKS_REGENERATION_ONLY','saved evidence reconstruction','original raw-to-demand regeneration/future production regeneration using historical generator','snapshot-derived demand/stop candidates reconstructable; executable reuse requires A source adoption; no complete reproduction claim'),
      ('STOP_SERVICE_EVENT_DEFINITION_UNRESOLVED','BLOCKS_GATE_A','concrete event/access policy','events / eligible service-stop freeze / B handoff','same-building membership known, one-visit compatibility not accepted'),
      ('STOP_DISPATCH_BATCH_DEFINITION_UNRESOLVED','NON_BLOCKING_LIMITATION','optional operational dispatch specialization','operational dispatch claims only','mandatory dispatch superseded by Planning Horizon; unresolved general horizon membership still blocks A'),
      ('STOP_PLANNING_HORIZON_MEMBERSHIP_UNACCEPTED','BLOCKS_GATE_A','generalized A5','executable source membership / event contract','day label supports candidate; not arbitrarily frozen'),
      ('STOP_VEHICLE_CLASS_UNRESOLVED','NON_BLOCKING_LIMITATION','Gate B','later concrete data','does not block A evidence decision'),
      ('LOAD_UNIT_OPEN','NON_BLOCKING_LIMITATION','Gate C/D','q_i/Q/m and instance materialization','not resolved or filled')]
    table('GATE_A_STOP_REASSESSMENT.csv',[dict(zip(['stop','classification','scope','blocked_scope','reason'],x)) for x in stop])
    four=[
      ('household-day source record','LOW: preserve saved identities','synthetic explicit count demand; not shipments','HIGH upstream lineage; event relation open','Ota household/statistical calibration; not observed demand'),
      ('building-day aggregation','HIGH if equated to one event','valid source count group; one-visit validity absent','PARTIAL; child lineage exists, event/access rule open','Ota geographic building grounding, modeled household allocation'),
      ('R03 routing proxy','MEDIUM/HIGH mapping rule transfer','road topology proxy, not physical entrance/service stop','PARTIAL old run_2; run_3/class/offset/reachability unaccepted','Ota road/building geography; no observed loading'),
      ('one synthetic day','LOW filtering; HIGH operational interpretation','valid designated realization; not representative operating day','PARTIAL source horizon; event/eligibility/schema acceptance missing','synthetic benchmark, no seasonal/weekday operation calibration'),
      ('one dispatch','HIGH new ungrounded membership','UNSUPPORTED operational meaning','OPEN optional horizon; no membership/departure','no applicable operational source'),
      ('one wave','HIGH invented split/bucket','UNSUPPORTED request-linked waves','OPEN no request timing','survey aggregate hours are external reference only'),
      ('one shift','HIGH invented duration/fleet','UNSUPPORTED shift evidence','OPEN; R24 lacks working-time constraints','no observed worker/vehicle shifts'),
      ('abstract horizon','MEDIUM controlled policy discretion','valid finite-set core, no concrete operation','PARTIAL; cannot remove A5/A6 before instances','controlled benchmark policy still to be reviewed'),
      ('snapshot continuation','LOW deterministic saved reconstruction','limited lineage, no historical generator reproduction','HIGH evidence; executable source adoption pending A','synthetic saved realization; immutable bytes not operational truth')]
    table('FOUR_AXIS_GATE_A_AUDIT.csv',[dict(zip(['candidate','arbitrariness','validity','compatibility','grounding_representativeness'],x)) for x in four])
    md('AUTHORITY_AMENDMENT_PROPOSAL.md','''# Minimal current-authority amendment proposal — existing files unchanged
This versioned evidence report does not edit historical hashed artifacts. Parent hashes remain in INSPECTED_FILES.csv. Proposed changes are limited to confirmed stale NEXT/mandatory dispatch/horizon schema mismatches; must be ratified/versioned before materialization.

1. R24_DATA_GATE_EXECUTION_PIPELINE.md: stale NEXT reconstruct event/batch evidence → current audit completion record and sole pending task finalize Planning Horizon. Change A event/batch wording to request/event/access/Planning Horizon membership.
2. GATE_A_SERVICE_EVENT_BATCH.md A3/A5/A6: within-batch → within selected Planning Horizon; require compatible event grouping and reproducible membership, dispatch only conditional. Preserve source-use, access and conservation acceptance, A→B gate dependency.
3. R24_PROBLEM_DATA_SPEC_FREEZE_REVIEW.md §3, DISPATCH_BATCH_SPEC.md and R24_DATA_SPECIFICATION_DRAFT.md: one_dispatch_batch mandatory field → planning_horizon_id/horizon_type/definition_version/source_scope/membership_manifest_hash/classification/acceptance; dispatch_id conditional. Preserve required unsplittable finite events, same one-tour/no-reload homogeneous fleet rules and scalar load core. Batch field lineage stays historical.
4. CUSTOMER_SERVICE_STOP_SPEC.md: cardinalities generalized to horizon, no automatic building/event/access equality. Do not manufacture event IDs.

LEGACY_DISPATCH_CONFLICTS.csv contains exact matching source lines and classifications. MARK_SUPERSEDED is a current-reuse recommendation, not retroactive deletion. KEEP_HISTORICAL source calibration, old fixtures, R23 evidence remain intact. KEEP_CURRENT limitation warnings retain their meaning. This proposal does not implement schema or adopt horizon.
''')
    md('PROVENANCE.md',f'''# Provenance and reproducibility boundary
Branch main; start SHA {START}; end SHA recorded by GIT_STATUS.json (unchanged; no commit). Initial tracked worktree clean. All existing tracked files unchanged; new evidence directory only. Outputs are ignored by existing .gitignore, not staged/committed; ordinary clean git status does not imply no new artifact. INSPECTED_FILES.csv supplies complete byte hashes/categories for inspected authority/data/scripts/configs/term-hit documents. DATA_FILE_CATALOG.csv and RAW_SOURCE_CATALOG.csv separate normalized field profiling from raw source byte inventory. The saved reporting recipe build_evidence.py executes profiling/joins/validation only, via repository .conda/bin/python. System python lacks pyarrow; its failed dependency check performed no generation. Historical demand generators, mapper and routing scripts are inspected, never executed.

Saved lineage: census-expanded synthetic households → calibrated expected household rates plus assumed Poisson realization (recorded seed20260829) → saved scoped housing/building allocation (seed20260830) → saved request/building relation → saved building-day child aggregation → later R03 road-edge proxy mapping. Generation/allocation dependency order is conceptual, not certified historical execution order. Original expansion/generator/config/scoped geometry candidate inputs/RNG/order/software remain incomplete. Existing summary config hashes alone do not recover missing configs. Missing named geospatial prerequisites are not replaced by unresolved historical candidates. Parquet variants are explicitly profiled/catalogued separately; no silent schema substitution.

Current evidence reconstruction selects no random seed/distribution, emits no request/parcel/event/dispatch/horizon/eligible population/instance data, and populates no physical load or fleet parameters. Counts and joins merely audit immutable saved inputs. Existing snapshot hash comparisons all pass; SHA equality is not raw-to-output reproduction. PRIMARY temporal information is synthetic date; statistical ss530 hours are source aggregate evidence only. Processing timestamps are artifact provenance clocks, not request clocks.

Scientific mutation NONE. Experiment execution NONE. Demand generation NONE. Optimization execution NONE. R23 rerun NONE. Vehicle/capacity decisions NONE. MILP/QUBO/QAOA/Aer/optimizer NONE. Gate B not executed. Horizon/schema/population not frozen or implemented. Gate verdict and proposals are evidence/documentation changes only.

Output hashes SHA256SUMS.txt cover every flat output including recipe, provenance, Git status and validation, excluding the hash manifest itself to avoid self-reference. Verification: cd this directory and sha256sum -c SHA256SUMS.txt. Re-running the recipe checks source inputs and existing tracked changes, but Git status reports may differ as untracked artifact list changes; scientific statistics and source hashes remain deterministic. End SHA equals start unless a separate future commit is made. No external data acquisition or messages sent.
''')

if __name__=='__main__': main()
