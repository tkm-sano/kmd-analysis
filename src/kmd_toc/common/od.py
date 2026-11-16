"""Directed, same-route metre/second OD; local OSRM only, no estimation."""
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import ipaddress
import json
import math
from pathlib import Path
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import numpy as np
from .config import digest_file, fingerprint, read_json


def array_digest(array):
    h = hashlib.sha256()
    h.update(str(array.dtype).encode())
    h.update(str(array.shape).encode())
    for row in array:
        h.update(np.ascontiguousarray(row).tobytes())
    return h.hexdigest()


@dataclass(frozen=True)
class OD:
    ids: tuple[str, ...]
    distance_m: np.ndarray
    duration_s: np.ndarray
    reachable: np.ndarray
    metadata: dict

    @property
    def fingerprint(self):
        return fingerprint({'ids': self.ids, 'metadata': self.metadata,
                            'arrays': [array_digest(a) for a in
                                       (self.distance_m, self.duration_s, self.reachable)]})

    def audit(self, *, require_all_reachable=True):
        n = len(self.ids)
        if not n or any(not isinstance(s, str) or not s for s in self.ids) or len(set(self.ids)) != n:
            raise ValueError('OD_IDS')
        if any(a.shape != (n, n) for a in (self.distance_m, self.duration_s, self.reachable)):
            raise ValueError('OD_SHAPE')
        if (self.distance_m.dtype != np.dtype('float64') or
                self.duration_s.dtype != np.dtype('float64') or self.reachable.dtype != np.dtype('bool')):
            raise ValueError('OD_DTYPE')
        if self.metadata.get('units') != {'distance': 'm', 'duration': 's'}:
            raise ValueError('OD_UNITS')
        if self.metadata.get('kind') not in ('synthetic', 'osm_osrm'):
            raise ValueError('OD_PROVENANCE_KIND')
        if not self.metadata.get('road_version') or not self.metadata.get('graph_id'):
            raise ValueError('OD_ROAD_VERSION')
        if self.metadata['kind'] == 'osm_osrm':
            validate_road_metadata(self.metadata)
        for a in (self.distance_m, self.duration_s):
            if np.any(np.diag(a) != 0) or not np.diag(self.reachable).all():
                raise ValueError('OD_DIAGONAL')
        unreachable = asymmetry = 0
        examples = []
        for lo in range(0, n, 100):
            sl = slice(lo, lo + 100)
            mask = self.reachable[sl]
            for a in (self.distance_m, self.duration_s):
                b = a[sl]
                if np.any(~np.isfinite(b[mask])) or np.any(b[mask] < 0):
                    raise ValueError('OD_MISSING_OR_INVALID_REACHABLE_VALUE')
                if np.any(~np.isnan(b[~mask])):
                    raise ValueError('OD_UNREACHABLE_MUST_BE_NULL')
            unreachable += int(np.count_nonzero(~mask))
            if len(examples) < 10:
                examples.extend((self.ids[lo + int(i)], self.ids[int(j)])
                                for i, j in np.argwhere(~mask)[:10-len(examples)])
            asymmetry += int(np.count_nonzero(mask & self.reachable[:, sl].T &
                                             (self.distance_m[sl] != self.distance_m[:, sl].T)))
        if require_all_reachable and unreachable:
            raise ValueError(f'OD_UNREACHABLE: {unreachable}; {examples}')
        return {'points': n, 'pairs': n*n, 'unreachable_pairs': unreachable,
                'unreachable_examples': examples, 'asymmetric_directed_cells': asymmetry}

    def leg(self, origin, destination):
        i, j = self.ids.index(origin), self.ids.index(destination)
        if not self.reachable[i, j]:
            raise ValueError(f'OD_UNREACHABLE: {origin}->{destination}')
        return float(self.distance_m[i, j]), math.ceil(float(self.duration_s[i, j]))


