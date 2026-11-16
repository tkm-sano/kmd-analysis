"""One same-seed S1 repeat per method; separate from registered A ranges."""
import json
from run_ad_experiments import ROOT,launch

if __name__=='__main__':
    ref=json.loads((ROOT/'EPSILON_REFERENCES.json').read_text())['S1']
    launch('S1','A2','repeat_angle0',offset=0)
    for method in ['B','C','D']:launch('S1',method,'repeat_primaryD_epsW_1',limit=ref['W_min'])
