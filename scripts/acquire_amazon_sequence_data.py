#!/usr/bin/env python3
"""Acquire public Amazon files within a fixed one-GB cap; never use AWS credentials."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://amazon-last-mile-challenges.s3.amazonaws.com/almrrc2021/'
FILES = {
    'pilot_routes.json': 'almrrc2021-data-training/model_apply_inputs/new_route_data.json',
    'pilot_times.json': 'almrrc2021-data-training/model_apply_inputs/new_travel_times.json',
    'pilot_actual.json': 'almrrc2021-data-training/model_score_inputs/new_actual_sequences.json',
    'eval_routes.json': 'almrrc2021-data-evaluation/model_apply_inputs/eval_route_data.json',
    'eval_times.json': 'almrrc2021-data-evaluation/model_apply_inputs/eval_travel_times.json',
    'eval_actual.json': 'almrrc2021-data-evaluation/model_score_inputs/eval_actual_sequences.json',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    config = json.loads((ROOT / 'configs/toc_delivery/a_sequence_external_v1.json').read_text())
    manifest = {'dataset': '2021 Amazon Last Mile Routing Research Challenge',
                'license': 'CC BY-NC 4.0; copyright Amazon.com, Inc. or affiliates',
                'registry': 'https://registry.opendata.aws/amazon-last-mile-challenges/',
                'acquisition': 'unsigned public HTTPS GET; no account or paid computation', 'files': {}}
    total = 0
    try:
        for name, key in FILES.items():
            begin, digest = time.monotonic(), hashlib.sha256()
            record = {'url': BASE + key, 'started_at_utc': datetime.now(timezone.utc).isoformat()}
            manifest['files'][name] = record
            with urlopen(Request(BASE + key), timeout=30) as response:
                length = int(response.headers['Content-Length'])
                if total + length > config['limits']['download_total_bytes']:
                    raise ValueError('DOWNLOAD_BYTE_CAP')
                record.update(content_length=length, etag=response.headers.get('ETag'),
                              last_modified=response.headers.get('Last-Modified'))
                received = 0
                with (out / (name + '.part')).open('xb') as stream:
                    while block := response.read(1024 * 1024):
                        if time.monotonic() - begin > config['limits']['download_wall_s_per_file']:
                            raise TimeoutError('DOWNLOAD_WALL_LIMIT')
                        received += len(block)
                        total += len(block)
                        if total > config['limits']['download_total_bytes'] or received > length:
                            raise ValueError('DOWNLOAD_BYTE_CAP_OR_LENGTH')
                        stream.write(block)
                        digest.update(block)
                if received != length:
                    raise ValueError('DOWNLOAD_TRUNCATED')
                (out / (name + '.part')).rename(out / name)
                record.update(status='COMPLETE', bytes=received, sha256=digest.hexdigest(),
                              elapsed_s=time.monotonic() - begin)
            print(json.dumps({'file': name, 'bytes': received, 'elapsed_s': record['elapsed_s']}), flush=True)
        manifest['status'] = 'COMPLETE'
    except Exception as error:
        manifest.update(status='FAILED', error={'type': type(error).__name__, 'message': str(error)})
        raise
    finally:
        manifest['total_bytes_received'] = total
        (out / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