def validate_road_metadata(meta):
    required = ('source_url', 'acquired_at', 'osm_timestamp', 'road_version', 'graph_id',
                'osrm_version', 'profile', 'profile_sha256', 'raw_sha256', 'graph_artifacts',
                'build_commands', 'generated_at')
    if any(not meta.get(k) for k in required):
        raise ValueError('OD_INCOMPLETE_ROAD_PROVENANCE')
    for value in [meta['profile_sha256'], meta['raw_sha256'], *meta['graph_artifacts'].values()]:
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('OD_PROVENANCE_HASH')
    if (meta.get('route_policy') != 'fastest_same_route' or
            meta.get('fallback_speed_allowed') is not False or meta.get('directed') is not True):
        raise ValueError('OD_ROUTE_POLICY')


def save_od(od, directory):
    od.audit(require_all_reachable=False)
    p = Path(directory)
    p.mkdir(parents=True, exist_ok=False)
    files = {}
    for key, array in [('distance_m', od.distance_m), ('duration_s', od.duration_s), ('reachable', od.reachable)]:
        name = key + '.npy'
        np.save(p / name, array, allow_pickle=False)
        files[name] = digest_file(p / name)
    manifest = {'schema_version': '1.0', 'status': 'COMPLETE', 'ids': od.ids,
                'metadata': od.metadata, 'files': files, 'od_hash': od.fingerprint}
    (p / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))


def load_od(directory):
    p = Path(directory)
    manifest = read_json(p / 'manifest.json')
    if manifest['schema_version'] != '1.0' or manifest['status'] != 'COMPLETE':
        raise ValueError('OD_INCOMPLETE_BUNDLE')
    names = ('distance_m.npy', 'duration_s.npy', 'reachable.npy')
    if set(manifest['files']) != set(names):
        raise ValueError('OD_FILE_INVENTORY')
    for name in names:
        if digest_file(p / name) != manifest['files'][name]:
            raise ValueError('OD_FILE_HASH: ' + name)
    arrays = [np.load(p / name, mmap_mode='r', allow_pickle=False) for name in names]
    od = OD(tuple(manifest['ids']), *arrays, manifest['metadata'])
    od.audit(require_all_reachable=False)
    if od.fingerprint != manifest['od_hash']:
        raise ValueError('OD_CONTENT_HASH')
    return od


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('OSRM_REDIRECT_FORBIDDEN')


class LocalOSRM:
    """No public endpoint or fallback option. Transport injectable for unit tests."""
    def __init__(self, endpoint='http://127.0.0.1:5000', transport=None):
        u = urlparse(endpoint)
        try:
            local = ipaddress.ip_address(u.hostname).is_loopback
        except ValueError:
            local = False
        if (not local or u.scheme != 'http' or u.username or u.password or
                u.path not in ('', '/') or u.query or u.fragment):
            raise ValueError('OSRM_LOCAL_LOOPBACK_ONLY')
        self.endpoint = endpoint.rstrip('/')
        self.transport = transport or self._get

    def _get(self, url):
        with build_opener(NoRedirect()).open(Request(url), timeout=120) as response:
            return json.load(response)

    def nearest(self, longitude, latitude, *, number=3):
        response = self.transport(f'{self.endpoint}/nearest/v1/driving/{longitude},{latitude}?number={number}')
        if response.get('code') != 'Ok' or not response.get('waypoints'):
            raise ValueError('OSRM_NO_SNAP')
        return response  # review candidates; never auto-select/approve a snap

    def table(self, origins, destinations, snaps):
        ids = tuple(dict.fromkeys((*origins, *destinations)))
        points = ';'.join(f'{snaps[i].longitude},{snaps[i].latitude}' for i in ids)
        query = urlencode({'sources': ';'.join(str(ids.index(i)) for i in origins),
                           'destinations': ';'.join(str(ids.index(i)) for i in destinations),
                           'hints': ';'.join(snaps[i].hint for i in ids),
                           'annotations': 'distance,duration', 'skip_waypoints': 'false'})
        response = self.transport(f'{self.endpoint}/table/v1/driving/{points}?{query}')
        if response.get('code') != 'Ok' or response.get('fallback_speed_cells'):
            raise ValueError('OSRM_RESPONSE_OR_FALLBACK')
        for key, group in [('sources', origins), ('destinations', destinations)]:
            waypoints = response.get(key, [])
            if len(waypoints) != len(group):
                raise ValueError('OSRM_WAYPOINT_COUNT')
            for waypoint, identifier in zip(waypoints, group):
                expected = snaps[identifier]
                location = waypoint.get('location', [])
                if len(location) != 2 or max(abs(location[0]-expected.longitude),
                                              abs(location[1]-expected.latitude)) > 1e-6:
                    raise ValueError('OSRM_SNAP_DRIFT')
        shape = (len(origins), len(destinations))
        d = np.array(response.get('distances'), dtype='float64')
        t = np.array(response.get('durations'), dtype='float64')
        if d.shape != shape or t.shape != shape or not np.array_equal(np.isnan(d), np.isnan(t)):
            raise ValueError('OSRM_MATRIX_SHAPE_OR_NULL_PAIR')
        return d, t, np.isfinite(d) & np.isfinite(t), response


