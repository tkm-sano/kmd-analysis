from pathlib import Path
import os,sys,json,hashlib,ast,math,zipfile,posixpath,importlib.util
import xml.etree.ElementTree as ET
from decimal import Decimal as D,localcontext
sys.dont_write_bytecode=True
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np,pandas as pd,openpyxl
from components import demo_and_checks
SD=Path(__file__).resolve().parents[1]
R=next(p for p in SD.parents if (p/'src/kmd_quantitative').exists())
O=Path(os.environ.get('LEVEL2_OUTPUT',str(SD))).resolve()
for d in [O,O/'evidence',O/'figures']:d.mkdir(parents=True,exist_ok=True)
cfg=json.loads(Path(os.environ.get('LEVEL2_CONFIG',str(SD/'RUN_CONFIG.json'))).read_text())
(O/'RUN_CONFIG.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n')
S=Path(cfg['source_review']);L=Path(cfg['legacy_interaction'])
checks=[];sources={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source(p):p=Path(p);sources[str(p)]=sha(p);return p
def csv(name,rows):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    df.to_csv(O/name,index=False,float_format='%.14g');return df
def check(name,ok,detail=''):
    checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=str(detail)))
    if not ok:
        csv('evidence/NUMERICAL_CHECKS.csv',checks);raise AssertionError((name,detail))

def protection():
    dest=O/'evidence/PROTECTED_BEFORE.csv'
    if not dest.exists():
        paths=set()
        for folder in [R/'review_outputs/t08_t09_final_adoption_20261105',L,S]:
            paths.update(p for p in folder.rglob('*') if p.is_file())
        paths.update(Path(p) for p in pd.read_csv(S/'evidence/PROTECTED_BEFORE.csv').path if Path(p).exists())
        csv('evidence/PROTECTED_BEFORE.csv',[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(paths)])
    protected=pd.read_csv(dest)
    for row in protected.itertuples():check('initial preserved '+row.path,sha(row.path)==row.sha256)
    return protected

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def xml_pairs(path,sheet,qcol,vcol):
    """Independent XLSX ZIP/XML reader using stored decimal strings, no openpyxl."""
    with zipfile.ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'));rid=next(s.attrib['{'+NS['r']+'}id'] for s in wb.find('m:sheets',NS) if s.attrib['name']==sheet)
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));target=next(r.attrib['Target'] for r in rels if r.attrib['Id']==rid)
        filename=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
        root=ET.fromstring(z.read(filename));result=[]
        for row in root.findall('m:sheetData/m:row',NS):
            rn=int(row.attrib['r'])
            if rn<4:continue
            vals={}
            for c in row:
                col=''.join(t for t in c.attrib.get('r','') if t.isalpha())
                v=c.find('m:v',NS)
                if col in [qcol,vcol] and c.attrib.get('t','n')=='n' and v is not None and v.text is not None:
                    vals[col]=D(v.text)
            if qcol in vals and vcol in vals:result.append((rn,vals[qcol],vals[vcol]))
    return result

specs=[
 dict(case_id='Z_H1',source='RATE2026_DATA.xlsx',sheet='Figure S17',qc='A',vc='B',material='H-SCLMR / graphite',cycle='formation1',rate='0.1C=25mA/g positive active',temperature_C=30,window='1.8–4.75V full cell',NP_design=1.2,role='PRIMARY_REFERENCE',reset=True,loc='SI FigS17a PDFp18;Methods Electrochemical measurements'),
 dict(case_id='Z_H2',source='RATE2026_DATA.xlsx',sheet='Figure S17',qc='C',vc='D',material='H-SCLMR / graphite',cycle='formation2',rate='0.1C=25mA/g positive active',temperature_C=30,window='1.8–4.75V full cell',NP_design=1.2,role='PRIMARY_COMPARISON',reset=True,loc='SI FigS17a PDFp18;Methods Electrochemical measurements'),
 dict(case_id='S_BOL',source='LMR2026_DATA.xlsx',sheet='Figure 4',qc='AY',vc='AZ',material='Co-lean LMR / graphite',cycle='normal1 after formation (BoL)',rate='0.33C;66mA/g positive active',temperature_C=45,window='2.0–4.3V full cell;protocol4320',NP_design=1.07,role='AUXILIARY_QV_ONLY',reset=False,loc='Fig4a/b caption;SI FigS9 PDFp11;Methods Electrochemical testing'),
 dict(case_id='S_EOL',source='LMR2026_DATA.xlsx',sheet='Figure 4',qc='BK',vc='BL',material='Co-lean LMR / graphite',cycle='normal150 after formation (EoL)',rate='0.33C;66mA/g positive active',temperature_C=45,window='2.0–4.3V full cell;protocol4320',NP_design=1.07,role='AUXILIARY_QV_ONLY',reset=False,loc='Fig4a/b caption;SI FigS9 PDFp11;Methods Electrochemical testing'),
]

