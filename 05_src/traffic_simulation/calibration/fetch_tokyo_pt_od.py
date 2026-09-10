#!/usr/bin/env python3
"""Acquire public Tokyo PT OD and zone files without submitting user forms."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "tokyo_pt_2018_od_by_purpose_and_main_mode.csv": (
        "https://www.e-stat.go.jp/stat-search/file-download?fileKind=1&statInfId=000032066127"
    ),
    "tokyo_pt_2018_zone_mode_hour_trip_ends.csv": (
        "https://www.e-stat.go.jp/stat-search/file-download?fileKind=1&statInfId=000032066125"
    ),
    "tokyo_pt_2018_zone_code.xlsx": (
        "https://www.tokyo-pt.jp/static/hp/file/data/H30_zonecode.xlsx"
    ),
    "tokyo_pt_2018_zone_geometry.zip": (
        "https://www.tokyo-pt.jp/static/hp/file/data/H30_gis.zip"
    ),
    "tokyo_pt_data_guide.pdf": (
        "https://www.tokyo-pt.jp/static/hp/file/data/tebiki.pdf"
    ),
    "tokyo_pt_terms.html": "https://www.tokyo-pt.jp/terms",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"immutable acquisition directory already exists: {output}")
    output.mkdir(parents=True)
    retrieved_at = datetime.now(timezone.utc).astimezone().isoformat()
    records = []
    for filename, url in SOURCES.items():
        destination = output / filename
        request = urllib.request.Request(url, headers={"User-Agent": "kmd-analysis-research/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            destination.write_bytes(response.read())
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
        records.append({
            "filename": filename,
            "source_url": url,
            "final_url": final_url,
            "content_type": content_type,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "retrieved_at": retrieved_at,
        })
    manifest = {
        "artifact_id": "TOKYO_PT_2018_PUBLIC_OD_ACQUISITION_V1",
        "retrieved_at": retrieved_at,
        "acquisition_boundary": "public HTTP files only; no form submission, login, or access-control bypass",
        "license": {
            "name": "公共データ利用規約（第1.0版）",
            "attribution_required": True,
            "source_page": "https://www.tokyo-pt.jp/terms",
        },
        "files": records,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"files": len(records), "bytes": sum(r["bytes"] for r in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
