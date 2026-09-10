"""Link the read-only execution-authorization recheck into the root manifest."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    path = OUT / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["files"]["authorization_recheck.json"] = sha(OUT / "authorization_recheck.json")
    path.write_bytes(canonical(manifest) + b"\n")

if __name__ == "__main__":
    main()
