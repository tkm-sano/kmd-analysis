# Current Research Pipeline Execution / Authority / Validation Reference

文書ID: `DOC-RESEARCH-PIPELINE-REFERENCE`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/indexes/research_repository_index_v17.yml`

状態: `CURRENT PIPELINE REFERENCE`

本書は、各研究工程の「実行 → artifact → 正本 → 検証 → acceptance → 次工程」を追跡する現行運用リファレンスである。研究の問い、概念枠組み、Stage 1–11 roadmap、milestoneは[Research Overview / Roadmap](RESEARCH_OVERVIEW.md)を参照する。本書は各Decision、仕様、config、schema、run、acceptance artifactへのindexであり、それらを置き換える第二の正本ではない。記載とcanonical artifactが矛盾する場合は、各sectionのAuthority / Source of truthに示すartifactを優先する。

## Update policy

次の場合に本書を更新する。

- current stage、immediate next task、またはmilestoneが変わる。
- production pipeline、artifact、validator、acceptance、CLI commandが追加・変更される。
- canonical input/output、authority pointer、schema、gate、handoffが変わる。
- stageがacceptedまたはDONEになる。

historical diagnostic runや一時的experiment outputは、current/canonicalへ採択されない限り本書のcurrent pathwayへ追加しない。更新時は本書専用validatorとrepository/Portal validatorを実行する。

## Status semantics

| Status | Meaning |
|---|---|
| `CURRENT / IMPLEMENTED` | current checkoutに実装または参照が存在する。 |
| `ACCEPTED` | acceptance artifactによって下流利用が許可されている。 |
| `DONE` | current roadmap上の完了条件を満たしている。 |
| `NEXT` | 現在着手すべきstage。 |
| `PLANNED` | roadmapにあるが完了していない。 |
| `FUTURE` | upstream gateが閉じている将来stage。 |
| `NOT IMPLEMENTED` | production code、runner、またはvalidatorが存在しない。 |
| `NOT AVAILABLE` | 必要artifactまたは結果が存在しない。 |
| `UNRESOLVED` | 研究判断またはparameter固定が必要。 |
| `HISTORICAL` | 過去の記録でcurrentではない。 |
| `SUPERSEDED` | 明示的に後継へ置換された。 |

command interfaceの存在はpipeline実装を意味しない。`--dry-run`が成功してもartifactの生成・validation・acceptanceを意味しない。

## Current Research Position — 今何をすべきか

| Item | Current state |
|---|---|
| Network Construction | `DONE` |
| Network Acceptance | `ACCEPTED` / `FORMAL_NETWORK_ACCEPTED = true` |
| Current milestone | `M1 Network Ready — DONE` |
| Current research stage | `Routing Baseline — NEXT` |
| Immediate next task | Define routing scope for delivery instances. |
| Accepted network SHA-256 | `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| First decision work | instance selection/Stop scope、depot、delivery vehicle class、routing cost definitionを固定する。 |

最初に次を使用する。

```bash
./research status
./research routing inputs
./research routing status
./research pipeline routing --dry-run
```

`39,956 × 39,956`のfull all-pairs matrixは採択済み前提ではない。対象delivery instanceと必要OD集合を先に定義する。

## Pipeline Map

```text
External / Open Data                         [DONE]
  ├─→ Baseline Demand                       [DONE]
  │     ↓
  │   Requests / Stops                      [DONE; local generated artifacts]
  └─→ Network Construction                  [DONE]
          ↓
        Stop Mapping                        [DONE]
          ↓
        Network Acceptance                  [ACCEPTED]
          ↓
        Routing Baseline                    [NEXT / NOT IMPLEMENTED]
          ↓
        Common Delivery Instance            [PLANNED / NOT IMPLEMENTED]
          ↓
        Classical Optimization              [PLANNED / NOT IMPLEMENTED]
          ↓
        QUBO                                [PLANNED / NOT IMPLEMENTED]
          ↓
        QAOA                                [FUTURE / NOT IMPLEMENTED]
          ↓
        Scenario Construction               [PLANNED / NOT IMPLEMENTED]
          ↓
        Delivery Simulation                 [PLANNED / NOT IMPLEMENTED]
          ↓
        Evaluation                          [PLANNED / NOT IMPLEMENTED]
          ↓
        Evidence-Supported Interpretation   [CURRENT EVIDENCE DESIGN / NO RESULT]
          ↓
        Sensitivity / Robustness             [PLANNED / NOT IMPLEMENTED]
          ↓
        Publication / Reproducibility Freeze [FUTURE / NOT IMPLEMENTED]
```

Roadmapの`PLANNED`とPortal execution mapの`FUTURE`が異なる下流stageでは、本書は`PLANNED / FUTURE / NOT IMPLEMENTED`と併記する。`PLANNED`は研究計画上の存在、`FUTURE`は現在の実行位置、`NOT IMPLEMENTED`はproduction実装の不在を表す。

## A. External / Open Data

### Purpose

入力sourceのidentity、取得元、取得日、hash、用途、利用制限を固定し、DemandとNetworkの派生処理へ渡す。

### Current status

`DONE`（governed source inputs）。datasetごとのreadinessと再配布可否は同一ではない。

### Entry conditions

sourceを台帳登録し、取得記録・local raw path・hash・利用条件を確認する。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Source registry | source identity / hash | [traffic_simulation_sources.csv](03_data/metadata/traffic_simulation_sources.csv) | `CURRENT` | sourceごとの用途・制限を記録。 |
| Provenance policy | raw/derived provenance | [data_provenance.md](03_data/metadata/data_provenance.md) | `CURRENT` | raw原本の一部は再配布されない。 |
| Acquisition records | source-specific acquisition evidence | [acquisition README](03_data/metadata/acquisition/README.md) | `CURRENT` | 個別記録から取得条件を追跡する。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research artifacts` | current input/artifact path確認 | Read-only | dataset内容の再取得・検証は行わない。 |
| `./research demand validate` | Demand consumer側からsource/config整合性を検証 | Read-only validation | source全体のacceptanceではない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Baseline consumer | [prepare_baseline_demand.py](05_src/traffic_simulation/demand/prepare_baseline_demand.py) | 登録sourceをbaseline demandへ変換。 |
| Network source processing | [traffic simulation README](05_src/traffic_simulation/README.md) | source道路表現の処理入口説明。 |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Source metadata | identity/hash/license/provenance | `03_data/metadata/` | `AVAILABLE` |
| Raw source data | acquired originals | `03_data/raw/traffic_simulation/` | dataset-dependent / local |
| Consumer inputs | normalized or derived input | consumer configが指定 | dataset-dependent |

### Authority / Source of truth

Source identityはsource registry、取得事実は個別acquisition record、consumer採択は各pipeline config/acceptanceが正本。本書はsource acceptanceを新設しない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Registry/consumer checks | `./research demand validate` | Demand testと必要current inputが成功 | `AVAILABLE`; source全体gateではない |
| Repository references | `./research portal check` | current path/index/link検証成功 | `PASS` |

### Acceptance / DONE criteria

source identity、hash、取得条件、用途、制限が台帳化され、利用pipelineのvalidatorがsourceを確認できること。Portal roadmap上は`DONE`。

### Provenance

source ID、取得日、URL、SHA-256はsource registryとacquisition recordに記録する。

### Known limitations

raw原本の一部はgit非追跡で再取得が必要。Open Dataは実配送運用を直接表さない。

### Unresolved decisions

future scenarioで採用する追加sourceと変換規則は`UNRESOLVED`。

### Next handoff

登録済みsource IDとhashをDemandまたはNetwork configへ渡す。

## B. Demand

### Purpose

公開統計から大田区500m meshのbaseline populationと`parcel_equivalent/day`需要proxyを生成・検証する。

### Current status

`DONE`（baseline）。safe integrated build runnerは`NOT IMPLEMENTED`。`./research demand status`は現行Portal node ID不一致により現在exit 1。

### Entry conditions

source registry上の人口・宅配便統計、大田区境界、baseline configが利用可能であること。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Demand specification | definition / boundary | [baseline demand and comparator](05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md) | `CURRENT_NORMATIVE` | 実注文・停止ではない。 |
| Demand config | parameters / output paths | [baseline_demand.yml](reproducibility/config/traffic_simulation/baseline_demand.yml) | `CURRENT` | `target_days: 1`、unitは`parcel_equivalent`。 |
| Source registry | governed inputs | [traffic_simulation_sources.csv](03_data/metadata/traffic_simulation_sources.csv) | `CURRENT` | config内source IDを解決。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research demand validate` | baseline implementation test＋accepted mapping consistency | Read-only validation | production demandを再生成しない。 |
| `./research demand build --dry-run` | 不足runner/dependencyを表示 | Read-only | build本体は`NOT IMPLEMENTED`。 |
| `./research demand status` | status表示 | Read-only | **現在失敗**: Portal node ID不一致。 |
| `./research demand future` | future demand利用可否表示 | Read-only refusal | `NOT IMPLEMENTED / UNRESOLVED`。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Baseline builder | [prepare_baseline_demand.py](05_src/traffic_simulation/demand/prepare_baseline_demand.py) | mesh人口・parcel-equivalent配賦。fixed canonical outputのためCLI buildからは実行しない。 |
| Unit tests | [test_prepare_baseline_demand.py](05_src/traffic_simulation/validation/test_prepare_baseline_demand.py) | source/config/配賦不変条件を検証。 |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Baseline demand | 191 meshのpopulation/demand proxy | `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet` | `AVAILABLE LOCALLY / GIT-IGNORED` |
| Quality summary | source/config/output hashesと集計 | `03_data/processed/traffic_simulation/validation/ota_ward_baseline_demand_2024_500m_quality_summary.json` | `AVAILABLE LOCALLY / GIT-IGNORED` |

