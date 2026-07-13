from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "use_case_scenario"
EN_CSV = OUT_DIR / "943_20260705_v03_tokyo_evrp_quantum_requirement_map.csv"
JA_CSV = OUT_DIR / "944_20260705_v03_tokyo_evrp_quantum_requirement_map_ja.csv"
JA_MD = OUT_DIR / "tokyo_evrp_quantum_requirement_map_summary_ja.md"


JA_ROWS = [
    {
        "要件ID": "REQ-01",
        "EVRP要件": "customers / demand nodes",
        "なぜ重要か": "配送需要の規模と、サービス対象地点の数を表すため。",
        "EVRP benchmarkでの根拠": "E-CVRPとSchneider/Goeke E-VRPTWの実ファイル解析では、customersは5-1000、平均112.129。",
        "Tokyo公開データで使えるもの": "Tokyo人口密度6402.6 persons/km2、Tokyo人口14047594人、OSM道路網。これらはsynthetic customer nodes設計のproxyになる。",
        "Tokyo subcaseでの状態": "partial",
        "量子VRP Figure 1で確認できること": "Figure 1で抽出できたproblem entitiesは3-200。ただし、多くの評価済み行は3-6 nodes/locations。Golden_5は200 customersだがresource estimateのみ。",
        "ギャップ": "実行・検証済みの量子VRP evidenceは多くがtoy-sizeであり、大きなcustomer数は主にresource estimateとして現れる。",
        "benchmark設計への示唆": "Tokyoのsynthetic customer nodesを明示的に定義する。EV stockやGTFS stopsから直接推定しない。",
        "限界": "Tokyo公開データは需要proxyであり、実配送顧客データではない。",
    },
    {
        "要件ID": "REQ-02",
        "EVRP要件": "vehicles / fleet size",
        "なぜ重要か": "fleet coordination、capacity allocation、route countを決めるため。",
        "EVRP benchmarkでの根拠": "E-CVRP実ファイル解析では、VEHICLESは3-207、平均33.333。",
        "Tokyo公開データで使えるもの": "Japan van EV stock 26000 vehicles、van EV sales share 0.96 percent。ただし背景指標である。",
        "Tokyo subcaseでの状態": "needs scenario assumption",
        "量子VRP Figure 1で確認できること": "Figure 1で車両数が確認できる範囲は2-5。抽出scopeにvehiclesが出てこない行も多い。",
        "ギャップ": "量子側はnodes/qubitsを報告することが多く、EVRP benchmark vehiclesに相当するfleet-size scenarioが十分に整理されていない。",
        "benchmark設計への示唆": "fleet sizeはscenario parameterとして設定する。national EV stockから変換しない。",
        "限界": "EV stockやsales shareは国レベル文脈であり、事業者fleet-sizeデータではない。",
    },
    {
        "要件ID": "REQ-03",
        "EVRP要件": "charging stations",
        "なぜ重要か": "station-choiceとrecharge feasibilityを加えるため、generic VRPとEVRPを分ける中核要件である。",
        "EVRP benchmarkでの根拠": "E-CVRPとSchneider/Goeke E-VRPTWの実ファイル解析では、charging stationsは2-21、平均13.078。",
        "Tokyo公開データで使えるもの": "Open Charge Map Tokyo bounding-box stations 173、fast charger share proxy 0.2716。",
        "Tokyo subcaseでの状態": "available as public-data proxy",
        "量子VRP Figure 1で確認できること": "Figure 1抽出scopeでcharging stationsが明示された行は0。",
        "ギャップ": "既存の量子VRP抽出データでは、charging-station evidenceが確認できない。",
        "benchmark設計への示唆": "geocoded chargersからcandidate station setを定義し、coverage limitationを明記する。",
        "限界": "Open Charge Mapのcoverage/statusは不完全な可能性があり、bounding-boxに周辺市が入る可能性がある。",
    },
    {
        "要件ID": "REQ-04",
        "EVRP要件": "vehicle capacity / cargo capacity",
        "なぜ重要か": "load feasibilityを表し、unconstrained routingとCVRP/E-CVRPを分けるため。",
        "EVRP benchmarkでの根拠": "E-CVRPとSchneider/Goeke E-VRPTWの実ファイル解析では、cargo capacityは33-30000、平均982.862。",
        "Tokyo公開データで使えるもの": "公開データからoperator load/cargoは直接得られていない。車種またはbenchmark仮定が必要。",
        "Tokyo subcaseでの状態": "needs scenario assumption",
        "量子VRP Figure 1で確認できること": "Golden_5 CVRP resource estimateではcapacity 900がある。他の評価済み行では同等のcargo-capacity fieldsは抽出scope上で十分確認できない。",
        "ギャップ": "capacityは一部CVRP/resource estimateに出るが、EV logistics constraintsと一貫して接続されていない。",
        "benchmark設計への示唆": "cargo capacityを明示的に設定し、EV stockや人口proxyとは分ける。",
        "限界": "Tokyo公開データはoperator package demandやvehicle payload distributionを提供しない。",
    },
    {
        "要件ID": "REQ-05",
        "EVRP要件": "battery / energy capacity",
        "なぜ重要か": "航続可能性と充電必要性を決めるため。",
        "EVRP benchmarkでの根拠": "E-CVRPとSchneider/Goeke E-VRPTWの実ファイル解析では、energy capacityは53-2773、平均256.476。解析した全benchmark instanceにenergy constraintsがある。",
        "Tokyo公開データで使えるもの": "車両別battery capacity datasetは未取得。Tokyo charger dataはstation/power contextであり、vehicle battery capacityではない。",
        "Tokyo subcaseでの状態": "needs scenario assumption",
        "量子VRP Figure 1で確認できること": "Figure 1抽出scopeでenergy constraintsが明示された行は0。",
        "ギャップ": "Energy/SOC constraintsはEVRP benchmarkで中核だが、Figure 1量子VRP行では見えない。",
        "benchmark設計への示唆": "battery/SOC parametersをbenchmark conventionまたは車両仕様仮定から設定する。",
        "限界": "charger countやEV stockからbattery capacityは推定できない。",
    },
    {
        "要件ID": "REQ-06",
        "EVRP要件": "energy consumption",
        "なぜ重要か": "route distanceとbattery depletionを接続するため。",
        "EVRP benchmarkでの根拠": "E-CVRPとSchneider/Goeke E-VRPTWの実ファイルにはENERGY_CONSUMPTIONまたはfuel consumption rateが含まれる。",
        "Tokyo公開データで使えるもの": "OSM road density 22.358 km/km2、road length proxy 44893.807 km。距離構造のproxyとして使える。",
        "Tokyo subcaseでの状態": "needs model assumption",
        "量子VRP Figure 1で確認できること": "Energy consumptionはFigure 1抽出scopeでは報告されていない。",
        "ギャップ": "量子VRP evidenceはrouting formulation/widthを報告する一方で、EV energy-consumption feasibilityは十分に扱っていない。",
        "benchmark設計への示唆": "Tokyo EVRP benchmarkを作る場合、distance-to-energy modelを定義する。",
        "限界": "OSM道路はnetwork geometryであり、車両のenergy consumptionではない。",
    },
    {
        "要件ID": "REQ-07",
        "EVRP要件": "depot",
        "なぜ重要か": "車両の出発・帰着地点とroute feasibilityを決めるため。",
        "EVRP benchmarkでの根拠": "解析したE-CVRP instancesにはDEPOT_SECTIONがあり、全instanceが1 depotを持つ。",
        "Tokyo公開データで使えるもの": "depot-location datasetは未取得。synthetic depotまたは物流施設データが必要。",
        "Tokyo subcaseでの状態": "needs scenario assumption",
        "量子VRP Figure 1で確認できること": "一部VRP formulationはdepotを含意するが、depot detailsは一貫して抽出されていない。",
        "ギャップ": "depot assumptionsがEVRP benchmark reconstructionに使える形で十分に報告されていない。",
        "benchmark設計への示唆": "Tokyo benchmark designではdepot coordinatesを明示する。",
        "限界": "公開データはoperator depot locationsを提供しない。",
    },
    {
        "要件ID": "REQ-08",
        "EVRP要件": "distance / travel-cost representation",
        "なぜ重要か": "route objectiveとfeasibility costを定義するため。",
        "EVRP benchmarkでの根拠": "E-CVRP filesにはEUC_2D coordinatesとEDGE_WEIGHT_TYPEが含まれ、Schneider/Goeke E-VRPTW filesにも座標とEuclidean distance前提がある。",
        "Tokyo公開データで使えるもの": "OSM road intersections 113710。Toei Bus GTFSは利用可能だがdelivery road networkではない。",
        "Tokyo subcaseでの状態": "available as public-data proxy",
        "量子VRP Figure 1で確認できること": "Figure 1はinstance sizeやencodingを報告するが、distance/cost matrix availabilityは抽出表上で一貫して確認できない。",
        "ギャップ": "量子側ではrouting costが抽象化されることが多く、public-data-grounded travel-cost constructionが不足している。",
        "benchmark設計への示唆": "OSMからdistance/travel-time matrixを作成または記録し、GTFSはsmart-city data readinessとして別扱いにする。",
        "限界": "OSM由来costは、travel-time calibrationがなければproxyである。",
    },
    {
        "要件ID": "REQ-09",
        "EVRP要件": "time windows",
        "なぜ重要か": "配送時間指定、service promises、operational feasibilityを表すため。",
        "EVRP benchmarkでの根拠": "Schneider/Goeke E-VRPTW実ファイル92件を解析し、customer ReadyTime, DueDate, ServiceTimeを確認した。E-CVRPファイルにはtime windowsはない。",
        "Tokyo公開データで使えるもの": "Japan LPI Timeliness 4/5、GTFS stop_time records 1304152。ただし配送time windowsではない。",
        "Tokyo subcaseでの状態": "benchmarkでは対応済み。ただしTokyo固有の配送時間帯は仮定が必要",
        "量子VRP Figure 1で確認できること": "Figure 1にはVRPTW関連行が5件あるが、抽出scope上ではEV charging/SOCと結合していない。",
        "ギャップ": "time-window evidenceは一部あるが、EV chargingとbattery feasibilityを同時に扱う証拠は弱い。",
        "benchmark設計への示唆": "time-window fieldsはSchneider/Goeke E-VRPTWをtemplateとして使える。ただしTokyo固有の配送時間帯は、事業者データがない限りscenario assumptionとして設定する。",
        "限界": "LPIとGTFSはparcel delivery time windowsを提供しない。",
    },
    {
        "要件ID": "REQ-10",
        "EVRP要件": "validation / feasibility evidence",
        "なぜ重要か": "benchmarkでは、circuit mappingだけでなく、routeが制約を満たすかを評価する必要があるため。",
        "EVRP benchmarkでの根拠": "E-CVRP filesはcapacity, energy, stations, depots, demand sectionsを通じてfeasibility constraintsを定義している。",
        "Tokyo公開データで使えるもの": "Tokyo dataはbenchmark constructionを支えるが、observed feasible operator routesは提供しない。",
        "Tokyo subcaseでの状態": "benchmark-design only",
        "量子VRP Figure 1で確認できること": "Figure 1にはsimulation, hardware-aware, hardware-targeted, resource-estimate stagesがある。ただしresource estimatesはhardware executionではない。",
        "ギャップ": "量子側ではwidth/depthだけでなく、EVRP constraint satisfactionやfeasibility reportingが必要である。",
        "benchmark設計への示唆": "将来の量子VRP評価では、EVRP-style instancesに対するconstraint coverageとfeasible-route evidenceを報告する。",
        "限界": "このmapはoperational deploymentやquantum advantageを主張しない。",
    },
]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def write_md(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Tokyo-EVRP-Quantum Requirement Map 要約",
        "",
        "## 目的",
        "",
        "この表は、Tokyo公開データ、EVRP benchmark実ファイルから抽出した要件、Figure 1の量子VRP evidenceを同じEVRP要件軸で接続するための橋渡し表である。",
        "",
        "EV stock、GTFS routes、qubit widthなどを直接比較するのではなく、一度EVRP benchmark要件へ変換した上で比較することを目的とする。",
        "",
        "## 主な結論",
        "",
        "E-CVRP実ファイル解析によりvehicles, charging stations, capacity, energy capacity, energy consumption, depot, distance/cost representationが確認でき、Schneider/Goeke E-VRPTW実ファイル解析によりcustomer ReadyTime, DueDate, ServiceTimeも確認できた。Tokyo公開データは、特にcharging stationsとroad-network contextを支えるが、fleet size、cargo capacity、battery/SOC、depot、Tokyo固有の配送時間帯はscenario assumptionが必要である。Figure 1の量子VRP evidenceは、EV固有制約についてはまだ限定的である。",
        "",
        "## 要件別の状態",
        "",
        "| EVRP要件 | Tokyo側の状態 | 主なギャップ |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['EVRP要件']} | {row['Tokyo subcaseでの状態']} | {row['ギャップ']} |")
    lines.extend(
        [
            "",
            "## 解釈ルール",
            "",
            "このmapは、TokyoのEV配送ルートを実測したことを示すものではない。また、量子VRPがdeployment-readyであることも示さない。どのEVRP benchmark要件がTokyo公開データで支えられ、どの要件が仮定を必要とし、どの要件がFigure 1の量子VRP evidenceでは不足しているかを整理するための表である。",
            "",
        ]
    )
    JA_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    fields = [
        "要件ID",
        "EVRP要件",
        "なぜ重要か",
        "EVRP benchmarkでの根拠",
        "Tokyo公開データで使えるもの",
        "Tokyo subcaseでの状態",
        "量子VRP Figure 1で確認できること",
        "ギャップ",
        "benchmark設計への示唆",
        "限界",
    ]
    write_csv(JA_CSV, JA_ROWS, fields)
    write_md(JA_ROWS)
    print(JA_CSV)
    print(JA_MD)


if __name__ == "__main__":
    main()