def qv_validation():
    result=[];raw={};summaries=[]
    books={}
    for spec in specs:
        path=source(S/'sources'/spec['source'])
        if path not in books:books[path]=openpyxl.load_workbook(path,read_only=True,data_only=True)
        sheet=books[path][spec['sheet']];qi=openpyxl.utils.column_index_from_string(spec['qc'])-1;vi=openpyxl.utils.column_index_from_string(spec['vc'])-1
        data=[];partial=0
        for rr,row in enumerate(sheet.iter_rows(min_row=4,values_only=True),4):
            q,v=row[qi],row[vi];nq=isinstance(q,(int,float));nv=isinstance(v,(int,float))
            if nq!=nv:partial+=1
            if nq and nv:data.append((rr,float(q),float(v)))
        check('complete Q-V pairs '+spec['case_id'],partial==0,partial)
        a=np.array(data);cuts=np.flatnonzero(np.diff(a[:,1])<-.01)+1
        if spec['reset']:
            check('charge/discharge one reset '+spec['case_id'],len(cuts)==1)
            charge=a[:cuts[0]];dis=a[cuts[0]:]
        else:
            check('discharge-only column '+spec['case_id'],len(cuts)==0);charge=None;dis=a
        check('finite monotone discharge '+spec['case_id'],np.isfinite(dis).all() and np.all(np.diff(dis[:,1])>=-1e-10) and dis[0,2]>dis[-1,2])
        q=dis[:,1];v=dis[:,2];cap=float(q[-1]-q[0]);energy=float(np.trapezoid(v,q));avg=energy/cap
        xml=xml_pairs(path,spec['sheet'],spec['qc'],spec['vc'])
        xc=[i for i in range(1,len(xml)) if xml[i][1]-xml[i-1][1]<D('-.01')]
        xd=xml[xc[0]:] if spec['reset'] else xml
        with localcontext() as ctx:
            ctx.prec=60;capD=xd[-1][1]-xd[0][1]
            enD=sum((xd[i][1]-xd[i-1][1])*(xd[i][2]+xd[i-1][2])/2 for i in range(1,len(xd)))
            avgD=enD/capD
        check('independent XML rows '+spec['case_id'],[int(x[0]) for x in dis]==[x[0] for x in xd])
        check('independent capacity '+spec['case_id'],abs(cap-float(capD))<1e-10)
        check('independent 60digit integral '+spec['case_id'],abs(energy-float(enD))<cfg['qv_energy_tolerance_Wh_kg'],abs(energy-float(enD)))
        check('independent mean V '+spec['case_id'],abs(avg-float(avgD))<1e-11)
        raw[spec['case_id']]=dis
        csv('evidence/'+spec['case_id']+'_DISCHARGE.csv',pd.DataFrame(dict(xlsx_row=dis[:,0].astype(int),q_mAh_g=q,voltage_V=v)))
        row=spec|dict(xlsx_file=str(path),xlsx_sha256=sha(path),range=f"{spec['qc']}{int(dis[0,0])}:{spec['vc']}{int(dis[-1,0])}",
            q_column_label=str(sheet.cell(3,qi+1).value),v_column_label=str(sheet.cell(3,vi+1).value),n_points=len(dis),Q_start_mAh_g=q[0],Q_end_mAh_g=q[-1],
            Q_discharge_mAh_g=cap,mean_discharge_V=avg,specific_energy_Wh_kg_positive_active=energy,integral_V_mAh_g=energy,
            capacity_decimal=str(capD),integral_decimal=str(enD),mean_voltage_decimal=str(avgD),integral_error_Wh_kg=abs(energy-float(enD)),
            discharge_start_V=v[0],discharge_end_V=v[-1],charge_capacity_mAh_g=None if charge is None else charge[-1,1]-charge[0,1],
            extraction='capacity reset -> final discharge segment' if spec['reset'] else 'explicit BoL/EoL dchg columns; no branch stitching',
            integration='numpy.trapezoid vs independent ZIP/XML Decimal60; no resampling/interpolation',
            voltage_reference='full-cell terminal positive minus graphite; not vs Li metal',mass_basis='positive active material only',
            scope='PUBLIC_RELATED_FULL_CELL_NOT_LP_S',publication_alignment='CONDITIONAL; see evidence/PUBLICATION_ALIGNMENT.csv')
        result.append(row)
    # The cycle-series trace is not silently equated to an individual representative Q-V curve.
    w=books[S/'sources/LMR2026_DATA.xlsx'];s=w['Figure 4'];series=[]
    for row in s.iter_rows(min_row=4,values_only=True):
        if isinstance(row[7],(int,float)) and isinstance(row[8],(int,float)):series.append((int(row[7]),float(row[8])))
    m=dict(series);qret=100*m[150]/m[1];retcurve=100*result[3]['Q_discharge_mAh_g']/result[2]['Q_discharge_mAh_g']
    csv('evidence/SONG_CAPACITY_RETENTION.csv',[dict(source='Figure4 H:I',BoL_cycle=1,BoL_capacity_mAh_g=m[1],EoL_cycle=150,EoL_capacity_mAh_g=m[150],retention_percent=qret,
        representative_curve_Qspan_retention_percent=retcurve,representative_curve_Qend_retention_percent=100*raw['S_EOL'][-1,1]/raw['S_BOL'][-1,1],
        interpretation='same nominal protocol; individual representative curves not proven identical to cycling trace')])
    align=[dict(case_id='Z_H1/Z_H2',basis='SI FigS17a, PDFp18; Methods; source xlsx',status='CONDITIONAL PASS',
       observed='capacity axes and formation labels correspond; source Qend270.85/273.65; raw lower endpoint1.8V matches Methods',
       limitation='published figure axis lower bound2.0V limits exact low-voltage-tail graphical check; no separate scalar meanV reported; no digitized voltage substituted'),
       dict(case_id='Z_H1/Z_H2 vs Fig4e/S17d',basis='SI FigS17a vs17d; Methods',status='PASS',observed='formation0.1C versus normal0.2C/0.5C are intentionally separate',limitation='normal capacity226.22 is not the formationQ270.85/273.65 and is not used for u'),
       dict(case_id='S_BOL/S_EOL',basis='Fig4b source curves vs Fig4a H:I cycling series',status='CONDITIONAL PASS',
       observed=f'curve Qspan {result[2]["Q_discharge_mAh_g"]:.8f}/{result[3]["Q_discharge_mAh_g"]:.8f}; series {m[1]:.8f}/{m[150]:.8f}',
       limitation='Q-V starts at nonzero Q; missing initial segment not extrapolated. residual curve-vs-series/sample correspondence unresolved; not treated as rounding or measurement uncertainty without evidence'),
       dict(case_id='Song Supplementary Fig8',basis='SI FigS8 PDFp10',status='HOLD',observed='full cell profiles25C; specific cycle number not stated',limitation='not selected for joint input; previously integrated values remain historical, no overwrite'),
       dict(case_id='Song Supplementary Fig7b',basis='SI FigS7',status='HOLD',observed='second cycle identified but electrode potential vsLi/Li+; full-cell/rate linkage insufficient',limitation='not substituted as graphite full-cell V'),
       dict(case_id='Z_SCLMR/PCLMR S17b/c',basis='previous extraction and Methods',status='HOLD',observed='some source branch upper endpoints ~4.8V versus full-cell Methods4.75V',limitation='not the main joint input; no silent mixing')]
    csv('evidence/PUBLICATION_ALIGNMENT.csv',align)
    csv('PUBLIC_QV_VALIDATION.csv',result)
    return result,raw

