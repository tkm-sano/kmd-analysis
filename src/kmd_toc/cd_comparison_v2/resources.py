"""Linux process telemetry without altering either existing Python environment."""
from pathlib import Path
import os

def sample(pid):
    try:
        raw=Path(f'/proc/{pid}/stat').read_text();fields=raw[raw.rfind(')')+2:].split()
        status=Path(f'/proc/{pid}/status').read_text().splitlines()
        memory={x.split(':',1)[0]:int(x.split()[1])*1024 for x in status if x.startswith(('VmRSS:','VmHWM:'))}
        return dict(PID=pid,CPU_s=(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'),
            RSS_bytes=memory.get('VmRSS',0),state=fields[0],start_ticks=int(fields[19]))
    except (FileNotFoundError,ProcessLookupError):return None
