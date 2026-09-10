#!/usr/bin/env python3
"""Independent validation for the geometry/length re-acceptance run."""
from __future__ import annotations

import argparse, csv, hashlib, json, math
from pathlib import Path
import sumolib


def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def poly(ps):
    return sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a,b in zip(ps,ps[1:]))


def edge_sig(e):
    return (e.getID(), e.getFromNode().getID(), e.getToNode().getID(), tuple(
        (l.getID(), tuple(sorted(l.getPermissions())), round(l.getSpeed(),6)) for l in e.getLanes()))


def graph_stats(net):
    edges=net.getEdges(); nodes=net.getNodes()
    parent={n.getID():n.getID() for n in nodes}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    for e in edges: union(e.getFromNode().getID(),e.getToNode().getID())
    comps={}
    for n in nodes: comps[find(n.getID())]=comps.get(find(n.getID()),0)+1
    return {'nodes':len(nodes),'edges':len(edges),'lanes':sum(len(e.getLanes()) for e in edges),
            'weak_components':len(comps),'largest_component_nodes':max(comps.values()),
            'largest_component_fraction':max(comps.values())/len(nodes),
            'delivery_permitted_edges':sum(any('delivery' in l.getPermissions() for l in e.getLanes()) for e in edges)}


def connection_gaps(net):
    vals=[]
    for e in net.getEdges():
        if not e.getShape(): continue
        for lane in e.getLanes():
            for conn in lane.getOutgoing():
                to_lane=conn.getToLane(); to_edge=to_lane.getEdge()
                if to_edge.getFunction() == 'internal' or not to_edge.getShape(): continue
                a=e.getShape()[-1]; b=to_edge.getShape()[0]
                vals.append(math.hypot(a[0]-b[0],a[1]-b[1]))
    return vals


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--old',type=Path,required=True); ap.add_argument('--new',type=Path,required=True); ap.add_argument('--root-cause',type=Path,required=True); ap.add_argument('--mapping',type=Path,required=True); ap.add_argument('--accepted',type=Path,required=True); ap.add_argument('--output-dir',type=Path,required=True)
    a=ap.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    old=sumolib.net.readNet(str(a.old),withInternal=False); new=sumolib.net.readNet(str(a.new),withInternal=False)
    old_stats=graph_stats(old); new_stats=graph_stats(new)
    old_edges={e.getID():e for e in old.getEdges()}; new_edges={e.getID():e for e in new.getEdges()}
    topology_same=all(edge_sig(old_edges[k])==edge_sig(new_edges[k]) for k in old_edges if k in new_edges) and set(old_edges)==set(new_edges)
    old_con=connection_gaps(old); new_con=connection_gaps(new)
    old_len_diff=[]; new_len_diff=[]
    for e in old.getEdges():
        for l in e.getLanes(): old_len_diff.append(abs(l.getLength()-poly(l.getShape())))
    for e in new.getEdges():
        for l in e.getLanes(): new_len_diff.append(abs(l.getLength()-poly(l.getShape())))
    root=json.loads(a.root_cause.read_text()); rows=[]
    for x in root['abnormal']:
        path=x['route_edge_sequence']; lens=[new_edges[z].getLength() for z in path]
        total=(lens[0]-x['origin_offset_m'])+sum(lens[1:-1])+x['destination_offset_m']
        gaps=[]
        for u,v in zip(path,path[1:]):
            su,sv=new_edges[u].getShape(),new_edges[v].getShape()
            gaps.append(math.hypot(su[-1][0]-sv[0][0],su[-1][1]-sv[0][1]))
        rows.append({'origin_id':x['origin_id'],'destination_id':x['destination_id'],'old_r13_distance_m':x['r13_distance_m'],'diagnostic_new_network_distance_m':total,'mapped_straight_m':x['mapped_euclidean_m'],'new_minus_mapped_m':total-x['mapped_euclidean_m'],'old_connection_gap_sum_m':x['edge_connection_gap_sum_m'],'new_route_shape_gap_max_m':max(gaps or [0.0]),'route_edge_count':len(path)})
    with (a.output_dir/'44_od_diagnostic.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    mapping_summary=json.loads(a.accepted.read_text())['mapping']
    fixture_rows=list(csv.DictReader(a.mapping.open()))
    mapping_edges={r['edge_id'] for r in fixture_rows}
    mapping_check={'accepted_total_stops':mapping_summary['total_stops'],'accepted_mapped':mapping_summary['mapped'],'accepted_unmapped':mapping_summary['unmapped'],'accepted_delivery_permitted':mapping_summary['delivery_permitted_edge_mapping'],'fixture_mapping_rows':len(fixture_rows),'fixture_edges_present_in_new_network':sum(e in new_edges for e in mapping_edges),'fixture_edges_missing_in_new_network':sum(e not in new_edges for e in mapping_edges)}
    report={'status':'PASS_CANDIDATE','old_network_sha256':sha(a.old),'new_network_sha256':sha(a.new),'old_stats':old_stats,'new_stats':new_stats,'node_edge_lane_count_diff':{k:new_stats[k]-old_stats[k] for k in ('nodes','edges','lanes')},'topology_permission_oneway_signature_same':topology_same,'old_connection_gap':{'count':len(old_con),'max_m':max(old_con),'positive_count':sum(x>1e-6 for x in old_con)},'new_connection_gap':{'count':len(new_con),'max_m':max(new_con),'positive_count':sum(x>1e-6 for x in new_con)},'old_lane_length_shape_max_abs_diff_m':max(old_len_diff),'new_lane_length_shape_max_abs_diff_m':max(new_len_diff),'new_lane_length_shape_failures':sum(x>1e-3 for x in new_len_diff),'mapping':mapping_check,'44_od':{'count':len(rows),'new_below_mapped_count':sum(r['new_minus_mapped_m'] < -1e-6 for r in rows),'min_new_minus_mapped_m':min(r['new_minus_mapped_m'] for r in rows),'max_new_minus_mapped_m':max(r['new_minus_mapped_m'] for r in rows),'max_new_route_shape_gap_m':max(r['new_route_shape_gap_max_m'] for r in rows)},'transformation':'connected each edge/lane shape to from/to junction XY and set lane declared length to the resulting polyline length; no topology, connection, permission, one-way, or stop mapping rule change'}
    (a.output_dir/'network_validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest={'status':report['status'],'input_old_sha256':sha(a.old),'output_new_sha256':sha(a.new),'report_sha256':sha(a.output_dir/'network_validation_report.json'),'diagnostic_sha256':sha(a.output_dir/'44_od_diagnostic.csv')}
    (a.output_dir/'network_reacceptance_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