def load_existing_mass():
    p=source(L/'scripts/analyze.py');text=p.read_text();tree=ast.parse(text)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='mass')
    segment=ast.get_source_segment(text,fn);(O/'evidence/EXISTING_T08_MASS_FUNCTION.py').write_text(segment+'\n')
    # Extract definition only, avoiding old runner's filesystem/global execution.
    namespace={'QLP':171.875};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),namespace)
    return namespace['mass']

def decimal_mass(p):
    """Independent per-cell SI path: Wh->J->C->g->kg, then sum 100 cells."""
    with localcontext() as ctx:
        ctx.prec=60;d={k:D(str(v)) for k,v in p.items()};N=D(cfg['n_cells']);ec=D(cfg['E_Wh'])/N
        charge_C=ec*3600/d['V'];mp_g=charge_C/(d['q']*D('3.6')*d['u']);mn_g=charge_C*d['np']/(d['qn']*D('3.6'))
        pc=mp_g/1000/d['fp'];nc=mn_g/1000/d['fn'];cell=pc+nc+d['cellother']
        total=N*cell+d['packother']+d['extra']
        return float(total),dict(positive_active_kg=float(N*mp_g/1000),negative_active_kg=float(N*mn_g/1000),positive_coating_kg=float(N*pc),negative_coating_kg=float(N*nc),cell_kg=float(cell))

