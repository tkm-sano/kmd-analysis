"""Add non-semantic aggregate R20/R21/R22 authority manifests."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reproducibility/outputs/traffic_simulation/r23_formal_instance_authority/20260911_v1"

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_bytes(canonical(value) + b"\n")
    return sha(path)

def main():
    summary = json.loads((OUT / "authority_summary.json").read_text())
    for stage in ("r20", "r21", "r22"):
        records = []
        for item in summary["instances"]:
            records.append({"instance_id": item["instance_id"], **item[stage]})
        payload = {"schema_version": f"r23-formal-{stage}-authority-set-v1", "instance_set_id": "R23_FORMAL_INSTANCE_SET_V1", "stage": stage.upper(), "count": len(records), "status": "PASS" if len(records) == 15 and all(x["status"].endswith("PASS") for x in records) else "FAIL", "records": records}
        write(OUT / f"{stage}_authority_set.json", payload)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name in ("r20_authority_set.json", "r21_authority_set.json", "r22_authority_set.json"):
        manifest["files"][name] = sha(OUT / name)
    write(manifest_path, manifest)

if __name__ == "__main__":
    main()
