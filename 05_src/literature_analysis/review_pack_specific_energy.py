#!/usr/bin/env python3
"""Rebuild documentary pack-stage tables. No vehicle/route simulation or authority writes.
Run: python 05_src/literature_analysis/review_pack_specific_energy.py
Only evaluates ANL's published correlation and dimensional mass identities.
"""
from pathlib import Path
import csv, hashlib, json, math, platform
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'01_research_design/methodology'
RAW=ROOT/'03_data/raw/pack_specific_energy_20261006'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_csv(name, rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def calc(x,y,chem='NiMn'):
    # ANL/CSE-24/1 p42 Eq A1 Table31: x rated kWh; y model year.
    A,B,C,D,E=(5.266,20.60,1.129,.3537,-.08158) if chem=='NiMn' else (6.602,25.62,1.016,.3597,-.09757)
    assert x>5 and 2023<=y<=2035
    return 1000/(A+B/x**C-D*(y-2023)*math.exp(E*(y-2023)))
def main():
    sources=json.loads((RAW/'sources.json').read_text()); sm={s['source_id']:s for s in sources}
    for s in sources: assert sha(ROOT/s['raw_file'])==s['sha256'],s['source_id']
    write_csv('PACK_SPECIFIC_ENERGY_SOURCE_REGISTER.csv',sources)
    records=[]
    def add(i,sid,status,energy,mass,val=None,lo=None,hi=None,use='cross-check only',eclass='SOURCE_FACT',horizon='',assumption='',limits='',locator=''):
        s=sm[sid]
        records.append(dict(record_id=i,source_id=sid,source_type=s['source_type'],source_class=s['source_class'],organization_or_paper=s['organization'],year=s['year'],technology_status=status,scenario_horizon=horizon,energy_boundary=energy,mass_boundary=mass,source_reported_value_Wh_kg=val,e_pack_Wh_kg=None if mass=='CELL' else val,e_pack_min_Wh_kg=lo,e_pack_max_Wh_kg=hi,unit='Wh/kg_cell' if mass=='CELL' else 'Wh/kg_system' if mass=='SYSTEM' else 'Wh/kg_pack',evidence_class=eclass,use=use,assumptions=assumption,limitations=limits,url=s['url'],doi=s['doi'],source_locator=locator or s['locator'],accessed_date='2026-10-06'))
    bench=[]; sizes=[65,75,80,90,105,110,130]
    for y in [2023,2026,2030]:
        for x in sizes+[20]:
            bench.append(dict(source_id='P01',chemistry_model='NiMn_PHEV_EV',model_year=y,rated_energy_kWh=x,e_pack_Wh_kg=calc(x,y),role='SOURCE_COMPACT_BEV300_ANCHOR' if x==80 else 'SIZE_TRANSFER_DIAGNOSTIC_NOT_STAGE' if x==20 else 'SOURCE_LD_BEV_SIZE_RANGE',energy_boundary='RATED_TOTAL_C3_MODEL',mass_boundary='PACK',calculation='ANL Eq A1 Table31; correlation evaluation not new BatPaC simulation'))
    for y,k in [(2023,0),(2026,1),(2030,2)]:
        vals=[calc(x,y) for x in sizes]
        add(f'A{k}','P01','MODELED_REFERENCE' if k==0 else 'MODELED_PROJECTION','RATED_TOTAL_C3_MODEL','PACK',calc(80,y),use=f'B{k} candidate',eclass='DERIVED_FROM_PUBLISHED_PACK_MODEL',horizon=y,assumption='Source BEV300 compact 80 rated kWh /130 kW; nearest10 Wh/kg representative; source-defined pack engineering model',limits='One correlated model family; not three independent empirical studies; deployment year not guaranteed')
        add(f'R{k}','P01','MODELED_REFERENCE' if k==0 else 'MODELED_PROJECTION','RATED_TOTAL_C3_MODEL','PACK',lo=min(vals),hi=max(vals),use=f'B{k} candidate range context',eclass='DERIVED_FROM_PUBLISHED_PACK_MODEL',horizon=y,assumption='Seven source LD BEV rated sizes65/75/80/90/105/110/130; unweighted design envelope',limits='Not a market distribution or confidence interval')
        add(f'D{k}','P01','SIZE_TRANSFER_DIAGNOSTIC','RATED_TOTAL_C3_MODEL','PACK',calc(20,y),eclass='DERIVED_FROM_PUBLISHED_PACK_MODEL',horizon=y,assumption='Same published PHEV/EV correlation evaluated at20kWh only',limits='20kWh not a source BEV300 design; illustrates scale dependence; not alternative stage or target pack prediction')
    add('L0','P01','MODELED_REFERENCE','RATED_TOTAL_C3_MODEL','PACK',calc(80,2023,'LFP'),horizon=2023,eclass='DERIVED_FROM_PUBLISHED_PACK_MODEL',limits='Different chemistry family; not pooled with selected NiMn model anchors')
    for i,chem,lo,hi in [('Q1','LFP',125,145),('Q2','NCA',150,174),('Q3','NMC',140,180)]:
        add(i,'P03','EMPIRICAL_PRODUCTION_SAMPLE','SOURCE_PACK_ENERGY_GROSS_NET_UNSPECIFIED','PACK',lo=lo,hi=hi,use='B0 contextual corroboration only',assumption=f'{chem}; paper section3.1 reported range; database145 models2020-2024; variable-specific subsets',limits='No standardized gross/net numerator verified; raw benchmark data not publicly reproduced; no pooled median or gross conversion')
    add('F0','P04','MODELED_SCENARIO','SOURCE_ENERGY_GROSS_NET_UNSPECIFIED','PACK',135,120,150,horizon=2020,assumption='Source cell mass share0.60; cell200/225/250 Wh/kg',limits='Historical projection not observed contemporary fleet baseline; source factor not universal')
    add('F1','P04','MODELED_PROJECTION','SOURCE_ENERGY_GROSS_NET_UNSPECIFIED','PACK',185,170,205,horizon=2030,assumption='Source cell mass share0.60; source rounded pack outputs retained',limits='More conservative model than ANL; not pooled; not claimed independent confirmation of selected250')
    add('J1','P05','FUTURE_MODEL_SCENARIO','MODEL_PACK_ENERGY_WITH_OVERSIZING_BURDEN','PACK',350,use='rejected for primary numeric adoption',horizon='future; no fixed calendar year',assumption='Source f_burden0.45 accounts for inactive hardware/thermal and oversizing; cell about770 Wh/kg implied',limits='Legitimate modeled pack candidate, but no clean equivalence to selected ANL rated-total boundary; historical aspirational case; do not transplant energy reduction')
    add('N1','P06','ROADMAP_TARGET','SOURCE_ENERGY_GROSS_NET_UNSPECIFIED','PACK',400,use='rejected for primary numeric adoption',horizon='mid-2030s',assumption='Fluoride automotive pack; at least400',limits='Target not demonstrated; detailed pack overhead and energy test boundary unresolved')
    for i,val,status in [('C1',350,'CELL_DEMONSTRATED'),('C2',500,'CELL_TARGET')]:
        add(i,'P07',status,'CELL_DISCHARGE_ENERGY','CELL',val,use='rejected',limits='Cell only; no source pack conversion in this progress summary; not pack Wh/kg')
    add('I1','I01','MANUFACTURER_ANNOUNCED_UP_TO','SYSTEM_ENERGY_GROSS_NET_UNSPECIFIED','SYSTEM',255,assumption='Ternary CTP3.0; launch2022; mass production expected2023 in this release',limits='External check only; up-to value not independent measurement or guaranteed20kWh pack; not parameter source')
    add('I2','I01','MANUFACTURER_ANNOUNCED_UP_TO','SYSTEM_ENERGY_GROSS_NET_UNSPECIFIED','SYSTEM',160,assumption='LFP CTP3.0',limits='Different chemistry; external check only; not parameter source')
    add('I3','I02','MANUFACTURER_CELL_CLAIM','CELL_ENERGY','CELL',350,use='rejected',assumption='2026 Qilin Condensed statement explicitly cell',limits='Current industry update does not establish350Wh/kg pack; no conversion')
    write_csv('PACK_SPECIFIC_ENERGY_EVIDENCE_TABLE.csv',records)
    write_csv('PACK_SPECIFIC_ENERGY_REJECTED_CANDIDATES.csv',[r for r in records if r['use'].startswith('rejected')])
    write_csv('PACK_SPECIFIC_ENERGY_ANL_CALCULATIONS.csv',bench)
    stages=[]; masses=[]
    for k,(year,label) in enumerate([(2023,'CURRENT_CONVENTIONAL_REPRESENTATIVE'),(2026,'ADVANCED_PACK_PERFORMANCE'),(2030,'HIGH_SPECIFIC_ENERGY_PACK_DEVELOPMENT')]):
        raw=calc(80,year);selected=10*math.floor(raw/10+.5)
        m=20000/selected;m0=20000/180
        stages.append(dict(stage_id=f'B{k}',stage_interpretation=label,e_pack_Wh_kg=selected,unrounded_anchor_Wh_kg=raw,main_evidence=f'P01:A{k}',supporting_evidence='P03:Q1-Q3;P04:F0-F1' if k==0 else 'P05:J1 mechanism only;P04:F1 alternative lower projection',industry_cross_check='I01:I1-I2; not used for numeric selection',source_model_year=year,energy_boundary='RATED_TOTAL_C3_MODEL_GROSS_COMPATIBLE',mass_boundary='PACK_INCLUDING_IN_PACK_OVERHEAD_EXCLUDING_EXTERNAL_COOLING',evidence_status='QUALIFIED_RESEARCH_SCENARIO_WITH_SCALE_TRANSFER_ASSUMPTION',selection_rule='source80kWh compactBEV300 anchor rounded to nearest10; surrounding LD-BEV source sizes checked',target_implementation_status='NOT_VALIDATED',capacity_axis=False,fixed_pack_energy_kWh=20,fixed_usable_energy_assumed_kWh=18,execution_allowed=False))
        masses.append(dict(stage_id=f'B{k}',e_pack_Wh_kg=selected,E_pack_fixed_kWh=20,E_pack_fixed_Wh=20000,m_pack_model_kg=m,m_vehicle_reference_B0_kg=1100,m_nonpack_model_residual_kg=1100-m0,m_vehicle_model_kg=1100-m0+m,delta_pack_mass_vs_B0_kg=m-m0,delta_vehicle_mass_vs_B0_kg=m-m0,vehicle_mass_reduction_pct=(m0-m)/1100*100,E_vehicle_usable_fixed_assumed_kWh=18,mass_status='MODEL_IDENTITY_NOT_MEASURED_MINICAB_PACK',vehicle_energy_reduction=None))
    write_csv('PACK_SPECIFIC_ENERGY_STAGE_TABLE.csv',stages);write_csv('PACK_SPECIFIC_ENERGY_MASS_PROPAGATION.csv',masses)
    assert [s['e_pack_Wh_kg'] for s in stages]==[180,220,250]
    assert all(abs(m['m_pack_model_kg']*m['e_pack_Wh_kg']-20000)<1e-8 for m in masses)
    assert all(abs(m['delta_vehicle_mass_vs_B0_kg']-m['delta_pack_mass_vs_B0_kg'])<1e-9 for m in masses)
    assert len({r['record_id'] for r in records})==len(records)
    assert all(r['e_pack_Wh_kg'] is None for r in records if r['mass_boundary']=='CELL')
    assert all(r['source_class']=='TIER_1' and r['mass_boundary']=='PACK' for r in records if r['record_id'] in ['A0','A1','A2'])
    before=json.loads((RAW/'pre_task_artifact_hashes.json').read_text());authorized='01_research_design/methodology/BATTERY_CAPABILITY_DEVELOPMENT_STAGE_FRAMEWORK.md'
    protected={p:h for p,h in before.items() if p!=authorized}
    drift=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h];assert not drift,drift
    a=ROOT/'01_research_design/scenario_evaluation/battery_soc_authority_completion_20261005'
    cur=json.loads((a/'CURRENT_BATTERY_SOC_DISCHARGE_AUTHORITY.json').read_text());freeze=a/cur['freeze_path'];assert sha(freeze)==cur['freeze_sha256']
    params=json.loads(freeze.read_text())['parameters'];assert params==json.loads((a/'BATTERY_SOC_DISCHARGE_AUTHORITY.json').read_text())
    assert params['usable_capacity_kwh']==18 and params['r_DC_kwh_per_km']==.109
    code=ROOT/'01_research_design/scenario_evaluation/battery_soc_production_20261005/production_v2/run_no_charge.py'
    assert 'e=r*dd/D(1000)' in code.read_text()
    outputs=sorted(OUT.glob('PACK_SPECIFIC_ENERGY_*.csv'))+list(OUT.glob('PACK_SPECIFIC_ENERGY_EVIDENCE_REVIEW.md'))+[OUT/'BATTERY_CAPABILITY_DEVELOPMENT_STAGE_FRAMEWORK.md']
    validation=dict(review_date='2026-10-06',environment={'python':platform.python_version(),'dependencies':'Python standard library only','calculation_scope':'published correlation and mass arithmetic only'},status=dict(PACK_SPECIFIC_ENERGY_REVIEW='COMPLETE',PRIMARY_SCENARIO_DIMENSION='BATTERY_CAPABILITY_DEVELOPMENT_STAGE',PRIMARY_BATTERY_DEVELOPMENT_PARAMETER='e_pack_Wh_per_kg_pack',B0=180,B1=220,B2=250,NUMERIC_STATUS='SELECTED_FOR_DOCUMENTED_RESEARCH_SCENARIOS_NOT_AUTHORITY',ENERGY_CAPACITY_FIXED=True,VEHICLE_MASS_TO_ENERGY_CONSUMPTION_BRIDGE='NOT_IMPLEMENTED',TARGET_CHEMISTRY='UNRESOLVED',MATERIAL_TO_VEHICLE_MAPPING_USED=False,AUTHORITY_MODIFIED=False,FREEZE_CREATED=False,OPERATIONAL_EXPERIMENT_EXECUTED=False),source_count=len(sources),record_count=len(records),independence_note='ANL model years and sizes are correlated; P02 is method support not independent corroboration; raw empirical samples and projections are not pooled',validation=dict(raw_hashes='PASS',arithmetic='PASS',unique_ids='PASS',units='PASS_KWH_TO_WH_FACTOR1000',same_selected_boundary='PASS_WITH_RATED_TOTAL_DEFINITION',source_energy_boundary_unknown_preserved='PASS',cell_values_excluded='PASS',industry_not_primary='PASS',missing_energy_reduction_preserved='PASS',protected_hash_count=len(protected),protected_drift=drift),protected_sha256=protected,authorized_framework_before_sha256=before[authorized],current_authority_readback=params,model_inspection=dict(path=str(code.relative_to(ROOT)),sha256=sha(code),formula='e=r*distance_m/1000',mass_input_used=False,scope='Current production_v2 battery model only; no operational run'),raw_manifest_sha256=sha(RAW/'sources.json'),outputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in outputs},script_sha256=sha(Path(__file__)),next_stage=['VALIDATE_VEHICLE_MASS_TO_ENERGY_CONSUMPTION_BRIDGE','THEN_RUN_IDENTICAL_DELIVERY_TASK_WITH_B0_B1_B2_MASS','THEN_COMPARE_TOTAL_DELIVERY_ELECTRICAL_ENERGY'])
    (OUT/'PACK_SPECIFIC_ENERGY_VALIDATION.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'stages':[s['e_pack_Wh_kg'] for s in stages],'protected_unchanged':len(protected),'sources':len(sources),'records':len(records),'masses':masses},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
