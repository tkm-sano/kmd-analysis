"""Sequential retries, repeatability and independent validation after main run."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--wait-pid',type=int);a=parser.parse_args()
    while a.wait_pid:
        try:os.kill(a.wait_pid,0)
        except ProcessLookupError:break
        time.sleep(2)
    for script,extra in [('run_ad_experiments.py',[]),('run_ad_reproducibility.py',[]),('audit_ad_results.py',[]),('audit_d_macro_scope.py',['--include-s1'])]:
        print('VALIDATION_STAGE',script,flush=True)
        subprocess.run([sys.executable,'scripts/'+script,*extra],check=True)
