# 現行研究パイプライン 実行・正本・検証リファレンス

文書ID: `DOC-RESEARCH-PIPELINE-REFERENCE`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/indexes/research_repository_index_v17.yml`

状態: `CURRENT PIPELINE REFERENCE`

本書は、各研究工程の「実行 → 成果物 → 正本 → 検証 → 受入 → 次工程」を追跡する現行運用リファレンスである。研究の問い、概念枠組み、Stage 1–11のロードマップ、マイルストーンは[研究概要・ロードマップ](RESEARCH_OVERVIEW.md)を参照する。本書は各Decision、仕様、設定、schema、run、受入成果物への索引であり、それらを置き換える第二の正本ではない。記載と正本成果物が矛盾する場合は、各節の「正本・信頼源」に示す成果物を優先する。

説明、見出し、表項目は日本語で記載する。実在するコマンド、ファイル名、field名、ID、`DONE`や`NOT IMPLEMENTED`などの機械可読な状態値は、repository内の正本表記を保持する。

## 更新方針

次の場合に本書を更新する。

- 現在の工程、直ちに行う作業、またはマイルストーンが変わる。
- 本番パイプライン、成果物、validator、受入、CLIコマンドが追加・変更される。
- 正本の入力・出力、正本pointer、schema、ゲート、引渡し内容が変わる。
- 工程が受入済みまたはDONEになる。

履歴上の診断runや一時的な実験出力は、現行・正本として採択されない限り本書の現行経路へ追加しない。更新時は本書専用validatorとrepository・Portal validatorを実行する。

## 状態の定義

| 状態 | 意味 |
|---|---|
| `CURRENT / IMPLEMENTED` | 現在のcheckoutに実装または参照が存在する。 |
| `ACCEPTED` | 受入成果物によって下流利用が許可されている。 |
| `DONE` | 現行ロードマップ上の完了条件を満たしている。 |
| `NEXT` | 現在着手すべき工程。 |
| `PLANNED` | ロードマップにあるが完了していない。 |
| `FUTURE` | 上流ゲートが閉じている将来工程。 |
| `NOT IMPLEMENTED` | 本番code、runner、またはvalidatorが存在しない。 |
| `NOT AVAILABLE` | 必要な成果物または結果が存在しない。 |
| `UNRESOLVED` | 研究判断またはparameterの固定が必要。 |
| `HISTORICAL` | 過去の記録でcurrentではない。 |
| `SUPERSEDED` | 明示的に後継へ置換された。 |

コマンドインターフェースの存在はパイプライン実装を意味しない。`--dry-run`が成功しても成果物の生成・検証・受入を意味しない。

## 現在の研究位置 — 今何をすべきか

| 項目 | 現在の状態 |
|---|---|
| ネットワーク構築 | `DONE` |
| ネットワーク受入 | `ACCEPTED` / `FORMAL_NETWORK_ACCEPTED = true` |
| 現在のマイルストーン | `M1 Network Ready — DONE` |
| 現在の研究工程 | `Routing Baseline — NEXT` |
| 直ちに行う作業 | 配送インスタンス用の経路計算範囲を定義する。 |
| 受入済みネットワークSHA-256 | `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| 最初に決める事項 | インスタンス選択・配送先範囲、デポ、配送車両クラス、経路コスト定義を固定する。 |

最初に次を使用する。

```bash
./research status
./research routing inputs
./research routing status
./research pipeline routing --dry-run
```

`39,956 × 39,956`の全組合せ行列は採択済み前提ではない。対象配送インスタンスと必要OD集合を先に定義する。

## パイプライン全体図

```text
外部・オープンデータ                        [DONE]
  ├─→ 基準需要                              [DONE]
  │     ↓
  │   リクエスト・配送先                    [DONE; ローカル生成成果物]
  └─→ ネットワーク構築                      [DONE]
          ↓
        配送先マッピング                    [DONE]
          ↓
        ネットワーク受入                    [ACCEPTED]
          ↓
        経路計算ベースライン                [NEXT / NOT IMPLEMENTED]
          ↓
        共通配送インスタンス                [PLANNED / NOT IMPLEMENTED]
          ↓
        古典最適化                          [PLANNED / NOT IMPLEMENTED]
          ↓
        QUBO                                [PLANNED / NOT IMPLEMENTED]
          ↓
        QAOA                                [FUTURE / NOT IMPLEMENTED]
          ↓
        シナリオ構築                        [PLANNED / NOT IMPLEMENTED]
          ↓
        配送シミュレーション                [PLANNED / NOT IMPLEMENTED]
          ↓
        評価                                [PLANNED / NOT IMPLEMENTED]
          ↓
        エビデンスに基づく解釈              [CURRENT EVIDENCE DESIGN / NO RESULT]
          ↓
        感度・頑健性                        [PLANNED / NOT IMPLEMENTED]
          ↓
        公開・再現性凍結                    [FUTURE / NOT IMPLEMENTED]
```

ロードマップの`PLANNED`とPortal実行mapの`FUTURE`が異なる下流工程では、本書は`PLANNED / FUTURE / NOT IMPLEMENTED`と併記する。`PLANNED`は研究計画上の存在、`FUTURE`は現在の実行位置、`NOT IMPLEMENTED`は本番実装の不在を表す。

## A. 外部・オープンデータ

### 目的

入力sourceのidentity、取得元、取得日、hash、用途、利用制限を固定し、DemandとNetworkの派生処理へ渡す。

### 現在の状態

`DONE`（governed source inputs）。datasetごとのreadinessと再配布可否は同一ではない。

### 開始条件

sourceを台帳登録し、取得記録・local raw path・hash・利用条件を確認する。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| source台帳 | source identity / hash | [traffic_simulation_sources.csv](03_data/metadata/traffic_simulation_sources.csv) | `CURRENT` | sourceごとの用途・制限を記録。 |
| 来歴policy | raw/derived provenance | [data_provenance.md](03_data/metadata/data_provenance.md) | `CURRENT` | raw原本の一部は再配布されない。 |
| 取得記録 | source-specific acquisition evidence | [acquisition README](03_data/metadata/acquisition/README.md) | `CURRENT` | 個別記録から取得条件を追跡する。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research artifacts` | current input/artifact path確認 | Read-only | dataset内容の再取得・検証は行わない。 |
| `./research demand validate` | Demand consumer側からsource/config整合性を検証 | Read-only validation | source全体のacceptanceではない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 基準値利用処理 | [prepare_baseline_demand.py](05_src/traffic_simulation/demand/prepare_baseline_demand.py) | 登録sourceをbaseline demandへ変換。 |
| ネットワークsource処理 | [traffic simulation README](05_src/traffic_simulation/README.md) | source道路表現の処理入口説明。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| source metadata | identity/hash/license/provenance | `03_data/metadata/` | `AVAILABLE` |
| raw sourceデータ | acquired originals | `03_data/raw/traffic_simulation/` | dataset-dependent / local |
| 利用側入力 | normalized or derived input | consumer configが指定 | dataset-dependent |

### 正本・信頼源

Source identityはsource registry、取得事実は個別acquisition record、consumer採択は各pipeline config/acceptanceが正本。本書はsource acceptanceを新設しない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| Registry・利用側確認 | `./research demand validate` | Demand testと必要current inputが成功 | `AVAILABLE`; source全体gateではない |
| リポジトリ参照 | `./research portal check` | current path/index/link検証成功 | `PASS` |

### 受入・DONE条件

source identity、hash、取得条件、用途、制限が台帳化され、利用pipelineのvalidatorがsourceを確認できること。Portal roadmap上は`DONE`。

### 来歴

source ID、取得日、URL、SHA-256はsource registryとacquisition recordに記録する。

### 既知の制約

raw原本の一部はgit非追跡で再取得が必要。Open Dataは実配送運用を直接表さない。

### 未解決の判断

future scenarioで採用する追加sourceと変換規則は`UNRESOLVED`。

### 次工程への引渡し

登録済みsource IDとhashをDemandまたはNetwork configへ渡す。

## B. 需要

### 目的

公開統計から大田区500m meshのbaseline populationと`parcel_equivalent/day`需要proxyを生成・検証する。

### 現在の状態

`DONE`（baseline）。safe integrated build runnerは`NOT IMPLEMENTED`。`./research demand status`は現行Portal node ID不一致により現在exit 1。

### 開始条件

source registry上の人口・宅配便統計、大田区境界、baseline configが利用可能であること。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 需要仕様 | definition / boundary | [baseline demand and comparator](05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md) | `CURRENT_NORMATIVE` | 実注文・停止ではない。 |
| 需要config | parameters / output paths | [baseline_demand.yml](reproducibility/config/traffic_simulation/baseline_demand.yml) | `CURRENT` | `target_days: 1`、unitは`parcel_equivalent`。 |
| source台帳 | governed inputs | [traffic_simulation_sources.csv](03_data/metadata/traffic_simulation_sources.csv) | `CURRENT` | config内source IDを解決。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research demand validate` | baseline implementation test＋accepted mapping consistency | Read-only validation | production demandを再生成しない。 |
| `./research demand build --dry-run` | 不足runner/dependencyを表示 | Read-only | build本体は`NOT IMPLEMENTED`。 |
| `./research demand status` | status表示 | Read-only | **現在失敗**: Portal node ID不一致。 |
| `./research demand future` | future demand利用可否表示 | Read-only refusal | `NOT IMPLEMENTED / UNRESOLVED`。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 基準値生成器 | [prepare_baseline_demand.py](05_src/traffic_simulation/demand/prepare_baseline_demand.py) | mesh人口・parcel-equivalent配賦。fixed canonical outputのためCLI buildからは実行しない。 |
| 単体test | [test_prepare_baseline_demand.py](05_src/traffic_simulation/validation/test_prepare_baseline_demand.py) | source/config/配賦不変条件を検証。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 基準需要 | 191 meshのpopulation/demand proxy | `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet` | `AVAILABLE LOCALLY / GIT-IGNORED` |
| 品質要約 | source/config/output hashesと集計 | `03_data/processed/traffic_simulation/validation/ota_ward_baseline_demand_2024_500m_quality_summary.json` | `AVAILABLE LOCALLY / GIT-IGNORED` |

