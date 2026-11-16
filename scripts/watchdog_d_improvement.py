"""Process-isolated safety budget; stdout log plus auditable termination record."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',required=True);p.add_argument('--log',required=True)
    p.add_argument('command',nargs=argparse.REMAINDER);args=p.parse_args()
    cfg=json.loads(Path('configs/toc_delivery_d_pricing_improvement_v1.json').read_text())['safety']
    begin=time.monotonic();peak=0.;reason=None
    with open(args.log,'x') as log:
        child=subprocess.Popen(args.command,stdout=log,stderr=subprocess.STDOUT)
        while child.poll() is None:
            try:
                status=Path(f'/proc/{child.pid}/status').read_text()
                rss=float(next(x for x in status.splitlines() if x.startswith('VmRSS:')).split()[1])/1024
                peak=max(peak,rss)
            except (FileNotFoundError,StopIteration):pass
            if peak>cfg['max_rss_mib']:reason='RSS_SAFETY_LIMIT'
            if time.monotonic()-begin>cfg['max_child_wall_seconds']:reason='WALL_SAFETY_LIMIT'
            if reason:
                child.terminate()
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:child.kill();child.wait()
                break
            time.sleep(.2)
    with open(args.record,'x') as record:
        json.dump({'command':args.command,'returncode':child.returncode,'seconds':time.monotonic()-begin,
                   'peak_observed_rss_mib':peak,'safety_limit_triggered':bool(reason),'reason':reason,'limits':cfg},record,indent=2)
    sys.exit(child.returncode if child.returncode is not None else 1)
