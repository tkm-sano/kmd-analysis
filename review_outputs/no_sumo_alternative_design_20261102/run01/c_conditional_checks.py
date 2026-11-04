"""Targeted independent material arithmetic and saved-result readback only."""
from support import *
def mass(s):
 p={k:F(str(v['value'])) for k,v in s['parameters'].items()};Q=p['gross_energy']/p['voltage'];positive=Q/p['q_ref']/p['utilization'];negative=Q*p['np_ratio']/p['q_negative'];return positive/p['f_positive']+negative/p['f_negative']+s['cell_topology']['n_cells']*p['cell_other_mass']+p['pack_other_mass']+p['additional_mass']
def components(x):
 f=lambda k:F(x[k]);Q=f('gross_design_Wh')/f('mean_voltage_design_V');mp=Q/f('q_reference_Ah_kg')/f('positive_utilization');mn=Q*f('NP_after_formation')/f('negative_q_Ah_kg')/(1-f('negative_unavailable_fraction'));fp=F('.96') if x['series'].startswith('A_') else F('.75');ap=f('positive_face_area_m2');an=f('negative_face_area_m2');ep=f('positive_porosity');en=f('negative_porosity')
 vals={'positive_coating_kg':mp/fp,'negative_coating_kg':mn/F('.98'),'Al_mass_kg':ap/2*f('Al_thickness_m')*2699,'Cu_mass_kg':an/2*f('Cu_thickness_m')*8960,'separator_dry_mass_kg':max(ap,an)*f('separator_areal_mass_kg_m2'),'liquid_mass_kg':(mp/fp/4458*ep/(1-ep)+mn/F('.98')/2200*en/(1-en)+max(ap,an)*F('.000025')*F('.41')+f('extra_liquid_volume_m3'))*1300};return vals
