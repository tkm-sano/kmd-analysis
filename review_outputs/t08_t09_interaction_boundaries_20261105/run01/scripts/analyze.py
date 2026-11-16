from pathlib import Path
import os, sys, json, hashlib, itertools, importlib.util, platform
sys.dont_write_bytecode = True
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parents[1]
R = next(p for p in SCRIPT_DIR.parents if (p/'src/kmd_quantitative').exists())
O = Path(os.environ.get('T08_T09_OUTPUT',str(SCRIPT_DIR))).resolve()
O.mkdir(parents=True,exist_ok=True)
OLD = R/'review_outputs/t08_t09_final_adoption_20261105'
ARCHIVE = Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
T9 = ARCHIVE/'review_outputs/t09_open_data_model_20261029/run01'
sys.path.insert(0, str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate, scalar_check, EXPECTED_SHA256

B = dict(q=195.959596,u=1.,V=3.5,fp=.75,fn=.98,qn=360.,np=1.1,
         rhop=4458.,rhon=2200.,L=.1,ep=.25,en=.25,al=15e-6,cu=10e-6,
         sep=.013275,ts=25e-6,es=.41,rhol=1300.,wet=1.,sat=1.,excess=0.,
         cellother=.19,packother=15.,extra=0.,nf=1.,unavail=0.)
QLP=171.875
LP=B|dict(q=QLP)
NONPACK=1155-20000/180
checks=[]
sources={}
for d in ['evidence','figures','data']: (O/d).mkdir(exist_ok=True)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source(p):
    p=Path(p); sources[str(p)]=sha(p); return p
def check(name, ok, detail=''):
    checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=str(detail)))
    if not ok:
        pd.DataFrame(checks).to_csv(O/'evidence/NUMERICAL_AUDIT.csv',index=False)
        raise AssertionError((name,detail))
def csv(name, rows):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    df.to_csv(O/name,index=False,float_format='%.12g'); return df

def mass(p,model='T08',policy='fixed_loading'):
    Q=20000/p['V']; mp=Q/(p['q']*p['u']); mn=Q*p['np']/(p['qn']*(1-p['unavail']))
    pc=mp/p['fp']; nc=mn/p['fn']
    out=dict(positive_active_kg=mp,negative_active_kg=mn,positive_coating_kg=pc,negative_coating_kg=nc)
    if model=='T08':
        out.update(other_kg=100*p['cellother']+p['packother']+p['extra'])
        total=pc+nc+out['other_kg']
    else:
        # Matches prior S-only policy: L is a design-area intervention in fixed_area_LP.
        A=mp/p['L'] if policy=='fixed_loading' else 20000/3.5/QLP/p['L']
        An=A*p['nf']; As=max(A,An)
        vp=pc/p['rhop']*p['ep']/(1-p['ep']); vn=nc/p['rhon']*p['en']/(1-p['en'])
        out.update(positive_area_m2=A,negative_area_m2=An,
                   positive_thickness_um=pc/p['rhop']/(1-p['ep'])/A*1e6,
                   negative_thickness_um=nc/p['rhon']/(1-p['en'])/An*1e6,
                   Al_kg=A/2*p['al']*2699,Cu_kg=An/2*p['cu']*8960,
                   separator_kg=As*p['sep'],
                   liquid_kg=((vp+vn+As*p['ts']*p['es'])*p['wet']*p['sat']+p['excess'])*p['rhol'],
                   overlap_condition='PASS_GEOMETRIC_AREA_ONLY' if An>=A else 'FAIL')
        total=pc+nc+sum(out[k] for k in ['Al_kg','Cu_kg','separator_kg','liquid_kg'])
    return total,out

M0=mass(LP)[0]; MS=mass(B)[0]; b=M0-MS
def delta(p,model='T08',policy='fixed_loading',lp=LP): return mass(lp,model,policy)[0]-mass(p,model,policy)[0]