### 正本・信頼源

定義はDemand specification、parameter/output pathはbaseline config、実行結果のhash・集計はquality summary。独立したDemand acceptance flagはない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 基準需要単体検証 | `./research demand validate` | `test_prepare_baseline_demand.py` PASS | `AVAILABLE` |
| 成果物の利用可否 | `./research artifacts` | Parquet/configが存在 | `AVAILABLE LOCALLY` |

### 受入・DONE条件

config、builder、unit test、Parquet、quality summaryが存在し、population/demand conservationとhashが確認できること。roadmap/Portalはbaselineを`DONE`とする。

### 来歴

quality summaryにsource SHA、config SHA、output SHA、generated timestampを記録する。

### 既知の制約

`82,023 parcel-equivalent/day`は顧客数、request数、stop数ではない。artifactはgit-ignoredでportable publicationではない。仕様文書の「未生成」記述とcurrent artifact存在にはdocumentation lagがある。

### 未解決の判断

future demandのscenario year、growth rate、spatial transformationは`UNRESOLVED`。

### 次工程への引渡し

baseline demand proxyをRequests / Stops生成契約へ渡す。parcel-equivalentを1個1停止へ直接変換しない。

## C. リクエスト・配送先

### 目的

合成需要からrequest recordを作り、building単位のdelivery stopへ集約する。request、parcel-equivalent、stopの単位を分離する。

### 現在の状態

`DONE`（current roadmap/Portal、accepted network mappingの入力）。安全なproduction regeneration runnerと専用validatorは`NOT IMPLEMENTED / NOT AVAILABLE`。

### 開始条件