def generate_local_od(ids, snaps, metadata, directory, *, client=None, block_size=100):
    """Opt-in precomputation only; partial output is retained on error, never loaded."""
    validate_road_metadata(metadata)
    if type(block_size) is not int or not 1 <= block_size <= 100:
        raise ValueError('OD_BLOCK_SIZE')
    if len(set(ids)) != len(ids) or set(ids) != set(snaps):
        raise ValueError('OD_SNAP_IDS')
    for snap in snaps.values():
        snap.validate(metadata['graph_id'], metadata['kind'])
    p = Path(directory)
    p.mkdir(parents=True, exist_ok=False)
    (p / 'responses').mkdir()
    start = time.perf_counter()
    manifest = {'schema_version': '1.0', 'status': 'INCOMPLETE', 'ids': ids,
                'metadata': metadata, 'completed_blocks': []}
    def checkpoint():
        (p / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    checkpoint()
    n = len(ids)
    arrays = [np.lib.format.open_memmap(p / name, mode='w+', dtype=dtype, shape=(n,n))
              for name, dtype in [('distance_m.npy', 'float64'), ('duration_s.npy', 'float64'),
                                  ('reachable.npy', 'bool')]]
    arrays[0][:] = arrays[1][:] = np.nan
    arrays[2][:] = False
    client = client or LocalOSRM()
    for i in range(0, n, block_size):
        for j in range(0, n, block_size):
            src, dst = ids[i:i+block_size], ids[j:j+block_size]
            d, t, mask, raw = client.table(src, dst, snaps)
            if raw.get('data_version') not in (None, metadata['osm_timestamp']):
                raise ValueError('OSRM_DATA_VERSION_DRIFT')
            for a, values in zip(arrays, (d, t, mask)):
                a[i:i+len(src), j:j+len(dst)] = values
                a.flush()
            with gzip.open(p / 'responses' / f'{i}_{j}.json.gz', 'wt') as stream:
                json.dump(raw, stream, allow_nan=False)
            manifest['completed_blocks'].append([i, j, len(src), len(dst)])
            checkpoint()
    od = OD(tuple(ids), *arrays, metadata)
    audit = od.audit(require_all_reachable=False)
    manifest.update(status='COMPLETE', od_hash=od.fingerprint,
                    files={name: digest_file(p/name) for name in
                           ('distance_m.npy', 'duration_s.npy', 'reachable.npy')},
                    audit=audit, preprocessing_wall_s=time.perf_counter()-start,
                    completed_at=datetime.now(timezone.utc).isoformat())
    checkpoint()
    return load_od(p)
