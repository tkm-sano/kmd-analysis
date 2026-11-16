"""Start measurements only after the complete S1 and validation bundles exist."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if __name__=='__main__':
    root=Path(os.environ['KMD_AD_OUTPUT_ROOT']);manifest=root/'roads/COMMON_BUNDLES.json'
    while not manifest.exists():time.sleep(2)
    while not {'S1','ROAD_N6','ROAD_N20','ROAD_N120','ROAD_N240'}<={r['id'] for r in json.loads(manifest.read_text())}:time.sleep(2)
    for script,args in [('run_ad_experiments.py',[]),('run_ad_reproducibility.py',[]),('audit_ad_results.py',[]),('audit_d_macro_scope.py',['--include-s1']),('audit_ad_full_routes.py',['--all-feasible'])]:
        print('STAGE',script,flush=True);subprocess.run([sys.executable,'scripts/'+script,*args],check=True)