### Authority / Source of truth

定義はDemand specification、parameter/output pathはbaseline config、実行結果のhash・集計はquality summary。独立したDemand acceptance flagはない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Baseline unit validation | `./research demand validate` | `test_prepare_baseline_demand.py` PASS | `AVAILABLE` |
| Artifact availability | `./research artifacts` | Parquet/configが存在 | `AVAILABLE LOCALLY` |

### Acceptance / DONE criteria

config、builder、unit test、Parquet、quality summaryが存在し、population/demand conservationとhashが確認できること。roadmap/Portalはbaselineを`DONE`とする。

### Provenance

quality summaryにsource SHA、config SHA、output SHA、generated timestampを記録する。

### Known limitations

`82,023 parcel-equivalent/day`は顧客数、request数、stop数ではない。artifactはgit-ignoredでportable publicationではない。仕様文書の「未生成」記述とcurrent artifact存在にはdocumentation lagがある。

### Unresolved decisions

future demandのscenario year、growth rate、spatial transformationは`UNRESOLVED`。

### Next handoff

baseline demand proxyをRequests / Stops生成契約へ渡す。parcel-equivalentを1個1停止へ直接変換しない。

## C. Requests / Stops

### Purpose

合成需要からrequest recordを作り、building単位のdelivery stopへ集約する。request、parcel-equivalent、stopの単位を分離する。

### Current status

`DONE`（current roadmap/Portal、accepted network mappingの入力）。安全なproduction regeneration runnerと専用validatorは`NOT IMPLEMENTED / NOT AVAILABLE`。

### Entry conditions