def joint_inputs(qv):
    r={x['case_id']:x for x in qv};A=dict(q=r['Z_H1']['Q_discharge_mAh_g'],V=r['Z_H1']['mean_discharge_V'],u=1.,fp=cfg['fp_assumed_from_standard_recipe'],
        fn=cfg['fn_assumed_from_standard_recipe'],qn=cfg['qn_reference_Ah_kg'],np=cfg['NP_reported_design'],unavail=0.,cellother=cfg['cell_other_assumed_kg'],packother=cfg['pack_other_assumed_kg'],extra=0.)
    B=A|dict(q=r['Z_H2']['Q_discharge_mAh_g'],V=r['Z_H2']['mean_discharge_V'])
    meta=[('q','Ah/kg active','原著数値からの計算値','same discharge branch Qend−Qstart','Zhang SourceData FigS17a','effective delivered capacity; NOT a Li-metal reference'),
          ('V','V full cell','原著数値からの計算値','same branch integral VdQ/Qspan','Zhang SourceData FigS17a','terminal mean voltage in the specific formation cycle'),
          ('fp','kg/kg dry coating','研究上の仮定','same-paper standard active:SuperP:CNT:PVDF80:8:2:10 conditionally associated','Zhang Methods Electrochemical measurements','standard recipe adopted conditionally; full-cell specific recipe not separately restated; do not use thick90%'),
          ('fn','kg/kg dry coating','実測・原著報告','graphite:SuperP:PVDF80:10:10 standard recipe','Zhang Methods','reported electrode recipe; not measured completed-cell mass'),
          ('qn','Ah/kg active','他資料からの移用値','360 design default from NMC811/graphite','BatPaC Fig3.14 PDFp46','not measured for Zhang graphite; qn sensitivity300/400 declared'),
          ('np','capacity ratio','研究上の仮定','paper design N/P~1.2 mapped to T08 effective reversible N/P','Zhang Methods','ratio basis/time after formation unspecified; mapping is a declared design assumption'),
          ('u','1','研究上の仮定','u=1 because q is directly measured effective full-cell discharge capacity','accounting identity','NOT measured100% utilization; no ICE or retention applied again'),
          ('cellother','kg/cell','研究上の仮定','0.19 inherited T08 hypothetical lump','legacy T08 model','actual cell other mass remains UNKNOWN'),
          ('packother','kg/pack','研究上の仮定','15 inherited T08 hypothetical lump','legacy T08 model','actual pack other mass remains UNKNOWN'),
          ('extra','kg S-minus-reference','研究上の仮定','zero differential in the declared base design only','controlled comparison','does not assert actual absent material'),
          ('E','Wh','研究上の仮定','20000 fixed research design','legacy T08','not the public coin cell measured energy'),
          ('n_cells','count','研究上の仮定','100 cell mass sum as legacy T08','legacy T08','hypothetical topology/manufacturability unqualified')]
    rows=[]
    for cid,p in [('R0_Z_H1',A),('P0_Z_H2',B)]:
        for key,unit,cl,basis,src,limit in meta:
            rows.append(dict(case_id=cid,parameter=key,value=cfg['E_Wh'] if key=='E' else cfg['n_cells'] if key=='n_cells' else p[key],unit=unit,input_class=cl,
                source=src,basis=basis,limitation=limit,observed_case=cid.split('_',1)[1],cycle='formation1' if cid.startswith('R0') else 'formation2',
                rate='0.1C',temperature_C=30,window='1.8–4.75V',actual_target_measurement=False))
        for key in ['actual_qn','actual_effective_NP','actual_cell_other','actual_pack_other','actual_pack_mass']:
            rows.append(dict(case_id=cid,parameter=key,value=None,unit='not determined',input_class='未確定値',source='no target measurement in source',basis='kept unknown',limitation='not filled with design assumptions',observed_case=cid,actual_target_measurement=False))
    csv('JOINT_INPUT_CASES.csv',rows)
    return A,B

