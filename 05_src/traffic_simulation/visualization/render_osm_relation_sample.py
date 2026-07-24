"""Render one registered OSM restriction relation with local road context."""

from __future__ import annotations

import argparse
import csv
import html
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence
from xml.etree import ElementTree

import folium
import geopandas as gpd
from branca.element import Element
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from traffic_simulation.network.study_areas import load_study_area
from traffic_simulation.paths import REPOSITORY_ROOT, RUN_OUTPUT_ROOT, SOURCE_REGISTRY
from traffic_simulation.visualization.render_study_area import (
    _run_osmium,
    build_map,
    prepare_osm_roads,
    resolve_repository_path,
    sha256_file,
    write_map,
)


DEFAULT_SOURCE_ID: Final = "osm_geofabrik_kanto_20260716"
DEFAULT_REGION_ID: Final = "ota_ward"
DEFAULT_OUTPUT_DIRECTORY: Final = RUN_OUTPUT_ROOT / "visualization"
CONTEXT_RADIUS_M: Final = 350.0
ROLE_COLORS: Final = {
    "from": "#d32f2f",
    "to": "#2e7d32",
    "via": "#6a1b9a",
}


@dataclass(frozen=True, slots=True)
class RelationMember:
    """One geometry-bearing member of a selected OSM relation."""

    member_type: str
    reference: str
    role: str
    geometry: BaseGeometry
    tags: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class RelationSample:
    """Parsed source relation and the members needed for visual review."""

    relation_id: str
    tags: Mapping[str, str]
    members: tuple[RelationMember, ...]

    @property
    def geometry(self) -> BaseGeometry:
        return unary_union([member.geometry for member in self.members])


def _registered_raw_source(source_id: str) -> tuple[Path, str]:
    with SOURCE_REGISTRY.open(newline="", encoding="utf-8-sig") as handle:
        matches = [
            row
            for row in csv.DictReader(handle)
            if row.get("source_id") == source_id
        ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one source-registry row for {source_id}, found {len(matches)}"
        )
    row = matches[0]
    if row.get("status") != "processed":
        raise ValueError(f"OSM source is not processed: {source_id}")
    raw_path = resolve_repository_path(
        str(row.get("local_raw_path") or ""),
        label="registered raw OSM path",
    )
    expected_hash = str(row.get("sha256") or "")
    if not raw_path.is_file():
        raise FileNotFoundError(f"registered raw OSM does not exist: {raw_path}")
    actual_hash = sha256_file(raw_path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"registered raw OSM SHA-256 mismatch: {actual_hash} != {expected_hash}"
        )
    return raw_path, actual_hash


