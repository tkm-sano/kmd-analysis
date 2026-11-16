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