baseline demand、household/building assignment source、固定seed、scope ruleが必要。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Baseline demand | aggregate demand proxy | `03_data/processed/traffic_simulation/demand/ota_ward_baseline_demand_2024_500m.parquet` | `AVAILABLE LOCALLY` | parcel-equivalent単位。 |
| Request artifact | synthetic request records | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv` | `AVAILABLE LOCALLY` | 73,547 data rows。 |
| Stop generation summary | generation/accounting | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/stop_generation_run_summary.json` | `AVAILABLE LOCALLY` | scoped parcel conservationを記録。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research demand validate` | file availability＋accepted mapping consistency | Read-only validation | request/stop generatorの再現を検証しない。 |
| `./research artifacts` | canonical local paths表示 | Read-only | availability inspection。 |
| `./research demand build --dry-run` | regeneration gap表示 | Read-only | integrated generator不在。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [demand.py](05_src/research_cli/demand.py) | generator不在時にbuildを拒否。 |
| Current generation implementation | — | `NOT AVAILABLE` in current checkout |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Requests | 1行1 synthetic request | `.../pipelines_v1/daily_requests.csv` | `AVAILABLE LOCALLY / GIT-IGNORED` |
| Stops | building集約delivery stop | `.../pipelines_v1/building_delivery_stops_scoped.csv` | `AVAILABLE LOCALLY / GIT-IGNORED`; 39,956 stops |
| Generation summaries | count/conservation/seed/hash | `.../pipelines_v1/*run_summary.json` | `AVAILABLE LOCALLY / GIT-IGNORED` |

### Authority / Source of truth

current pathsはCLI coreとPortal map、下流利用状態はaccepted network authority/acceptanceが参照する。Requests / Stops単独のmachine-readable acceptance artifactは`NOT AVAILABLE`。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Accepted mapping consistency | `./research demand validate` | authority validator PASS、required files存在 | `AVAILABLE` |
| Request/stop regeneration validator | — | deterministic generation＋conservation | `NOT AVAILABLE` |

### Acceptance / DONE criteria

現行roadmapはartifact存在とaccepted stop mappingで`DONE`としている。完全な再現性にはgenerator、schema、専用validator、portable artifact policyが追加で必要。

### Provenance

local run summariesにseed、config hash、input artifact hash、request/stop/parcel accountingを記録。

### Known limitations

baseline 82,023 parcel-equivalent、generated request 73,547 rows、39,956 stopsは異なる単位。scoped stop parcel-equivalentはfull request scopeより小さく、full conservationはfalse、assigned scope conservationのみtrue。

### Unresolved decisions

production regeneration contract、portable publication、future scenario別生成interface。

### Next handoff

Requests、Stops、scope/accountingをStop MappingとRouting scope definitionへ渡す。

## D. Network Construction

### Purpose

source道路表現をThree-tier provenance（DIRECT / INFERRED / FALLBACK）でFormal Networkへ完成し、SUMO `net.xml`へmaterializeする。

### Current status

`DONE / ACCEPTED`。安全な新規isolated end-to-end CLI buildは`NOT IMPLEMENTED`。accepted runを再利用する。

### Entry conditions

current Decision、policy、pipeline、registry/schema、source/structural input lockが必要。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Current authority pointer | authority resolver | [current_network_completion_authority_v17.yml](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | 唯一のcurrent network入口。 |
| Decision | method adoption | [phase13 Formal Completion Decision](reproducibility/config/traffic_simulation/decisions/phase13_formal_completion_three_tier_v1.yml) | `CURRENT` | Decision ID `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`。 |
| Normative specification | Three-tier policy | [formal completion specification](05_src/traffic_simulation/specifications/20260903_20260903_formal_completion_three_tier_policy_v17.md) | `CURRENT_NORMATIVE` | strict/hybridをcurrentへ混ぜない。 |
| Pipeline specification | ordered stages/gates | [network completion pipeline specification](05_src/traffic_simulation/specifications/20260903_20260903_network_completion_pipeline_v17.md) | `CURRENT_NORMATIVE` | SOURCE→…→ACCEPTANCE。 |
| Registry / schemas | machine-readable contract | [Three-tier registry](reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml) | `CURRENT` | policy/record schemasはauthorityから解決。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research network status` | accepted pointer/hash/status表示 | Read-only | 推奨inspection。 |
| `./research network validate` | current accepted networkを全gate検証 | Read-only validation | buildしない。 |
| `./research network acceptance` | acceptance JSON表示 | Read-only | flag/gates/mappingを表示。 |
| `./research network build --dry-run` | unsafe fixed-output limitation表示 | Read-only | build本体は拒否される。 |
| `./research pipeline network` | accepted networkを再利用してvalidate | Read-only validation | accepted runを上書きしない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Three-tier completion | [execute_three_tier_completion_streaming.py](05_src/traffic_simulation/network/execute_three_tier_completion_streaming.py) | accepted build provenance上のcompletion implementation。 |
| Registry validator | [validate_formal_completion_three_tier_registry.py](05_src/traffic_simulation/network/validate_formal_completion_three_tier_registry.py) | policy/registry/schema整合性。 |
| Pipeline validator | [validate_network_completion_pipeline.py](05_src/traffic_simulation/network/validate_network_completion_pipeline.py) | stage ordering/gate contract。 |
| Authority validator | [validate_current_network_completion_authority.py](05_src/traffic_simulation/network/validate_current_network_completion_authority.py) | pointer/hash/acceptance integrity。 |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Accepted run | current run directory | `reproducibility/outputs/.../phase13_20260903_three_tier_completion/run_2` | `ACCEPTED` |
| Accepted network | SUMO network | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `ACCEPTED` |
| Provenance accounting | DIRECT/INFERRED/FALLBACK counts | [quality_accounting.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1/quality_accounting.json) | `CURRENT REFERENCE FROM AUTHORITY` |

### Authority / Source of truth

[current network authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml)がDecision、specification、registry/schema、accepted run/network/acceptance、SHAを解決する。Hierarchical Hybridは`SUPERSEDED`、strict v17と旧runは`HISTORICAL`。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Registry/schema | `./research network validate` | registry/schema validator PASS | `PASS` |
| Pipeline definition | same | current Decision/order/gates一致 | `PASS` |
| SUMO build/attributes/connectivity | same | build、lane、speed、permission、connectivity PASS | `PASS` |
| SHA integrity | same | actual SHA＝authority SHA | `PASS` |

### Acceptance / DONE criteria

all network gates PASS、accepted `net.xml`存在、SHA一致、Stop Mapping/routeability gate PASS、`FORMAL_NETWORK_ACCEPTED=true`。

### Provenance

accepted run ID `three_tier_run_2`、network ID `P13-THREE-TIER-RUN-2`、source commit、input/output SHA、quality accountingをauthority/acceptanceに記録。

### Known limitations

SUMO import warning保持、185 components、routeabilityはsample gate。current CLIはcaller-supplied unique run IDを持つ安全なrebuildを提供しない。

### Unresolved decisions

Network stage自体のcurrent acceptance blockerはない。将来の安全なisolated rebuild runnerは未実装。

### Next handoff

accepted network pointerとSHAをStop Mapping、Routing Baseline、Simulationへ渡す。

## E. Stop Mapping

### Purpose

39,956 Stopsをaccepted SUMO network上のdelivery-permitted edgeへ決定的に対応付ける。

### Current status

`DONE / ACCEPTED AS PART OF NETWORK ACCEPTANCE`。

### Entry conditions

scoped Stops、SUMO network、delivery vehicle permissions、deterministic mapping ruleが必要。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Scoped Stops | mapping targets | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `AVAILABLE LOCALLY` | 39,956 stops。 |
| Accepted network | permitted edges | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `ACCEPTED` | authority-bound SHA。 |
| Routeable overrides | limited mapping fix | [routeable_edge_overrides.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/routeable_edge_overrides.json) | `CURRENT RUN ARTIFACT` | recorded 17-failed-OD cohort fix。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research network acceptance` | mapping count/status表示 | Read-only | 39,956 / 39,956。 |
| `./research network validate` | mappingをauthority chain内で再検証 | Read-only validation | accepted artifactを書き換えない。 |
| `./research routing inputs` | mapped Stopsのhandoff確認 | Read-only | Routing input readiness。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Mapping acceptance builder | [accept_three_tier_network_run.py](05_src/traffic_simulation/network/accept_three_tier_network_run.py) | mapping artifactとacceptance accountingを生成した固定run script。日常実行しない。 |
| Routeability fix validator | [validate_three_tier_routeability_fix.py](05_src/traffic_simulation/network/validate_three_tier_routeability_fix.py) | mapping fix後のrouteabilityを検証。 |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Stop mapping | stop→edge対応 | [request_stop_mapping.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json) | `ACCEPTED` |
| Mapping accounting | mapped/unmapped/distance | network acceptance JSON `/mapping` | `ACCEPTED` |

### Authority / Source of truth

current authorityのaccepted runと[network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json)。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Mapping coverage | `./research network acceptance` | mapped＝total＝39,956、unmapped＝0 | `PASS` |
| Permitted-edge mapping | `./research network validate` | delivery-permitted mappingとrouteability gate PASS | `PASS` |

### Acceptance / DONE criteria

全Stops mapped、mapping rate 1.0、delivery permission、primary routeability sample 100/100、network acceptanceに含まれること。

### Provenance

mapping path、coverage、distance statistics、override名、sample countはacceptance JSONに記録。

### Known limitations

nearest-edge indexはdeterministic edge midpoint方式。routeabilityはall-pairs proofではない。additional non-gating sanity sampleは91/100。

### Unresolved decisions

Routing instanceで使用するStop subsetと到達不能組のpolicy。

### Next handoff

accepted Stop→edge mappingをRouting Baselineの端点定義へ渡す。

## F. Network Acceptance

### Purpose

Network Construction、SUMO validity、Stop Mapping、routeabilityを研究利用可能な一つのaccepted stateへ束ねる。

### Current status

`ACCEPTED / DONE`。

### Entry conditions

SUMO build、lane/speed/permission/connectivity、mapping、routeability validationが完了していること。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Authority pointer | accepted run resolution | [current authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | run/network/SHAを固定。 |
| Acceptance artifact | formal gate state | [network_acceptance.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/network_acceptance.json) | `ACCEPTED` | `FORMAL_NETWORK_ACCEPTED=true`。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research network acceptance` | accepted flags/gates表示 | Read-only | primary inspection。 |
| `./research network validate` | authorityから全accepted gate再検証 | Read-only validation | current stateを変更しない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Authority validator | [validate_current_network_completion_authority.py](05_src/traffic_simulation/network/validate_current_network_completion_authority.py) | path、SHA、flag整合性。 |
| Portal/network validator | [validate_research_map_portal.py](05_src/traffic_simulation/network/validate_research_map_portal.py) | accepted metricsとcurrent display整合性。 |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Acceptance JSON | formal accepted state | `.../run_2/network_acceptance.json` | `ACCEPTED` |
| Current authority | stable pointer | `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml` | `CURRENT` |

### Authority / Source of truth

acceptance結果はacceptance JSON、current選択はauthority pointer。Portalや本書はacceptance authorityではない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Formal flag | `./research network acceptance` | `FORMAL_NETWORK_ACCEPTED=true` | `PASS` |
| Primary routeability | same | deterministic 100 pairs、100 routeable | `PASS` |
| SHA binding | `./research network validate` | `4625dbbc…e40f`一致 | `PASS` |

### Acceptance / DONE criteria

acceptance artifact存在、all prior gates PASS、formal flag true、authority pointerとSHA一致。

### Provenance

Decision ID、network ID、source commit、source input SHA、network semantic SHA、SUMO versionをacceptance JSONに記録。

### Known limitations

routeability acceptanceはsample-based。additional sanity sampleは非gatingで91/100。これをcurrent failureへ昇格しないが、all-pairs保証とも表現しない。

### Unresolved decisions

なし（current acceptance scope内）。

### Next handoff

accepted network、mapping、known limitationsをRouting Baselineへ渡す。

## G. Routing Baseline

### Purpose

選択したdelivery instanceに必要なtravel-time cost、distance cost、routeability、routing provenanceを固定する。

### Current status

`NEXT / NOT IMPLEMENTED / NOT YET PRODUCTION COMPLETE`。Network prerequisiteは`PASS`。

### Entry conditions

accepted network、accepted Stop mapping、Requests / Stops、および採択済みrouting scope/depot/vehicle class/cost definition。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Accepted network | routing graph | [three_tier.net.xml](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/three_tier.net.xml) | `READY` | SHA-bound。 |
| Accepted mapping | route endpoints | [request_stop_mapping.json](reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_2/request_stop_mapping.json) | `READY` | full Stops mapping。 |
| Requests | demand records | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv` | `READY LOCALLY` | instance scope未選択。 |
| Stops | candidate delivery endpoints | `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv` | `READY LOCALLY` | 39,956 all-pairsを前提にしない。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research routing inputs` | available inputsと未決定事項表示 | Read-only | 現在の主inspection。 |
| `./research routing status` | stage/runner/artifact状態表示 | Read-only | `NEXT`。 |
| `./research routing build --dry-run` | missing decisions/runner表示 | Read-only | production buildは拒否。 |
| `./research routing validate --dry-run` | missing artifact/validator表示 | Read-only | validationは未実装。 |
| `./research pipeline routing --dry-run` | inputs→build→validation gateをinspection | Read-only | artifactを作らない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI readiness guard | [routing.py](05_src/research_cli/routing.py) | input/gate表示、未実装build拒否。 |
| Production routing runner | — | `NOT IMPLEMENTED` |
| Production routing validator | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Travel-time cost | required OD travel-time | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| Distance cost | required OD distance | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| Routeability | required OD feasibility | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |
| Routing provenance | method/version/command/input hashes | path `UNRESOLVED` | `EXPECTED / NOT YET AVAILABLE` |

### Authority / Source of truth

current stage/decision boundaryは[Research Overview Stage 1](RESEARCH_OVERVIEW.md#stage-1--routing-baseline-next)と[Portal map](reproducibility/config/research_portal/research_map_v1.yml)。production routing authorityは`NOT AVAILABLE`。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Network prerequisite | `./research routing inputs` | accepted network/mapping READY | `PASS` |
| Routing artifact validator | `./research routing validate --dry-run` | method fixed、required OD complete、routeability/provenance valid | `NOT AVAILABLE` |

### Acceptance / DONE criteria

routing method/scope fixed、必要OD集合のみを完全生成、validator PASS、input/output hashと再現commandを保存し、downstream利用をacceptすること。

### Provenance

将来artifactにnetwork SHA、mapping/input hashes、method/version、vehicle class、OD scope、command、runtimeを記録する必要がある。現時点では`NOT AVAILABLE`。

### Known limitations

39,956 Stops full all-pairsは採択していない。sample routeability acceptanceはproduction routing cost artifactではない。

### Unresolved decisions

routing scope、depot、delivery vehicle class、routing cost definition、unreachable pair policy、artifact/schema/provenance contract。

### Next handoff

validated required-OD cost/routeability artifactをCommon Delivery Instanceへ渡す。

## H. Common Delivery Instance

### Purpose

需要、Stops、depot、routing costs、vehicle/battery constraintsをsolver-independentな共通問題へ凍結する。

### Current status

`PLANNED / NOT IMPLEMENTED / NOT AVAILABLE`。Portal execution positionは`PLANNED`。

### Entry conditions

validated Routing Baseline、resolved depot/fleet size/vehicle capacity/battery parameters、adopted schemaが必要。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Requests / Stops | common demand | current local paths | `AVAILABLE LOCALLY` | subset rule未確定。 |
| Routing Baseline | matrices/feasibility | path未定 | `NOT AVAILABLE` | blocking input。 |
| Comparison protocol | design constraint | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | common inputs/evaluatorを要求。 |
| EV profile | candidate fixed model assumption | [managed_urban_ev_delivery_v1.yml](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml) | `CURRENT MODEL ASSUMPTION` | fleet/battery instance acceptanceではない。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research instance status` | missing validator/upstream/artifact表示 | Read-only | current module pathはMISSING。 |
| `./research instance build --dry-run` | missing inputs/generator表示 | Read-only | no artifact。 |
| `./research instance validate --dry-run` | missing validator/artifact表示 | Read-only | no acceptance。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [instance.py](05_src/research_cli/instance.py) | current absenceを明示。 |
| `common_delivery_instance.py` | `05_src/optimization/common_delivery_instance.py` | `NOT AVAILABLE` in current checkout |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Instance schema | solver-independent contract | path未定 | `EXPECTED / NOT AVAILABLE` |
| Production instance | frozen common problem | path未定 | `EXPECTED / NOT AVAILABLE` |
| Validation/acceptance | completeness/feasibility/hash | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 2 roadmapとcomparison protocolが設計参照。production authority、schema、accepted artifactは存在しない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Instance validator | `./research instance validate --dry-run` | schema fixed、placeholderなし、hash/feasibility PASS | `NOT AVAILABLE` |

### Acceptance / DONE criteria

schema、generator、validatorがcurrent checkoutに存在し、validated routingとresolved constraintsからreproducible production instanceを生成・acceptすること。

### Provenance

将来はRequests/Stops/routing/config hashes、node ordering、vehicle/constraint version、generation commandを保存する。

### Known limitations

過去候補はroadmap上のreview materialでありcurrent implementationではない。fixed EV profileだけでCommon Instance成立とはしない。

### Unresolved decisions

contract復元/改訂/置換、depot、fleet size、capacity、battery/energy semantics、instance scope。

### Next handoff

accepted common instanceをClassical OptimizationとQUBOへ同一入力として渡す。

## I. Classical Optimization

### Purpose

量子手法と比較するclassical baselineを、共通instance・共通feasibility/evaluator上で確立する。

### Current status

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED`。production solver/resultなし。

### Entry conditions

accepted Common Delivery Instance、fixed formulation/objective/constraints、solver budget、seed、correctness fixtures。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Common Delivery Instance | solver input | path未定 | `NOT AVAILABLE` | blocking。 |
| Comparison protocol | fairness boundary | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | solver実装ではない。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research optimization classical status` | upstream/solver状態表示 | Read-only | no result。 |
| `./research optimization classical run --dry-run` | missing solver/upstream表示 | Read-only | production run拒否。 |
| `./research optimization classical validate --dry-run` | missing result/validator表示 | Read-only | no acceptance。 |
| `./research pipeline optimization --dry-run` | instance→classical→validation inspection | Read-only | partial orchestration。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [optimization.py](05_src/research_cli/optimization.py) | missing production solverを明示。 |
| Production formulation/solver | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Mathematical formulation | adopted objective/constraints | path未定 | `EXPECTED / NOT AVAILABLE` |
| Classical solution | raw/repaired feasible solution | path未定 | `EXPECTED / NOT AVAILABLE` |
| Validation evidence | small-instance correctness | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 3 roadmapとcomparison protocolのみ。production Decision/config/result/acceptanceは`NOT AVAILABLE`。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Classical correctness | `./research optimization classical validate --dry-run` | fixtures、feasibility、objective、result provenance PASS | `NOT AVAILABLE` |

### Acceptance / DONE criteria

formulation固定、solver実装、small-instance correctness PASS、production baseline生成、common evaluatorで検証・accept。

### Provenance

将来はinstance hash、solver/version、budget、seed、raw/repaired output、runtime boundariesを保存する。

### Known limitations

exact objective、algorithm、fleet parameters、budgetは未採択。fake solver/objective/resultを置かない。

### Unresolved decisions

optimizer algorithm、mathematical formulation、budget、seed set、correctness threshold。

### Next handoff

validated classical baselineをQUBO equivalence、Classical-vs-QAOA comparison、Delivery Simulationへ渡す。

## J. QUBO

### Purpose

固定済みclassical problemを検証可能なQUBOとencoder/decoder契約へ写像する。

### Current status

`PLANNED / FUTURE / NOT IMPLEMENTED`。formulation、builder、artifact、validatorなし。

### Entry conditions

accepted Common Delivery Instance、fixed Classical formulation、small exact instances、adopted penalties/scaling。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Common instance | variable/data source | path未定 | `NOT AVAILABLE` | blocking。 |
| Classical formulation/optimum | equivalence reference | path未定 | `NOT AVAILABLE` | blocking。 |
| Comparison protocol | fairness/output accounting | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | QUBO仕様ではない。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research quantum status` | QUBO/QAOA state表示 | Read-only | QUBO planned。 |
| `./research quantum qubo build --dry-run` | missing formulation/builder表示 | Read-only | no QUBO。 |
| `./research quantum qubo validate --dry-run` | missing equivalence inputs表示 | Read-only | no validation。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [quantum.py](05_src/research_cli/quantum.py) | unimplemented stateを返す。 |
| QUBO builder/validator | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| QUBO formulation | variables/objective/penalties/scaling | path未定 | `EXPECTED / NOT AVAILABLE` |
| Encoder/decoder contract | instance↔binary mapping | path未定 | `EXPECTED / NOT AVAILABLE` |
| Equivalence report | QUBO vs exact classical | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 4A/4B roadmapのみ。current QUBO authorityは存在しない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| QUBO equivalence | `./research quantum qubo validate --dry-run` | small-instance optimum、decode、feasibility一致 | `NOT AVAILABLE` |

### Acceptance / DONE criteria

versioned formulation/contract、penalty rationale、builder、exact fixtures、equivalence validatorがPASS。

### Provenance

将来はclassical/instance hashes、coefficient scaling、penalties、builder version、decoded solutionを保存する。

### Known limitations

low energyだけではequivalenceを示さない。QUBO係数・penaltyを推測しない。

### Unresolved decisions

encoding、penalty values、scaling、constraint representation、acceptance tolerances。

### Next handoff

validated QUBOとdecoder/feasibility contractをQAOAへ渡す。

## K. QAOA

### Purpose

validated QUBOを明示したbackend・sampling・decode/repair規則で実行し、classical baselineと公平に比較可能な候補解を作る。

### Current status

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED`。quantum hardware executionも`NOT IMPLEMENTED`。

### Entry conditions

validated QUBO、adopted backend/depth/optimizer/shots/seeds、decode/repair、measurement boundary。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Validated QUBO | quantum problem | path未定 | `NOT AVAILABLE` | blocking。 |
| Classical baseline | comparison reference | path未定 | `NOT AVAILABLE` | blocking。 |
| Comparison protocol | fairness | [optimization_comparison_protocol.md](05_src/traffic_simulation/optimization_comparison_protocol.md) | `CURRENT DESIGN` | Aer結果はquantum advantageを示さない。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research quantum qaoa run --dry-run` | missing QUBO/runner表示 | Read-only | no circuit/result。 |
| `./research quantum compare --dry-run` | common validated results不足表示 | Read-only | no comparison。 |
| `./research quantum status` | quantum stage inspection | Read-only | hardware未実装も表示。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [quantum.py](05_src/research_cli/quantum.py) | execution refusal/state表示。 |
| QAOA runner/comparator | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Quantum candidate | samples/parameters/raw solution | path未定 | `EXPECTED / NOT AVAILABLE` |
| Decoded/repaired solution | common feasibility format | path未定 | `EXPECTED / NOT AVAILABLE` |
| Comparison evidence | quality/feasibility/runtime/resources | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 4C/4D roadmapとcomparison protocolのみ。backend/result acceptanceはない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| QAOA result validation | — | reproducible config、decode、common checker PASS | `NOT AVAILABLE` |
| Classical/quantum comparison | `./research quantum compare --dry-run` | same instance/budget/evaluator | `NOT AVAILABLE` |

### Acceptance / DONE criteria

validated QUBOのみを入力し、backend/config/seedを固定、raw/repaired結果を保存、common checkerとcomparison protocolに合格。

### Provenance

将来はbackend type/version、depth、optimizer、shots、seeds、circuit/resource counts、decode/repair timeを保存する。

### Known limitations

Qiskit Aerはquantum hardwareではない。quantum advantageを前提・主張しない。

### Unresolved decisions

depth、optimizer、shots、backend、hardware assumption、budget、repair rules。

### Next handoff

validated plan candidatesをDelivery Simulationとmethod comparisonへ渡す。

## L. Scenario Construction

### Purpose

baselineを上書きせず、future demand、EV technology、optimization/quantum capabilityを分離したversioned scenario inputへする。

### Current status

`PLANNED / NOT IMPLEMENTED`。EV profileは`CURRENT FIXED MODEL ASSUMPTION`だが、accepted future scenario parameterizationではない。

### Entry conditions

accepted baseline、evidence-backed parameter sources、scenario scope/year、transformation rules、pre-registered combinations。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Baseline demand config | baseline comparator | [baseline_demand.yml](reproducibility/config/traffic_simulation/baseline_demand.yml) | `CURRENT` | future valuesで上書きしない。 |
| EV vehicle profile | fixed model assumption | [managed_urban_ev_delivery_v1.yml](reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml) | `CURRENT ASSUMPTION` | measured real vehicleではない。 |
| Future scenario roadmap | planned dimensions/gates | [Research Overview Stage 5](RESEARCH_OVERVIEW.md) | `PLANNED` | year/rates未固定。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research demand future` | future demand availability表示 | Read-only refusal | returns `NOT IMPLEMENTED`。 |
| `./research demand build --dry-run` | baseline/future build boundary inspection | Read-only | scenario生成なし。 |
| `./research quantum status` | quantum capability stage state | Read-only | capability scenarioを生成しない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| EV profile schema/config | [managed vehicle profile schema](reproducibility/config/traffic_simulation/schemas/managed_vehicle_profile.schema.json) | current vehicle assumption contract。 |
| Future demand/scenario builder | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Technology scenario config | EV/optimization capability ranges | path未定 | `EXPECTED / NOT AVAILABLE` |
| Demand scenario config | year/total/spatial transformation | path未定 | `EXPECTED / NOT AVAILABLE` |
| Combination registry | pre-registered comparisons | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 5 roadmapがdesign authority。adopted production scenario authorityは`NOT AVAILABLE`。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| EV profile schema tests | no dedicated `./research` command | profile schema semantics valid | component exists; not scenario acceptance |
| Future scenario validator | — | source/range/transformation/baseline separation PASS | `NOT AVAILABLE` |

### Acceptance / DONE criteria

scenario parameters、sources、scope/year、transformation、baseline comparison、combinationsをversion化しvalidator PASS。

### Provenance

将来はexternal evidence IDs、parameter range、transformation code/config hash、scenario versionを保存する。

### Known limitations

vehicle profileのpayload等をactual fleet値とみなさない。future demandやquantum capabilityを現在値として扱わない。

### Unresolved decisions

scenario year、demand growth/spatial change、EV battery ranges、optimization/quantum capability assumptions。

### Next handoff

accepted scenario configをscenario-specific Requests/Stops、Common Instance、Optimization、Simulationへ渡す。

## M. Delivery Simulation

### Purpose

accepted network/scenario上でvalidated delivery plansを実行し、planとrealized model behaviorを分離して記録する。

### Current status

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED / NOT PRODUCTION COMPLETE`。

### Entry conditions

accepted network、Common Instance、validated plans、accepted scenarios/traffic config、seeds、plan-to-SUMO conversion contract。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Accepted network | SUMO environment | current authority resolves | `READY` | network validation simulationとは別。 |
| Validated plans | delivery execution plan | path未定 | `NOT AVAILABLE` | blocking。 |
| Scenario config | technology/demand conditions | path未定 | `NOT AVAILABLE` | blocking。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research simulation status` | production readiness表示 | Read-only | traffic/network validation simulationsを除外。 |
| `./research simulation run --dry-run` | missing runner/plan表示 | Read-only | no simulation。 |
| `./research simulation validate --dry-run` | missing result/validator表示 | Read-only | no acceptance。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [simulation.py](05_src/research_cli/simulation.py) | delivery simulation不在を明示。 |
| Production delivery runner/validator | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Simulation run | realized routes/times/SOC/completions/failures | path未定 | `EXPECTED / NOT AVAILABLE` |
| Run manifest | plan/scenario/network/seed hashes | path未定 | `EXPECTED / NOT AVAILABLE` |
| Validation report | execution/failure accounting | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 6 roadmapと[V&V reference](05_src/traffic_simulation/20260730_20260903_simulation_model_development_and_vv.md)。production run authorityなし。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Delivery simulation validator | `./research simulation validate --dry-run` | reproducible plan conversion、run/failure accounting PASS | `NOT AVAILABLE` |

### Acceptance / DONE criteria

accepted inputsからreproducible runを生成し、plan/run provenance、completion/failure accounting、validator、acceptanceを満たす。

### Provenance

将来はnetwork/plan/instance/scenario hashes、SUMO/software versions、seed、command、run manifestを保存する。

### Known limitations

current repoのnetwork/traffic validation runsは本研究のproduction delivery simulation resultではない。

### Unresolved decisions

plan conversion、traffic scenario、seed set、completion/failure event schema、output/acceptance paths。

### Next handoff

validated simulation outcomesをEvaluationへ渡す。

## N. Evaluation

### Purpose

validated simulation outputからprimary fulfillment metricとauxiliary diagnosticsを共通定義で算出する。

### Current status

`PLANNED`（roadmap）/ `FUTURE`（Portal）/ `NOT IMPLEMENTED`。式はcurrent research designだがcanonical evaluatorとformal metric artifactはない。

### Entry conditions

validated Delivery Simulation、fixed denominator population/time horizon/exclusions、metric schema、fixtures。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Metric design | primary formula | [Research Overview Stage 7](RESEARCH_OVERVIEW.md) | `CURRENT RESEARCH DESIGN / NEEDS FORMALIZATION` | denominator scope unresolved。 |
| Baseline demand spec | demand/P_eq semantics | [baseline demand and comparator](05_src/traffic_simulation/demand/20260718_20260903_baseline_demand_and_comparator.md) | `CURRENT_NORMATIVE` | metric priority documentation conflict remains. |
| Simulation result | evaluator input | path未定 | `NOT AVAILABLE` | blocking。 |

Primary design:

```text
delivery_fulfillment_rate
  = delivered_parcel_equivalent / total_parcel_equivalent
```

Auxiliary metrics include delivered/unserved parcel-equivalent、vehicle utilization、travel time、distance、battery use、unreachable demand。これらをprimary metricと混同しない。

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research evaluate status` | formula/evaluator/denominator状態表示 | Read-only | formalization gapを表示。 |
| `./research evaluate fulfillment --dry-run` | missing evaluator/input/scope表示 | Read-only | metricを計算しない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| CLI guard | [evaluate.py](05_src/research_cli/evaluate.py) | missing evaluatorを明示。 |
| Canonical evaluator | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Primary metric | delivery fulfillment rate | path未定 | `EXPECTED / NOT AVAILABLE` |
| Auxiliary metrics | cause/resource diagnostics | path未定 | `EXPECTED / NOT AVAILABLE` |
| Evaluation manifest | definitions/input hashes/aggregation | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

current roadmapがprimary designを示すが、formal metric schema/evaluator/acceptanceは`NOT AVAILABLE`。本書は式をnormative化しない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Fulfillment evaluator | `./research evaluate fulfillment --dry-run` | formula/unit/scope/denominator/exclusions/aggregation fixtures PASS | `NOT AVAILABLE` |

### Acceptance / DONE criteria

metric contract、denominator/time horizon、exclusion policyを固定し、canonical evaluator/fixtures PASS、result再現、uncertainty/failure decomposition保存。

### Provenance

将来はsimulation hash、metric version、scope、denominator、exclusions、aggregation、evaluator versionを保存する。

### Known limitations

fulfillment resultは未算出。`P_eq`とfulfillment rateのpriority差がlegacy Portal registry上の未解決documentation conflictとして残る。

### Unresolved decisions

denominator scope、time horizon、unreachable/excluded demand treatment、primary/auxiliary metric contract。

### Next handoff

validated metrics、uncertainty、failure decompositionをInterpretationとSensitivityへ渡す。

## O. Evidence-Supported Interpretation

### Purpose

直接分析境界`Delivery Fulfillment`の外側を、独立Evidenceに基づく条件付きinterpretationとして接続する。計算pipelineではない。

### Current status

Evidence modelは`CURRENT / IMPLEMENTED`、overall assessmentは`SUPPORTED_WITH_CONDITIONS`。研究resultに適用する段階は`FUTURE / NOT AVAILABLE`。

### Entry conditions

一般的interpretation設計の閲覧にはEvidence artifactのみ必要。研究結果の解釈にはvalidated fulfillment result、scenario、uncertainty、sensitivityが必要。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Interpretation Evidence | claims/sources/boundaries | [fleet_capacity_interpretation_v1.yml](reproducibility/evidence/fleet_capacity_interpretation_v1.yml) | `CURRENT` | network authorityとは分離。 |
| Evidence schema | status/traceability contract | [fleet_capacity_interpretation_v1.schema.json](reproducibility/evidence/fleet_capacity_interpretation_v1.schema.json) | `CURRENT` | source verification debtを保持。 |
| Fulfillment result | study-specific direct metric | path未定 | `NOT AVAILABLE` | result interpretationは未実行。 |

Pathway:

```text
Technology / Optimization
  → Delivery Fulfillment
════════ DIRECT ANALYSIS BOUNDARY ════════
  → Unserved Delivery Demand
  → Potential Effective Delivery-Capacity Requirement
  → Potential Need for Fleet Expansion / Replacement
```

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research portal status` | boundary/assessment表示 | Read-only | resultを生成しない。 |
| `./research portal check` | Evidence schema/state/traceability検証 | Read-only validation | research calculationなし。 |
| `./research artifacts` | Evidence artifact/schema path表示 | Read-only | source metadata inspection入口。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Evidence validator | [validate_fleet_interpretation_evidence.py](05_src/traffic_simulation/validation/validate_fleet_interpretation_evidence.py) | schema/status/source refs/index separation検証。 |
| Portal state/UI | [serve.py](research_portal/serve.py) | artifactからnode/panel/traceability生成。 |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Evidence model | reusable interpretation design | `reproducibility/evidence/fleet_capacity_interpretation_v1.yml` | `AVAILABLE` |
| Portal evidence state | node/link/source status | `/api/state` | runtime `AVAILABLE` |
| Study-specific interpretation | evaluated resultへのbounded claim | path未定 | `NOT AVAILABLE` |

### Authority / Source of truth

Evidence artifactがinterpretation source。roleは`INTERPRETATION_ONLY`でありFormal Network acceptance chainを変更しない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Evidence artifact/schema | `./research portal check` | 5 nodes/5 links、status/source refs/index separation valid | `PASS` |
| Interpretation result trace | — | claim→metric→scenario→Evidence追跡可能 | `NOT AVAILABLE` |

### Acceptance / DONE criteria

Evidence designはvalidator PASS。study-specific interpretationのDONEにはvalidated evaluation/sensitivityと、各claimのresult/Evidence traceが必要。

### Provenance

Evidence ID、source verification status、claim/link status、artifact/schema pathをEvidence artifactとrepository indexに記録。

### Known limitations

required additional vehicle count、fleet sizing optimization、investment amount、actual corporate investment predictionは`OUT OF SCOPE`。unserved demandはvehicle shortageと同義ではない。

### Unresolved decisions

10 sourceの完全bibliographic metadataが`NEEDS_SOURCE_VERIFICATION`。study-specific result interpretationはupstream未完了。

### Next handoff

bounded claimsとconditionsをSensitivity / Robustnessおよび最終publication claim traceへ渡す。

## P. Sensitivity / Robustness

### Purpose

重要仮定を事前登録範囲で変化させ、結論をrobust、conditional、insufficient evidenceへ分類する。

### Current status

`PLANNED / NOT IMPLEMENTED`。過去のnetwork-specific sensitivity/pilotを研究全体Stage 10のcurrent resultとして扱わない。

### Entry conditions

accepted baseline results、uncertain parameters/ranges、rerun/comparison protocol、claim interpretation。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Stage 10 roadmap | required domains/gate | [Research Overview Stage 10](RESEARCH_OVERVIEW.md) | `PLANNED` | routing/network/demand/battery/optimization/QUBO/scenarioを横断。 |
| Accepted baseline results | comparison anchor | path未定 | `NOT AVAILABLE` | blocking。 |
| Sensitivity registry/protocol | preregistered ranges | path未定 | `NOT AVAILABLE` | blocking。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research status` | upstream stage state確認 | Read-only | sensitivity専用commandなし。 |
| `./research pipeline full --dry-run` | closed upstream gates確認 | Read-only | sensitivity runは含まない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| General sensitivity runner/validator | — | `NOT IMPLEMENTED` |
| Historical/network-specific pilots | `reproducibility/outputs/...` | `HISTORICAL / NOT CURRENT STAGE 10` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Sensitivity matrix | parameter×outcome comparison | path未定 | `EXPECTED / NOT AVAILABLE` |
| Robustness summary | robust/conditional/insufficient classification | path未定 | `EXPECTED / NOT AVAILABLE` |
| Failure boundaries | conditions changing conclusions | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 10 roadmapのみ。production sensitivity authorityはない。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Sensitivity validator | — | preregistered ranges、complete runs、comparison/accounting valid | `NOT AVAILABLE` |

### Acceptance / DONE criteria

important uncertaintiesをsystematically varyし、missing/failed runsをaccountし、conclusion classificationをtrace可能にする。

### Provenance

将来はbaseline hash、parameter registry、run matrix、seeds、failure accounting、comparison code/versionを保存する。

### Known limitations

individual network sensitivity evidenceの存在はend-to-end research conclusion robustnessを示さない。

### Unresolved decisions

ranges、factorial design、rerun budget、robustness threshold、missing-run policy。

### Next handoff

robustness classificationとfailure boundariesをPublication / Reproducibility Freezeへ渡す。

## Q. Publication / Reproducibility Freeze

### Purpose

公開claimに必要なaccepted artifact、config、schema、hash、software version、command、Portal、documentationを一つのfreezeへ束ねる。

### Current status

`FUTURE / NOT IMPLEMENTED`。repository index、current authority、Markdown/link validatorsは現在利用可能な部分機構だが、研究全体freeze/release commandではない。

### Entry conditions

公開対象となる全stageのaccepted outputs、validation evidence、claim trace、sensitivity/limitations。

### Canonical inputs

| Input | Role | Canonical path | Status | Notes |
|---|---|---|---|---|
| Repository index | current cross-reference | [research_repository_index_v17.yml](reproducibility/indexes/research_repository_index_v17.yml) | `CURRENT` | final freeze manifestではない。 |
| Current authority | accepted network pointer | [current network authority](reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml) | `CURRENT` | Network scopeのみ。 |
| Roadmap | Stage 11 gate | [Research Overview](RESEARCH_OVERVIEW.md) | `CURRENT` | final inputs未完了。 |

### Commands

| Command | Purpose | Read/Write | Notes |
|---|---|---|---|
| `./research validate` | current authority/index/Portal横断validation | Read-only | final freezeを作らない。 |
| `./research portal check` | current Portal/document/artifact consistency | Read-only validation | final publication acceptanceではない。 |
| `./research artifacts` | current known artifact paths | Read-only | complete publication inventoryではない。 |

### Implementation

| Component | Path | Role |
|---|---|---|
| Repository index validator | [validate_research_repository_index.py](05_src/traffic_simulation/network/validate_research_repository_index.py) | current pointers existence。 |
| Markdown/link validator | [validate_current_markdown_index.py](05_src/traffic_simulation/network/validate_current_markdown_index.py) | current metadata/link/inventory。 |
| Final freeze/release runner | — | `NOT IMPLEMENTED` |

### Outputs

| Output | Meaning | Canonical path / pattern | Current availability |
|---|---|---|---|
| Current indexes | present-state navigation | `reproducibility/indexes/` | `AVAILABLE` |
| Final freeze manifest | all publication claims/artifacts/hashes | path未定 | `EXPECTED / NOT AVAILABLE` |
| Archive/release | immutable publication package | path未定 | `EXPECTED / NOT AVAILABLE` |

### Authority / Source of truth

Stage 11 roadmap defines the future gate。current network freeze mechanismsはNetwork scopeに限定される。研究全体publication authorityは`NOT AVAILABLE`。

### Validation

| Validator / Gate | Command | Pass condition | Current status |
|---|---|---|---|
| Current cross-reference | `./research validate` | authority/index/Portal PASS | `PASS for current scope` |
| Final reproducibility audit | — | all claims→accepted evidence、links/hashes/env/commands valid | `NOT AVAILABLE` |

### Acceptance / DONE criteria

全公開claimがfrozen accepted evidenceへ追跡可能、reproduction/link audit PASS、versions/commands/hashes固定、Portal/overview/reference一致。

### Provenance

将来freeze manifestにGit commit、artifact hashes、environment/software versions、commands、acceptance IDsを保存する。

### Known limitations

current indexesとNetwork accepted stateだけでは研究全体のpublication freezeにならない。

### Unresolved decisions

freeze manifest schema、archive location、release procedure、claim inventory、final environment lock。

### Next handoff

publication、submission、archive release。

## Research Command Index

`./research commands`がmachine-adjacentなcanonical command catalog。本節は運用上のread/write、prerequisite、dry-run supportを補足する。全41 interfaceを収録する。

### Global / Inspection / Validation

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research status` | research-wide position | Portal/current authority readable | status | none | no |
| `./research artifacts` | current paths | authority/index readable | path list | none | no |
| `./research commands` | command catalog | CLI importable | 41-command index | none | no |
| `./research validate` | authority/index/Portal checks | current artifacts | validation result | none | yes |

### Demand

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research demand status` | demand status | current Portal node IDs | status | none | no; **currently exits 1** |
| `./research demand validate` | baseline test＋mapping consistency | local demand/requests/stops | validation result | none | yes |
| `./research demand build` | baseline→requests→stops | safe integrated runner | artifact | none now; `NOT IMPLEMENTED` | yes |
| `./research demand future` | future demand availability | adopted parameters | status/refusal | none | no |

### Network

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research network status` | accepted network status | authority | status/hash | none | no |
| `./research network acceptance` | acceptance inspection | acceptance JSON | gates/flag | none | no |
| `./research network validate` | accepted network validation | current accepted artifacts | validation result | none | yes |
| `./research network build` | isolated build | safe unique-output runner | run artifact | none now; `NOT IMPLEMENTED` | yes |

### Routing

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research routing inputs` | inputs/decisions | authority/current data | readiness report | none | no |
| `./research routing status` | stage state | authority | status | none | no |
| `./research routing build` | routing costs | adopted scope/method＋runner | artifact | none now; `NOT IMPLEMENTED` | yes |
| `./research routing validate` | routing validation | production artifact/validator | result | none now; `NOT IMPLEMENTED` | yes |

### Common Delivery Instance

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research instance status` | instance readiness | repository | status | none | no |
| `./research instance build` | production instance | validated routing/constraints/generator | artifact | none now; `NOT IMPLEMENTED` | yes |
| `./research instance validate` | instance validation | artifact/validator | result | none now; `NOT IMPLEMENTED` | yes |

### Classical Optimization

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research optimization classical status` | classical readiness | repository | status | none | no |
| `./research optimization classical run` | solve common instance | accepted instance/solver | solution | none now; `NOT IMPLEMENTED` | yes |
| `./research optimization classical validate` | solution validation | result/validator | result | none now; `NOT IMPLEMENTED` | yes |

### QUBO / QAOA

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research quantum status` | quantum stage state | research map | status | none | no |
| `./research quantum qubo build` | QUBO build | fixed formulation/instance | QUBO | none now; `NOT IMPLEMENTED` | yes |
| `./research quantum qubo validate` | equivalence check | QUBO/exact optimum | result | none now; `NOT IMPLEMENTED` | yes |
| `./research quantum qaoa run` | QAOA execution | validated QUBO/runner | candidate | none now; `NOT IMPLEMENTED` | yes |
| `./research quantum compare` | classical/quantum comparison | validated common results | evidence | none now; `NOT IMPLEMENTED` | yes |

### Simulation / Evaluation

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research simulation status` | simulation readiness | research map | status | none | no |
| `./research simulation run` | execute plans | validated plan/runner | outcome | none now; `NOT IMPLEMENTED` | yes |
| `./research simulation validate` | validate outcome | artifact/validator | result | none now; `NOT IMPLEMENTED` | yes |
| `./research evaluate status` | evaluation readiness | research map | status/formula | none | no |
| `./research evaluate fulfillment` | compute metric | validated simulation/evaluator/scope | metrics | none now; `NOT IMPLEMENTED` | yes |

### Portal

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research portal status` | Portal/current state | canonical artifacts | status | none | no |
| `./research portal start` | serve Portal | Python dependencies/artifacts | local server | process only; repo unchanged | yes |
| `./research portal check` | authority/index/map/Evidence validation | current artifacts | result | none | yes |
| `./research portal build` | standalone handoff | generator | handoff | none now; `NOT IMPLEMENTED` | yes |

### Orchestration

| Command | Purpose | Prerequisites | Output | Mutation | Dry-run |
|---|---|---|---|---|---|
| `./research pipeline network` | reuse/validate accepted network | accepted network | validation | none | yes |
| `./research pipeline routing` | inputs→build→validate | routing decisions/runner | artifact | none now; `PARTIAL` | yes |
| `./research pipeline optimization` | instance→classical→validate | validated routing | baseline | none now; `PARTIAL` | yes |
| `./research pipeline portal` | current state validation | canonical artifacts | result | none | yes |
| `./research pipeline full` | run until first closed gate | governed upstream | stage summary | currently stops at Routing; `PARTIAL` | yes |

## Artifact / Authority Matrix

| Stage | Decision | Specification | Config / Registry | Schema | Run / Output | Acceptance | Current authority |
|---|---|---|---|---|---|---|---|
| External Data | — | provenance records | source registry | source-specific | local raw/derived | consumer-specific | source registry＋consumer authority |
| Demand | — | baseline demand spec | baseline demand config | embedded/config validation | local Parquet＋quality JSON | no separate acceptance | config/spec＋quality summary |
| Requests / Stops | — | roadmap/design records | local run summaries | `NOT AVAILABLE` | local CSVs | mapping acceptance only | Portal map＋network acceptance |
| Network Construction | Three-tier Decision | Formal Completion＋Pipeline specs | Three-tier registry | policy＋record schemas | run_2 / `three_tier.net.xml` | network acceptance JSON | current network authority |
| Stop Mapping | Three-tier Decision | Network Pipeline spec | accepted run mapping | acceptance structure | run_2 mapping JSON | network acceptance `/mapping` | current network authority |
| Network Acceptance | Three-tier Decision | Network Pipeline spec | authority pointer | policy/record | run_2 | `FORMAL_NETWORK_ACCEPTED=true` | current network authority |
| Routing | `UNRESOLVED` | roadmap Stage 1 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | roadmap/Portal stage only |
| Common Instance | `UNRESOLVED` | roadmap Stage 2＋comparison protocol | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | design only |
| Classical | `UNRESOLVED` | roadmap Stage 3＋comparison protocol | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | design only |
| QUBO | `UNRESOLVED` | roadmap Stage 4A/4B | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | design only |
| QAOA | `UNRESOLVED` | roadmap Stage 4C/4D | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | design only |
| Scenario | `UNRESOLVED` | roadmap Stage 5 | EV profile＋baseline config | vehicle profile schema | `NOT AVAILABLE` | `NOT AVAILABLE` | design/current assumption only |
| Delivery Simulation | `UNRESOLVED` | roadmap Stage 6＋V&V reference | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | design only |
| Evaluation | `UNRESOLVED` | roadmap Stage 7 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | research design only |
| Interpretation | Evidence design | Evidence artifact | Evidence artifact | Evidence schema | Portal state | Evidence validator PASS | interpretation-only artifact |
| Sensitivity | `UNRESOLVED` | roadmap Stage 10 | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | design only |
| Publication Freeze | `UNRESOLVED` | roadmap Stage 11 | repository index (partial) | `NOT AVAILABLE` | `NOT AVAILABLE` | `NOT AVAILABLE` | future gate only |

## Validation Matrix

| Stage | Validator | Gate | Current result | Blocking next stage? |
|---|---|---|---|---|
| External Data | consumer-specific / Demand test | registered source/hash usable | available; no unified acceptance | no for current baseline |
| Demand | `test_prepare_baseline_demand.py` via `demand validate` | config/source/conservation | `PASS when run` | no for current baseline |
| Requests / Stops | authority consistency via `demand validate` | files exist/mapping accepted | `PASS`; regeneration validator absent | reproducibility debt |
| Network | `network validate` suite | registry/pipeline/SUMO/attributes/connectivity | `PASS` | no |
| Stop Mapping | network acceptance/Portal validator | 39,956/39,956, permitted edges | `PASS` | no |
| Network Acceptance | authority validator | flag true＋SHA match | `PASS` | no |
| Routing | production routing validator | required OD/method/provenance | `NOT AVAILABLE` | **yes** |
| Common Instance | production instance validator | schema/completeness/feasibility | `NOT AVAILABLE` | **yes** |
| Classical | correctness/result validator | formulation/fixtures/result | `NOT AVAILABLE` | **yes** |
| QUBO | equivalence validator | classical/QUBO equivalence | `NOT AVAILABLE` | **yes** |
| QAOA | common feasibility/comparison | reproducible candidate/common checker | `NOT AVAILABLE` | **yes** |
| Scenario | scenario validator | source/range/transformation | `NOT AVAILABLE` | **yes** |
| Delivery Simulation | production simulation validator | run/failure/provenance | `NOT AVAILABLE` | **yes** |
| Evaluation | canonical evaluator fixtures | scope/denominator/formula | `NOT AVAILABLE` | **yes** |
| Interpretation | Evidence validator | schema/status/source trace | `PASS` for design; result gate unavailable | yes for result claims |
| Sensitivity | sensitivity validator | preregistered matrix/accounting | `NOT AVAILABLE` | **yes** |
| Publication Freeze | final audit | claims/links/hashes/env/commands | `NOT AVAILABLE` | final gate |

## Dependency Matrix

| Downstream stage | Requires |
|---|---|
| Demand | governed open-data sources＋baseline config/spec |
| Requests / Stops | validated baseline demand＋generation/scope contract |
| Stop Mapping | Stops＋Formal/SUMO network＋vehicle permission |
| Network Acceptance | SUMO validity＋mapping＋primary routeability gate |
| Routing | accepted network＋accepted mapping＋Requests/Stops＋resolved scope/depot/vehicle/cost |
| Common Instance | validated Routing＋demand/Stops＋depot/fleet/capacity/battery constraints |
| Classical | accepted Common Instance＋fixed formulation/checker/budget |
| QUBO | accepted Common Instance＋fixed Classical formulation＋exact fixtures |
| QAOA | validated QUBO＋adopted execution/decoding protocol |
| Scenario | accepted baseline＋evidence-backed parameters/year/transformations |
| Simulation | accepted network/instance/scenario＋validated delivery plans |
| Evaluation | validated simulation＋fixed metric denominator/scope |
| Interpretation | validated evaluation＋scenario/uncertainty＋Evidence artifact |
| Sensitivity | accepted baseline results＋preregistered uncertain ranges/protocol |
| Publication Freeze | all claimed stages accepted＋claim/evidence trace＋reproducibility audit |

## Current lifecycle boundary

- `CURRENT / ACCEPTED`: Three-tier Formal Completion、run_2 network、mapping、network acceptance。
- `CURRENT DESIGN`: baseline demand spec/config、comparison protocol、EV profile assumption、interpretation Evidence。
- `HISTORICAL`: strict v17、old run_4/run_5/run_6、old blockers/failures、temporary diagnostics。
- `SUPERSEDED`: Hierarchical Hybrid Decisionとpre-Three-tier pipeline policies。
- historical/superseded artifactsをcurrent command inputまたはcurrent acceptanceとして再利用しない。

## Role separation

`RESEARCH_OVERVIEW.md` = Research overview / roadmap

`RESEARCH_PIPELINE_REFERENCE.md` = Current pipeline execution / authority / validation reference
