"""Read the pinned PBF; make a bounded display layer and a disk node index."""
import array
import hashlib
import json
import resource
import time
from pathlib import Path
import numpy as np
import osmium

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PBF = REPO / '03_data/raw/traffic_simulation/osm/kanto-260716.osm.pbf'
EXPECTED = 'aef890f28b652ed7bd2b0d77e86f263219b479fe3eedbdd8610dcfc1572c420d'


class Extract(osmium.SimpleHandler):
    def __init__(self, bbox):
        super().__init__()
        self.ids = array.array('q'); self.xy = array.array('i'); self.bbox = bbox
        self.roads = []; self.nodes = None; self.coords = None

    def node(self, n):
        self.ids.append(n.id)
        self.xy.extend([round(n.location.lon * 1e7), round(n.location.lat * 1e7)])
        if len(self.ids) % 5000000 == 0: print('PBF nodes', len(self.ids), flush=True)

    def way(self, w):
        road = w.tags.get('highway', '')
        if road not in {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service',
                        'motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}:
            return
        if self.nodes is None:
            self.nodes = np.frombuffer(self.ids, dtype=np.int64)
            self.coords = np.frombuffer(self.xy, dtype=np.int32).reshape(-1, 2)
            if not np.all(self.nodes[1:] > self.nodes[:-1]): raise ValueError('PBF node IDs not sorted')
        refs = np.array([x.ref for x in w.nodes], dtype=np.int64)
        ix = np.searchsorted(self.nodes, refs)
        if np.any(ix >= len(self.nodes)) or np.any(self.nodes[ix] != refs): return
        coords = self.coords[ix] / 1e7
        x0,y0,x1,y1 = self.bbox
        inside = (coords[:,0] >= x0) & (coords[:,0] <= x1) & (coords[:,1] >= y0) & (coords[:,1] <= y1)
        if not inside.any(): return
        self.roads.append({'id':int(w.id),'highway':road,'oneway':w.tags.get('oneway',''),
                           'access':w.tags.get('access',''), 'coordinates':coords.tolist()})


def main():
    start = time.perf_counter()
    digest = hashlib.file_digest(PBF.open('rb'), 'sha256').hexdigest()
    if digest != EXPECTED: raise ValueError('Pinned PBF hash mismatch')
    s3 = json.loads((REPO/'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S3/input.json').read_text())
    points = [(x['longitude'],x['latitude']) for x in [s3['depot'],*s3['stops']]]
    xy = np.array(points); bbox = [float(xy[:,0].min()-.025),float(xy[:,1].min()-.02),float(xy[:,0].max()+.025),float(xy[:,1].max()+.02)]
    h = Extract(bbox); h.apply_file(str(PBF))
    nodes = np.frombuffer(h.ids,dtype=np.int64); coords = np.frombuffer(h.xy,dtype=np.int32).reshape(-1,2)
    np.save(ROOT/'data/osm_node_ids.npy',nodes); np.save(ROOT/'data/osm_node_xy_e7.npy',coords)
    (ROOT/'data/roads.json').write_text(json.dumps(h.roads,separators=(',',':')))
    result = {'source':str(PBF.relative_to(REPO)), 'source_sha256':digest,'nodes':len(nodes),'display_ways':len(h.roads),
              'display_bbox_wgs84':bbox, 'display_scope':'OSM motor-road context; not a separate routing graph or all access validation',
              'node_coordinate_encoding':'int32 degrees times 1e7, original OSM coordinates',
              'node_index_bytes':nodes.nbytes+coords.nbytes,'elapsed_s':time.perf_counter()-start,
              'max_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (ROOT/'ROAD_EXTRACTION.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__': main()