def _tags(element: ElementTree.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for tag in element.findall("tag"):
        key = tag.attrib.get("k", "")
        value = tag.attrib.get("v", "")
        if not key or key in result:
            raise ValueError("OSM sample contains an empty or duplicate tag key")
        result[key] = value
    return result


def parse_relation_xml(path: Path, relation_id: str) -> RelationSample:
    """Parse a self-contained OSM XML relation extract."""

    root = ElementTree.parse(path).getroot()
    if root.tag != "osm":
        raise ValueError("OSM relation extract root must be <osm>")

    nodes: dict[str, Point] = {}
    for node in root.findall("node"):
        node_id = node.attrib.get("id", "")
        if not node_id or node_id in nodes:
            raise ValueError("OSM relation extract has a missing or duplicate node")
        nodes[node_id] = Point(float(node.attrib["lon"]), float(node.attrib["lat"]))

    ways: dict[str, tuple[LineString, Mapping[str, str]]] = {}
    for way in root.findall("way"):
        way_id = way.attrib.get("id", "")
        if not way_id or way_id in ways:
            raise ValueError("OSM relation extract has a missing or duplicate way")
        references = [nd.attrib.get("ref", "") for nd in way.findall("nd")]
        if len(references) < 2 or any(reference not in nodes for reference in references):
            raise ValueError(f"relation member way {way_id} has missing node references")
        ways[way_id] = (
            LineString([(nodes[reference].x, nodes[reference].y) for reference in references]),
            _tags(way),
        )

    relations = [
        relation
        for relation in root.findall("relation")
        if relation.attrib.get("id") == relation_id
    ]
    if len(relations) != 1:
        raise ValueError(
            f"expected one relation {relation_id}, found {len(relations)}"
        )
    relation = relations[0]
    relation_tags = _tags(relation)
    relation_type = relation_tags.get("type", "")
    if not relation_type.startswith("restriction"):
        raise ValueError(f"relation {relation_id} is not a restriction relation")

    members: list[RelationMember] = []
    for member in relation.findall("member"):
        member_type = member.attrib.get("type", "")
        reference = member.attrib.get("ref", "")
        role = member.attrib.get("role", "")
        if member_type == "node":
            if reference not in nodes:
                raise ValueError(f"relation {relation_id} has missing node {reference}")
            geometry: BaseGeometry = nodes[reference]
            member_tags: Mapping[str, str] = {}
        elif member_type == "way":
            if reference not in ways:
                raise ValueError(f"relation {relation_id} has missing way {reference}")
            geometry, member_tags = ways[reference]
        else:
            raise ValueError(
                f"relation {relation_id} has unsupported member type {member_type}"
            )
        members.append(
            RelationMember(
                member_type=member_type,
                reference=reference,
                role=role,
                geometry=geometry,
                tags=member_tags,
            )
        )

    roles = {member.role for member in members}
    if not {"from", "via", "to"} <= roles:
        raise ValueError(f"relation {relation_id} lacks from/via/to members")
    return RelationSample(
        relation_id=relation_id,
        tags=relation_tags,
        members=tuple(members),
    )


def load_relation_sample(
    source_id: str,
    relation_id: str,
    *,
    osmium_command: str = "osmium",
) -> tuple[RelationSample, str]:
    """Extract one relation and all referenced members from a registered PBF."""

    raw_path, raw_hash = _registered_raw_source(source_id)
    with tempfile.TemporaryDirectory(prefix="render-osm-relation-") as directory:
        output = Path(directory) / "relation.osm.xml"
        _run_osmium(
            [
                osmium_command,
                "getid",
                str(raw_path),
                f"r{relation_id}",
                "--add-referenced",
                "--output-format",
                "osm",
                "--output",
                str(output),
            ]
        )
        return parse_relation_xml(output, relation_id), raw_hash


def _context_geometry(sample: RelationSample, metric_crs: Any) -> BaseGeometry:
    via_geometries = [
        member.geometry for member in sample.members if member.role == "via"
    ]
    if not via_geometries:
        raise ValueError(f"relation {sample.relation_id} has no via geometry")
    series = gpd.GeoSeries([unary_union(via_geometries)], crs="EPSG:4326")
    return series.to_crs(metric_crs).buffer(CONTEXT_RADIUS_M).to_crs("EPSG:4326").iloc[0]


def add_relation_layer(
    map_object: folium.Map,
    sample: RelationSample,
    *,
    display_extent: BaseGeometry,
) -> None:
    """Add cased from/to ways and a via marker for the selected relation."""

    layer = folium.FeatureGroup(
        name=f"Selected restriction relation {sample.relation_id}",
        show=True,
    )
    for member in sample.members:
        color = ROLE_COLORS.get(member.role, "#455a64")
        properties = {
            "relation_id": sample.relation_id,
            "role": member.role,
            "member_type": member.member_type,
            "member_id": member.reference,
            "name": str(member.tags.get("name") or ""),
            "highway": str(member.tags.get("highway") or ""),
        }
        if isinstance(member.geometry, Point):
            folium.CircleMarker(
                location=(member.geometry.y, member.geometry.x),
                radius=7,
                color="#ffffff",
                weight=4,
                fill=True,
                fill_color=color,
                fill_opacity=1,
                tooltip=(
                    f"Relation {sample.relation_id} / {member.role} "
                    f"{member.member_type} {member.reference}"
                ),
            ).add_to(layer)
            continue

        visible_geometry = member.geometry.intersection(display_extent)
        if visible_geometry.is_empty:
            continue
        tooltip = folium.Tooltip(
            f"Relation {sample.relation_id} / {member.role} way "
            f"{member.reference} / {properties['name'] or '(unnamed)'}"
        )
        visible_lines = (
            list(visible_geometry.geoms)
            if visible_geometry.geom_type == "MultiLineString"
            else [visible_geometry]
        )
        for visible_line in visible_lines:
            coordinates = [(lat, lon) for lon, lat in visible_line.coords]
            folium.PolyLine(
                coordinates,
                color="#ffffff",
                weight=11,
                opacity=0.96,
            ).add_to(layer)
            folium.PolyLine(
                coordinates,
                color=color,
                weight=7,
                opacity=1,
                tooltip=tooltip,
            ).add_to(layer)
    layer.add_to(map_object)


def _sample_panel(
    sample: RelationSample,
    source_id: str,
    raw_hash: str,
) -> Element:
    restriction = sample.tags.get("restriction") or sample.tags.get(
        "restriction:conditional", ""
    )
    member_rows = "".join(
        "<tr>"
        f"<td>{html.escape(member.role)}</td>"
        f"<td>{html.escape(member.member_type)}</td>"
        f"<td style='font-family:monospace'>{html.escape(member.reference)}</td>"
        "</tr>"
        for member in sample.members
    )
    return Element(
        f"""
        <div style="position:fixed; right:10px; bottom:25px; z-index:9999;
                    width:min(360px,calc(100vw - 20px));
                    max-height:42vh; overflow:auto;
                    background:rgba(255,255,255,0.96); border:1px solid #444;
                    border-radius:4px; padding:10px; font:12px sans-serif;">
          <div style="font-size:14px; font-weight:bold; margin-bottom:5px;">
            OSM restriction sample
          </div>
          <div>Relation: <strong>{html.escape(sample.relation_id)}</strong></div>
          <div>Type: {html.escape(sample.tags.get("type", ""))}</div>
          <div>Restriction: {html.escape(restriction)}</div>
          <div>Source: {html.escape(source_id)}</div>
          <table style="width:100%; margin-top:6px; border-collapse:collapse;">
            <thead><tr><th>Role</th><th>Type</th><th>ID</th></tr></thead>
            <tbody>{member_rows}</tbody>
          </table>
          <div style="margin-top:7px;">
            <span style="color:{ROLE_COLORS['from']}; font-weight:bold;">━ from</span>
            &nbsp;
            <span style="color:{ROLE_COLORS['to']}; font-weight:bold;">━ to</span>
            &nbsp;
            <span style="color:{ROLE_COLORS['via']}; font-weight:bold;">● via</span>
          </div>
          <hr style="margin:7px 0;">
          <div style="font-weight:bold; color:#b71c1c;">
            Review visualization only
          </div>
          <div>
            This relation was excluded by the executed v15 exact-type scope.
            It is a next-version formal blocker, not an accepted SUMO turn.
          </div>
          <details style="margin-top:5px;">
            <summary>Registered raw SHA-256</summary>
            <div style="font-family:monospace; overflow-wrap:anywhere;">
              {html.escape(raw_hash)}
            </div>
          </details>
        </div>
        """
    )


def build_relation_sample_map(
    relation_id: str,
    *,
    region_id: str = DEFAULT_REGION_ID,
    source_id: str = DEFAULT_SOURCE_ID,
    basemap: bool = True,
) -> folium.Map:
    area = load_study_area(region_id)
    sample, raw_hash = load_relation_sample(source_id, relation_id)
    context = _context_geometry(sample, area.metric_crs)
    roads = prepare_osm_roads(
        source_id,
        area,
        display_extent=context,
    )
    map_object, _, _, _ = build_map(
        area,
        osm_roads=roads,
        basemap=basemap,
        fit_extent=context,
        add_layer_control=False,
    )
    add_relation_layer(map_object, sample, display_extent=context)
    folium.LayerControl(collapsed=False).add_to(map_object)
    map_object.get_root().html.add_child(
        _sample_panel(sample, source_id, raw_hash)
    )
    return map_object


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render one registered OSM restriction relation"
    )
    parser.add_argument("--relation-id", required=True)
    parser.add_argument("--region", default=DEFAULT_REGION_ID)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--output")
    parser.add_argument("--no-basemap", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.relation_id.isdigit() or int(args.relation_id) <= 0:
        raise ValueError("--relation-id must be a positive OSM relation ID")
    if args.output:
        output = resolve_repository_path(args.output, label="output path")
    else:
        output = (
            DEFAULT_OUTPUT_DIRECTORY
            / f"{args.region}_osm_relation_{args.relation_id}.html"
        )
    map_object = build_relation_sample_map(
        args.relation_id,
        region_id=args.region,
        source_id=args.source_id,
        basemap=not args.no_basemap,
    )
    write_map(map_object, output, overwrite=args.overwrite)
    print(f"relation: {args.relation_id}")
    print(f"map: {output.relative_to(REPOSITORY_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
