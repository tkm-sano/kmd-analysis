#!/usr/bin/env python3
"""Stream audit of SUMO XML geometry, lengths and connection gaps."""
from __future__ import annotations
import argparse, json, math
import xml.etree.ElementTree as ET
from pathlib import Path

def d(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def pts(s): return [tuple(map(float,x.split(',')[:2])) for x in s.split() if ',' in x]
def plen(p): return sum(d(a,b) for a,b in zip(p,p[1:]))

def audit(path: Path):
    junction={}; counts={'junction':0,'edge':0,'lane':0,'connection':0}
    for _,e in ET.iterparse(path,events=('end',)):
        if e.tag=='junction':
            counts['junction']+=1; junction[e.attrib['id']]=(float(e.attrib['x']),float(e.attrib['y']))
        e.clear()
    edges={}; lane_diffs=[]; node_gaps=[]
    for _,e in ET.iterparse(path,events=('end',)):
        if e.tag=='edge':
            counts['edge']+=1; eid=e.attrib['id']; f=e.attrib.get('from'); t=e.attrib.get('to'); sh=pts(e.attrib.get('shape',''))
            edges[eid]={'from':f,'to':t,'function':e.attrib.get('function',''),'shape':sh}
            if sh and f in junction and t in junction:
                node_gaps.append(max(d(sh[0],junction[f]),d(sh[-1],junction[t])))
            for l in e.findall('lane'):
                counts['lane']+=1
                if 'length' in l.attrib:
                    ls=pts(l.attrib.get('shape','')); L=float(l.attrib['length'])
                    lane_diffs.append(abs(L-plen(ls)))
        elif e.tag=='connection': counts['connection']+=1
        e.clear()
    conn_gaps=[]
    for _,e in ET.iterparse(path,events=('end',)):
        if e.tag=='connection':
            u=e.attrib.get('from'); v=e.attrib.get('to')
            if u in edges and v in edges and edges[u]['function']!='internal' and edges[v]['function']!='internal':
                a=edges[u]['shape']; b=edges[v]['shape']
                if a and b: conn_gaps.append(d(a[-1],b[0]))
        e.clear()
    return {'counts':counts,'edge_node_endpoint_gap_max_m':max(node_gaps or [0.0]),'edge_node_endpoint_gap_failures':sum(x>1e-6 for x in node_gaps),'lane_declared_vs_shape_max_abs_m':max(lane_diffs or [0.0]),'lane_declared_vs_shape_failures':sum(x>1e-3 for x in lane_diffs),'connection_shape_gap_count':len(conn_gaps),'connection_shape_gap_max_m':max(conn_gaps or [0.0]),'connection_shape_gap_failures':sum(x>1e-6 for x in conn_gaps)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--old',type=Path,required=True); ap.add_argument('--new',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True); out={'old':audit(a.old),'new':audit(a.new)}; a.output.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
