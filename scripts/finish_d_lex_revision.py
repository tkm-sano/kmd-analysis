"""Sequential audits after the preserved, lex-corrected D experiments."""
import argparse
import os
import subprocess
import sys
import time

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--wait-pid',type=int,required=True);a=p.parse_args()
    while True:
        try:os.kill(a.wait_pid,0)
        except ProcessLookupError:break
        time.sleep(2)
    stages=[('run_ad_reproducibility.py',[]),('audit_ad_results.py',[]),('audit_d_macro_scope.py',['--include-s1']),('audit_d_attribution.py',[]),('audit_ad_full_routes.py',['--all-feasible']),('summarize_ad_reproducibility.py',[]),('plot_ad_tradeoffs.py',[])]
    for name,args in stages:
        print('FINAL_LEX_STAGE',name,flush=True);subprocess.run([sys.executable,'scripts/'+name,*args],check=True)
