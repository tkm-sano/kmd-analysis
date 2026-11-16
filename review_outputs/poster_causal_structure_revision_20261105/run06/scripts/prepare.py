from pathlib import Path
import csv,json,hashlib,shutil,statistics,collections
R=Path(__file__).resolve().parents[1]; ROOT=R.parents[2]
P=ROOT/'review_outputs/quantum_ev_step5_20261105'; M=ROOT/'review_outputs/t08_t09_interaction_boundaries_20261105/run01'; OLD=R.parent/'run05'
paths=[OLD/'poster.pptx',OLD/'poster.pdf',OLD/'poster_text.txt',P/'THESIS_FULL_TEXT.md',P/'THESIS_STEP5_REVISED.docx',P/'STEP5_FINAL_REPORT.md',P/'STEP5_PATHWAY1_CONDITIONS.md',P/'data/INPUT_UNIT_STATISTICS.csv',P/'data/IMPROVED_EQUAL_WORSENED.csv',P/'data/FULL_SUPPORT_EXISTENCE_BY_INPUT.csv',P/'data/DC_MASS_KERNEL_INDEPENDENT.csv',P/'data/DC_MASS_KERNEL_SUMMARY.csv',P/'data/B_INPUT_CONDITIONS_460.csv',M/'FINAL_REPORT_JA.md',M/'INTERACTION_RESULTS.csv',M/'BOUNDARY_SURFACES.csv',M/'data/T09_UNKNOWN_REPRESENTATIVES.csv',M/'data/BOUNDARY_REPRESENTATIVE_DC.csv',M/'data/T09_POLICY_COMPARISON.csv',M/'data/PARAMETER_PROVENANCE.csv',M/'T08_T09_COMPARABILITY.md',M/'evidence/RUN_RESULT.json',M/'evidence/NUMERICAL_AUDIT.csv',OLD/'evidence/SCALE_METHOD_STATISTICS.csv']
def read(f):return list(csv.DictReader(f.open(encoding='utf-8-sig')))
def write(name,rows):
 with (R/'evidence'/name).open('w',newline='',encoding='utf-8-sig') as o:
  w=csv.DictWriter(o,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write('SOURCE_SHA256.csv',[dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in paths])
for f in [P/'data/IMPROVED_EQUAL_WORSENED.csv',P/'data/FULL_SUPPORT_EXISTENCE_BY_INPUT.csv',P/'data/DC_MASS_KERNEL_SUMMARY.csv',OLD/'evidence/SCALE_METHOD_STATISTICS.csv',M/'data/T09_UNKNOWN_REPRESENTATIVES.csv',M/'data/BOUNDARY_REPRESENTATIVE_DC.csv',M/'data/PARAMETER_PROVENANCE.csv']:
 shutil.copy2(f,R/'evidence'/f.name)
# Saved trajectory derivatives only; histogram aggregation is descriptive, no new simulation.
rows=read(P/'data/DC_MASS_KERNEL_INDEPENDENT.csv');assert len(rows)==920
hist=[]
for case in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
 rr=[r for r in rows if r['rolling_case']==case];assert len(rr)==460
 vals=[float(r['right_derivative_lo_Wh_kg']) for r in rr]
 assert min(vals)>0 and all(float(r['mass_lo_kg'])==1000 and float(r['mass_hi_kg'])==1250 for r in rr)
 for lo in range(6):hist.append(dict(rolling_case=case,bin_lower_Wh_kg=lo,bin_upper_Wh_kg=lo+1,count=sum(lo<=v<lo+1 for v in vals),denominator=460))
 summary=next(r for r in read(P/'data/DC_MASS_KERNEL_SUMMARY.csv') if r['rolling_case']==case)
 assert abs(statistics.mean(vals)-float(summary['slope_mean']))<1e-10
 assert abs(statistics.stdev(vals)-float(summary['slope_SD']))<1e-10
write('MASS_RESPONSE_HISTOGRAM.csv',hist)
# Verify all six displayed local settings are identical within every scale.
u=read(P/'data/INPUT_UNIT_STATISTICS.csv');print('unit fields',list(u[0]))
s=read(OLD/'evidence/SCALE_METHOD_STATISTICS.csv');assert len(s)==18
cnt=read(P/'data/IMPROVED_EQUAL_WORSENED.csv');allc={r['classification']:int(r['count']) for r in cnt if r['level']=='all_plans'};assert allc==dict(improved=0,equal=28200,worsened=8600)
f=read(P/'data/FULL_SUPPORT_EXISTENCE_BY_INPUT.csv');counts=collections.Counter(r['A_full_support_status'] for r in f);assert len(f)==460
result=json.loads((M/'evidence/RUN_RESULT.json').read_text());assert result['failures']==0 and result['checks']==12374
(R/'evidence/DATA_BINDING.json').write_text(json.dumps(dict(counts=allc,support_counts=dict(counts),material_audit=result,material_sources='Latest additional calculation is distinct from Step5 thesis; inverse capacity remains reference only.'),ensure_ascii=False,indent=2))
print('Read-only evidence binding PASS')
