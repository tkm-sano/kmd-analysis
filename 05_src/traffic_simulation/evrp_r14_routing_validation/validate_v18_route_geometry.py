#!/usr/bin/env python3
"""Validate V18 lane geometry/length on the immutable R13 route sequences."""
from __future__ import annotations
import argparse, csv, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / '.local/sumo-1.24.0/share/sumo/tools'))
import sumolib  # type: ignore

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--network', required=True); ap.add_argument('--r13-dir', required=True); ap.add_argument('--output', required=True)
    a = ap.parse_args(); network, r13, output = Path(a.network), Path(a.r13_dir), Path(a.output)
    net = sumolib.net.readNet(str(network)); rows = list(csv.DictReader((r13/'routing_arcs.csv').open()))
    route_edges = set(); lane_failures = []; connection_gaps = []; missing_connection_records = []; representative_edge_gaps = []
    for row in rows:
        if row['reachable'] != 'True': continue
        path = json.loads(row['path_edge_sequence']); route_edges.update(path)
        for edge_id in path:
            edge = net.getEdge(edge_id)
            for lane in edge.getLanes():
                shape = lane.getShape(); poly = sum(math.dist(x, y) for x, y in zip(shape, shape[1:]))
                if not (math.isfinite(lane.getLength()) and math.isfinite(poly) and lane.getLength() > 0 and poly > 0 and abs(lane.getLength()-poly) <= 1e-6):
                    lane_failures.append({'edge': edge_id, 'lane': lane.getID(), 'declared_length_m': lane.getLength(), 'shape_polyline_m': poly})
        for left, right in zip(path, path[1:]):
            le, re = net.getEdge(left), net.getEdge(right)
            representative_edge_gaps.append(math.dist(le.getShape()[-1], re.getShape()[0]))
            matches = []
            for lane in le.getLanes():
                for connection in lane.getOutgoing():
                    target = connection.getToLane()
                    if target.getEdge().getID() == right:
                        matches.append(math.dist(lane.getShape()[-1], target.getShape()[0]))
            if not matches:
                missing_connection_records.append({'origin_id': row['origin_id'], 'destination_id': row['destination_id'], 'from_edge': left, 'to_edge': right, 'reason': 'no lane connection record; edge-level R13 graph transition retained as diagnostic'})
            else:
                for gap in matches:
                    if gap > 1e-6: connection_gaps.append({'origin_id': row['origin_id'], 'destination_id': row['destination_id'], 'from_edge': left, 'to_edge': right, 'gap_m': gap})
    report = {
        'status': 'PASS' if not lane_failures and not connection_gaps else 'FAIL',
        'route_count': len(rows), 'unique_route_edges': len(route_edges),
        'lane_declared_vs_shape_checks': sum(len(net.getEdge(e).getLanes()) for e in route_edges),
        'lane_declared_vs_shape_mismatch_count': len(lane_failures),
        'lane_connection_geometry_gap_count': len(connection_gaps),
        'lane_connection_record_missing_count': len(missing_connection_records),
        'max_lane_connection_gap_m': max((x.get('gap_m', 0.0) for x in connection_gaps), default=0.0),
        'representative_edge_shape_gap_count': sum(x > 1e-6 for x in representative_edge_gaps),
        'max_representative_edge_shape_gap_m': max(representative_edge_gaps, default=0.0),
        'representative_edge_shape_gap_interpretation': 'diagnostic only; multi-lane edge shape is not the lane connection geometry used by SUMO',
        'failures': lane_failures[:100] + connection_gaps[:100],
        'diagnostic_missing_connection_records': missing_connection_records[:100],
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False)); return 0 if report['status'] == 'PASS' else 1
if __name__ == '__main__': raise SystemExit(main())
