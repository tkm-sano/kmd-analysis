"""Two toy trajectories show distance/time do not identify controlled DC."""
from support import *
def energy(v,m=1200,p=4.5):
 total=0.;d=0.
 for u,w in zip(v,v[1:]):
  ds=w;d+=ds;cr=.005+(.01+.0095*(3.6*w/100)**2)/p
  W=m*9.80665*cr*ds+.5*1.2041*1.175*w*w*ds+.5*(m+61)*(w*w-u*u)
  total+=max(W,0)/.90/3600
 return d,total
def main():
 t=time.monotonic();out=[]
 for label,v in [('concentrated_cruise',[0,10,10,0,0]),('distributed_acceleration',[0,5,5,10,0])]:
  d,e=energy(v);out.append({'fixture_id':label,'timestamps_s':'[0,1,2,3,4]','speed_m_s':json.dumps(v),'distance_m':d,'duration_s':4,'DC_Wh':e,'mass_kg':1200,'mass_scope':'TOY_ONLY_NOT_B_ADOPTION','interpretation':'CONDITIONAL_SYNTHETIC_INPUT_NOT_EXISTING_B_TRAJECTORY'})
 check('same distance',out[0]['distance_m'],out[1]['distance_m']);check('same time',out[0]['duration_s'],out[1]['duration_s']);check('different energy',True,abs(out[0]['DC_Wh']-out[1]['DC_Wh'])>1e-6);table('B_ENERGY_NONIDENTIFICATION_FIXTURES.csv',out);finish('TOY',t,{'toy_profiles':2,'B_new_energy_evaluations':0,'claim':'Distance and time alone do not identify W1-W4 DC; no quantitative B energy effect inferred'})
if __name__=='__main__':main()
