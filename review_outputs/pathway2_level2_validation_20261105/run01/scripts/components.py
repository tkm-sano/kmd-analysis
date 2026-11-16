"""SI component accounting for explicit design inputs. None always means unknown.
These primitives implement volume/mass bookkeeping, not a full BatPaC solver.
"""
from dataclasses import dataclass
from math import isfinite

def valid(x,name,strict=True):
    if not isinstance(x,(int,float)) or not isfinite(x) or (x<=0 if strict else x<0):
        raise ValueError(name+' must be finite and '+('positive' if strict else 'nonnegative'))

def panel_kg(area_m2,thickness_m,density_kg_m3,count=1):
    if any(x is None for x in [area_m2,thickness_m,density_kg_m3,count]):return None
    valid(area_m2,'area');valid(thickness_m,'thickness');valid(density_kg_m3,'density');valid(count,'count',False)
    if int(count)!=count:raise ValueError('integer count required')
    return area_m2*thickness_m*density_kg_m3*count

def laminate_kg(developed_area_m2,layers):
    """Area is the TOTAL developed envelope area including both sides and seals.
    Layers are (thickness_m, density_kg_m3); no invented pouch layer defaults.
    """
    if developed_area_m2 is None or layers is None or any(t is None or r is None for t,r in layers):return None
    if not layers:raise ValueError('unknown/empty laminate is not mass zero')
    return sum(panel_kg(developed_area_m2,t,r) for t,r in layers)

def tab_kg(width_m,length_m,thickness_m,density_kg_m3,count=1):
    if width_m is None or length_m is None:return None
    valid(width_m,'width');valid(length_m,'length')
    return panel_kg(width_m*length_m,thickness_m,density_kg_m3,count)

def foil_increment_kg(uncoated_tab_margin_area_m2,extra_end_foil_area_m2,thickness_m,density_kg_m3):
    """Adds only the area not already counted in T09 face_area/2.
    Zero end area is allowed only as an explicit known absence, never as None.
    Integral foil tabs belong to uncoated area, not an extra terminal part.
    """
    if any(x is None for x in [uncoated_tab_margin_area_m2,extra_end_foil_area_m2,thickness_m,density_kg_m3]):return None
    valid(uncoated_tab_margin_area_m2,'uncoated area',False);valid(extra_end_foil_area_m2,'end area',False)
    valid(thickness_m,'thickness');valid(density_kg_m3,'density')
    return (uncoated_tab_margin_area_m2+extra_end_foil_area_m2)*thickness_m*density_kg_m3

def closed_box_kg(length_m,width_m,height_m,wall_m,density_kg_m3):
    """Exact uniform closed rectangular-shell volume; not a pouch seam model."""
    if any(x is None for x in [length_m,width_m,height_m,wall_m,density_kg_m3]):return None
    for x,n in [(length_m,'L'),(width_m,'W'),(height_m,'H'),(wall_m,'wall'),(density_kg_m3,'density')]:valid(x,n)
    if 2*wall_m>=min(length_m,width_m,height_m):raise ValueError('wall exceeds dimensions')
    return (length_m*width_m*height_m-(length_m-2*wall_m)*(width_m-2*wall_m)*(height_m-2*wall_m))*density_kg_m3

BDU_G=dict(main_contactor=750,aux_contactor=180,precharge_contactor=90,precharge_resistor=185,service_disconnect=150,service_fuse=80,charger_fuse=24,current_sensor=55)
def bms_kg(n_pcb,n_asic,bdu_counts):
    """Manual secs7.2,7.6: BMU 40g/PCB +20g/ASIC, 10% enclosure;
    1.3*(BMU+BDU) at pack level. Explicit architecture/PCB count is required.
    Module electronics 46g/module is accounted in MODULE, not here.
    Wiring is lumped in BMU/module; it must not be added separately.
    """
    if n_pcb is None or n_asic is None or bdu_counts is None or any(v is None for v in bdu_counts.values()):return None
    if set(bdu_counts)!=set(BDU_G):raise ValueError('all BDU categories require explicit counts')
    for n in [n_pcb,n_asic,*bdu_counts.values()]:
        valid(n,'component count',False)
        if int(n)!=n:raise ValueError('integer count required')
    bmu=1.1*(.040*n_pcb+.020*n_asic)
    bdu=sum(BDU_G[k]/1000*n for k,n in bdu_counts.items())
    return 1.3*(bmu+bdu)

