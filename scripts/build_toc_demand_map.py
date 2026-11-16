"""Visualize the pinned demand CSVs only; never generate or alter demand."""

from collections import Counter
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kmd_toc.frozen_demand import load_frozen_demand

BUNDLE = ROOT / "03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1"
REVIEW = ROOT / "review_outputs/toc_demand_map_depot_20261110"
VENDOR = ROOT / "review_outputs/toc_demand_map_20261110/vendor"
OUTPUT = ROOT / "output/toc_delivery/demand_map/v1/toc_demand_S1_S3_map.html"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new_or_identical(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Refusing to overwrite different artifact: {path}")
        return
    with path.open("xb") as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update-map", action="store_true", help="update only the previously recorded visualization")
    args = parser.parse_args()
    if not json.loads((ROOT / "review_outputs/toc_demand_freeze_20261110/COMPLETION_CHECK.json").read_text())["status"] == "GO":
        raise ValueError("HOLD: demand freeze incomplete")
    before = {p.name: digest(p.read_bytes()) for p in BUNDLE.iterdir()}
    audit_manifest = ROOT / "review_outputs/toc_stops_full_audit_20261108/run_20261108T091121Z_attempt02/INPUT_MANIFEST.json"
    depot_sources = {}
    for entry in json.loads(audit_manifest.read_text()):
        name = Path(entry["path"]).name
        if name in ("DEPOT_ROUTING_DEFINITION.json", "SUMO_FACILITY_MAPPING_FREEZE_MANIFEST.json"):
            content = Path(entry["path"]).read_bytes()
            if digest(content) != entry["sha256"]:
                raise ValueError("Depot source differs from the audited frozen source")
            depot_sources[name] = dict(path=entry["path"], sha256=entry["sha256"], data=json.loads(content))
    routing = depot_sources["DEPOT_ROUTING_DEFINITION.json"]["data"]
    facility = depot_sources["SUMO_FACILITY_MAPPING_FREEZE_MANIFEST.json"]["data"]["depot"]
    if any(routing[k] != facility[k] for k in ("depot_id", "longitude", "latitude")):
        raise ValueError("Depot identity/coordinates inconsistent")
    depot = {k: facility[k] for k in ("depot_id", "facility_name", "longitude", "latitude", "proxy_or_observed")}
    if depot["proxy_or_observed"] != "proxy":
        raise ValueError("Expected the existing virtual/proxy depot definition")
    cases = {}
    for scenario in ("S1", "S2", "S3"):
        checked = load_frozen_demand(scenario, method_id="A")
        raw = (BUNDLE / f"{scenario}.csv").read_bytes()
        if digest(raw) != checked.csv_sha256:
            raise ValueError("CSV changed after pinned validation")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"), newline="")))
        if len(rows) != checked.N:
            raise ValueError("CSV length mismatch")
        cases[scenario] = {r["stop_id"]: r for r in rows}
    if not cases["S1"].keys() < cases["S2"].keys() < cases["S3"].keys():
        raise ValueError("HOLD: nesting mismatch")

    # Coordinates and IDs are kept as their original CSV strings in the HTML.
    data = []
    for stop_id, row in cases["S3"].items():
        first = 1 if stop_id in cases["S1"] else 2 if stop_id in cases["S2"] else 3
        record = {k: v for k, v in row.items() if k != "scenario_id"}
        record["minimum_series"] = first
        data.append(record)
    for scenario, level in (("S1", 1), ("S2", 2), ("S3", 3)):
        actual = {r["stop_id"]: {k: v for k, v in r.items() if k != "minimum_series"}
                  for r in data if r["minimum_series"] <= level}
        expected = {sid: {k: v for k, v in row.items() if k != "scenario_id"}
                    for sid, row in cases[scenario].items()}
        if actual != expected:
            raise ValueError("Embedded attributes differ from fixed CSV")
    if Counter(r["minimum_series"] for r in data) != {1: 1000, 2: 1000, 3: 2000}:
        raise ValueError("Wrong incremental group counts")

    resources = {}
    for name, url in {
        "leaflet.js": "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
        "leaflet.css": "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
        "LICENSE": "https://unpkg.com/leaflet@1.9.4/LICENSE",
    }.items():
        path = VENDOR / name
        if path.exists():
            content = path.read_bytes()
        else:
            with urlopen(url, timeout=25) as response:
                content = response.read()
            write_new_or_identical(path, content)
        resources[name] = {"url": url, "sha256": digest(content), "bytes": len(content)}
    leaflet_js = (VENDOR / "leaflet.js").read_text()
    leaflet_css = (VENDOR / "leaflet.css").read_text()
    license_text = (VENDOR / "LICENSE").read_text()
    # No marker-image or layer-control assets are needed for Canvas circles.
    leaflet_css = re.sub(r"url\([^)]*\)", "none", leaflet_css)
    leaflet_js = re.sub(r"//# sourceMappingURL=[^\n]*", "", leaflet_js)
    embedded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    source_hashes = json.dumps({s: before[s + ".csv"] for s in cases}, sort_keys=True)
    html = TEMPLATE.replace("__LEAFLET_CSS__", leaflet_css).replace("__LEAFLET_JS__", leaflet_js)
    html = html.replace("__LEAFLET_LICENSE__", license_text.replace("--", "—"))
    html = html.replace("__DEMAND_JSON__", embedded).replace("__SOURCE_HASHES__", source_hashes)
    html = html.replace("__DEPOT_JSON__", json.dumps(depot, ensure_ascii=False).replace("<", "\\u003c"))
    encoded = html.encode("utf-8")
    if OUTPUT.exists() and OUTPUT.read_bytes() != encoded and args.update_map:
        recorded = json.loads((REVIEW / "BEFORE.json").read_text())["files"][str(OUTPUT.relative_to(ROOT))]
        if digest(OUTPUT.read_bytes()) != recorded:
            raise ValueError("Map differs from the recorded pre-edit version")
        OUTPUT.write_bytes(encoded)
    else:
        write_new_or_identical(OUTPUT, encoded)
    # Verify the serialized payload again, not merely the pre-serialization objects.
    saved = OUTPUT.read_text()
    serialized = json.loads(saved.split('<script id="demand-data" type="application/json">')[1].split("</script>")[0])
    if serialized != data:
        raise ValueError("Serialized HTML data mismatch")
    after = {p.name: digest(p.read_bytes()) for p in BUNDLE.iterdir()}
    if before != after:
        raise ValueError("Frozen bundle changed during map generation")
    report = dict(status="PASS", html=str(OUTPUT.relative_to(ROOT)), html_sha256=digest(OUTPUT.read_bytes()),
                  data_input="fixed S1.csv/S2.csv/S3.csv only; manifest/pin used only for validation",
                  scenario_counts={s: len(rows) for s, rows in cases.items()},
                  incremental_counts={"S1": 1000, "S2_added": 1000, "S3_added": 2000},
                  embedded_unique_stops=len(data), all_ids_and_original_strings_match=True,
                  frozen_bundle_before=before, frozen_bundle_after=after, resources=resources,
                  embedded_leaflet_version="1.9.4", csv_fetch_required=False, javascript_cdn_required=False,
                  background="GSI pale tiles; network required only for background",
                  depot_marker=True, depot=depot,
                  depot_sources={name: {k: v for k, v in entry.items() if k != "data"}
                                 for name, entry in depot_sources.items()},
                  depot_use="visualization of historical proxy depot; not confirmation of an observed entrance",
                  administrative_boundary_overlay=False, routing_performed=False)
    write_new_or_identical(REVIEW / "BUILD_VALIDATION.json",
                           (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"html": str(OUTPUT), "counts": report["scenario_counts"],
                      "hashes_unchanged": before == after, "bytes": OUTPUT.stat().st_size}))


