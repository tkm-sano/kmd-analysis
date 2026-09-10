#!/usr/bin/env python3
"""Small deterministic tests for the R13 offset and directed-path contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compute_routing import route_between  # noqa: E402


class Node:
    def __init__(self, node_id: str):
        self._id = node_id
        self._out = []

    def getID(self):
        return self._id

    def getOutgoing(self):
        return list(self._out)


class Edge:
    def __init__(self, edge_id: str, source: Node, target: Node, length: float, speed: float = 1.0):
        self._id, self._source, self._target = edge_id, source, target
        self._length, self._speed = length, speed
        source._out.append(self)

    def getID(self): return self._id
    def getFromNode(self): return self._source
    def getToNode(self): return self._target
    def getLength(self): return self._length
    def getSpeed(self): return self._speed
    def getPermissions(self): return ["delivery"]


class Net:
    def __init__(self, edges): self.edges = {edge.getID(): edge for edge in edges}
    def getEdge(self, edge_id): return self.edges.get(edge_id)
    def getNodes(self):
        return list({node for edge in self.edges.values() for node in (edge.getFromNode(), edge.getToNode())})


def point(edge: str, offset: float) -> dict[str, str]:
    return {"mapped_edge_id": edge, "edge_offset_m": str(offset)}


def main() -> int:
    # A: same directed edge, forward offset difference.
    a, b, c, d = (Node(x) for x in "ABCD")
    e = Edge("E", a, b, 10, 2)
    reverse = Edge("ER", b, a, 10, 2)
    bridge = Edge("BC", b, c, 30, 3)
    target = Edge("T", c, d, 20, 4)
    net = Net([e, reverse, bridge, target])
    forward = route_between(point("E", 2), point("E", 7), net, "delivery")
    assert forward["reachable"] and abs(forward["distance_m"] - 5) < 1e-9 and abs(forward["travel_time_s"] - 2.5) < 1e-9

    # B: same edge, reverse offsets use a directed network path, not abs(delta).
    reverse_offset = route_between(point("E", 8), point("E", 2), net, "delivery")
    assert reverse_offset["reachable"] and abs(reverse_offset["distance_m"] - 14) < 1e-9 and reverse_offset["distance_m"] != 6

    # C: origin partial + graph path + destination partial.
    different = route_between(point("E", 3), point("T", 5), net, "delivery")
    assert different["reachable"] and abs(different["distance_m"] - 42) < 1e-9 and abs(different["travel_time_s"] - 14.75) < 1e-9

    # D/E: no directed return path means legitimate unreachable; no reverse-edge invention.
    disconnected = Net([Edge("ONLY", Node("X"), Node("Y"), 10, 1), Edge("DEST", Node("Z"), Node("W"), 10, 1)])
    unreachable = route_between(point("ONLY", 2), point("DEST", 5), disconnected, "delivery")
    assert not unreachable["reachable"] and unreachable["distance_m"] is None and unreachable["travel_time_s"] is None

    result = {
        "status": "PASS",
        "checks": {
            "same_edge_forward_offset_difference": True,
            "same_edge_reverse_does_not_use_absolute_difference": True,
            "different_edge_partial_segments_are_added": True,
            "directed_unreachable_uses_nulls": True,
            "no_nearest_node_rounding": True,
        },
    }
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
