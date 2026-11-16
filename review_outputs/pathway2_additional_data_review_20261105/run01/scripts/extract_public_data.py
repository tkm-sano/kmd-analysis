from pathlib import Path
import json,csv,math
import openpyxl,numpy as np,pandas as pd
from PIL import Image
O=Path(__file__).resolve().parents[1]
out=[];audit=[]
def curve(wb,sheet,qcol,vcol,start=4):
 s=wb[sheet];pairs=[]
 for row in s.iter_rows(min_row=start,values_only=False):
  q,v=row[qcol-1].value,row[vcol-1].value
  if isinstance(q,(int,float)) and isinstance(v,(int,float)) and math.isfinite(q) and math.isfinite(v):pairs.append((row[qcol-1].row,float(q),float(v)))
 return np.array(pairs)
def profile(source,sheet,qcol,vcol,label,split=False):
 wb=workbooks[source];a=curve(wb,sheet,qcol,vcol)
 reset=np.flatnonzero(np.diff(a[:,1])<-.01)+1
 segs=np.split(a,reset)
 if split:
  assert len(segs)==2,(source,sheet,qcol,len(segs))
  charge,dis=segs
  assert charge[-1,2]>charge[0,2] and dis[-1,2]<dis[0,2]
 else:dis=a;charge=None
 assert np.all(np.diff(dis[:,1])>=-1e-9)
 assert dis[0,2]>dis[-1,2]
 q=dis[:,1];v=dis[:,2];span=q[-1]-q[0]
 energy=float(np.trapezoid(v,q));avg=energy/span
 row=dict(source_id=source,sheet=sheet,label=label,column_Q=openpyxl.utils.get_column_letter(qcol),column_V=openpyxl.utils.get_column_letter(vcol),
          start_row=int(dis[0,0]),end_row=int(dis[-1,0]),n=len(dis),discharge_capacity_mAh_g=span,mean_discharge_voltage_V=avg,
          discharge_specific_energy_Wh_kg_positive_active=energy,start_V=v[0],end_V=v[-1],charge_capacity_mAh_g=charge[-1,1]-charge[0,1] if split else None,
          computed_CE_percent=100*span/(charge[-1,1]-charge[0,1]) if split else None,
          calculation='trapezoid V dQ / Qspan; no resampling, no interpolation; discharge identified by capacity reset',
          applicability='SENSITIVITY_ONLY_FOR_LP_S; numerical source-data derivation for related material')
 out.append(row)
 err=abs(energy-float(sum(.5*(v[1:]+v[:-1])*np.diff(q))))
 audit.append(dict(check='quadrature '+label,status='PASS' if err<1e-8 else 'FAIL',error=err))
 pd.DataFrame(dict(source_row=dis[:,0].astype(int),capacity_mAh_g=q,voltage_V=v)).to_csv(O/'evidence'/(label+'_discharge.csv'),index=False)
workbooks={n:openpyxl.load_workbook(O/'sources'/(n+'.xlsx'),data_only=True,read_only=True) for n in ['LMR2026_DATA','RATE2026_DATA']}
for qcol,vcol,p in [(1,2,'4620'),(4,5,'4330'),(7,8,'4320')]:profile('LMR2026_DATA','Supplementary Fig. 8',qcol,vcol,'LMR2026_protocol_'+p)
for material,q1 in [('H-SCLMR',1),('SCLMR',5),('PCLMR',9)]:
 for cycle,add in [(1,0),(2,2)]:profile('RATE2026_DATA','Figure S17',q1+add,q1+add+1,'RATE2026_'+material+'_formation_cycle'+str(cycle),True)