def preflight():
    # Snapshot existing adopted outputs and all thesis DOCX/PDF files; never write to them.
    for p in OLD.rglob('*'):
        if p.is_file(): source(p)
    for p in R.rglob('*.docx'): source(p)
    for p in R.rglob('*.pdf'):
        if 'thesis' in str(p).lower() or '修士' in str(p): source(p)
    for p in [R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py',
              R/'src/kmd_quantitative/energy/controlled_dc.py',
              R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',T9/'model.py']:
        source(p)
    freeze=json.loads((R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text())
    saved=pd.read_csv(source(R/'review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv'))
    saved=saved[saved.dataset=='CLASSICAL']
    targets=[('T08 baseline mass saving',b,5.448297415,5e-10,'kg'),
             ('S additional mass boundary',b,5.448297415,5e-10,'kg'),
             ('S utilization boundary',QLP/B['q'],.877094072,5e-10,'1'),
             ('S voltage boundary',20000*(1/(B['q']*.75)+1.1/(360*.98))/(M0-34),3.193155684,5e-10,'V')]
    for rc,expected in [('CRR_LOWER_BOUND',.412579),('CRR_UPPER_BOUND',.413590)]:
        g=saved[saved.rolling_case==rc]; a=g[g.scenario_id=='COND_LP_REF'].net_DC_Wh.sum(); s=g[g.scenario_id=='COND_S200_REF'].net_DC_Wh.sum()
        targets.append((rc+' saving',100*(a-s)/a,expected,5e-7,'%'))
    reproduction=[]
    for name,got,expected,tol,unit in targets:
        check(name,abs(got-expected)<=tol,got)
        reproduction.append(dict(item=name,recomputed=got,reported=expected,absolute_error=abs(got-expected),tolerance=tol,unit=unit,status='PASS'))
    csv('evidence/REPRODUCTION.csv',reproduction)
    check('saved 460 unique trajectories',saved.trajectory_sha256.nunique()==460)
    check('T08 historical LP mass',abs(M0-96.14565479871604)<1e-10)
    check('frozen kernel hash',sha(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py')==EXPECTED_SHA256)
    old=pd.read_csv(OLD/'data/MASS_SENSITIVITY.csv')
    check('239 old mass rows',len(old)==239)
    check('115 old T08/DC conditions',sum(old.model=='T08')==115)
    print('REPRODUCTION PASS: six targets; 239 mass rows, 115 DC conditions.',flush=True)
    return freeze,saved,old

def fingerprint(p,model,policy,lp=LP):
    keys=['q','u','V','fp','fn','qn','np','unavail']
    keys+=['cellother','packother','extra'] if model=='T08' else ['rhop','rhon','L','ep','en','al','cu','sep','ts','es','rhol','wet','sat','excess','nf']
    # Round only to identify old decimal serialization; mass equality checked separately.
    return json.dumps([model,policy,[[k,round(p[k],11),round(lp[k],11)] for k in keys]],separators=(',',':'))

def build_design(old):
    oldmap={}; inv=[]
    for r in old.to_dict('records'):
        p=B.copy()
        if r['axis']=='u_V': p.update(u=r['u_S'],V=r['V_S'])
        elif r['axis']!='baseline': p[r['axis']]=r['value']
        key=fingerprint(p,r['model'],r['policy']); oldmap.setdefault(key,[]).append(r['case_id'])
        val=mass(p,r['model'],r['policy'])[0]
        check('old mass reconstruction '+r['case_id'],abs(val-r['S_mass_or_known_kg'])<1e-8)
        inv.append(dict(old_case_id=r['case_id'],model=r['model'],policy=r['policy'],fingerprint=key,
                        first_equivalent_id=oldmap[key][0],is_repeated_input=len(oldmap[key])>1,DC_evaluated=r['model']=='T08'))
    csv('data/EXISTING_CASE_INVENTORY.csv',inv)
    cases=[]; lookup={}; memberships=[]
    def add(p,model='T08',policy='fixed_loading',family='baseline',lp=LP):
        key=fingerprint(p,model,policy,lp)
        if key not in lookup:
            cid=f'N{len(cases):04d}'; lookup[key]=cid
            lm,lparts=mass(lp,model,policy); sm,parts=mass(p,model,policy)
            oldids=oldmap.get(key,[])
            cases.append(dict(case_id=cid,model=model,policy=policy,family=family,
                              origin='EXISTING_INPUT_REUSED' if oldids else 'NEW_EXPLORATORY_INPUT',
                              existing_case_ids='|'.join(oldids),input_class='DESIGN_EXPLORATION_NOT_EXPERIMENT',
                              LP_mass_or_known_kg=lm,S_mass_or_known_kg=sm,delta_mass_kg=lm-sm,
                              effective_q_Ah_kg=p['q']*p['u'],**{'S_'+k:v for k,v in p.items()},
                              **{'LP_'+k:v for k,v in lp.items()},**{'S_'+k:v for k,v in parts.items()},
                              LP_complete_pack_kg=lm if model=='T08' else None,S_complete_pack_kg=sm if model=='T08' else None,
                              p=p.copy(),lp=lp.copy()))
        memberships.append(dict(case_id=lookup[key],family=family))
        return lookup[key]
    add(B)
    grids={
        'q_V':('q','V',sorted(set(np.linspace(150,240,9))|{QLP,B['q']}),sorted(set(np.linspace(3,3.8,9))|{3.5})),
        'q_u':('q','u',sorted(set(np.linspace(150,240,9))|{QLP,B['q']}),np.linspace(.7,1,9)),
        'q_extra':('q','extra',sorted(set(np.linspace(150,240,9))|{QLP,B['q']}),sorted(set(np.linspace(0,20,9))|{b})),
        'u_extra':('u','extra',sorted(set(np.linspace(.7,1,9))|{QLP/B['q']}),sorted(set(np.linspace(0,20,9))|{b}))}
    interactions=[]
    for family,(x,y,xs,ys) in grids.items():
        for xv,yv in itertools.product(xs,ys):
            p=B|{x:float(xv),y:float(yv)}; cid=add(p,family=family)
            mixed=delta(p)-delta(B|{x:float(xv)})-delta(B|{y:float(yv)})+b
            interactions.append(dict(family=family,case_id=cid,x=x,y=y,x_value=xv,y_value=yv,
                                     mixed_difference_kg=mixed,definition='D(x,y)-D(x,y0)-D(x0,y)+D(x0,y0)',
                                     x_anchor=B[x],y_anchor=B[y],comparison='S_ONLY_LP_FIXED'))
    for policy in ['fixed_loading','fixed_area_LP']:
        for L,ep,en in itertools.product([.02,.05,.1,.15,.2],[.25,.35,.45],[.25,.35,.45]):
            p=B|dict(L=L,ep=ep,en=en);cid=add(p,'T09',policy,'L_ep_en')
            d0=delta(B,'T09',policy)
            mix=delta(p,'T09',policy)-delta(B|{'L':L},'T09',policy)-delta(B|{'ep':ep,'en':en},'T09',policy)+d0
            interactions.append(dict(family='L_ep_en',case_id=cid,x='L',y='ep_en',x_value=L,y_value=f'{ep}/{en}',mixed_difference_kg=mix,comparison=policy))
    for mode in ['S_ONLY','COMMON_ANODE']:
        for npv,qn,fn in itertools.product([1.,1.1,1.2],[300.,360.,400.],[.94,.98,.99]):
            changes=dict(np=npv,qn=qn,fn=fn);p=B|changes;lp=LP if mode=='S_ONLY' else LP|changes
            add(p,family='NP_qn_fn_'+mode,lp=lp)
    # Dedicated local and range points: same normalized 1% diagnostic, not uncertainty.
    ranges=dict(q=[150.,240.],V=[3.,3.8],u=[.7,1.],extra=[0.,20.],np=[1.,1.2],qn=[300.,400.],fn=[.94,.99],
                fp=[.75,.96],cellother=[.095,.285],packother=[7.5,22.5])
    for k,ends in ranges.items():
        for v in ends: add(B|{k:v},family='factor_range_'+k)
        # derivatives only are analytic below; avoid impossible u>1 exploration.
    # Exact boundary and +/- points; voltage, utilization, extra perturbation units explicit.
    reps=[]
    for name,q,u in [('q_V',180.,1.),('q_u',210.,1.),('q_extra',210.,1.),('u_extra',B['q'],.9)]:
        if name=='q_V': axis='V';root=20000*(1/(q*u*.75)+B['np']/(B['qn']*B['fn']))/(M0-34);eps=.01
        elif name=='q_u': axis='u';root=QLP/q;eps=.01
        else:
            axis='extra';root=delta(B|dict(q=q,u=u));eps=.1
        for sign in [-1,0,1]:
            p=B|dict(q=q,u=u)|{axis:root+sign*eps};cid=add(p,family='boundary_representative')
            expected=sign if axis in ['V','u'] else -sign
            check('boundary representative '+name+str(sign),abs(delta(p))<1e-9 if sign==0 else np.sign(delta(p))==expected)
            reps.append(dict(boundary=name,case_id=cid,axis=axis,boundary_value=root,offset=sign*eps,delta_mass_kg=delta(p),expected_sign=expected))
    csv('data/BOUNDARY_REPRESENTATIVES.csv',reps)
    csv('data/CASE_MEMBERSHIP.csv',memberships)
    csv('data/MIXED_DIFFERENCES.csv',interactions)
    csv('INTERACTION_RESULTS.csv',[{k:v for k,v in c.items() if k not in ['p','lp']} for c in cases])
    return cases,oldmap,ranges

def boundaries():
    rows=[]
    for q in np.linspace(150,240,181):
        v=20000*(1/(q*.75)+B['np']/(B['qn']*B['fn']))/(M0-34)
        u=QLP/q; ext=delta(B|{'q':q})
        for typ,axis,val in [('q_V','V',v),('q_u','u',u),('q_extra','extra',ext)]:
            p=B|{'q':q,axis:val};err=delta(p)
            check('analytic boundary '+typ+str(q),abs(err)<1e-9)
            # Sign checks on both sides of every computed boundary.
            step=1e-5 if axis!='extra' else .001
            dl=delta(p|{axis:val-step});dh=delta(p|{axis:val+step})
            check('boundary signs '+typ+str(q),dl<0<dh if axis!='extra' else dh<0<dl)
            rows.append(dict(boundary=typ,q_Ah_kg=q,u=val if axis=='u' else 1,V=val if axis=='V' else 3.5,
                             extra_S_minus_LP_kg=val if axis=='extra' else 0,root_variable=axis,root_value=val,
                             mass_residual_kg=err,feasible_basic_domain=0< u <=1 if axis=='u' else (val>=0 if axis=='extra' else val>0),
                             physical_realization='UNVERIFIED',source='analytic T08; LP fixed; conditional reference'))
    for u in np.linspace(.7,1,121):
        ext=delta(B|{'u':u});check('u extra boundary '+str(u),abs(delta(B|{'u':u,'extra':ext}))<1e-9)
        rows.append(dict(boundary='u_extra',q_Ah_kg=B['q'],u=u,V=3.5,extra_S_minus_LP_kg=ext,
                         root_variable='extra',root_value=ext,mass_residual_kg=delta(B|{'u':u,'extra':ext}),
                         feasible_basic_domain=ext>=0,physical_realization='UNVERIFIED',source='analytic T08'))
    # Continuous surface delta*(q,u), useful beyond separate two-variable slices.
    for q,u in itertools.product(np.linspace(150,240,31),np.linspace(.7,1,31)):
        ext=delta(B|dict(q=q,u=u));rows.append(dict(boundary='q_u_extra_surface',q_Ah_kg=q,u=u,V=3.5,
                         extra_S_minus_LP_kg=ext,root_variable='extra',root_value=ext,mass_residual_kg=delta(B|dict(q=q,u=u,extra=ext)),
                         feasible_basic_domain=ext>=0,physical_realization='UNVERIFIED',source='analytic T08'))
    for policy in ['fixed_loading','fixed_area_LP']:
        for L,ep,en in itertools.product(np.linspace(.02,.2,19),np.linspace(.25,.45,5),np.linspace(.25,.45,5)):
            bk=delta(B|dict(L=L,ep=ep,en=en),'T09',policy)
            for offset in [-.1,0,.1]:
                check('T09 unknown difference sign '+str((policy,L,ep,en,offset)),abs(bk-(bk+offset)+offset)<1e-10)
            rows.append(dict(boundary='T09_known_unknown',policy=policy,L_kg_m2=L,ep=ep,en=en,
                             known_difference_kg=bk,unknown_S_minus_LP_boundary_kg=bk,root_variable='unknown_S_minus_LP',root_value=bk,
                             mass_residual_kg=0.,feasible_basic_domain=True,physical_realization='UNVERIFIED',
                             source='T09 known subtotal; complete LP/S masses NULL',LP_complete_pack_kg=None,S_complete_pack_kg=None))
    return csv('BOUNDARY_SURFACES.csv',rows)

def verify_t09(cases):
    spec=importlib.util.spec_from_file_location('preserved_t09',T9/'model.py');mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    for c in cases:
        if c['model']!='T09': continue
        p=c['p'];_,s=mass(p,'T09',c['policy'])
        pg=mod.geometry(s['positive_active_kg'],p['fp'],s['positive_active_kg']/s['positive_area_m2'],p['ep'],solid_mixture_density_kg_m3=p['rhop'])
        ng=mod.geometry(s['negative_active_kg'],p['fn'],s['negative_active_kg']/s['negative_area_m2'],p['en'],solid_mixture_density_kg_m3=p['rhon'])
        A=max(s['positive_area_m2'],s['negative_area_m2'])
        liq=mod.liquid_mass(pg['pore_volume_m3']+ng['pore_volume_m3']+A*p['ts']*p['es'],p['wet'],p['sat'],p['excess'],p['rhol'])
        expected=s['positive_coating_kg']+s['negative_coating_kg']+mod.foil_mass(s['positive_area_m2'],2,p['al'],2699)+mod.foil_mass(s['negative_area_m2'],2,p['cu'],8960)+A*p['sep']+liq
        check('new T09 preserved functions '+c['case_id'],abs(expected-c['S_mass_or_known_kg'])<1e-9 and c['S_complete_pack_kg'] is None)

def run_dc(freeze,saved,cases):
    cs=[c for c in cases if c['model']=='T08'];n=len(cs)
    olddc=pd.read_csv(source(OLD/'data/DC_TRANSMISSION.csv.gz'))
    oldlookup=olddc.set_index(['case_id','trajectory_sha256','rolling_case'])
    m0=np.array([NONPACK+c['LP_mass_or_known_kg'] for c in cs]);m1=np.array([NONPACK+c['S_mass_or_known_kg'] for c in cs]);dm=m0-m1
    low=min(m0.min(),m1.min())-1; high=max(m0.max(),m1.max())+1
    distance_rows=[];summary_rows=[];operation=[];extremes=[];derivatives=[]
    # Re-evaluate repeated masses once per trajectory, then map to all designs.
    um,indices=np.unique(np.r_[m0,m1],return_inverse=True);i0=indices[:n];i1=indices[n:]
    filename=O/'DC_INTERACTION_RESULTS.csv'; first=True
    # Frozen direct checks at all unique masses on shortest/median/longest windows.
    length=saved[saved.scenario_id=='COND_LP_REF'].drop_duplicates('trajectory_sha256').sort_values('observed_interval_count')
    deep=set(length.iloc[[0,len(length)//2,-1]].trajectory_sha256)
    metrics=[]
    for ni,(h,g) in enumerate(saved.groupby('trajectory_sha256',sort=True)):
        path=Path(g.iloc[0].trajectory_path)
        if not path.exists():path=ARCHIVE/path.relative_to(R)
        source(path);check('trajectory hash '+h,sha(path)==h)
        df=pd.read_csv(path,usecols=['timestamp_s','speed_m_s']);t=df.timestamp_s.to_numpy();v=df.speed_m_s.to_numpy();dt=np.diff(t);cur=v[1:];dv=cur**2-v[:-1]**2;ds=cur*dt
        check('sampling '+h,np.all(dt==1) and np.isfinite(v).all() and np.all(v>=0))
        acc=np.diff(v)/dt;stop=(v<=.1); starts=int(np.count_nonzero(stop[:-1]&~stop[1:])); km=ds.sum()/1000
        md=dict(trajectory_sha256=h,physical_instance_id=g.iloc[0].physical_instance_id,parent_id=g.iloc[0].parent_id,group_id=g.iloc[0].group_id,
                distance_km=km,duration_s=t[-1]-t[0],mean_speed_kmh=km/((t[-1]-t[0])/3600),moving_mean_speed_kmh=cur[cur>.1].mean()*3.6,
                rms_acceleration_m_s2=np.sqrt(np.mean(acc**2)),positive_dv2_m2_s2=np.maximum(dv,0).sum(),
                mean_positive_acceleration_m_s2=acc[acc>0].mean(),mean_deceleration_magnitude_m_s2=-acc[acc<0].mean(),
                stop_fraction=np.mean(stop),restart_count=starts,restarts_per_km=starts/km,
                source='saved trajectory; descriptive dependent routes')
        metrics.append(md)
        for rc,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
            ebase,arr=evaluate(t,v,freeze,pressure,{'running_mass_kg':NONPACK+M0})
            esref,arrs=evaluate(t,v,freeze,pressure,{'running_mass_kg':NONPACK+MS})
            if ni==0:scalar_check(t,v,freeze,pressure,{'running_mass_kg':NONPACK+M0},ebase)
            for sid,out in [('COND_LP_REF',ebase),('COND_S200_REF',esref)]:
                obs=float(g[(g.rolling_case==rc)&(g.scenario_id==sid)].net_DC_Wh.iloc[0]);check('direct saved '+h+rc+sid,abs(out['net_DC_Wh']-obs)<1e-7)
            # Affine interval wheel work a*m+c; exact positive-part compression, no model change.
            cr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure
            rollcoef=freeze['g']['value']*cr*ds/3600;transcoef=.5*dv/3600
            a=rollcoef+transcoef;c=(.5*61*dv+.5*1.2041*1.175*cur**2*ds)/3600
            wl=a*low+c;wh=a*high+c;always=(wl>0)&(wh>0);switch=(wl>0)!=(wh>0)
            aa=a[switch];cc=c[switch];ca=a[always].sum();cb=c[always].sum()
            eu=(ca*um+cb+np.maximum(um[:,None]*aa+cc,0).sum(axis=1))/.9
            check('compressed direct baseline '+h+rc,abs((ca*(NONPACK+M0)+cb+np.maximum((NONPACK+M0)*aa+cc,0).sum())/.9-ebase['net_DC_Wh'])<1e-7)
            if h in deep:
                maxerr=0
                for massv,energy in zip(um,eu):
                    direct,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':massv});maxerr=max(maxerr,abs(direct['net_DC_Wh']-energy))
                check('all unique masses direct '+h+rc,maxerr<1e-7,maxerr)
            slope_min=min((ca+aa[(aa*low+cc)>0].sum())/.9,(ca+aa[(aa*high+cc)>0].sum())/.9)
            check('positive mass response throughout interval '+h+rc,slope_min>0,slope_min)
            mask=arr['wheel']>0
            w1kg=rollcoef[mask].sum()/.9;w2kg=transcoef[mask].sum()/.9
            # Existing thesis convention: W1=rolling, W2=aero, W3=translation, W4=rotation.
            # Per-case correction from exact energy minus baseline-mask linear attribution.
            e0=eu[i0];e1=eu[i1];de=e0-e1
            correction=de-dm*(w1kg+w2kg)
            reused=np.zeros(n,dtype=bool);reuse_error=0.
            for j,case in enumerate(cs):
                if case['existing_case_ids']:
                    oldid=case['existing_case_ids'].split('|')[0];r=oldlookup.loc[(oldid,h,rc)]
                    reuse_error=max(reuse_error,abs(e0[j]-r.LP_DC_Wh),abs(e1[j]-r.S_DC_Wh));reused[j]=True
                    # Saved absolute values are authoritative for reused conditions.
                    e0[j]=r.LP_DC_Wh;e1[j]=r.S_DC_Wh
            check('old DC reuse consistency '+h+rc,reuse_error<1e-7,reuse_error)
            de=e0-e1;correction=de-dm*(w1kg+w2kg)
            # Shared anode designs have different baseline mass; their baseline mask must be recomputed.
            for j in np.flatnonzero(np.abs(m0-(NONPACK+M0))>1e-9):
                w0=a*m0[j]+c;maskj=w0>0
                correction[j]=de[j]-dm[j]*(rollcoef[maskj].sum()+transcoef[maskj].sum())/.9
            w1s=np.full(n,w1kg);w2s=np.full(n,w2kg)
            for j in np.flatnonzero(np.abs(m0-(NONPACK+M0))>1e-9):
                maskj=(a*m0[j]+c)>0;w1s[j]=rollcoef[maskj].sum()/.9;w2s[j]=transcoef[maskj].sum()/.9
            check('component closure '+h+rc,np.max(np.abs(de-dm*(w1s+w2s)-correction))<1e-8)
            nz=np.abs(dm)>1e-9;sensitivity=np.full(n,np.nan);np.divide(de,dm,out=sensitivity,where=nz)
            out=pd.DataFrame(dict(case_id=[x['case_id'] for x in cs],trajectory_sha256=h,rolling_case=rc,
                    LP_vehicle_running_kg=m0,S_vehicle_running_kg=m1,delta_vehicle_mass_kg=dm,
                    distance_km=km,mean_speed_kmh=md['mean_speed_kmh'],rms_acceleration_m_s2=md['rms_acceleration_m_s2'],
                    restart_count=starts,restarts_per_km=starts/km,LP_DC_Wh=e0,S_DC_Wh=e1,delta_DC_Wh=de,
                    saving_percent=100*de/e0,delta_Wh_per_km=de/km,delta_Wh_per_kg=sensitivity,
                    W1_rolling_mask_saving_Wh=dm*w1s,W2_aero_mask_saving_Wh=0.,
                    W3_translation_mask_saving_Wh=dm*w2s,W4_rotation_mask_saving_Wh=0.,positive_branch_correction_Wh=correction,
                    minimum_terminal_stock_Wh=18000-np.maximum(e0,e1),origin=np.where(reused,'EXISTING_DC_REUSED','NEW_DC'),
                    boundary='OBSERVED_WINDOW_NO_REGEN_AUX_GRADE_EXCLUDED'))
            out.to_csv(filename,index=False,mode='w' if first else 'a',header=first,float_format='%.12g');first=False
            for j,case in enumerate(cs):
                summary_rows.append(dict(case_id=case['case_id'],rolling_case=rc,LP_DC_Wh=e0[j],S_DC_Wh=e1[j],delta_DC_Wh=de[j],saving_percent=100*de[j]/e0[j],
                   W1=dm[j]*w1s[j],W2=dm[j]*w2s[j],correction=correction[j],Wh_per_km=de[j]/km,Wh_per_kg=sensitivity[j]))
            refde=ebase['net_DC_Wh']-esref['net_DC_Wh'];isw=(arr['wheel']>0)!=(arrs['wheel']>0)
            corr_exact=np.sum(((arr['wheel']>0).astype(int)-(arrs['wheel']>0).astype(int))*arrs['wheel'])/.9
            check('exact baseline branch decomposition '+h+rc,abs(refde-b*(w1kg+w2kg)-corr_exact)<1e-7)
            operation.append(dict(**md,rolling_case=rc,LP_DC_Wh=ebase['net_DC_Wh'],S_DC_Wh=esref['net_DC_Wh'],delta_DC_Wh=refde,
                   saving_percent=100*refde/ebase['net_DC_Wh'],delta_Wh_per_km=refde/km,delta_Wh_per_kg=refde/b,
                   W1_rolling_Wh=b*w1kg,W2_aero_Wh=0.,W3_translation_Wh=b*w2kg,W4_rotation_Wh=0.,
                   branch_correction_Wh=corr_exact,switch_intervals=int(isw.sum()),
                   Crr_distance_weighted=np.sum(cr*ds)/ds.sum(),baseline_aero_Wh=ebase['aero_Wh'],baseline_rotational_signed_Wh=ebase['rotational_signed_Wh'],
                   baseline_rolling_Wh=ebase['rolling_Wh'],baseline_translational_signed_Wh=ebase['translational_signed_Wh'],
                   baseline_translational_positive_Wh=ebase['translational_positive_Wh'],baseline_translational_negative_Wh=ebase['translational_negative_Wh']))
            maskS=(a*(NONPACK+MS)+c)>0;slope=a[maskS].sum()/.9
            derivatives.append(dict(trajectory_sha256=h,rolling_case=rc,dE_dm_Wh_kg=slope,baseline_DC_Wh=ebase['net_DC_Wh']))
        if ni%50==0: print('DC trajectories',ni+1,'/',460,'unique masses',len(um),flush=True)
    sr=pd.DataFrame(summary_rows)
    summary=sr.groupby(['case_id','rolling_case']).agg(n=('delta_DC_Wh','size'),LP_sum_Wh=('LP_DC_Wh','sum'),S_sum_Wh=('S_DC_Wh','sum'),
               delta_sum_Wh=('delta_DC_Wh','sum'),mean_delta_Wh=('delta_DC_Wh','mean'),min_delta_Wh=('delta_DC_Wh','min'),max_delta_Wh=('delta_DC_Wh','max'),
               W1_sum_Wh=('W1','sum'),W3_sum_Wh=('W2','sum'),branch_correction_sum_Wh=('correction','sum'),
               mean_Wh_per_km=('Wh_per_km','mean'),min_Wh_per_kg=('Wh_per_kg','min'),max_Wh_per_kg=('Wh_per_kg','max')).reset_index()
    summary['saving_percent']=100*summary.delta_sum_Wh/summary.LP_sum_Wh
    csv('data/DC_SUMMARY.csv',summary);csv('data/TRAJECTORY_METRICS.csv',metrics);op=csv('data/BASELINE_OPERATION_RESPONSE.csv',operation)
    strata=[];correlations=[]
    for rc,g in op.groupby('rolling_case'):
        for factor in ['distance_km','mean_speed_kmh','rms_acceleration_m_s2','restarts_per_km','stop_fraction','positive_dv2_m2_s2']:
            bins=pd.qcut(g[factor],4,duplicates='drop')
            for label,z in g.groupby(bins,observed=True):
                strata.append(dict(rolling_case=rc,factor=factor,bin=str(label),n=len(z),factor_min=z[factor].min(),factor_max=z[factor].max(),mean_delta_Wh=z.delta_DC_Wh.mean(),min_delta_Wh=z.delta_DC_Wh.min(),max_delta_Wh=z.delta_DC_Wh.max(),mean_delta_Wh_per_km=z.delta_Wh_per_km.mean(),mean_Wh_per_kg=z.delta_Wh_per_kg.mean(),interpretation='DESCRIPTIVE_DEPENDENT_TRAJECTORIES_NO_CAUSAL_IDENTIFICATION'))
            for outcome in ['delta_DC_Wh','delta_Wh_per_km','delta_Wh_per_kg']:
                correlations.append(dict(rolling_case=rc,factor=factor,outcome=outcome,spearman=g[[factor,outcome]].rank().corr().iloc[0,1],interpretation='FINITE_SET_DESCRIPTIVE_NO_P_NO_CI'))
    csv('data/DRIVING_STRATA.csv',strata);csv('data/DESCRIPTIVE_CORRELATIONS.csv',correlations)
    csv('data/DC_LOCAL_MASS_RESPONSE.csv',derivatives)
    return summary,op,pd.DataFrame(derivatives),dict(DC_rows=n*920,T08_cases=n,unique_masses=len(um),mass_interval=[low,high],deep_checked_trajectories=sorted(deep))

def factors(cases,summary,derivs,ranges):
    deriv=dict(q=-20000/(B['V']*B['fp']*B['u']*B['q']**2),
               u=-20000/(B['V']*B['fp']*B['q']*B['u']**2),
               V=-(MS-34)/B['V'],extra=1.,np=20000/(B['V']*B['qn']*B['fn']),
               qn=-20000*B['np']/(B['V']*B['fn']*B['qn']**2),
               fn=-20000*B['np']/(B['V']*B['qn']*B['fn']**2),
               fp=-20000/(B['V']*B['q']*B['u']*B['fp']**2),cellother=100.,packother=1.)
    rows=[]
    for k,ends in ranges.items():
        h=1e-5*max(abs(B[k]),1);fd=(mass(B|{k:B[k]+h})[0]-mass(B|{k:B[k]-h})[0])/(2*h)
        check('analytic local derivative '+k,abs(fd-deriv[k])<1e-6*max(1,abs(deriv[k])))
        for rc,g in derivs.groupby('rolling_case'):
            ids=[c['case_id'] for c in cases if c['family']=='factor_range_'+k or (c['model']=='T08' and c['p'] in [B|{k:v} for v in ends] and c['lp']==LP)]
            z=summary[(summary.case_id.isin(ids))&(summary.rolling_case==rc)]
            rawmass=[mass(B|{k:v})[0] for v in ends]
            # A common 1% relative perturbation; extra has zero reference, use 1 kg scale.
            scale=B[k] if k!='extra' else 1.
            rows.append(dict(model='T08',factor=k,rolling_case=rc,baseline_input=B[k],range_min=ends[0],range_max=ends[1],
                dS_mass_kg_per_input=deriv[k],normalized_mass_derivative_per_fraction=deriv[k]*scale/M0,
                diagnostic_input_step=.01*scale,local_delta_saving_kg_for_step=-deriv[k]*.01*scale,
                local_mean_delta_DC_Wh_for_step=-deriv[k]*.01*scale*g.dE_dm_Wh_kg.mean(),
                normalized_DC_derivative_per_fraction=-deriv[k]*scale*g.dE_dm_Wh_kg.sum()/g.baseline_DC_Wh.sum(),
                min_S_mass_kg=min(rawmass),max_S_mass_kg=max(rawmass),mass_range_span_kg=max(rawmass)-min(rawmass),
                min_mean_DC_saving_Wh=z.mean_delta_Wh.min(),max_mean_DC_saving_Wh=z.mean_delta_Wh.max(),
                DC_range_span_mean_Wh=z.mean_delta_Wh.max()-z.mean_delta_Wh.min(),
                scale_definition='relative input; extra=1kg reference scale',uncertainty='NO_DISTRIBUTION_DESIGN_RANGE_NOT_CI'))
    for policy in ['fixed_loading','fixed_area_LP']:
        for k,ends in dict(L=[.02,.2],ep=[.25,.45],en=[.25,.45],rhop=[3566.4,5349.6],rhon=[1760.,2640.],
                           al=[10e-6,20e-6],cu=[8e-6,15e-6],sep=[.008,.020],rhol=[1040.,1560.]).items():
            h=1e-5*B[k];d=(mass(B|{k:B[k]+h},'T09',policy)[0]-mass(B|{k:B[k]-h},'T09',policy)[0])/(2*h)
            vals=[mass(B|{k:v},'T09',policy)[0] for v in ends]
            rows.append(dict(model='T09',policy=policy,factor=k,baseline_input=B[k],range_min=ends[0],range_max=ends[1],
                dS_mass_kg_per_input=d,normalized_mass_derivative_per_fraction=d*B[k]/mass(LP,'T09',policy)[0],
                mass_range_span_kg=max(vals)-min(vals),min_S_mass_kg=min(vals),max_S_mass_kg=max(vals),
                uncertainty='KNOWN_SUBTOTAL_ONLY_COMPLETE_DC_HOLD'))
    return csv('FACTOR_IMPORTANCE.csv',rows)

def figures(cases,bounds,op,importance):
    df=pd.DataFrame([{k:v for k,v in c.items() if k not in ['p','lp']} for c in cases])
    def save(fig,name):
        fig.savefig(O/'figures'/f'{name}.png',dpi=180,bbox_inches='tight');fig.savefig(O/'figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(11,8))
    for ax,(fam,x,y,xlabel,ylabel) in zip(axs.flat,[('q_V','S_q','S_V','S cathode reference q (Ah/kg)','S mean full-cell voltage (V)'),('q_u','S_q','S_u','S cathode reference q (Ah/kg)','S utilization (1)'),('q_extra','S_q','S_extra','S cathode reference q (Ah/kg)','S additional mass (kg)'),('u_extra','S_u','S_extra','S utilization (1)','S additional mass (kg)')]):
        # Evaluate the complete regular surface directly for visualization; CSV contains sampled boundary.
        xx=np.linspace(150,240,121) if x=='S_q' else np.linspace(.7,1,121)
        yy=np.linspace(3,3.8,121) if y=='S_V' else np.linspace(.7,1,121) if y=='S_u' else np.linspace(0,20,121)
        zz=np.array([[delta(B|{x[2:]:a,y[2:]:b}) for a in xx] for b in yy])
        im=ax.contourf(xx,yy,zz,20,cmap='coolwarm');ax.contour(xx,yy,zz,[0],colors='black');ax.set(xlabel=xlabel,ylabel=ylabel,title=f'T08 {fam}; LP fixed')
        fig.colorbar(im,ax=ax,label='LP-S pack mass (kg)')
    fig.suptitle('Conditional design exploration; black=zero boundary; reference q is back-calculated, not measured initial capacity',fontsize=9);fig.tight_layout();save(fig,'T08_BOUNDARY_MAPS')
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for ax,policy in zip(axs,['fixed_loading','fixed_area_LP']):
        for ep in [.25,.35,.45]:
            z=df[(df.model=='T09')&(df.policy==policy)&(df.S_ep==ep)&(df.S_en==.25)].sort_values('S_L')
            ax.plot(z.S_L*100,z.delta_mass_kg,'o-',label=f'ep={ep}, en=0.25')
        ax.axhline(0,color='k');ax.set(xlabel='S cathode active loading (mg/cm2)',ylabel='LP-S known subtotal (kg)',title=policy);ax.legend(fontsize=8)
    fig.suptitle('T09 S-only exploration; LP L=10mg/cm2, ep=en=0.25; unknown BOM excluded from subtotal, full pack HOLD',fontsize=9);fig.tight_layout();save(fig,'T09_LOADING_POROSITY')
    fig,axs=plt.subplots(1,3,figsize=(13,4))
    for rc,g in op.groupby('rolling_case'):
        label=rc.replace('CRR_','')
        axs[0].scatter(g.distance_km,g.delta_DC_Wh,s=7,alpha=.5,label=label)
        axs[1].scatter(g.restarts_per_km,g.delta_Wh_per_km,s=7,alpha=.5,label=label)
        axs[2].scatter(g.W1_rolling_Wh,g.W3_translation_Wh,s=7,alpha=.5,label=label)
    for ax in axs:ax.legend(fontsize=7)
    axs[0].set(xlabel='Observed distance (km)',ylabel='DC saving (Wh)');axs[1].set(xlabel='Restarts per km (v crosses 0.1 m/s)',ylabel='DC saving (Wh/km)');axs[2].set(xlabel='W1 rolling contribution (Wh)',ylabel='W3 translation contribution (Wh)')
    fig.suptitle('Frozen DC; 5.448297415kg saving; 460 dependent saved trajectories x 2 Crr; descriptive, no regen/aux/grade',fontsize=9);fig.tight_layout();save(fig,'DRIVING_INTERACTION')
    fig,axs=plt.subplots(1,2,figsize=(10,4));z=importance[(importance.model=='T08')&(importance.rolling_case=='CRR_LOWER_BOUND')]
    axs[0].barh(z.factor,z.local_mean_delta_DC_Wh_for_step);axs[0].set(xlabel='Local mean DC saving change (Wh)',title='1% input step; extra: 0.01 kg')
    axs[1].barh(z.factor,z.DC_range_span_mean_Wh);axs[1].set(xlabel='Mean DC saving span (Wh)',title='Declared exploration ranges (not uncertainty)')
    fig.suptitle('T08 S-only design; frozen 460 trajectories, CRR lower bound; no practical qualification',fontsize=9);fig.tight_layout();save(fig,'FACTOR_IMPORTANCE')

def main():
    freeze,saved,old=preflight()
    if '--reproduce-only' in sys.argv:
        csv('evidence/NUMERICAL_AUDIT.csv',checks);return
    cases,oldmap,ranges=build_design(old)
    bounds=boundaries();verify_t09(cases)
    summary,op,derivs,stats=run_dc(freeze,saved,cases)
    importance=factors(cases,summary,derivs,ranges);figures(cases,bounds,op,importance)
    for p,h in sources.items():check('source unchanged '+p,sha(p)==h)
    csv('evidence/SOURCE_MANIFEST.csv',[dict(path=p,sha256=h,preserved=True) for p,h in sources.items()])
    csv('evidence/NUMERICAL_AUDIT.csv',checks)
    stats.update(mass_cases=len(cases),old_rows=239,old_unique_inputs=len(oldmap),old_unique_T08=sum(json.loads(k)[0]=='T08' for k in oldmap),
                 new_inputs=sum(c['origin']=='NEW_EXPLORATORY_INPUT' for c in cases),reused_inputs=sum(c['origin']=='EXISTING_INPUT_REUSED' for c in cases),
                 checks=len(checks),failures=0,source_count=len(sources),python=sys.version,numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__,
                 M0=M0,MS=MS,b=b,scientific_verdict='CONDITIONAL GO',practical_pack='HOLD',T09_complete_pack='HOLD')
    (O/'evidence/RUN_RESULT.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(stats,indent=2),flush=True)

if __name__=='__main__':main()
