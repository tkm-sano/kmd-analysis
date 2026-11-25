"""Start registered follow-up only after stage A has closed all measured groups."""
from datetime import datetime,timezone
import subprocess
import sys
import time
from .study import OUT,dump


def main():
    final_gate=OUT/'gates/screen_S3_n12_K20_R5_seed9201.json'
    start=time.monotonic()
    while not final_gate.exists():
        if time.monotonic()-start>5400:raise TimeoutError('STAGE_A_NOT_CLOSED_NO_FOLLOWUP_STARTED')
        time.sleep(5)
    dump(OUT/'FOLLOWUP_AUTOSTART.json',{'started_utc':datetime.now(timezone.utc).isoformat(),
        'gate':str(final_gate),'reason':'last A preflight reached; earlier measured groups fully collected',
        'controller':'followup_v3','main_experiment':False})
    result=subprocess.run([sys.executable,'-B','-m','kmd_toc.nkr_p2_study.followup_v3','execute'])
    if result.returncode:raise SystemExit(result.returncode)


if __name__=='__main__':main()