pd.DataFrame(out).to_csv(O/'evidence/PUBLIC_PROFILE_INTEGRALS.csv',index=False,float_format='%.10g')
# S17d is NORMAL CYCLING; S17a-c are FORMATION. Keep the time bases separate.
s=workbooks['RATE2026_DATA']['Figure S17'];ce=[]
for i,row in enumerate(out[3:]):
 material=['H-SCLMR','SCLMR','PCLMR'][i//2];cycle=i%2+1;col={'H-SCLMR':14,'SCLMR':15,'PCLMR':16}[material]
 reported=s.cell(row=cycle+3,column=col).value
 ce.append(dict(label=row['label'],source_cell=s.cell(row=cycle+3,column=col).coordinate,reported_NORMAL_CYCLING_CE_percent=reported,computed_FORMATION_CE_percent=row['computed_CE_percent'],status='NOT_COMPARABLE_DIFFERENT_RATE_AND_CYCLE_BASIS',basis='SI FigS17a-c formation 0.1C; FigS17d normal cycling 0.2C/0.5C at30C'))
pd.DataFrame(ce).to_csv(O/'evidence/CE_CROSSCHECK.csv',index=False)
# Source workbook first and last cycling values, not independent repeated experiments.
cycling=[]
s=workbooks['RATE2026_DATA']['Figure 4']
for col,material in [(87,'H-SCLMR'),(88,'PCLMR'),(89,'SCLMR')]:
 vals=[(r[85].row,r[85].value,r[col-1].value) for r in s.iter_rows(min_row=4) if isinstance(r[85].value,(int,float)) and isinstance(r[col-1].value,(int,float))]
 cycling.append(dict(source_id='RATE2026_DATA',sheet=s.title,material=material,cycle_first=vals[0][1],capacity_first=vals[0][2],cycle_last=vals[-1][1],capacity_last=vals[-1][2],retention_percent=100*vals[-1][2]/vals[0][2],cells=f'CH{vals[0][0]}:{openpyxl.utils.get_column_letter(col)}{vals[-1][0]}',scope='normal cycles after two formation cycles; mAh/g positive active'))
s=workbooks['LMR2026_DATA']['Figure 7']
vals=[(r[21].row,r[21].value,r[22].value) for r in s.iter_rows(min_row=4) if isinstance(r[21].value,(int,float)) and isinstance(r[22].value,(int,float))]
cycling.append(dict(source_id='LMR2026_DATA',sheet=s.title,material='Co-lean LMR 40Ah protocol 4.25-2.0V',cycle_first=vals[0][1],capacity_first=vals[0][2],cycle_last=vals[-1][1],capacity_last=vals[-1][2],retention_percent=100*vals[-1][2]/vals[0][2],cells=f'V{vals[0][0]}:W{vals[-1][0]}',scope='specific energy Wh/kg positive active, NOT complete cell mass basis'))
pd.DataFrame(cycling).to_csv(O/'evidence/PUBLIC_CYCLING_ENDPOINTS.csv',index=False)
# Fig.5g approximate mid/late-cycle points, directly from embedded raster, not new measurements.
a=np.asarray(Image.open(O/'evidence/source-17.png').convert('RGB')).astype(float)
R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]
maskblue=(B>180)&(G>110)&(G<215)&(B-R>65)&(G-R>25)
maskgray=(abs(R-G)<4)&(abs(G-B)<4)&(R>80)&(R<210)
digit=[]
for material,mask in [('LP',maskgray),('S-200',maskblue)]:
 for cycle in [5,10,20,40,60,80,100]:
  x=min(539.,10+(544-10)*cycle/100);xs=np.arange(max(12,int(round(x))-2),min(541,int(round(x))+2)+1)
  yy,xx=np.where(mask[35:225,xs]);yy=yy+35
  if len(yy)==0:continue
  # At these selected cycles data lie above inset (except final point outside inset width).
  y=float(np.median(yy));q=(432-y)*200/(432-40)
  digit.append(dict(material=material,cycle=cycle,x_pixel=x,y_pixel=y,capacity_mAh_g_approx=round(q),reading_resolution_mAh_g=5,
      method='median color-mask pixels in 5-column band; q=200*(432-y)/(432-40); x=min(539,10+534*n/100)',
      source='Chen Fig5g PDFp8 embedded source-17.png; main plot excludes inset',adoption='SENSITIVITY_ONLY',limitation='overlapping hollow markers; +/-5 mAh/g operational readout resolution, not statistical CI; cycle100 samples near99-100 to exclude frame; first cycle not assigned'))
pd.DataFrame(digit).to_csv(O/'evidence/CHEN_FIG5G_DIGITIZED.csv',index=False)
pd.DataFrame(audit).to_csv(O/'evidence/EXTRACTION_AUDIT.csv',index=False)
print(pd.DataFrame(out)[['label','discharge_capacity_mAh_g','mean_discharge_voltage_V','computed_CE_percent']].to_string(index=False))
print(pd.DataFrame(ce)[['label','status']].to_string(index=False))
print(pd.DataFrame(cycling).to_string(index=False))
print(pd.DataFrame(digit)[['material','cycle','capacity_mAh_g_approx']].to_string(index=False))
assert all(r['status']=='PASS' for r in audit)