def external_cooler_kg(required_cooling_W,fast_charge=False):
    """Manual Table8.2, one-pack example. Return None above published capacities.
    This mass belongs to BATTERY SYSTEM, not pack. Heat load is mandatory.
    """
    if required_cooling_W is None or fast_charge is None:return None
    valid(required_cooling_W,'cooling load',False)
    if fast_charge:return 7.0
    for watts,kg in [(500,2.),(1000,3.),(3000,5.),(6000,7.)]:
        if required_cooling_W<=watts:return kg
    return None

@dataclass(frozen=True)
class Part:
    name:str
    mass_kg:float|None
    scope:str
    coverage:tuple[str,...]
    provenance:str

class Ledger:
    def __init__(self):self.parts=[];self.covered=set()
    def add(self,part):
        if part.scope not in ['PACK','SYSTEM_EXTERNAL']:raise ValueError('unknown boundary')
        if part.mass_kg is not None:valid(part.mass_kg,part.name,False)
        if not part.coverage or len(set(part.coverage))!=len(part.coverage):raise ValueError('unique physical coverage required')
        if self.covered.intersection(part.coverage):raise ValueError('physical component double counting')
        self.parts.append(part);self.covered.update(part.coverage)
    def summarize(self,required_coverage):
        if not set(required_coverage).issubset(self.covered):raise ValueError('required components omitted; supply explicit None')
        pack=[p for p in self.parts if p.scope=='PACK'];external=[p for p in self.parts if p.scope=='SYSTEM_EXTERNAL']
        unknown=[p.name for p in pack if p.mass_kg is None]
        K=sum(p.mass_kg for p in pack if p.mass_kg is not None)
        pack_total=None if unknown else K
        ext_unknown=[p.name for p in external if p.mass_kg is None]
        system_total=None if unknown or ext_unknown else K+sum(p.mass_kg for p in external)
        return dict(known_design_subtotal_kg=K,unknown_pack_parts=unknown,unknown_external_parts=ext_unknown,
                    complete_pack_kg=pack_total,complete_system_kg=system_total,
                    external_known_kg=sum(p.mass_kg for p in external if p.mass_kg is not None))

