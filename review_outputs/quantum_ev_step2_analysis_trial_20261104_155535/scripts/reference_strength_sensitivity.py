from common import *
t=time.perf_counter();ref=frame(O/'EXACT_REFERENCE_STATUS.csv',dtype=str);lookup=ref.set_index('problem_id');pairs=frame(O/'PATH1_PAIRED_COMPARISONS.csv');ip=frame(O/'PATH1_INPUT_CONFIG_STATISTICS.csv')
for col in ['reference_evidence_class','status']:
 name='reference_evidence_class' if col=='reference_evidence_class' else 'reference_status'
 pairs[name]=pairs.problem_id.map(lookup[col]);ip[name]=ip.problem_id.map(lookup[col])
table('PATH1_PAIRED_COMPARISONS.csv',pairs);table('PATH1_INPUT_CONFIG_STATISTICS.csv',ip);p=pairs[pairs.primary_comparison].copy();p['quantum_gap_percent']=pd.to_numeric(p.quantum_gap_percent,errors='coerce');p['optimal_match_numeric']=p.optimal_match.map(lambda v:float(v is True or str(v)=='True'));rows=[]
for scale in sorted(p.scale.unique())+['ALL']:
 g=p if scale=='ALL' else p[p.scale==scale]
 for cfg,h in g.groupby('config_id'):
  for label,subset in [('ACCEPTED_REFERENCE',h[h.exact_available]),('EXCLUDE_SAVED_MIP_ONLY',h[h.exact_available & h.reference_evidence_class.ne('SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR')])]:
   ii=subset.groupby('problem_id').agg(gap=('quantum_gap_percent','mean'),optimal=('optimal_match_numeric','mean'));rows.append(dict(scale=scale,config_id=cfg,reference_scope=label,reference_inputs=len(ii),reference_measurement_reps=len(subset),input_equal_weight_gap_percent=ii.gap.mean(),optimal_match_percent=100*ii.optimal.mean(),scope='reference-evidence sensitivity; selected subsets, not independent samples',excluded_evidence='41 saved MIP equality without external certificate' if label=='EXCLUDE_SAVED_MIP_ONLY' else 'none among accepted414'))
table('PATH1_REFERENCE_STRENGTH_SENSITIVITY.csv',rows);ck('strength sensitivity all scope414/373',set(x['reference_inputs'] for x in rows if x['scale']=='ALL')=={414,373});finish('REFERENCE_STRENGTH_SENSITIVITY',t,{'rows':len(rows),'new_reference_metadata_columns':True,'primary_values_changed':False})