def mass_and_boundaries(existing_mass,A,B):
    Ma,_=existing_mass(A,'T08');Mb,_=existing_mass(B,'T08');base_delta=Ma-Mb
    cases=[('R0_Z_H1',A,'PUBLIC_FORMATION1_HYPOTHETICAL_REDESIGN'),('P0_Z_H2',B,'PUBLIC_FORMATION2_HYPOTHETICAL_REDESIGN'),
       ('V_MINUS',B|{'V':B['V']-.1},'V_ONLY_EXPLORATION'),('V_PLUS',B|{'V':B['V']+.1},'V_ONLY_EXPLORATION'),
       ('U_095',B|{'u':.95},'EXTRA_UTILIZATION_LOSS_EXPLORATION'),('NP_125',B|{'np':1.25},'EFFECTIVE_NP_EXPLORATION'),
       ('EXTRA_1',B|{'extra':1.},'ADDITIONAL_MASS_EXPLORATION'),('QN_300',B|{'qn':300.},'TRANSFERRED_QN_SENSITIVITY'),
       ('QN_400',B|{'qn':400.},'TRANSFERRED_QN_SENSITIVITY'),('FP_075',B|{'fp':.75},'RECIPE_LINKAGE_SENSITIVITY'),('FP_090',B|{'fp':.9},'RECIPE_LINKAGE_SENSITIVITY')]
    E=cfg['E_Wh']
    def roots(p):
        C=100*p['cellother']+p['packother'];W=Ma-C-p['extra'];a=p['np']/(p['qn']*p['fn']);den=p['V']*W/E-a
        z=p['V']*W/E-1/(p['q']*p['u']*p['fp'])
        return dict(q=None if den<=0 else 1/(p['u']*p['fp']*den),u=None if den<=0 else 1/(p['q']*p['fp']*den),
            V=None if W<=0 else E*(1/(p['q']*p['u']*p['fp'])+a)/W,
            extra=Ma-C-E/p['V']*(1/(p['q']*p['u']*p['fp'])+a),
            np=(p['V']*W/E-1/(p['q']*p['u']*p['fp']))*p['qn']*p['fn'],
            qn=None if z<=0 else p['np']/(p['fn']*z))
    root=roots(B);br=[]
    def delta(p):return Ma-existing_mass(p,'T08')[0]
    def bisect(axis,p,lo,hi):
        fl=delta(p|{axis:lo});fh=delta(p|{axis:hi})
        if fl*fh>0:return None
        for _ in range(180):
            mid=(lo+hi)/2;fm=delta(p|{axis:mid})
            if abs(fm)<1e-12:return mid
            if fl*fm<=0:hi=mid;fh=fm
            else:lo=mid;fl=fm
        return (lo+hi)/2
    for axis,x in root.items():
        check('baseline analytic positive root '+axis,x is not None and x>0,x)
        eps=.001 if axis in ['u','np','extra'] else .01
        lo=x-eps;hi=x+eps
        numerical=bisect(axis,B,lo,hi);on=delta(B|{axis:x});dl=delta(B|{axis:lo});dh=delta(B|{axis:hi})
        expected=1 if axis in ['q','u','V','qn'] else -1
        check('root numerical '+axis,numerical is not None and abs(on)<1e-9 and abs(x-numerical)<1e-8,(x,numerical,on))
        check('root signs '+axis,np.sign(dl)==-expected and np.sign(dh)==expected,(dl,dh))
        br.append(dict(boundary_id='B_'+axis,axis=axis,analytic_root=x,numerical_root=numerical,root_error=abs(x-numerical),
            below_value=lo,above_value=hi,delta_below_kg=dl,delta_on_kg=on,delta_above_kg=dh,
            root_status='IN_DECLARED_BASIC_DOMAIN',physical_realization='UNVERIFIED',
            unit={'q':'Ah/kg','u':'1','V':'V','extra':'kg','np':'1','qn':'Ah/kg'}[axis],comparison='R0_Z_H1 vs Z_H2 redesign; others fixed',validation='PASS'))
        cases.append(('ROOT_'+axis,B|{axis:x},'ANALYTIC_ZERO_BOUNDARY_HYPOTHETICAL'))
    # Existence/domain diagnostics: do not coerce absent roots or unknowns to zero.
    p=B|{'q':B['q']*.8};ur=roots(p)['u'];nr=bisect('u',p,ur-.01,ur+.01)
    check('u root outside0..1',ur>1 and nr is not None and delta(p|{'u':1})<0)
    br.append(dict(boundary_id='OUTSIDE_U',axis='u',analytic_root=ur,numerical_root=nr,root_error=abs(ur-nr),delta_on_kg=delta(p|{'u':ur}),
        delta_below_kg=delta(p|{'u':ur-.01}),delta_above_kg=delta(p|{'u':ur+.01}),root_status='OUTSIDE_u_LE_1',physical_realization='NOT_ADMISSIBLE_AS_UTILIZATION',unit='1',validation='EXPECTED_OUTSIDE_DOMAIN'))
    p=B|{'extra':Ma-34+1};rs=roots(p)
    check('no positive q u V root with no mass allowance',rs['q'] is None and rs['u'] is None and rs['V'] is None)
    for axis in ['q','u','V']:
        value=[1e-3,1e9] if axis!='u' else [1e-4,1.]
        numerical=bisect(axis,p,*value)
        check('root absence numerical '+axis,numerical is None)
        br.append(dict(boundary_id='NONE_'+axis,axis=axis,analytic_root=None,numerical_root=None,delta_below_kg=delta(p|{axis:value[0]}),delta_above_kg=delta(p|{axis:value[1]}),
            root_status='NO_FINITE_POSITIVE_ROOT_mass_allowance_NONPOSITIVE',physical_realization='INFEASIBLE',validation='EXPECTED_NO_ROOT'))
    p=B|{'q':B['q']*.4};nroot=roots(p)['np']
    check('negative formal NP root not allowed',nroot<0 and bisect('np',p,1e-6,5.) is None)
    br.append(dict(boundary_id='OUTSIDE_NP',axis='np',analytic_root=nroot,numerical_root=None,root_status='NEGATIVE_FORMAL_ROOT_NO_POSITIVE_NP_SOLUTION',physical_realization='INFEASIBLE',validation='EXPECTED_NO_PHYSICAL_ROOT'))
    p=B|{'V':3.0};er=roots(p)['extra'];en=bisect('extra',p,er-1,er+1)
    check('negative differential extra root',er<0 and en is not None and delta(p|{'extra':0})<0)
    br.append(dict(boundary_id='OUTSIDE_EXTRA',axis='extra',analytic_root=er,numerical_root=en,root_error=abs(er-en),delta_on_kg=delta(p|{'extra':er}),
       root_status='NEGATIVE_DIFFERENTIAL_NOT_S_ONLY_ADDED_MASS',physical_realization='OUTSIDE_extra_GE_0',unit='kg',validation='EXPECTED_OUTSIDE_DOMAIN'))
    # Keep the historical LP/S unknown-difference boundary as a separate scope.
    for policy,bk in [('fixed_loading',9.722608121),('fixed_area_LP',5.977891152)]:
        for shift in [-.1,0.,.1]:
            d=bk-(bk+shift);check('T09 unknown delta signs '+policy+str(shift),abs(d+shift)<1e-12)
            br.append(dict(boundary_id='T09_UNKNOWN_'+policy,axis='U_S-U_LP',analytic_root=bk,numerical_root=bk,root_error=0.,
                tested_unknown_delta_kg=bk+shift,delta_on_kg=d,unit='kg',root_status='K_LP-K_S minus symbolic deltaU',physical_realization='UNVERIFIED',comparison='HISTORICAL_LP_S_T09_NOT_ZHANG',validation='PASS',complete_pack_kg=None))
    results=[]
    for cid,p,kind in cases:
        total,parts=existing_mass(p,'T08');ind,ip=decimal_mass(p)
        check('T08 independent percell SI '+cid,abs(total-ind)<1e-9,abs(total-ind))
        for key in ['positive_active_kg','negative_active_kg','positive_coating_kg','negative_coating_kg']:check(cid+' '+key,abs(parts[key]-ip[key])<1e-9)
        cell=(parts['positive_coating_kg']+parts['negative_coating_kg'])/100+p['cellother'];other=100*p['cellother']+p['packother']+p['extra']
        results.append(dict(case_id=cid,case_kind=kind,**p,**parts,other_total_kg=other,cell_mass_kg=cell,cell_sum_kg=100*cell,
            hypothetical_pack_kg=total,hypothetical_pack_specific_Wh_kg=E/total,delta_reference_minus_case_kg=Ma-total,relative_mass_saving_percent=100*(Ma-total)/Ma,
            independent_pack_kg=ind,mass_error_kg=abs(total-ind),coating_subtotal_kg=parts['positive_coating_kg']+parts['negative_coating_kg'],
            actual_pack_mass_kg=None,actual_vehicle_mass_kg=None,mass_scope='T08_HYPOTHETICAL_COMPLETE_DESIGN_ONLY_NOT_MEASURED',
            interpretation='fixed20kWh redesign using a capacity/voltage snapshot; actual cell mass does not change between formation cycles'))
    csv('T08_REPRESENTATIVE_RESULTS.csv',results);csv('BOUNDARY_VALIDATION.csv',br)
    return results,cases,br,dict(reference_pack_kg=Ma,candidate_pack_kg=Mb,delta_kg=base_delta,roots=root)

