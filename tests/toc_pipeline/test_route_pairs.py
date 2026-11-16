import json
from pathlib import Path
from urllib.parse import urlsplit
import pytest
from kmd_toc.baseline_a.fixtures import artificial_problem
from kmd_toc.pipeline.route_pairs import build_route_matrix


@pytest.mark.parametrize('n,block',[(1,1),(3,2)])
@pytest.mark.parametrize('processes',[0,2])
def test_route_per_pair_evidence_resume_and_ancestor_reuse(monkeypatch,tmp_path,n,block,processes):
    p=artificial_problem(n,2,1);points=[(p.depot.longitude,p.depot.latitude)]+[(s.longitude,s.latitude) for s in p.stops];calls=[]
    class Connection:
        def __init__(self,*args,**kwargs):pass
        def request(self,method,path,headers):
            assert headers=={'Connection':'close'}
            calls.append(path);coords=urlsplit(path).path.rsplit('/',1)[1].split(';');self.indices=[points.index(tuple(map(float,s.split(',')))) for s in coords]
        def getresponse(self):
            a,b=self.indices
            raw={'code':'Ok','waypoints':[{'location':points[i]} for i in [a,b]],'routes':[{'distance':float(p.od.distance_m[a,b]),'duration':float(p.od.duration_s[a,b]),'legs':[{'annotation':{'nodes':[a,b]}}]}]}
            class Response:
                status=200
                def read(self):return json.dumps(raw).encode()
            return Response()
        def close(self):pass
    monkeypatch.setattr('kmd_toc.pipeline.route_pairs.http.client.HTTPConnection',Connection)
    od=build_route_matrix(p,p.od.metadata,tmp_path/'first',block_size=block,process_workers=processes)
    expected_calls=(n+1)**2 if not processes else 0
    assert len(calls)==expected_calls and od.fingerprint==p.od.fingerprint
    resumed=build_route_matrix(p,p.od.metadata,tmp_path/'first',block_size=block,process_workers=processes)
    assert len(calls)==expected_calls and resumed.fingerprint==od.fingerprint
    inherited=build_route_matrix(p,p.od.metadata,tmp_path/'second',block_size=block,process_workers=processes,ancestor={'od':od,'hash':od.fingerprint,'directory':str(tmp_path/'first')})
    assert len(calls)==expected_calls and inherited.fingerprint==od.fingerprint
    checkpoint=json.loads((tmp_path/'second/CHECKPOINT.json').read_text())
    assert checkpoint['service']=='Route' and checkpoint['status']=='COMPLETE'
    rawfile=next((tmp_path/'first/blocks').glob('*.json.gz'));rawfile.write_bytes(rawfile.read_bytes()+b'altered')
    with pytest.raises(ValueError,match='CACHE_HASH'):build_route_matrix(p,p.od.metadata,tmp_path/'first',block_size=block,process_workers=processes)