def demo_and_checks():
    """Declared synthetic geometry only; no target material/real pack prediction."""
    checks=[];rows=[]
    def test(name,ok,detail=''):
        checks.append(dict(check=name,status='PASS' if ok else 'FAIL',detail=str(detail)))
        if not ok:raise AssertionError((name,detail))
    layers=[(40e-6,2700.),(80e-6,900.)];lam=laminate_kg(.1,layers)
    test('laminate SI: 0.1m2*(40um*2700+80um*900)=0.018kg',abs(lam-.018)<1e-12)
    foil=foil_increment_kg(.002,.001,10e-6,8960.)
    test('foil increment: 3e-3m2*10um*8960',abs(foil-.0002688)<1e-12)
    terminal=tab_kg(.04,.02,.0012,2700.,2)
    test('2 Al terminals SI',abs(terminal-.005184)<1e-12)
    box=closed_box_kg(.2,.1,.05,.001,2700.)
    volume_by_panels=2*.2*.1*.001+2*.2*.001*(.05-.002)+2*.001*(.1-.002)*(.05-.002)
    test('box corners counted once, independent panel partition',abs(box-volume_by_panels*2700)<1e-12)
    counts=dict(main_contactor=2,aux_contactor=2,precharge_contactor=1,precharge_resistor=1,service_disconnect=1,service_fuse=1,charger_fuse=1,current_sensor=1)
    bms=bms_kg(1,10,counts);expected=1.3*(1.1*(.04+.2)+1.5+.36+.09+.185+.15+.08+.024+.055)
    test('BMS separate BMU/BDU/enclosures',abs(bms-expected)<1e-12)
    for name,value in [('laminate',lam),('foil_increment',foil),('terminals',terminal),('closed_box',box),('pack_BMS',bms),('external_cooler',external_cooler_kg(800.))]:
        rows.append(dict(component=name,mass_kg=value,scope='SYSTEM_EXTERNAL' if name=='external_cooler' else 'PACK',basis='SYNTHETIC_UNIT_FIXTURE_ONLY'))
    required={'cell.active_coatings','cell.foils.base','cell.foils.uncoated','cell.pouch','cell.terminals','cell.separator_liquid','cell.other','module.structure','module.connections','module.electronics','pack.structure','pack.connections','thermal.internal','protection','bms.pack','bms.interface','thermal.external','thermal.external_other'}
    L=Ledger()
    parts=[Part('coatings',None,'PACK',('cell.active_coatings',),'missing target'),Part('base foil',None,'PACK',('cell.foils.base',),'missing target'),
           Part('uncoated foil',foil,'PACK',('cell.foils.uncoated',),'toy .003m2'),Part('pouch',lam,'PACK',('cell.pouch',),'toy area/layers'),
           Part('terminals',terminal,'PACK',('cell.terminals',),'toy geometry'),Part('separator and liquid',None,'PACK',('cell.separator_liquid',),'missing target'),
           Part('other cell hardware',None,'PACK',('cell.other',),'not specified'),
           Part('module structure',None,'PACK',('module.structure',),'not specified'),Part('module connections',None,'PACK',('module.connections',),'not specified'),
           Part('pack connections',None,'PACK',('pack.connections',),'not specified'),Part('internal thermal parts and coolant',None,'PACK',('thermal.internal',),'not specified'),
           Part('protection and gas release',None,'PACK',('protection',),'not specified'),Part('module electronics',.046*10,'PACK',('module.electronics',),'10 module fixture'),
           Part('pack structure',box,'PACK',('pack.structure',),'toy closed box'),Part('pack BMS',bms,'PACK',('bms.pack','bms.interface'),'wiring lumped'),
           Part('external cooler',external_cooler_kg(800.),'SYSTEM_EXTERNAL',('thermal.external',),'toy 800W, 1pack'),
           Part('heater and vehicle AC additions',None,'SYSTEM_EXTERNAL',('thermal.external_other',),'not in BatPaC pack mass; actual hardware unknown')]
    for p in parts:L.add(p)
    summary=L.summarize(required)
    test('unknown pack and system stay NULL',summary['complete_pack_kg'] is None and summary['complete_system_kg'] is None)
    test('external cooler excluded from pack K',abs(summary['known_design_subtotal_kg']-sum(p.mass_kg for p in parts if p.scope=='PACK' and p.mass_kg is not None))<1e-12 and summary['external_known_kg']==3.)
    for name,action in [('duplicate interface wiring',lambda:L.add(Part('extra wiring',.1,'PACK',('bms.interface',),'invalid duplicate'))),
                        ('duplicate base+full foil',lambda:L.add(Part('full foil again',.1,'PACK',('cell.foils.base','cell.foils.uncoated'),'invalid duplicate'))),
                        ('omitted unknown required item',lambda:Ledger().summarize(required))]:
        try:action();rejected=False
        except ValueError:rejected=True
        test(name+' rejected',rejected)
    test('unknown laminate does not default zero',laminate_kg(.1,[(None,2700.)]) is None)
    test('unknown foil end area does not default zero',foil_increment_kg(.002,None,10e-6,8960.) is None)
    test('unknown cooler load does not default zero',external_cooler_kg(None) is None)
    test('cooler absolute shared mass cancels',external_cooler_kg(800.)-external_cooler_kg(800.)==0.)
    test('no T08 fixed 34kg in T09 ledger',all('34' not in p.provenance for p in parts))
    return rows,checks,summary
