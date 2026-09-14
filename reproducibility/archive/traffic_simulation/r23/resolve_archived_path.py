"""Resolve frozen historical paths without rewriting evidence or launching a run."""
import csv
import hashlib
from pathlib import Path
import sys

ARCHIVE = Path(__file__).resolve().parent
REPOSITORY = ARCHIVE.parents[3]


def resolve(old_path):
    supplied = Path(old_path)
    if supplied.is_absolute():
        supplied = supplied.relative_to(REPOSITORY)
    key = supplied.as_posix()
    with (ARCHIVE / "ARCHIVE_MANIFEST.csv").open(newline="") as stream:
        matches = [row for row in csv.DictReader(stream) if row["old_path"] == key]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one archived path, found {len(matches)}: {key}")
    row = matches[0]
    target = REPOSITORY / row["new_path"]
    if not target.is_file():
        raise FileNotFoundError(target)
    if target.stat().st_size != int(row["size_before"]):
        raise ValueError(f"Size mismatch: {target}")
    if hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256_before"]:
        raise ValueError(f"SHA256 mismatch: {target}")
    return target


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python resolve_archived_path.py OLD_REPOSITORY_PATH")
    print(resolve(sys.argv[1]))
