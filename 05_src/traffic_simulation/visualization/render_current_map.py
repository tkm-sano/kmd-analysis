"""Render the current accepted network and scoped Stops as a dated snapshot."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import folium
from branca.element import Element, MacroElement, Template
from pyproj import Transformer
from shapely import wkt
import yaml

from research_cli.core import AUTHORITY_PATH, RESEARCH_MAP_PATH, ROOT, STOPS_PATH
from traffic_simulation.network.study_areas import load_study_area
from traffic_simulation.visualization.render_study_area import add_boundary_layers, write_map

OUTPUT = ROOT / "reproducibility/outputs/traffic_simulation/visualization/ota_ward_current_map.html"


class RawScript(MacroElement):
    """Append JS after the map without reparsing data/CSS as Jinja syntax."""

    def render(self, **kwargs) -> None:
        element = Element()
        element.source = self.script
        element._template = Template("{{this.source | safe}}")
        self.get_root().script.add_child(element, name=self.get_name())


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_network(path: Path, details: dict | None = None) -> tuple[list, int, int]:
    """Read external edges; keep one representative lane shape per directed edge."""
    roads, lane_count, nodes = [], 0, set()
    connections, junctions, signals = [], {}, {}
    transformer = None
    offset = (0.0, 0.0)
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag == "location":
            offset = tuple(map(float, element.attrib["netOffset"].split(",")))
            transformer = Transformer.from_crs(element.attrib["projParameter"], "EPSG:4326", always_xy=True)
        elif element.tag == "edge":
            if element.get("function") != "internal" and element.get("from"):
                if transformer is None:
                    raise ValueError("SUMO location is missing")
                lanes = element.findall("lane")
                points = [tuple(map(float, p.split(","))) for p in lanes[0].attrib["shape"].split()]
                coordinates = []
                for x, y in points:
                    lon, lat = transformer.transform(x - offset[0], y - offset[1])
                    if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
                        raise ValueError("Invalid transformed coordinate")
                    coordinates.append([round(lat, 7), round(lon, 7)])
                if len(coordinates) < 2:
                    raise ValueError("Edge has no usable geometry")
                allowed = any(
                    ("allow" not in lane.attrib or "delivery" in lane.get("allow", "").split() or "all" in lane.get("allow", "").split())
                    and not {"delivery", "all"}.intersection(lane.get("disallow", "").split())
                    for lane in lanes
                )
                roads.append([element.attrib["id"], coordinates, allowed, len(lanes), round(float(lanes[0].attrib["speed"]) * 3.6, 1)])
                if details is not None:
                    details[element.attrib["id"]] = {
                        "attributes": dict(element.attrib),
                        "params": {p.get("key"): p.get("value") for p in element.findall("param")},
                        "lanes": [dict(lane.attrib) | {"params": {p.get("key"): p.get("value") for p in lane.findall("param")}} for lane in lanes],
                        "incoming": [], "outgoing": [],
                    }
                    for lane in details[element.attrib["id"]]["lanes"]:
                        lane["coordinates"] = []
                        for point in lane.pop("shape").split():
                            x, y = map(float, point.split(","))
                            lon, lat = transformer.transform(x - offset[0], y - offset[1])
                            if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
                                raise ValueError("Invalid lane coordinate")
                            lane["coordinates"].append([round(lat, 7), round(lon, 7)])
                lane_count += len(lanes)
                nodes.update((element.attrib["from"], element.attrib["to"]))
            element.clear()
        elif element.tag in {"junction", "connection", "tlLogic"}:
            if details is not None:
                if element.tag == "connection":
                    connections.append(dict(element.attrib))
                elif element.tag == "junction":
                    junctions[element.get("id")] = {k: v for k, v in element.attrib.items() if k in {"id", "type", "incLanes", "intLanes"}}
                else:
                    signals.setdefault(element.get("id"), []).append({"attributes": dict(element.attrib), "phases": [dict(p.attrib) for p in element.findall("phase")]})
            element.clear()
    if details is not None:
        for connection in connections:
            if connection.get("from") in details and connection.get("to") in details:
                details[connection["from"]]["outgoing"].append(connection)
                details[connection["to"]]["incoming"].append(connection)
        for detail in details.values():
            detail["junctions"] = {key: junctions.get(detail["attributes"][key]) for key in ("from", "to")}
            detail["signals"] = {c["tl"]: signals.get(c["tl"], []) for c in detail["incoming"] + detail["outgoing"] if "tl" in c}

    return roads, lane_count, len(nodes)


def generate(*, overwrite: bool = False) -> dict:
    authority = yaml.safe_load(AUTHORITY_PATH.read_text())
    research = yaml.safe_load(RESEARCH_MAP_PATH.read_text())
    accepted = authority["accepted_run"]
    acceptance_path = ROOT / accepted["acceptance_artifact"]
    acceptance = json.loads(acceptance_path.read_text())
    network = ROOT / accepted["network_file"]
    actual_sha = digest(network)
    if not acceptance["FORMAL_NETWORK_ACCEPTED"] or actual_sha != accepted["network_sha256"] or actual_sha != acceptance["network_semantic_sha256"]:
        raise ValueError("Current network acceptance/hash mismatch")
    details = {}
    roads, lanes, nodes = read_network(network, details)
    counts = acceptance["validation"]["counts"]
    if (len(roads), lanes, nodes) != (counts["edges"], counts["lanes"], counts["nodes"]):
        raise ValueError("Rendered network counts differ from acceptance")
    stops = []
    with STOPS_PATH.open() as stream:
        for row in csv.DictReader(stream):
            point = wkt.loads(row["building_representative_point"])
            if point.geom_type != "Point" or point.is_empty or not (-180 <= point.x <= 180 and -90 <= point.y <= 90):
                raise ValueError("Invalid Stop coordinate")
            stops.append([row["stop_id"], [round(point.y, 7), round(point.x, 7)], int(row["request_count"]), float(row["parcel_equivalent"]), row["evaluation_date"]])
    if len(stops) != acceptance["mapping"]["total_stops"] or len({s[0] for s in stops}) != len(stops):
        raise ValueError("Scoped Stops differ from acceptance count or contain duplicate IDs")
    area = load_study_area("ota_ward")
    center = area.api_boundary.representative_point()
    map_object = folium.Map(location=[center.y, center.x], zoom_start=12, prefer_canvas=True, control_scale=True)
    add_boundary_layers(map_object, area)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority_effective_at": authority["effective_at"],
        "accepted_run": accepted["run_id"], "network_sha256": actual_sha,
        "counts": counts, "rendered_stops": len(stops),
        "sources": {str(p.relative_to(ROOT)): digest(p) for p in (AUTHORITY_PATH, RESEARCH_MAP_PATH, acceptance_path, STOPS_PATH)},
    }
    # Content-addressed shards keep old HTML snapshots bound to their own data.
    shard_urls = []
    buckets = [{} for _ in range(128)]
    for index, road in enumerate(roads):
        shard = index % len(buckets)
        road.append(shard)
        buckets[shard][road[0]] = details[road[0]]
    detail_directory = OUTPUT.parent / "current_map_details"
    detail_directory.mkdir(parents=True, exist_ok=True)
    for bucket in buckets:
        content = ("window.researchMapDetails = " + json.dumps(bucket, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + ";\n").encode()
        filename = hashlib.sha256(content).hexdigest() + ".js"
        target = detail_directory / filename
        if not target.exists():
            temporary = target.with_suffix(".part")
            temporary.write_bytes(content)
            temporary.replace(target)
        shard_urls.append("current_map_details/" + filename)
    esc = lambda value: html.escape(str(value))
    position = research["current_position"]
    stages = "".join(f'<li>{esc(s["label"])} <strong>{esc(s["status"])}</strong></li>' for s in research["public_view"]["pipeline"])
    limitations = "".join(f"<li>{esc(s)}</li>" for s in acceptance["known_limitations"])
    panel = f'''<style>
    #research-panel {{position:fixed;left:12px;top:80px;z-index:1000;background:#fffef8;padding:18px;border-radius:12px;width:310px;max-height:70vh;overflow:auto;box-shadow:0 3px 18px #0003;font:14px/1.6 sans-serif}}
    #research-panel h1 {{font-size:19px;margin:0 0 8px}} #research-panel ul {{padding-left:20px}} #research-panel strong {{color:#16665c}}
    @media(max-width:650px) {{#research-panel {{top:auto;bottom:12px;width:calc(100% - 60px);max-height:28vh}}}}
    </style><aside id="research-panel"><h1>大田区・研究の現在地</h1>
    <p>道路網受入済み · {esc(authority['effective_at'])}<br>生成日時（UTC）: {esc(metadata['generated_at'])}</p>
    <p><strong>{esc(position['current_stage'])}</strong><br>{esc(research['public_view']['current_stage_explanation'])}<br>次: {esc(position['immediate_next_task'])}</p>
    <p>道路 {len(roads):,} 有向エッジ / {nodes:,} ノード<br>配送地点 {len(stops):,} 件（建物代表点）</p>
    <p>青: delivery通行可 / 灰: その他 / 橙: 配送地点<br>地図をクリックすると近くの道路・地点の属性を表示します。</p>
    <details><summary>研究工程</summary><ul>{stages}</ul></details>
    <details><summary>表示の範囲・受入上の限界</summary><p>静的な生成時点の地図です。道路はエッジごとの代表レーン形状で、内部接続は省略します。配送地点は建物位置であり、対応先エッジ位置ではありません。配送ルート・渋滞・車両移動の結果は未生成です。背景は閲覧時のOSMタイルです。</p><ul>{limitations}</ul></details>
    <details><summary>出典・生成情報</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">{esc(json.dumps(metadata, ensure_ascii=False, indent=2))}</pre></details>
    </aside>'''
    panel_element = Element()
    panel_element.panel = panel
    panel_element._template = Template("{{this.panel | safe}}")
    map_object.get_root().html.add_child(panel_element)
    layer = RawScript()
    script = Path(__file__).with_name("current_map.js").read_text()
    payload = json.dumps({"roads": roads, "stops": stops, "detail_shards": shard_urls}, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    layer.script = script.replace("{{this._parent.get_name()}}", map_object.get_name()).replace("__PAYLOAD__", payload)
    map_object.add_child(layer)
    west, south, east, north = area.api_boundary.bounds
    map_object.fit_bounds([[south, west], [north, east]])
    write_map(map_object, OUTPUT, overwrite=overwrite)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if OUTPUT.exists() and not args.overwrite:
        parser.error("Output already exists; use --overwrite to refresh the snapshot")
    print(json.dumps(generate(overwrite=args.overwrite), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