baseline demand、household/building assignment source、固定seed、scope ruleが必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 基準需要 | aggregate demand proxy | `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet` | `AVAILABLE LOCALLY` | parcel-equivalent単位。 |
| リクエスト成果物 | synthetic request records | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv` | `AVAILABLE LOCALLY` | 73,547 data rows。 |
| 配送先生成要約 | generation/accounting | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json` | `AVAILABLE LOCALLY` | scoped parcel conservationを記録。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research demand validate` | file availability＋accepted mapping consistency | Read-only validation | request/stop generatorの再現を検証しない。 |
| `./research artifacts` | canonical local paths表示 | Read-only | availability inspection。 |
| `./research demand build --dry-run` | regeneration gap表示 | Read-only | integrated generator不在。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [demand.py](05_src/research_cli/demand.py) | generator不在時にbuildを拒否。 |
| 現行生成実装 | — | `NOT AVAILABLE` in current checkout |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| リクエスト | 1行1 synthetic request | `.../pipelines_v1/daily_requests.csv` | `AVAILABLE LOCALLY / GIT-IGNORED` |
| 配送先 | building集約delivery stop | `.../pipelines_v1/building_delivery_stops_scoped.csv` | `AVAILABLE LOCALLY / GIT-IGNORED`; 39,956 stops |
| 生成要約 | count/conservation/seed/hash | `.../pipelines_v1/*run_summary.json` | `AVAILABLE LOCALLY / GIT-IGNORED` |

### 正本・信頼源

current pathsはCLI coreとPortal map、下流利用状態はaccepted network authority/acceptanceが参照する。Requests / Stops単独のmachine-readable acceptance artifactは`NOT AVAILABLE`。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 受入済みmapping整合性 | `./research demand validate` | authority validator PASS、required files存在 | `AVAILABLE` |
| リクエスト・配送先再生成validator | — | deterministic generation＋conservation | `NOT AVAILABLE` |

### 受入・DONE条件

現行roadmapはartifact存在とaccepted stop mappingで`DONE`としている。完全な再現性にはgenerator、schema、専用validator、portable artifact policyが追加で必要。

### 来歴

local run summariesにseed、config hash、input artifact hash、request/stop/parcel accountingを記録。

### 既知の制約

baseline 82,023 parcel-equivalent、generated request 73,547 rows、39,956 stopsは異なる単位。scoped stop parcel-equivalentはfull request scopeより小さく、full conservationはfalse、assigned scope conservationのみtrue。

### 未解決の判断

production regeneration contract、portable publication、future scenario別生成interface。

### 次工程への引渡し

Requests、Stops、scope/accountingをStop MappingとRouting scope definitionへ渡す。

## D. ネットワーク構築

### 目的

source道路表現をThree-tier provenance（DIRECT / INFERRED / FALLBACK）でFormal Networkへ完成し、SUMO `net.xml`へmaterializeする。

### 現在の状態

`DONE / ACCEPTED`。安全な新規isolated end-to-end CLI buildは`NOT IMPLEMENTED`。accepted runを再利用する。

### 開始条件

current Decision、policy、pipeline、registry/schema、source/structural input lockが必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 現行正本pointer | authority resolver | [current_network_completion_authority_v17.yml](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | 唯一のcurrent network入口。 |
| 判断 | method adoption | [phase13 Formal Completion Decision](reproducibility/config/traffic_simulation/decisions/phase13_formal_completion_three_tier_v1.yml) | `CURRENT` | Decision ID `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`。 |
| 規範仕様 | Three-tier policy | [formal completion specification](05_src/traffic_simulation/specifications/20260903_20260903_formal_completion_three_tier_policy_v17.md) | `CURRENT_NORMATIVE` | strict/hybridをcurrentへ混ぜない。 |
| パイプライン仕様 | ordered stages/gates | [network completion pipeline specification](05_src/traffic_simulation/specifications/20260903_20260903_network_completion_pipeline_v17.md) | `CURRENT_NORMATIVE` | SOURCE→…→ACCEPTANCE。 |
| Registry・schema | machine-readable contract | [Three-tier registry](reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml) | `CURRENT` | policy/record schemasはauthorityから解決。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research network status` | accepted pointer/hash/status表示 | Read-only | 推奨inspection。 |
| `./research network validate` | current accepted networkを全gate検証 | Read-only validation | buildしない。 |
| `./research network acceptance` | acceptance JSON表示 | Read-only | flag/gates/mappingを表示。 |
| `./research network build --dry-run` | unsafe fixed-output limitation表示 | Read-only | build本体は拒否される。 |
| `./research pipeline network` | accepted networkを再利用してvalidate | Read-only validation | accepted runを上書きしない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| Three-tier補完 | [execute_three_tier_completion_streaming.py](05_src/traffic_simulation/network/execute_three_tier_completion_streaming.py) | accepted build provenance上のcompletion implementation。 |
| Registry validator | [validate_formal_completion_three_tier_registry.py](05_src/traffic_simulation/network/validate_formal_completion_three_tier_registry.py) | policy/registry/schema整合性。 |
| パイプラインvalidator | [validate_network_completion_pipeline.py](05_src/traffic_simulation/network/validate_network_completion_pipeline.py) | stage ordering/gate contract。 |
| 正本validator | [validate_current_network_completion_authority.py](05_src/traffic_simulation/network/validate_current_network_completion_authority.py) | pointer/hash/acceptance integrity。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 受入済みrun | current run directory | `reproducibility/outputs/.../phase13_20260903_three_tier_completion/run_2` | `ACCEPTED` |
| 受入済みnetwork | SUMO network | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `ACCEPTED` |
| ネットワークグラフ規模 | routing graphのnode / directed edge数とSUMO lane数 | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) `/validation/counts` | `ACCEPTED` |
| 来歴集計 | DIRECT/INFERRED/FALLBACK counts | [quality_accounting.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1/quality_accounting.json) | `CURRENT REFERENCE FROM AUTHORITY` |

### 正本・信頼源

[current network authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml)がDecision、specification、registry/schema、accepted run/network/acceptance、SHAを解決する。Hierarchical Hybridは`SUPERSEDED`、strict v17と旧runは`HISTORICAL`。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| Registry・schema | `./research network validate` | registry/schema validator PASS | `PASS` |
| パイプライン定義 | same | current Decision/order/gates一致 | `PASS` |
| SUMO build・属性・接続性 | same | build、lane、speed、permission、connectivity PASS | `PASS` |
| SHA完全性 | same | actual SHA＝authority SHA | `PASS` |

### 受入・DONE条件

all network gates PASS、accepted `net.xml`存在、SHA一致、Stop Mapping/routeability gate PASS、`FORMAL_NETWORK_ACCEPTED=true`。

### 来歴

accepted run ID `three_tier_run_2`、network ID `P13-THREE-TIER-RUN-2`、source commit、input/output SHA、quality accountingをauthority/acceptanceに記録。

ネットワークグラフ規模は受入成果物の`validation.counts`を正本とする。`network_node_count = 70,050`、`network_edge_count = 147,168`（方向別に定義されたSUMO edgeを数える有向edge）、`network_lane_count = 154,728`。論文表記は`Traffic network size: |V| nodes, |E| directed edges`とし、lane数はSUMO固有の補助指標とする。

### 既知の制約

SUMO import warning保持、185 components、routeabilityはsample gate。current CLIはcaller-supplied unique run IDを持つ安全なrebuildを提供しない。

### 未解決の判断

Network stage自体のcurrent acceptance blockerはない。将来の安全なisolated rebuild runnerは未実装。

### 次工程への引渡し

accepted network pointerとSHAをStop Mapping、Routing Baseline、Simulationへ渡す。

## E. 配送先マッピング

### 目的

39,956 Stopsをaccepted SUMO network上のdelivery-permitted edgeへ決定的に対応付ける。

### 現在の状態

`DONE / ACCEPTED AS PART OF NETWORK ACCEPTANCE`。

### 開始条件

scoped Stops、SUMO network、delivery vehicle permissions、deterministic mapping ruleが必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 対象範囲内配送先 | mapping targets | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `AVAILABLE LOCALLY` | 39,956 stops。 |
| 受入済みnetwork | permitted edges | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `ACCEPTED` | authority-bound SHA。 |
| 到達可能edge override | limited mapping fix | [routeable_edge_overrides.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/routeable_edge_overrides.json) | `CURRENT RUN ARTIFACT` | recorded 17-failed-OD cohort fix。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research network acceptance` | mapping count/status表示 | Read-only | 39,956 / 39,956。 |
| `./research network validate` | mappingをauthority chain内で再検証 | Read-only validation | accepted artifactを書き換えない。 |
| `./research routing inputs` | mapped Stopsのhandoff確認 | Read-only | Routing input readiness。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| mapping受入生成器 | [accept_three_tier_network_run.py](05_src/traffic_simulation/network/accept_three_tier_network_run.py) | mapping artifactとacceptance accountingを生成した固定run script。日常実行しない。 |
| 到達可能性修正validator | [validate_three_tier_routeability_fix.py](05_src/traffic_simulation/network/validate_three_tier_routeability_fix.py) | mapping fix後のrouteabilityを検証。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 配送先mapping | stop→edge対応 | [request_stop_mapping.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json) | `ACCEPTED` |
| mapping集計 | mapped/unmapped/distance | network acceptance JSON `/mapping` | `ACCEPTED` |

### 正本・信頼源

current authorityのaccepted runと[network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json)。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| mapping網羅率 | `./research network acceptance` | mapped＝total＝39,956、unmapped＝0 | `PASS` |
| 許可edge mapping | `./research network validate` | delivery-permitted mappingとrouteability gate PASS | `PASS` |

### 受入・DONE条件

全Stops mapped、mapping rate 1.0、delivery permission、primary routeability sample 100/100、network acceptanceに含まれること。

### 来歴

mapping path、coverage、distance statistics、override名、sample countはacceptance JSONに記録。

### 既知の制約

nearest-edge indexはdeterministic edge midpoint方式。routeabilityはall-pairs proofではない。additional non-gating sanity sampleは91/100。

### 未解決の判断

Routing instanceで使用するStop subsetと到達不能組のpolicy。

### 次工程への引渡し

accepted Stop→edge mappingをRouting Baselineの端点定義へ渡す。

## F. ネットワーク受入

### 目的

Network Construction、SUMO validity、Stop Mapping、routeabilityを研究利用可能な一つのaccepted stateへ束ねる。

### 現在の状態

`ACCEPTED / DONE`。

### 開始条件

SUMO build、lane/speed/permission/connectivity、mapping、routeability validationが完了していること。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 正本pointer | accepted run resolution | [current authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | run/network/SHAを固定。 |
| 受入成果物 | formal gate state | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) | `ACCEPTED` | `FORMAL_NETWORK_ACCEPTED=true`。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research network acceptance` | accepted flags/gates表示 | Read-only | primary inspection。 |
| `./research network validate` | authorityから全accepted gate再検証 | Read-only validation | current stateを変更しない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 正本validator | [validate_current_network_completion_authority.py](05_src/traffic_simulation/network/validate_current_network_completion_authority.py) | path、SHA、flag整合性。 |
| Portal・network validator | [validate_research_map_portal.py](05_src/traffic_simulation/network/validate_research_map_portal.py) | accepted metricsとcurrent display整合性。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 受入JSON | formal accepted state | `.../run_2/network_acceptance.json` | `ACCEPTED` |
| 現行正本 | stable pointer | `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml` | `CURRENT` |

### 正本・信頼源

acceptance結果はacceptance JSON、current選択はauthority pointer。Portalや本書はacceptance authorityではない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 正式flag | `./research network acceptance` | `FORMAL_NETWORK_ACCEPTED=true` | `PASS` |
| 主要routeability | same | deterministic 100 pairs、100 routeable | `PASS` |
| SHA紐付け | `./research network validate` | `4625dbbc…e40f`一致 | `PASS` |

### 受入・DONE条件

acceptance artifact存在、all prior gates PASS、formal flag true、authority pointerとSHA一致。

### 来歴

Decision ID、network ID、source commit、source input SHA、network semantic SHA、SUMO versionをacceptance JSONに記録。

### 既知の制約

routeability acceptanceはsample-based。additional sanity sampleは非gatingで91/100。これをcurrent failureへ昇格しないが、all-pairs保証とも表現しない。

### 未解決の判断

なし（current acceptance scope内）。

### 次工程への引渡し

accepted network、mapping、known limitationsをRouting Baselineへ渡す。

## G. 経路計算ベースライン

### 目的

選択したdelivery instanceに必要なtravel-time cost、distance cost、routeability、routing provenanceを固定する。

### 現在の状態

`NEXT / NOT IMPLEMENTED / NOT YET PRODUCTION COMPLETE`。Network prerequisiteは`PASS`。

### 開始条件

accepted network、accepted Stop mapping、Requests / Stops、および採択済みrouting scope/depot/vehicle class/cost definition。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 受入済みnetwork | routing graph | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `READY` | SHA-bound。 |
| ネットワークグラフ規模 | graph traversal substrate scale | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) `/validation/counts` | `READY` | Nodes 70,050 / directed edges 147,168 / lanes 154,728。 |
| 受入済みmapping | route endpoints | [request_stop_mapping.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json) | `READY` | full Stops mapping。 |
| リクエスト | demand records | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv` | `READY LOCALLY` | instance scope未選択。 |
| 配送先 | candidate delivery endpoints | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `READY LOCALLY` | 39,956 all-pairsを前提にしない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research routing inputs` | available inputsと未決定事項表示 | Read-only | 現在の主inspection。 |
| `./research routing status` | stage/runner/artifact状態表示 | Read-only | `NEXT`。 |
| `./research routing build --dry-run` | missing decisions/runner表示 | Read-only | production buildは拒否。 |
| `./research routing validate --dry-run` | missing artifact/validator表示 | Read-only | validationは未実装。 |
| `./research pipeline routing --dry-run` | inputs→build→validation gateをinspection | Read-only | artifactを作らない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI準備状況制御 | [routing.py](05_src/research_cli/routing.py) | input/gate表示、未実装build拒否。 |
| 本番routing runner | — | `NOT IMPLEMENTED` |
| 本番routing validator | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 所要時間cost | required OD travel-time | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| 距離cost | required OD distance | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| 経路到達可能性 | required OD feasibility | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| 経路計算来歴 | method/version/command/input hashes | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |

### 正本・信頼源

current stage/decision boundaryは[Research Overview Stage 1](RESEARCH_OVERVIEW.md#stage-1--routing-baseline-next)と[Portal map](reproducibility/config/research_portal/research_map_v1.yml)。production routing authorityは`NOT AVAILABLE`。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| ネットワーク前提条件 | `./research routing inputs` | accepted network/mapping READY | `PASS` |
| 経路計算成果物validator | `./research routing validate --dry-run` | method fixed、required OD complete、routeability/provenance valid | `NOT AVAILABLE` |

### 受入・DONE条件

routing method/scope fixed、必要OD集合のみを完全生成、validator PASS、input/output hashと再現commandを保存し、downstream利用をacceptすること。

### 来歴

将来artifactにnetwork SHA、mapping/input hashes、method/version、vehicle class、OD scope、command、runtimeを記録する必要がある。現時点では`NOT AVAILABLE`。

### 既知の制約

ネットワークグラフ規模（`|V|`ノード・`|E|`有向edge・lane数）と経路計算負荷（origin・destination・必要OD pair）、さらに配送インスタンス規模（request・stop・vehicle・instance route pair）は、別々の問題規模である。39,956配送先の全組合せは採択しておらず、`routing_origin_count`、`routing_destination_count`、`required_od_pair_count`は`NOT YET AVAILABLE`。sample routeability acceptanceは本番routing cost成果物ではない。

### 未解決の判断

routing scope、depot、delivery vehicle class、routing cost definition、unreachable pair policy、artifact/schema/provenance contract。

### 次工程への引渡し

validated required-OD cost/routeability artifactをCommon Delivery Instanceへ渡す。

## H. 共通配送インスタンス

### 目的

需要、Stops、depot、routing costs、vehicle/battery constraintsをsolver-independentな共通問題へ凍結する。

### 現在の状態

`PLANNED / NOT IMPLEMENTED / NOT AVAILABLE`。Portal execution positionは`PLANNED`。

### 開始条件

validated Routing Baseline、resolved depot/fleet size/vehicle capacity/battery parameters、adopted schemaが必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| リクエスト・配送先 | common demand | current local paths | `AVAILABLE LOCALLY` | subset rule未確定。 |
| 経路計算baseline | matrices/feasibility | path未定 | `NOT AVAILABLE` | blocking input。 |
| 比較protocol | design constraint | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | common inputs/evaluatorを要求。 |
| EVプロファイル | candidate fixed model assumption | [managed_urban_ev_delivery_v1.yml](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml) | `CURRENT MODEL ASSUMPTION` | fleet/battery instance acceptanceではない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research instance status` | missing validator/upstream/artifact表示 | Read-only | current module pathはMISSING。 |
| `./research instance build --dry-run` | missing inputs/generator表示 | Read-only | no artifact。 |
| `./research instance validate --dry-run` | missing validator/artifact表示 | Read-only | no acceptance。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [instance.py](05_src/research_cli/instance.py) | current absenceを明示。 |
| `common_delivery_instance.py` | `05_src/optimization/common_delivery_instance.py` | `NOT AVAILABLE` in current checkout |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| インスタンスschema | solver-independent contract | path未定 | `EXPECTED / NOT AVAILABLE` |
| 本番インスタンス | frozen common problem | path未定 | `EXPECTED / NOT AVAILABLE` |
| 検証・受入 | completeness/feasibility/hash | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 2 roadmapとcomparison protocolが設計参照。production authority、schema、accepted artifactは存在しない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| インスタンスvalidator | `./research instance validate --dry-run` | schema fixed、placeholderなし、hash/feasibility PASS | `NOT AVAILABLE` |

### 受入・DONE条件

schema、generator、validatorがcurrent checkoutに存在し、validated routingとresolved constraintsからreproducible production instanceを生成・acceptすること。

### 来歴

将来はRequests/Stops/routing/config hashes、node ordering、vehicle/constraint version、generation commandを保存する。

### 既知の制約

過去候補はroadmap上のreview materialでありcurrent implementationではない。fixed EV profileだけでCommon Instance成立とはしない。

### 未解決の判断

contract復元/改訂/置換、depot、fleet size、capacity、battery/energy semantics、instance scope。

### 次工程への引渡し

accepted common instanceをClassical OptimizationとQUBOへ同一入力として渡す。

## I. 古典最適化

### 目的

量子手法と比較するclassical baselineを、共通instance・共通feasibility/evaluator上で確立する。

### 現在の状態

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED`。production solver/resultなし。

### 開始条件

accepted Common Delivery Instance、fixed formulation/objective/constraints、solver budget、seed、correctness fixtures。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 共通配送インスタンス | solver input | path未定 | `NOT AVAILABLE` | blocking。 |
| 比較protocol | fairness boundary | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | solver実装ではない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research optimization classical status` | upstream/solver状態表示 | Read-only | no result。 |
| `./research optimization classical run --dry-run` | missing solver/upstream表示 | Read-only | production run拒否。 |
| `./research optimization classical validate --dry-run` | missing result/validator表示 | Read-only | no acceptance。 |
| `./research pipeline optimization --dry-run` | instance→classical→validation inspection | Read-only | partial orchestration。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [optimization.py](05_src/research_cli/optimization.py) | missing production solverを明示。 |
| 本番定式化・solver | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 数理定式化 | adopted objective/constraints | path未定 | `EXPECTED / NOT AVAILABLE` |
| 古典解 | raw/repaired feasible solution | path未定 | `EXPECTED / NOT AVAILABLE` |
| 検証Evidence | small-instance correctness | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 3 roadmapとcomparison protocolのみ。production Decision/config/result/acceptanceは`NOT AVAILABLE`。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 古典解法の正当性 | `./research optimization classical validate --dry-run` | fixtures、feasibility、objective、result provenance PASS | `NOT AVAILABLE` |

### 受入・DONE条件

formulation固定、solver実装、small-instance correctness PASS、production baseline生成、common evaluatorで検証・accept。

### 来歴

将来はinstance hash、solver/version、budget、seed、raw/repaired output、runtime boundariesを保存する。

### 既知の制約

exact objective、algorithm、fleet parameters、budgetは未採択。fake solver/objective/resultを置かない。

### 未解決の判断

optimizer algorithm、mathematical formulation、budget、seed set、correctness threshold。

### 次工程への引渡し

validated classical baselineをQUBO equivalence、Classical-vs-QAOA comparison、Delivery Simulationへ渡す。

## J. QUBO

### 目的

固定済みclassical problemを検証可能なQUBOとencoder/decoder契約へ写像する。

### 現在の状態

`PLANNED / FUTURE / NOT IMPLEMENTED`。formulation、builder、artifact、validatorなし。

### 開始条件

accepted Common Delivery Instance、fixed Classical formulation、small exact instances、adopted penalties/scaling。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 共通インスタンス | variable/data source | path未定 | `NOT AVAILABLE` | blocking。 |
| 古典定式化・最適値 | equivalence reference | path未定 | `NOT AVAILABLE` | blocking。 |
| 比較protocol | fairness/output accounting | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | QUBO仕様ではない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research quantum status` | QUBO/QAOA state表示 | Read-only | QUBO planned。 |
| `./research quantum qubo build --dry-run` | missing formulation/builder表示 | Read-only | no QUBO。 |
| `./research quantum qubo validate --dry-run` | missing equivalence inputs表示 | Read-only | no validation。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [quantum.py](05_src/research_cli/quantum.py) | unimplemented stateを返す。 |
| QUBO生成器・validator | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| QUBO定式化 | variables/objective/penalties/scaling | path未定 | `EXPECTED / NOT AVAILABLE` |
| encoder・decoder contract | instance↔binary mapping | path未定 | `EXPECTED / NOT AVAILABLE` |
| 等価性report | QUBO vs exact classical | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 4A/4B roadmapのみ。current QUBO authorityは存在しない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| QUBO等価性 | `./research quantum qubo validate --dry-run` | small-instance optimum、decode、feasibility一致 | `NOT AVAILABLE` |

### 受入・DONE条件

versioned formulation/contract、penalty rationale、builder、exact fixtures、equivalence validatorがPASS。

### 来歴

将来はclassical/instance hashes、coefficient scaling、penalties、builder version、decoded solutionを保存する。

### 既知の制約

low energyだけではequivalenceを示さない。QUBO係数・penaltyを推測しない。

### 未解決の判断

encoding、penalty values、scaling、constraint representation、acceptance tolerances。

### 次工程への引渡し

validated QUBOとdecoder/feasibility contractをQAOAへ渡す。

## K. QAOA

### 目的

validated QUBOを明示したbackend・sampling・decode/repair規則で実行し、classical baselineと公平に比較可能な候補解を作る。

### 現在の状態

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED`。quantum hardware executionも`NOT IMPLEMENTED`。

### 開始条件

validated QUBO、adopted backend/depth/optimizer/shots/seeds、decode/repair、measurement boundary。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 検証済みQUBO | quantum problem | path未定 | `NOT AVAILABLE` | blocking。 |
| 古典baseline | comparison reference | path未定 | `NOT AVAILABLE` | blocking。 |
| 比較protocol | fairness | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | Aer結果はquantum advantageを示さない。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research quantum qaoa run --dry-run` | missing QUBO/runner表示 | Read-only | no circuit/result。 |
| `./research quantum compare --dry-run` | common validated results不足表示 | Read-only | no comparison。 |
| `./research quantum status` | quantum stage inspection | Read-only | hardware未実装も表示。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [quantum.py](05_src/research_cli/quantum.py) | execution refusal/state表示。 |
| QAOA runner・比較器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 量子候補解 | samples/parameters/raw solution | path未定 | `EXPECTED / NOT AVAILABLE` |
| decode・repair済み解 | common feasibility format | path未定 | `EXPECTED / NOT AVAILABLE` |
| 比較Evidence | quality/feasibility/runtime/resources | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 4C/4D roadmapとcomparison protocolのみ。backend/result acceptanceはない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| QAOA結果検証 | — | reproducible config、decode、common checker PASS | `NOT AVAILABLE` |
| 古典・量子比較 | `./research quantum compare --dry-run` | same instance/budget/evaluator | `NOT AVAILABLE` |

### 受入・DONE条件

validated QUBOのみを入力し、backend/config/seedを固定、raw/repaired結果を保存、common checkerとcomparison protocolに合格。

### 来歴

将来はbackend type/version、depth、optimizer、shots、seeds、circuit/resource counts、decode/repair timeを保存する。

### 既知の制約

Qiskit Aerはquantum hardwareではない。quantum advantageを前提・主張しない。

### 未解決の判断

depth、optimizer、shots、backend、hardware assumption、budget、repair rules。

### 次工程への引渡し

validated plan candidatesをDelivery Simulationとmethod comparisonへ渡す。

## L. シナリオ構築

### 目的

baselineを上書きせず、future demand、EV technology、optimization/quantum capabilityを分離したversioned scenario inputへする。

### 現在の状態

`PLANNED / NOT IMPLEMENTED`。EV profileは`CURRENT FIXED MODEL ASSUMPTION`だが、accepted future scenario parameterizationではない。

### 開始条件

accepted baseline、evidence-backed parameter sources、scenario scope/year、transformation rules、pre-registered combinations。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 基準需要config | baseline comparator | [baseline_demand.yml](reproducibility/config/traffic_simulation/baseline_demand.yml) | `CURRENT` | future valuesで上書きしない。 |
| EV車両profile | fixed model assumption | [managed_urban_ev_delivery_v1.yml](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml) | `CURRENT ASSUMPTION` | measured real vehicleではない。 |
| 将来scenario roadmap | planned dimensions/gates | [Research Overview Stage 5](RESEARCH_OVERVIEW.md) | `PLANNED` | year/rates未固定。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research demand future` | future demand availability表示 | Read-only refusal | returns `NOT IMPLEMENTED`。 |
| `./research demand build --dry-run` | baseline/future build boundary inspection | Read-only | scenario生成なし。 |
| `./research quantum status` | quantum capability stage state | Read-only | capability scenarioを生成しない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| EV profile schema・config | [managed vehicle profile schema](reproducibility/config/traffic_simulation/schemas/managed_vehicle_profile.schema.json) | current vehicle assumption contract。 |
| 将来需要・scenario生成器 | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 技術scenario config | EV/optimization capability ranges | path未定 | `EXPECTED / NOT AVAILABLE` |
| 需要scenario config | year/total/spatial transformation | path未定 | `EXPECTED / NOT AVAILABLE` |
| 組合せregistry | pre-registered comparisons | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 5 roadmapがdesign authority。adopted production scenario authorityは`NOT AVAILABLE`。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| EV profile schema test | no dedicated `./research` command | profile schema semantics valid | component exists; not scenario acceptance |
| 将来scenario validator | — | source/range/transformation/baseline separation PASS | `NOT AVAILABLE` |

### 受入・DONE条件

scenario parameters、sources、scope/year、transformation、baseline comparison、combinationsをversion化しvalidator PASS。

### 来歴

将来はexternal evidence IDs、parameter range、transformation code/config hash、scenario versionを保存する。

### 既知の制約

vehicle profileのpayload等をactual fleet値とみなさない。future demandやquantum capabilityを現在値として扱わない。

### 未解決の判断

scenario year、demand growth/spatial change、EV battery ranges、optimization/quantum capability assumptions。

### 次工程への引渡し

accepted scenario configをscenario-specific Requests/Stops、Common Instance、Optimization、Simulationへ渡す。

## M. 配送シミュレーション

### 目的

accepted network/scenario上でvalidated delivery plansを実行し、planとrealized model behaviorを分離して記録する。

### 現在の状態

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED / NOT PRODUCTION COMPLETE`。

### 開始条件

accepted network、Common Instance、validated plans、accepted scenarios/traffic config、seeds、plan-to-SUMO conversion contract。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 受入済みnetwork | SUMO environment | current authority resolves | `READY` | network validation simulationとは別。 |
| 検証済みplan | delivery execution plan | path未定 | `NOT AVAILABLE` | blocking。 |
| シナリオconfig | technology/demand conditions | path未定 | `NOT AVAILABLE` | blocking。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research simulation status` | production readiness表示 | Read-only | traffic/network validation simulationsを除外。 |
| `./research simulation run --dry-run` | missing runner/plan表示 | Read-only | no simulation。 |
| `./research simulation validate --dry-run` | missing result/validator表示 | Read-only | no acceptance。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [simulation.py](05_src/research_cli/simulation.py) | delivery simulation不在を明示。 |
| 本番配送runner・validator | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| シミュレーションrun | realized routes/times/SOC/completions/failures | path未定 | `EXPECTED / NOT AVAILABLE` |
| run manifest | plan/scenario/network/seed hashes | path未定 | `EXPECTED / NOT AVAILABLE` |
| 検証report | execution/failure accounting | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 6 roadmapと[V&V reference](05_src/traffic_simulation/20260730_20260903_simulation_model_development_and_vv.md)。production run authorityなし。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 配送simulation validator | `./research simulation validate --dry-run` | reproducible plan conversion、run/failure accounting PASS | `NOT AVAILABLE` |

### 受入・DONE条件

accepted inputsからreproducible runを生成し、plan/run provenance、completion/failure accounting、validator、acceptanceを満たす。

### 来歴

将来はnetwork/plan/instance/scenario hashes、SUMO/software versions、seed、command、run manifestを保存する。

### 既知の制約

current repoのnetwork/traffic validation runsは本研究のproduction delivery simulation resultではない。

### 未解決の判断

plan conversion、traffic scenario、seed set、completion/failure event schema、output/acceptance paths。

### 次工程への引渡し

validated simulation outcomesをEvaluationへ渡す。

## N. 評価

### 目的

validated simulation outputからprimary fulfillment metricとauxiliary diagnosticsを共通定義で算出する。

### 現在の状態

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED`。式はcurrent research designだがcanonical evaluatorとformal metric artifactはない。

### 開始条件

validated Delivery Simulation、fixed denominator population/time horizon/exclusions、metric schema、fixtures。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 指標設計 | primary formula | [Research Overview Stage 7](RESEARCH_OVERVIEW.md) | `CURRENT RESEARCH DESIGN / NEEDS FORMALIZATION` | denominator scope unresolved。 |
| 基準需要仕様 | demand/P_eq semantics | [baseline demand and comparator](05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md) | `CURRENT_NORMATIVE` | metric priority documentation conflict remains. |
| シミュレーション結果 | evaluator input | path未定 | `NOT AVAILABLE` | blocking。 |

主要な研究設計：

```text
delivery_fulfillment_rate
  = delivered_parcel_equivalent / total_parcel_equivalent
```

補助指標には、配送済み・未配送parcel-equivalent、車両稼働率、所要時間、距離、電池使用量、到達不能需要を含む。これらを主要指標と混同しない。

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research evaluate status` | formula/evaluator/denominator状態表示 | Read-only | formalization gapを表示。 |
| `./research evaluate fulfillment --dry-run` | missing evaluator/input/scope表示 | Read-only | metricを計算しない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| CLI安全制御 | [evaluate.py](05_src/research_cli/evaluate.py) | missing evaluatorを明示。 |
| 正本evaluator | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 主要指標 | delivery fulfillment rate | path未定 | `EXPECTED / NOT AVAILABLE` |
| 補助指標 | cause/resource diagnostics | path未定 | `EXPECTED / NOT AVAILABLE` |
| 評価manifest | definitions/input hashes/aggregation | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

current roadmapがprimary designを示すが、formal metric schema/evaluator/acceptanceは`NOT AVAILABLE`。本書は式をnormative化しない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 充足率evaluator | `./research evaluate fulfillment --dry-run` | formula/unit/scope/denominator/exclusions/aggregation fixtures PASS | `NOT AVAILABLE` |

### 受入・DONE条件

metric contract、denominator/time horizon、exclusion policyを固定し、canonical evaluator/fixtures PASS、result再現、uncertainty/failure decomposition保存。

### 来歴

将来はsimulation hash、metric version、scope、denominator、exclusions、aggregation、evaluator versionを保存する。

### 既知の制約

fulfillment resultは未算出。`P_eq`とfulfillment rateのpriority差がlegacy Portal registry上の未解決documentation conflictとして残る。

### 未解決の判断

denominator scope、time horizon、unreachable/excluded demand treatment、primary/auxiliary metric contract。

### 次工程への引渡し

validated metrics、uncertainty、failure decompositionをInterpretationとSensitivityへ渡す。

## O. エビデンスに基づく解釈

### 目的

直接分析境界`Delivery Fulfillment`の外側を、独立Evidenceに基づく条件付きinterpretationとして接続する。計算pipelineではない。

### 現在の状態

Evidence modelは`CURRENT / IMPLEMENTED`、overall assessmentは`SUPPORTED_WITH_CONDITIONS`。研究resultに適用する段階は`FUTURE / NOT AVAILABLE`。

### 開始条件

一般的interpretation設計の閲覧にはEvidence artifactのみ必要。研究結果の解釈にはvalidated fulfillment result、scenario、uncertainty、sensitivityが必要。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| 解釈Evidence | claims/sources/boundaries | [fleet_capacity_interpretation_v1.yml](reproducibility/evidence/fleet_capacity_interpretation_v1.yml) | `CURRENT` | network authorityとは分離。 |
| エビデンスschema | status/traceability contract | [fleet_capacity_interpretation_v1.schema.json](reproducibility/evidence/fleet_capacity_interpretation_v1.schema.json) | `CURRENT` | source verification debtを保持。 |
| 充足率結果 | study-specific direct metric | path未定 | `NOT AVAILABLE` | result interpretationは未実行。 |

解釈経路：

```text
技術・最適化
  → 配送充足
════════ 直接分析の境界 ════════
  → 未充足配送需要
  → 潜在的な実効配送能力要件
  → フリート増強・更新の潜在的必要性
```

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research portal status` | boundary/assessment表示 | Read-only | resultを生成しない。 |
| `./research portal check` | Evidence schema/state/traceability検証 | Read-only validation | research calculationなし。 |
| `./research artifacts` | Evidence artifact/schema path表示 | Read-only | source metadata inspection入口。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| エビデンスvalidator | [validate_fleet_interpretation_evidence.py](05_src/traffic_simulation/validation/validate_fleet_interpretation_evidence.py) | schema/status/source refs/index separation検証。 |
| Portal状態・UI | [serve.py](research_portal/serve.py) | artifactからnode/panel/traceability生成。 |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| エビデンスmodel | reusable interpretation design | `reproducibility/evidence/fleet_capacity_interpretation_v1.yml` | `AVAILABLE` |
| Portal Evidence状態 | node/link/source status | `/api/state` | runtime `AVAILABLE` |
| 研究固有の解釈 | evaluated resultへのbounded claim | path未定 | `NOT AVAILABLE` |

### 正本・信頼源

Evidence artifactがinterpretation source。roleは`INTERPRETATION_ONLY`でありFormal Network acceptance chainを変更しない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| Evidence成果物・schema | `./research portal check` | 5 nodes/5 links、status/source refs/index separation valid | `PASS` |
| 解釈結果trace | — | claim→metric→scenario→Evidence追跡可能 | `NOT AVAILABLE` |

### 受入・DONE条件

Evidence designはvalidator PASS。study-specific interpretationのDONEにはvalidated evaluation/sensitivityと、各claimのresult/Evidence traceが必要。

### 来歴

Evidence ID、source verification status、claim/link status、artifact/schema pathをEvidence artifactとrepository indexに記録。

### 既知の制約

required additional vehicle count、fleet sizing optimization、investment amount、actual corporate investment predictionは`OUT OF SCOPE`。unserved demandはvehicle shortageと同義ではない。

### 未解決の判断

10 sourceの完全bibliographic metadataが`NEEDS_SOURCE_VERIFICATION`。study-specific result interpretationはupstream未完了。

### 次工程への引渡し

bounded claimsとconditionsをSensitivity / Robustnessおよび最終publication claim traceへ渡す。

## P. 感度・頑健性

### 目的

重要仮定を事前登録範囲で変化させ、結論をrobust、conditional、insufficient evidenceへ分類する。

### 現在の状態

`PLANNED / NOT IMPLEMENTED`。過去のnetwork-specific sensitivity/pilotを研究全体Stage 10のcurrent resultとして扱わない。

### 開始条件

accepted baseline results、uncertain parameters/ranges、rerun/comparison protocol、claim interpretation。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| Stage 10ロードマップ | required domains/gate | [Research Overview Stage 10](RESEARCH_OVERVIEW.md) | `PLANNED` | routing/network/demand/battery/optimization/QUBO/scenarioを横断。 |
| 受入済みbaseline結果 | comparison anchor | path未定 | `NOT AVAILABLE` | blocking。 |
| 感度分析registry・protocol | preregistered ranges | path未定 | `NOT AVAILABLE` | blocking。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research status` | upstream stage state確認 | Read-only | sensitivity専用commandなし。 |
| `./research pipeline full --dry-run` | closed upstream gates確認 | Read-only | sensitivity runは含まない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| 汎用感度分析runner・validator | — | `NOT IMPLEMENTED` |
| 履歴・network固有pilot | `reproducibility/outputs/...` | `HISTORICAL / NOT CURRENT STAGE 10` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 感度分析matrix | parameter×outcome comparison | path未定 | `EXPECTED / NOT AVAILABLE` |
| 頑健性要約 | robust/conditional/insufficient classification | path未定 | `EXPECTED / NOT AVAILABLE` |
| 失敗境界 | conditions changing conclusions | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 10 roadmapのみ。production sensitivity authorityはない。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 感度分析validator | — | preregistered ranges、complete runs、comparison/accounting valid | `NOT AVAILABLE` |

### 受入・DONE条件

important uncertaintiesをsystematically varyし、missing/failed runsをaccountし、conclusion classificationをtrace可能にする。

### 来歴

将来はbaseline hash、parameter registry、run matrix、seeds、failure accounting、comparison code/versionを保存する。

### 既知の制約

individual network sensitivity evidenceの存在はend-to-end research conclusion robustnessを示さない。

### 未解決の判断

ranges、factorial design、rerun budget、robustness threshold、missing-run policy。

### 次工程への引渡し

robustness classificationとfailure boundariesをPublication / Reproducibility Freezeへ渡す。

## Q. 公開・再現性凍結

### 目的

公開claimに必要なaccepted artifact、config、schema、hash、software version、command、Portal、documentationを一つのfreezeへ束ねる。

### 現在の状態

`FUTURE / NOT IMPLEMENTED`。repository index、current authority、Markdown/link validatorsは現在利用可能な部分機構だが、研究全体freeze/release commandではない。

### 開始条件

公開対象となる全stageのaccepted outputs、validation evidence、claim trace、sensitivity/limitations。

### 正本入力

| 入力 | 役割 | 正本パス | 状態 | 注記 |
|---|---|---|---|---|
| リポジトリ索引 | current cross-reference | [research_repository_index_v17.yml](reproducibility/indexes/research_repository_index_v17.yml) | `CURRENT` | final freeze manifestではない。 |
| 現行正本 | accepted network pointer | [current network authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | Network scopeのみ。 |
| ロードマップ | Stage 11 gate | [Research Overview](RESEARCH_OVERVIEW.md) | `CURRENT` | final inputs未完了。 |

### コマンド

| コマンド | 目的 | 読取/書込 | 注記 |
|---|---|---|---|
| `./research validate` | current authority/index/Portal横断validation | Read-only | final freezeを作らない。 |
| `./research portal check` | current Portal/document/artifact consistency | Read-only validation | final publication acceptanceではない。 |
| `./research artifacts` | current known artifact paths | Read-only | complete publication inventoryではない。 |

### 実装

| 構成要素 | パス | 役割 |
|---|---|---|
| リポジトリ索引validator | [validate_research_repository_index.py](05_src/traffic_simulation/network/validate_research_repository_index.py) | current pointers existence。 |
| Markdown・link validator | [validate_current_markdown_index.py](05_src/traffic_simulation/network/validate_current_markdown_index.py) | current metadata/link/inventory。 |
| 最終凍結・release runner | — | `NOT IMPLEMENTED` |

### 出力

| 出力 | 意味 | 正本パス・パターン | 現在の利用可否 |
|---|---|---|---|
| 現行索引 | present-state navigation | `reproducibility/indexes/` | `AVAILABLE` |
| 最終凍結manifest | all publication claims/artifacts/hashes | path未定 | `EXPECTED / NOT AVAILABLE` |
| 保管・release | immutable publication package | path未定 | `EXPECTED / NOT AVAILABLE` |

### 正本・信頼源

Stage 11のロードマップが将来ゲートを定義する。現行のnetwork凍結機構はNetwork範囲に限定され、研究全体の公開正本は`NOT AVAILABLE`である。

### 検証

| Validator・ゲート | コマンド | 合格条件 | 現在の状態 |
|---|---|---|---|
| 現行相互参照 | `./research validate` | authority/index/Portal PASS | `PASS for current scope` |
| 最終再現性監査 | — | all claims→accepted evidence、links/hashes/env/commands valid | `NOT AVAILABLE` |

### 受入・DONE条件

全公開claimがfrozen accepted evidenceへ追跡可能、reproduction/link audit PASS、versions/commands/hashes固定、Portal/overview/reference一致。

### 来歴

将来freeze manifestにGit commit、artifact hashes、environment/software versions、commands、acceptance IDsを保存する。

### 既知の制約

current indexesとNetwork accepted stateだけでは研究全体のpublication freezeにならない。

### 未解決の判断

freeze manifest schema、archive location、release procedure、claim inventory、final environment lock。

### 次工程への引渡し

publication、submission、archive release。

## 研究コマンド索引

`./research commands`が機械可読情報に近い正本コマンド一覧である。本節では運用上の読取・書込、前提条件、dry-run対応を補足する。全41インターフェースを収録する。

### 全体・確認・検証

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research status` | 研究全体の現在位置を表示 | Portal・現行正本を読取可能 | 状態 | なし | no |
| `./research artifacts` | 現行パスを表示 | 正本・索引を読取可能 | パス一覧 | なし | no |
| `./research commands` | コマンド一覧を表示 | CLIをimport可能 | 41コマンドの索引 | なし | no |
| `./research validate` | 正本・索引・Portalを検証 | 現行成果物 | 検証結果 | なし | yes |

### 需要

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research demand status` | 需要の状態を表示 | 現行Portal node ID | 状態 | なし | no、**現在は終了コード1** |
| `./research demand validate` | 基準需要testとmapping整合性を検証 | ローカルの需要・リクエスト・配送先 | 検証結果 | なし | yes |
| `./research demand build` | 基準需要→リクエスト→配送先を生成 | 安全な統合runner | 成果物 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research demand future` | 将来需要の利用可否を表示 | 採択済みparameter | 状態・拒否理由 | なし | no |

### ネットワーク

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research network status` | 受入済みnetwork状態を表示 | 正本 | 状態・hash | なし | no |
| `./research network acceptance` | 受入状態を確認 | acceptance JSON | ゲート・flag | なし | no |
| `./research network validate` | 受入済みnetworkを検証 | 現行の受入済み成果物 | 検証結果 | なし | yes |
| `./research network build` | 分離されたbuildを実行 | 一意な安全出力runner | run成果物 | 現在はなし、`NOT IMPLEMENTED` | yes |

### 経路計算

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research routing inputs` | 入力・判断事項を表示 | 正本・現行データ | 準備状況 | なし | no |
| `./research routing status` | 工程状態を表示 | 正本 | 状態 | なし | no |
| `./research routing build` | 経路コストを生成 | 採択済み範囲・方式とrunner | 成果物 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research routing validate` | 経路計算を検証 | 本番成果物・validator | 結果 | 現在はなし、`NOT IMPLEMENTED` | yes |

### 共通配送インスタンス

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research instance status` | インスタンス準備状況を表示 | repository | 状態 | なし | no |
| `./research instance build` | 本番インスタンスを生成 | 検証済みrouting・制約・generator | 成果物 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research instance validate` | インスタンスを検証 | 成果物・validator | 結果 | 現在はなし、`NOT IMPLEMENTED` | yes |

### 古典最適化

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research optimization classical status` | 古典最適化の準備状況を表示 | repository | 状態 | なし | no |
| `./research optimization classical run` | 共通インスタンスを解く | 受入済みinstance・solver | 解 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research optimization classical validate` | 解を検証 | 結果・validator | 結果 | 現在はなし、`NOT IMPLEMENTED` | yes |

### QUBO / QAOA

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research quantum status` | 量子工程の状態を表示 | 研究map | 状態 | なし | no |
| `./research quantum qubo build` | QUBOを構築 | 固定済み定式化・instance | QUBO | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research quantum qubo validate` | 等価性を検証 | QUBO・厳密最適値 | 結果 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research quantum qaoa run` | QAOAを実行 | 検証済みQUBO・runner | 候補解 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research quantum compare` | 古典・量子結果を比較 | 検証済み共通結果 | evidence | 現在はなし、`NOT IMPLEMENTED` | yes |

### シミュレーション・評価

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research simulation status` | simulation準備状況を表示 | 研究map | 状態 | なし | no |
| `./research simulation run` | 計画を実行 | 検証済みplan・runner | 結果 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research simulation validate` | simulation結果を検証 | 成果物・validator | 結果 | 現在はなし、`NOT IMPLEMENTED` | yes |
| `./research evaluate status` | 評価準備状況を表示 | 研究map | 状態・式 | なし | no |
| `./research evaluate fulfillment` | 指標を計算 | 検証済みsimulation・evaluator・範囲 | 指標 | 現在はなし、`NOT IMPLEMENTED` | yes |

### ポータル

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research portal status` | Portal・現行状態を表示 | 正本成果物 | 状態 | なし | no |
| `./research portal start` | Portalを起動 | Python依存関係・成果物 | ローカルserver | processのみ、repo変更なし | yes |
| `./research portal check` | 正本・索引・map・Evidenceを検証 | 現行成果物 | 結果 | なし | yes |
| `./research portal build` | 単独handoffを生成 | generator | handoff | 現在はなし、`NOT IMPLEMENTED` | yes |

### 統合実行

| コマンド | 目的 | 前提条件 | 出力 | 変更 | dry-run |
|---|---|---|---|---|---|
| `./research pipeline network` | 受入済みnetworkを再利用・検証 | 受入済みnetwork | 検証 | なし | yes |
| `./research pipeline routing` | 入力→build→検証 | routing判断・runner | 成果物 | 現在はなし、`PARTIAL` | yes |
| `./research pipeline optimization` | instance→古典最適化→検証 | 検証済みrouting | baseline | 現在はなし、`PARTIAL` | yes |
| `./research pipeline portal` | 現行状態を検証 | 正本成果物 | 結果 | なし | yes |
| `./research pipeline full` | 最初の閉じたgateまで実行 | 統制済み上流工程 | 工程要約 | 現在はRoutingで停止、`PARTIAL` | yes |

## 成果物・正本対応表

| 工程 | 判断 | 仕様 | 設定・Registry | スキーマ | 実行・出力 | 受入 | 現行正本 |
|---|---|---|---|---|---|---|---|
| 外部データ | — | 来歴記録 | source registry | source固有 | ローカルraw・派生データ | 利用側工程ごと | source registry＋利用側正本 |
| 需要 | — | 基準需要仕様 | 基準需要config | 組込み・config検証 | ローカルParquet＋品質JSON | 独立した受入なし | config・仕様＋品質要約 |
| リクエスト・配送先 | — | roadmap・設計記録 | ローカルrun要約 | `NOT AVAILABLE` | ローカルCSV | mapping受入のみ | Portal map＋network受入 |
| ネットワーク構築 | Three-tier Decision | Formal Completion＋Pipeline仕様 | Three-tier registry | policy＋record schema | run_2・`three_tier.net.xml` | network acceptance JSON | 現行network正本 |
| 配送先マッピング | Three-tier Decision | Network Pipeline仕様 | 受入済みrun mapping | acceptance構造 | run_2 mapping JSON | network acceptance `/mapping` | 現行network正本 |
| ネットワーク受入 | Three-tier Decision | Network Pipeline仕様 | 正本pointer | policy・record | run_2 | `FORMAL_NETWORK_ACCEPTED=true` | 現行network正本 |
| 経路計算 | `UNRESOLVED` | roadmap Stage 1 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | roadmap・Portal工程のみ |
| 共通インスタンス | `UNRESOLVED` | roadmap Stage 2＋比較protocol | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 古典最適化 | `UNRESOLVED` | roadmap Stage 3＋比較protocol | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| QUBO | `UNRESOLVED` | roadmap Stage 4A/4B | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| QAOA | `UNRESOLVED` | roadmap Stage 4C/4D | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| シナリオ | `UNRESOLVED` | roadmap Stage 5 | EV profile＋baseline config | vehicle profile schema | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計・現行仮定のみ |
| 配送シミュレーション | `UNRESOLVED` | roadmap Stage 6＋V&V参照 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 評価 | `UNRESOLVED` | roadmap Stage 7 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 研究設計のみ |
| 解釈 | Evidence設計 | Evidence成果物 | Evidence成果物 | Evidence schema | Portal状態 | Evidence validator PASS | 解釈専用成果物 |
| 感度分析 | `UNRESOLVED` | roadmap Stage 10 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 設計のみ |
| 公開・再現性凍結 | `UNRESOLVED` | roadmap Stage 11 | repository index（一部） | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | 将来gateのみ |

## 検証対応表

| 工程 | Validator | ゲート | 現在の結果 | 次工程を阻害するか |
|---|---|---|---|---|
| 外部データ | 利用側固有・Demand test | 登録source・hashを利用可能 | 利用可能、統合受入なし | 現行baselineではno |
| 需要 | `demand validate`経由の`test_prepare_baseline_demand.py` | config・source・保存則 | 実行時`PASS` | 現行baselineではno |
| リクエスト・配送先 | `demand validate`経由の正本整合性 | file存在・mapping受入済み | `PASS`、再生成validatorなし | 再現性上の負債 |
| ネットワーク | `network validate`一式 | registry・pipeline・SUMO・属性・接続性 | `PASS` | no |
| 配送先マッピング | network acceptance・Portal validator | 39,956/39,956、許可edge | `PASS` | no |
| ネットワーク受入 | 正本validator | flag true＋SHA一致 | `PASS` | no |
| 経路計算 | 本番routing validator | 必要OD・方式・来歴 | `NOT AVAILABLE` | **yes** |
| 共通インスタンス | 本番instance validator | schema・完全性・実行可能性 | `NOT AVAILABLE` | **yes** |
| 古典最適化 | 正当性・結果validator | 定式化・fixture・結果 | `NOT AVAILABLE` | **yes** |
| QUBO | 等価性validator | 古典・QUBO等価性 | `NOT AVAILABLE` | **yes** |
| QAOA | 共通実行可能性・比較 | 再現可能な候補・共通checker | `NOT AVAILABLE` | **yes** |
| シナリオ | scenario validator | source・範囲・変換 | `NOT AVAILABLE` | **yes** |
| 配送シミュレーション | 本番simulation validator | run・failure・来歴 | `NOT AVAILABLE` | **yes** |
| 評価 | 正本evaluator fixture | 範囲・分母・式 | `NOT AVAILABLE` | **yes** |
| 解釈 | Evidence validator | schema・status・source trace | 設計は`PASS`、結果gateは利用不可 | 結果主張にはyes |
| 感度分析 | sensitivity validator | 事前登録済みmatrix・集計 | `NOT AVAILABLE` | **yes** |
| 公開・再現性凍結 | 最終監査 | 主張・link・hash・環境・command | `NOT AVAILABLE` | 最終gate |

## 依存関係表

| 下流工程 | 必要条件 |
|---|---|
| 需要 | 統制済みopen-data source＋baseline config・仕様 |
| リクエスト・配送先 | 検証済みbaseline需要＋生成・範囲contract |
| 配送先マッピング | 配送先＋Formal・SUMO network＋vehicle permission |
| ネットワーク受入 | SUMO validity＋mapping＋主要routeability gate |
| 経路計算 | 受入済みnetwork＋受入済みmapping＋リクエスト・配送先＋解決済みscope・depot・vehicle・cost |
| 共通インスタンス | 検証済みrouting＋需要・配送先＋depot・fleet・capacity・battery制約 |
| 古典最適化 | 受入済み共通インスタンス＋固定済み定式化・checker・budget |
| QUBO | 受入済み共通インスタンス＋固定済み古典定式化＋厳密解fixture |
| QAOA | 検証済みQUBO＋採択済み実行・decode protocol |
| シナリオ | 受入済みbaseline＋Evidenceに基づくparameter・年・変換 |
| シミュレーション | 受入済みnetwork・instance・scenario＋検証済み配送plan |
| 評価 | 検証済みsimulation＋固定済み指標分母・範囲 |
| 解釈 | 検証済み評価＋scenario・不確実性＋Evidence成果物 |
| 感度分析 | 受入済みbaseline結果＋事前登録済み不確実範囲・protocol |
| 公開・再現性凍結 | 主張対象の全工程を受入済み＋主張・Evidence trace＋再現性監査 |

## 現行ライフサイクル境界

- `CURRENT / ACCEPTED`: Three-tier Formal Completion、run_2 network、mapping、network acceptance。
- `CURRENT DESIGN`: baseline demand spec/config、comparison protocol、EV profile assumption、interpretation Evidence。
- `HISTORICAL`: strict v17、old run_4/run_5/run_6、old blockers/failures、temporary diagnostics。
- `SUPERSEDED`: Hierarchical Hybrid Decisionとpre-Three-tier pipeline policies。
- historical/superseded artifactsをcurrent command inputまたはcurrent acceptanceとして再利用しない。

## 文書の役割分担

`RESEARCH_OVERVIEW.md` = 研究概要・ロードマップ

`RESEARCH_PIPELINE_REFERENCE.md` = 現行パイプラインの実行・正本・検証リファレンス
