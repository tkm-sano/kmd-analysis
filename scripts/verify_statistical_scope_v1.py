#!/usr/bin/env python3
"""Verify the user-approved statistical specification and machine policy."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from kmd_toc.descriptive_v1.policy import require_frozen,VERSION,PINS
if __name__=='__main__':
    require_frozen()
    print(json.dumps({'version':VERSION,'specification':'PASS','sha256':PINS,'formal_J':'HOLD'},ensure_ascii=False))