def main():
 t=time.monotonic();t8=U/'review_outputs/material_ev_stage2_20261026/run02';t9=U/'review_outputs/t09_open_data_model_20261029/run01';bridge=U/'review_outputs/t08_t09_conditional_bridge_20261030/run01';sc=js(t8/'SCENARIOS.json')['scenarios'];m={s['scenario_id']:mass(s) for s in sc};delta=m['COND_LP_REF']-m['COND_S200_REF'];check('T08 target difference',5.448297415,delta,1e-9)
 # These capacities are retention back-calculated references, not observed initial capacities.
 check('LP retention reference arithmetic',F('171.875'),F(121)/F('.704'));check('S200 retention reference arithmetic',195.959595959596,F(194)/F('.99'),1e-10)
 ener=rows(t8/'MATERIAL_ENERGY.csv',['dataset','physical_instance_id','method','rolling_case','scenario_id']);data={(x['physical_instance_id'],x['rolling_case'],x['scenario_id']):x for x in ener if x['dataset']=='CLASSICAL'};out=[]
 for roll in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
  pairs=[(x,data[(pid,roll,'COND_S200_REF')]) for (pid,r,s),x in data.items() if r==roll and s=='COND_LP_REF'];tot=sum((F(x['net_DC_Wh']) for x,y in pairs),F(0));saving=sum((F(x['net_DC_Wh'])-F(y['net_DC_Wh']) for x,y in pairs),F(0));mean=sum(((F(x['net_DC_Wh'])-F(y['net_DC_Wh']))/F(x['net_DC_Wh'])*100 for x,y in pairs),F(0))/len(pairs);out.append({'rolling_case':roll,'trajectory_count':len(pairs),'baseline_sum_Wh':float(tot),'saving_sum_Wh':float(saving),'weighted_saving_percent':float(100*saving/tot),'mean_individual_percent':float(mean)});check(roll+' matched trajectories',460,len(pairs))
 check('T08 lower weighted target',.412579010,out[0]['weighted_saving_percent'],1e-9);table('C_T08_SAVED_DC_AGGREGATE.csv',out)
 pack=rows(t9/'PACK_20KWH_SENSITIVITY.csv');bounds=rows(bridge/'T09_MASS_BOUNDARIES.csv',['scenario_id']);selected={x['scenario_id']:x for x in bounds if x['scenario_id'] in ['T09_ROW_031','T09_ROW_032','T09_ROW_103','T09_ROW_104']};calc=[];known={}
 for sid,b in selected.items():
  ix=int(sid.rsplit('_',1)[1])-1;x=pack[ix];v=components(x)
  for key,val in v.items():check(sid+' '+key,F(x[key]),val,1e-8)
  total=sum(v.values(),F(0));known[sid]=total;check(sid+' known sum',F(x['known_cell_components_sum_kg']),total,1e-8);calc.append({'scenario_id':sid,'source_csv_row':ix+2,'material':x['material'],'policy':x['area_policy'],'known_mass_independent_kg':float(total),'known_mass_saved_kg':x['known_cell_components_sum_kg'],'complete_pack_mass_saved_kg':x['complete_pack_mass_kg']})
 bload=known['T09_ROW_031']-known['T09_ROW_032'];barea=known['T09_ROW_103']-known['T09_ROW_104'];check('T09 fixed loading expected',9.722608121,bload,1e-9);check('T09 fixed area expected',5.977891152,barea,1e-9);table('C_T09_COMPONENT_SMALL_CHECKS.csv',calc)
 check('T09 unknown pack rows',183,sum(not x['complete_pack_mass_kg'] for x in pack));bad=[{'source_row':i+2,'material':x['material'],'area_policy':x['area_policy'],'overlap_condition':x['overlap_condition'],'positive_face_area_m2':x['positive_face_area_m2'],'negative_face_area_m2':x['negative_face_area_m2']} for i,x in enumerate(pack) if x['overlap_condition']=='FAIL_IF_SAME_STACK_FOOTPRINT'];check('T09 full opposing footprint failure',1,len(bad));table('C_T09_PRESERVED_FAIL.csv',bad)
 boundary=[]
 for policy,b in [('fixed_loading',bload),('fixed_area_LP',barea)]:
  for d in [b-1,b,b+1]:boundary.append({'policy':policy,'known_saving_b_kg':float(b),'unknown_difference_S_minus_LP_kg':float(d),'net_mass_saving_b_minus_delta_kg':float(b-d),'state':'SAVING' if d<b else 'CANCELLED' if d==b else 'REVERSED','basis':'DERIVED_BOUNDARY_FIXTURE_NOT_MEASURED_UNKNOWN_BOM'})
 table('C_UNKNOWN_MASS_BOUNDARY_FIXTURES.csv',boundary)
 response=rows(bridge/'DC_MASS_RESPONSE.csv');few=response[:6];readbacks=[]
 for i,x in enumerate(few,2):
  net=F(x['known_mass_boundary_kg'])-F(x['unknown_mass_difference_probe_kg']);dc=F(x['baseline_DC_Wh'])-F(x['S_DC_Wh']);check('bridge mass row'+str(i),F(x['net_mass_saving_probe_kg']),net,1e-8);check('bridge DC row'+str(i),F(x['DC_saving_Wh']),dc,1e-8);readbacks.append({'source_row':i,'pair_id':x['pair_id'],'probe_id':x['probe_id'],'trajectory_sha256':x['trajectory_sha256'],'mass_saving_kg':float(net),'DC_saving_Wh':float(dc),'status':'PASS_CONDITIONAL_FIXED_TRAJECTORY'})
 table('C_BRIDGE_SMALL_READBACK.csv',readbacks)
 for p in [t9/'PARAMETER_SOURCES.csv',t9/'DATA_PROVENANCE.csv',t9/'CELL_MASS_ACCOUNTING_MODEL.md',t9/'ELECTRODE_GEOMETRY_MODEL.md',t8/'T08.json',t8/'DC_BOUNDARIES.json',bridge/'T08_T09_DC_COMPARISON.csv',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json']:use(p).read_text()
 use(E/'SOURCES/chen2020.pdf');use(O/'CHEN2020_TEXT.txt').read_text();dump('C_LITERATURE_LOCATORS.json',{'pdf_path':str(E/'SOURCES/chen2020.pdf'),'pdf_sha256':sha(E/'SOURCES/chen2020.pdf'),'text_path':str(O/'CHEN2020_TEXT.txt'),'text_sha256':sha(O/'CHEN2020_TEXT.txt'),'retention_locator':'Fig5g and extracted text lines604-609: LP121/70.4%, S200194/99.0%, after100cycles at1C','calculation_locator':'Computations, extracted text lines867-868: DFT implemented in VASP; not quantum-computer material improvement','interpretation':'Published material test conditions, not measured full pack, vehicle or quantum-computing benefit'})
 for root in [t8,t9,bridge]:
  for p in (root/'SOURCE_SNAPSHOT').rglob('*.py'):use(p).read_text()
 finish('C',t,{'T08_mass_difference_kg':float(delta),'T08_lower_weighted_percent':out[0]['weighted_saving_percent'],'T09_known_fixed_loading_difference_kg':float(bload),'T09_known_fixed_area_difference_kg':float(barea),'T09_complete_mass_HOLD_rows':183,'T09_preserved_footprint_FAIL_rows':len(bad),'bridge_saved_rows':len(response),'bridge_saved_trajectory_hashes':len({x['trajectory_sha256'] for x in response}),'bridge_new_small_checks':len(few),'new_trajectory_energy_evaluations':0,'evidence':'CONDITIONAL_ARCHIVED_SPEED_TRAJECTORIES_NOT_ACCEPTED_REGIONAL_TRAFFIC','quantum_to_material_improvement':'UNTESTED'})
if __name__=='__main__':main()
