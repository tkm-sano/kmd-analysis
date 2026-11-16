"""Read current-process VmHWM, separately from inherited getrusage history."""
import json
from pathlib import Path
import sys
import time

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'output/toc_delivery/dwt_balance_20261113_v1/revision_1_1')
existing = root / 'RESOURCE_SAMPLES.json'
seen = json.loads(existing.read_text())['trials'] if existing.exists() else {}
while True:
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():
            continue
        try:
            cmd = (p / 'cmdline').read_bytes().decode().replace('\0', ' ')
            if 'kmd_toc.dwt.worker --spec ' not in cmd or str(root) not in cmd:
                continue
            status = (p / 'status').read_text()
            fields = dict(x.split(':', 1) for x in status.splitlines() if ':' in x)
            hwm = int(fields['VmHWM'].split()[0])
            trial = Path(cmd.split('--spec ', 1)[1].strip()).parent.name
            row = seen.setdefault(trial, {'pid': int(p.name), 'sampled_current_mm_peak_RSS_KiB': 0, 'samples': 0})
            row['sampled_current_mm_peak_RSS_KiB'] = max(row['sampled_current_mm_peak_RSS_KiB'], hwm)
            row['samples'] += 1
        except (OSError, ValueError, KeyError):
            continue
    (root / 'RESOURCE_SAMPLES.json').write_text(json.dumps({'scope': '/proc VmHWM samples after exec; may miss early trials/final milliseconds; not exact allocation attribution', 'trials': seen}, indent=2) + '\n')
    if (root / 'STOP_RESOURCE_MONITOR').exists():
        break
    time.sleep(.2)