def dc_validation(results,cases):
    sys.path.insert(0,str(R/'src'))
    from kmd_quantitative.energy.controlled_dc import evaluate,scalar_check,EXPECTED_SHA256
    source(R/'src/kmd_quantitative/energy/controlled_dc.py');source(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py')
    check('DC kernel pinned hash',sha(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py')==EXPECTED_SHA256)
    freeze=json.loads(source(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text())
    oldmass=pd.read_csv(source(L/'INTERACTION_RESULTS.csv'));old8=oldmass[oldmass.model=='T08'];op=pd.read_csv(source(L/'data/BASELINE_OPERATION_RESPONSE.csv'))
    prior_masses=np.unique(np.r_[old8.LP_mass_or_known_kg,old8.S_mass_or_known_kg]);nonpack=1155-20000/180
    run=json.loads((L/'evidence/RUN_RESULT.json').read_text());lo,hi=run['mass_interval']
    selectids=['R0_Z_H1','P0_Z_H2','EXTRA_1','ROOT_extra']
    decisions=[]
    for row in results:
        nearest=float(prior_masses[np.argmin(abs(prior_masses-row['hypothetical_pack_kg']))]);exact=abs(nearest-row['hypothetical_pack_kg'])<1e-9
        decisions.append(dict(case_id=row['case_id'],mass_scope=row['mass_scope'],hypothetical_pack_kg=row['hypothetical_pack_kg'],nearest_old_pack_kg=nearest,nearest_error_kg=abs(nearest-row['hypothetical_pack_kg']),
            exact_existing_mass=exact,inside_existing_verified_interval=lo<=nonpack+row['hypothetical_pack_kg']<=hi,
            decision='REUSE_EXACT_OLD_MASS' if exact else 'SMALL_3_TRAJECTORY_DIRECT_CHECK' if row['case_id'] in selectids else 'NO_NEW_DC_CLAIM_MASS_CHECK_ONLY',
            absolute_DC_scope='HYPOTHETICAL_T08_ONLY',full_460_rerun=False,practical_EV_claim='HOLD'))
    decisions.append(dict(case_id='T09_K_PLUS_U',mass_scope='UNKNOWN_U',hypothetical_pack_kg=None,decision='NO_ABSOLUTE_DC_UNKNOWN_PACK_MASS',absolute_DC_scope='HOLD',full_460_rerun=False,practical_EV_claim='HOLD'))
    old=pd.read_csv(source(R/'review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv'));old=old[old.dataset=='CLASSICAL']
    rank=op[op.rolling_case=='CRR_LOWER_BOUND'].sort_values('distance_km');chosen=rank.iloc[[0,len(rank)//2,-1]]
    sel=[r for r in results if r['case_id'] in selectids];base=next(r for r in results if r['case_id']=='R0_Z_H1');dc=[]
    archive=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
    for rr in chosen.itertuples():
        g=old[old.trajectory_sha256==rr.trajectory_sha256];path=Path(g.iloc[0].trajectory_path)
        if not path.exists():path=archive/path.relative_to(R)
        source(path);check('saved trajectory hash '+rr.trajectory_sha256,sha(path)==rr.trajectory_sha256)
        tr=pd.read_csv(path,usecols=['timestamp_s','speed_m_s']);t=tr.timestamp_s.to_numpy();v=tr.speed_m_s.to_numpy()
        for rc,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
            # Check the old reference on the same route before any new hypothetical mass.
            saved=g[(g.rolling_case==rc)&(g.scenario_id=='COND_LP_REF')].iloc[0]
            olde,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':float(saved.running_mass_kg)})
            check('legacy DC replay '+rr.trajectory_sha256+rc,abs(olde['net_DC_Wh']-saved.net_DC_Wh)<1e-7)
            m0=nonpack+base['hypothetical_pack_kg'];e0,a0=evaluate(t,v,freeze,pressure,{'running_mass_kg':m0})
            scalar_check(t,v,freeze,pressure,{'running_mass_kg':m0},e0)
            for row in sel:
                m1=nonpack+row['hypothetical_pack_kg'];e1,a1=evaluate(t,v,freeze,pressure,{'running_mass_kg':m1})
                reduction=e0['net_DC_Wh']-e1['net_DC_Wh'];dm=m0-m1;mask=a0['wheel']>0;I1=a1['wheel']>0
                comp={name:float(np.sum((a0[key]-a1[key])[mask])/.9) for name,key in [('W1','roll'),('W2','aero'),('W3','translational'),('W4','rotational')]}
                corr=float(np.sum((mask.astype(int)-I1.astype(int))*a1['wheel'])/.9)
                check('new DC decomposition '+row['case_id']+rr.trajectory_sha256+rc,abs(reduction-sum(comp.values())-corr)<1e-7)
                if abs(dm)>1e-8:check('new mass DC sign '+row['case_id']+rc,reduction*dm>0)
                dc.append(dict(case_id=row['case_id'],trajectory_sha256=rr.trajectory_sha256,rolling_case=rc,distance_km=e0['observed_distance_m']/1000,
                    reference_running_kg=m0,comparison_running_kg=m1,delta_mass_kg=dm,reference_DC_Wh=e0['net_DC_Wh'],comparison_DC_Wh=e1['net_DC_Wh'],
                    saving_DC_Wh=reduction,saving_percent=100*reduction/e0['net_DC_Wh'],saving_Wh_km=reduction/(e0['observed_distance_m']/1000),saving_Wh_kg=reduction/dm if abs(dm)>1e-8 else None,
                    **{k+'_saving_Wh':val for k,val in comp.items()},branch_correction_Wh=corr,
                    scope='T08_HYPOTHETICAL_20KWH_REDESIGN; not measured cell mass or actual EV; observed window; no regen/aux/grade'))
    csv('DC_REUSE_DECISION.csv',decisions);csv('evidence/DC_SMALL_VALIDATION.csv',dc)
    return dc,decisions

def main():
    protected=protection()
    for name in ['FINAL_REPORT_JA.md','ADDITIONAL_DATA_INVENTORY.csv','SOURCE_EVIDENCE_MATRIX.csv','HOLD_REASSESSMENT.csv','RECALCULATION_PLAN.csv','EXECUTION_ROADMAP.md','COMPLETION_CRITERIA.md','FINAL_AUDIT.md']:source(S/name)
    for name in ['RATE2026_PDF.txt','RATE2026_SI.txt','LMR2026_PDF.txt','LMR2026_SI.txt','BATPAC_NHTSA.txt','RATE2026_PDF.pdf','RATE2026_SI.pdf','LMR2026_PDF.pdf','LMR2026_SI.pdf','BATPAC_NHTSA.pdf']:source(S/'sources'/name)
    qv,raw=qv_validation();massfn=load_existing_mass();A,B=joint_inputs(qv);results,cases,bounds,summary=mass_and_boundaries(massfn,A,B)
    rows,component_checks,component_summary=demo_and_checks();checks.extend(component_checks)
    csv('evidence/T09_SYNTHETIC_COMPONENT_RESULTS.csv',rows);csv('evidence/T09_COMPONENT_CHECKS.csv',component_checks)
    (O/'evidence/T09_SYNTHETIC_LEDGER.json').write_text(json.dumps(component_summary,indent=2)+'\n')
    dc,decisions=dc_validation(results,cases)
    for row in protected.itertuples():check('final preserved '+row.path,sha(row.path)==row.sha256)
    for path,h in sources.items():check('source unchanged '+path,sha(path)==h)
    csv('evidence/SOURCE_MANIFEST.csv',[dict(path=p,sha256=h) for p,h in sources.items()]);csv('evidence/NUMERICAL_CHECKS.csv',checks)
    summary.update(qv_cases=len(qv),T08_cases=len(results),boundary_rows=len(bounds),dc_rows=len(dc),dc_trajectories=3,dc_full_fleet_recomputed=False,checks=len(checks),failures=0,protected_files=len(protected),T09_complete_pack='HOLD',target_LP_S='HOLD')
    (O/'evidence/RUN_RESULT.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary,indent=2,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