TEMPLATE = r'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A〜D共通の固定需要v1。系列切替で包含関係と地点情報を確認する研究用地図。">
<title>大田区ToC配送研究：固定需要地点分布</title>
<style>__LEAFLET_CSS__</style>
<style>
:root{--ink:#162e39;--muted:#526670;--line:#d9e3e6;--s1:#007c83;--s2:#bf7414;--s3:#7951b0}
*{box-sizing:border-box}body{margin:0;color:var(--ink);font-family:system-ui,-apple-system,"Noto Sans CJK JP",sans-serif;background:#eef3f4}
header{height:88px;background:#fff;padding:17px 28px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);gap:16px}
h1{font-size:22px;line-height:1.5;margin:0;font-weight:750;letter-spacing:.02em}.eyebrow{font-size:11px;letter-spacing:.15em;color:var(--muted);margin-bottom:3px}.badge{font-size:12px;background:#eaf5f2;color:#236650;border:1px solid #c9e7de;padding:6px 12px;border-radius:20px;white-space:nowrap}
main{height:calc(100dvh - 88px);min-height:480px;display:grid;grid-template-columns:300px minmax(0,1fr)}
aside{background:#fff;border-right:1px solid var(--line);padding:24px 22px;overflow:auto;z-index:1100;box-shadow:2px 0 10px #17323b05}
.label{font-size:11px;font-weight:750;letter-spacing:.1em;color:var(--muted);margin:0 0 12px}.switch{display:flex;border:1px solid var(--line);border-radius:9px;padding:4px;gap:4px;background:#f5f8f9}
.switch button{flex:1;border:0;background:transparent;border-radius:6px;padding:10px 0;cursor:pointer;color:var(--muted);font-weight:700;font-size:14px}.switch button[aria-pressed=true]{background:var(--ink);color:#fff;box-shadow:0 1px 4px #1233}
.count{margin:23px 0 4px;display:flex;align-items:baseline;gap:8px}.count strong{font-size:43px;font-weight:650;letter-spacing:-.045em;font-variant-numeric:tabular-nums}.count span{font-size:14px;color:var(--muted)}
#series-label{font-size:13px;margin-bottom:22px;color:var(--muted)}.divider{border:0;border-top:1px solid var(--line);margin:22px 0}
.legend-row{display:grid;grid-template-columns:12px 1fr auto;gap:10px;align-items:center;font-size:13px;margin:14px 0;transition:opacity .15s}.legend-row[data-visible=false]{opacity:.3}.dot{height:10px;width:10px;border-radius:50%;background:var(--color)}.legend-row small{color:var(--muted);font-variant-numeric:tabular-nums;font-size:12px}
.hint{font-size:12px;color:var(--muted);line-height:1.8;margin:14px 0}.small-button{border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink);padding:8px 12px;font-size:12px;cursor:pointer;width:100%}.small-button:hover{background:#f1f6f7}
.depot-card{margin:16px 0;padding:13px;border:1px solid #ecc1c1;border-left:4px solid #b3292d;border-radius:7px;background:#fff7f6;font-size:12px;line-height:1.7}.depot-card strong{display:block;color:#a02429;font-size:14px}.depot-card span{display:block;margin:2px 0 10px}.depot-card button{background:#fff;color:#a02429;border-color:#dcb3b3}.depot-pin{filter:drop-shadow(0 3px 4px #49202070)}.depot-label{background:#fff9f8;border:2px solid #b3292d;border-radius:7px;padding:8px 12px;color:#8c2026;box-shadow:0 2px 8px #391d1d26;font-size:12px;line-height:1.6}.depot-label strong{display:block;font-size:14px}.depot-label:before{border-right-color:#b3292d!important;border-left-color:#b3292d!important}.depot-label small{display:block;color:#715457;font-size:10px}
.toggle{font-size:12px;display:flex;gap:7px;align-items:center;margin:12px 0}.toggle input{accent-color:var(--ink)}#tile-status{font-size:11px;color:var(--muted);line-height:1.6;min-height:18px}
details{font-size:12px;line-height:1.9;color:var(--muted)}summary{cursor:pointer;color:var(--ink);font-weight:600}details p{margin:10px 0}details code{overflow-wrap:anywhere;font-size:10px}a{color:#086978}
#map{width:100%;height:100%;background-color:#eef3f4;background-image:linear-gradient(#cdd9df55 1px,transparent 1px),linear-gradient(90deg,#cdd9df55 1px,transparent 1px);background-size:32px 32px;isolation:isolate}.leaflet-container{font-family:inherit}.leaflet-control-scale-line{font-size:11px}.leaflet-popup-content{margin:17px 20px;min-width:245px;max-width:330px}.popup-heading{font-size:13px;font-weight:750;margin-bottom:12px}.popup-group{display:inline-block;font-size:11px;padding:2px 7px;border-radius:4px;background:#f0f4f5;margin-bottom:12px}.popup-grid{display:grid;grid-template-columns:68px 1fr;gap:8px 10px;font-size:11px;line-height:1.7}.popup-grid dt{color:var(--muted)}.popup-grid dd{margin:0;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}.leaflet-popup-close-button{margin:4px}
@media(max-width:760px){header{height:auto;min-height:88px;padding:14px 16px}h1{font-size:17px}.badge{display:none}main{height:calc(100dvh - 88px);display:flex;flex-direction:column;min-height:600px}aside{padding:12px 16px;max-height:235px;border-right:0;border-bottom:1px solid var(--line);flex-shrink:0}.switch{max-width:260px}.count{margin:10px 0 0}.count strong{font-size:28px}#series-label{margin-bottom:8px}.divider{margin:10px 0}.legend-row{display:inline-grid;margin:6px 8px 4px 0;font-size:11px;gap:5px}.legend-row small{display:none}.label,.hint,details,.small-button,.toggle,#tile-status{display:none}#map{flex:1;min-height:365px}}
</style>
</head>
<body>
<header><div><div class="eyebrow">KMD · ToC DELIVERY STUDY / DEMAND v1</div><h1>大田区ToC配送研究：固定需要地点分布</h1></div><span class="badge">A〜D 共通・固定入力</span></header>
<main>
<aside aria-label="需要系列と凡例">
<p class="label">表示する系列</p>
<div class="switch" role="group" aria-label="需要系列の切替">
<button data-scenario="1" aria-pressed="false">S1</button><button data-scenario="2" aria-pressed="false">S2</button><button data-scenario="3" aria-pressed="true">S3</button>
</div>
<div class="count" aria-live="polite"><strong id="visible-count">4,000</strong><span>地点</span></div>
<div id="series-label">S3 · 全3群を表示</div>
<div class="depot-card"><strong>出発点</strong><span>京浜トラックターミナル<br>（既存研究の仮想拠点）</span><button class="small-button" id="focus-depot">出発点へ移動</button></div>
<hr class="divider"><p class="label">最初に含まれる系列</p>
<div class="legend-row" data-group="1" data-visible="true"><span class="dot" style="--color:var(--s1)"></span><span>S1に含まれる地点</span><small>1,000</small></div>
<div class="legend-row" data-group="2" data-visible="true"><span class="dot" style="--color:var(--s2)"></span><span>S2追加分</span><small>1,000</small></div>
<div class="legend-row" data-group="3" data-visible="true"><span class="dot" style="--color:var(--s3)"></span><span>S3追加分</span><small>2,000</small></div>
<p class="hint">S1 ⊂ S2 ⊂ S3<br>地点をクリックすると、固定CSVの情報を確認できる。</p>
<button class="small-button" id="fit">表示地点の全体を見る</button>
<hr class="divider">
<label class="toggle"><input type="checkbox" id="basemap" checked>背景地図を表示（通信が必要）</label>
<div id="tile-status" role="status">背景地図を読み込み中</div>
<hr class="divider">
<details><summary>出典と生成方式</summary><p>需要入力：固定需要v1のS1.csv・S2.csv・S3.csv。元の合成候補39,956地点の町丁目構成比を最大剰余法で配分し、監査PASS34,912地点から共通SHA-256順位で抽出した。</p><p>全地点1個は研究上の制御条件であり、実配送実績・取扱量の推定ではない。地図表示のための再生成・再抽出は行っていない。</p><p>出発点は既存の凍結済みDEP_006と施設台帳で一致した代理拠点座標を表示する。実際の出入口・車両停車位置の確認を意味しない。</p><p>背景：<a href="https://maps.gsi.go.jp/development/ichiran.html#pale" target="_blank" rel="noopener">国土地理院・淡色地図</a>。背景のみインターネット接続が必要である。地点・地図操作ライブラリはHTML内蔵であり、オフラインでも切替・拡大縮小・クリックが可能である。</p><p>行政界の重ね合わせ、配送ルートは追加していない。</p><p>固定CSVのSHA-256：<code id="hash-note"></code></p></details>
</aside>
<div id="map" aria-label="固定需要地点の地図"></div>
</main>
<noscript>地点地図の表示にはJavaScriptを有効にする必要がある。</noscript>
<!-- Leaflet 1.9.4 license:
__LEAFLET_LICENSE__
-->
<script>__LEAFLET_JS__</script>
<script id="demand-data" type="application/json">__DEMAND_JSON__</script>
<script>
'use strict';
(() => {
const records = JSON.parse(document.getElementById('demand-data').textContent);
const sourceHashes = __SOURCE_HASHES__;
const depot = __DEPOT_JSON__;
const colors = {1:'#007c83',2:'#bf7414',3:'#7951b0'};
const names = {1:'S1',2:'S2追加分',3:'S3追加分'};
const expected = {1:1000,2:2000,3:4000};
const map = L.map('map',{preferCanvas:true,maxZoom:19,minZoom:9,zoomControl:false});
L.control.zoom({position:'topright',zoomInTitle:'拡大',zoomOutTitle:'縮小'}).addTo(map);
L.control.scale({position:'bottomleft',imperial:false,maxWidth:140}).addTo(map);
const canvas = L.canvas({padding:.3,tolerance:2});
const layers = {1:L.layerGroup(),2:L.layerGroup(),3:L.layerGroup()};
const markerById = new Map();
function popupFor(record) {
  const box = document.createElement('div');
  box.dataset.stopId = record.stop_id;
  const heading = document.createElement('div'); heading.className='popup-heading'; heading.textContent='固定需要地点';box.appendChild(heading);
  const tag = document.createElement('span');tag.className='popup-group';tag.textContent=names[record.minimum_series];tag.style.color=colors[record.minimum_series];box.appendChild(tag);
  const dl = document.createElement('dl');dl.className='popup-grid';
  for (const [field,label,value] of [
    ['stop_id','地点ID',record.stop_id],['building_id','建物ID',record.building_id],['chocho_code','町丁目',record.chocho_code],
    ['latitude','緯度',record.latitude],['longitude','経度',record.longitude],['parcel_count','荷物個数',record.parcel_count],['minimum_series','最小系列',names[record.minimum_series]]]) {
    const dt=document.createElement('dt');dt.textContent=label;const dd=document.createElement('dd');dd.dataset.field=field;dd.textContent=value;dl.append(dt,dd);
  }
  box.appendChild(dl);return box;
}
for (const record of records) {
  if(markerById.has(record.stop_id)) throw new Error('Duplicate embedded stop');
  const marker=L.circleMarker([Number(record.latitude),Number(record.longitude)],{renderer:canvas,radius:3.5,color:colors[record.minimum_series],weight:.5,fillColor:colors[record.minimum_series],fillOpacity:.8});
  marker.demandRecord=record;
  marker.bindPopup(()=>popupFor(record),{maxWidth:360,autoPanPadding:[25,25]});
  markerById.set(record.stop_id,marker);layers[record.minimum_series].addLayer(marker);
}
const depotIcon=L.divIcon({className:'depot-pin',iconSize:[56,64],iconAnchor:[28,60],tooltipAnchor:[0,-34],popupAnchor:[0,-54],html:'<svg viewBox="0 0 56 64" width="56" height="64" aria-hidden="true"><path d="M28 61C23 53 5 38 5 26a23 23 0 1 1 46 0C51 38 33 53 28 61Z" fill="#b3292d" stroke="white" stroke-width="4"/><path d="M16 25l12-10 12 10v15H16Z" fill="white"/><path d="M25 29h7v11h-7Z" fill="#b3292d"/></svg>'});
const depotMarker=L.marker([Number(depot.latitude),Number(depot.longitude)],{icon:depotIcon,title:'出発点：京浜トラックターミナル（仮想拠点）',alt:'配送出発点',zIndexOffset:2000}).addTo(map);
const depotLabel=document.createElement('div');const depotTitle=document.createElement('strong');depotTitle.textContent='出発点';const depotName=document.createElement('span');depotName.textContent=depot.facility_name;const depotNote=document.createElement('small');depotNote.textContent='既存研究の仮想拠点';depotLabel.append(depotTitle,depotName,depotNote);
depotMarker.bindTooltip(depotLabel,{permanent:true,direction:'auto',offset:[26,0],className:'depot-label',opacity:1});
const depotPopup=document.createElement('div');const depotPopupTitle=document.createElement('strong');depotPopupTitle.textContent='出発点｜'+depot.facility_name;const depotPopupText=document.createElement('p');depotPopupText.textContent=depot.depot_id+' / 緯度 '+depot.latitude+' / 経度 '+depot.longitude+'。既存研究の代理拠点であり、実際の出入口の確認ではない。';depotPopup.append(depotPopupTitle,depotPopupText);depotMarker.bindPopup(depotPopup,{maxWidth:340});
let active=3;
const tiles=L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',{maxNativeZoom:18,maxZoom:19,attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'});
const tileStats={loaded:0,errors:0};
tiles.on('tileload',()=>{tileStats.loaded++;document.getElementById('tile-status').textContent=tileStats.errors?'背景地図：一部を取得できない':'背景地図：表示中';});
tiles.on('tileerror',()=>{tileStats.errors++;document.getElementById('tile-status').textContent='背景地図を取得できない。地点表示・操作は利用可能。';});
tiles.addTo(map);
function visibleRecords(){return records.filter(r=>r.minimum_series<=active);}
function fitVisible(){const points=visibleRecords().map(r=>[Number(r.latitude),Number(r.longitude)]);points.push(depotMarker.getLatLng());map.fitBounds(L.latLngBounds(points),{padding:[65,65],animate:false});}
function setScenario(level){
  if(!expected[level]) throw new Error('Unknown scenario');
  map.closePopup();active=level;
  for(let group=1;group<=3;group++){
    const shown=group<=level;
    if(shown&&!map.hasLayer(layers[group]))layers[group].addTo(map);
    if(!shown&&map.hasLayer(layers[group]))map.removeLayer(layers[group]);
    document.querySelector(`[data-group="${group}"]`).dataset.visible=String(shown);
  }
  const count=visibleRecords().length;if(count!==expected[level])throw new Error('Scenario count mismatch');
  document.getElementById('visible-count').textContent=count.toLocaleString('ja-JP');
  document.getElementById('series-label').textContent=`S${level} · ${level===1?'第1群':level===2?'第1・第2群':'全3群'}を表示`;
  document.querySelectorAll('[data-scenario]').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.scenario)===level)));
}
document.querySelectorAll('[data-scenario]').forEach(button=>button.addEventListener('click',()=>setScenario(Number(button.dataset.scenario))));
document.getElementById('fit').addEventListener('click',fitVisible);
document.getElementById('focus-depot').addEventListener('click',()=>{map.setView(depotMarker.getLatLng(),16,{animate:false});depotMarker.openPopup();});
document.getElementById('basemap').addEventListener('change',event=>{if(event.target.checked){tiles.addTo(map);document.getElementById('tile-status').textContent='背景地図を読み込み中';}else{map.removeLayer(tiles);document.getElementById('tile-status').textContent='背景なし · 地点・操作はオフライン対応';}});
document.getElementById('hash-note').textContent=Object.entries(sourceHashes).map(([s,h])=>`${s}: ${h}`).join(' / ');
setScenario(3);fitVisible();
// Inspection hooks expose the rendered data; they do not generate demand.
window.tocDemandMap=Object.freeze({map,markerById,layers,records,sourceHashes,tileStats,visibleRecords,fitVisible,depot,depotMarker,get active(){return active;}});
})();
</script>
</body></html>
'''


if __name__ == "__main__":
    main()
