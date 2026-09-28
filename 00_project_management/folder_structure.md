<a id="folder-structure-and-policy"></a>

# フォルダー構成と管理方針

<a id="before"></a>

## 整理前

このプロジェクトでは、現行スクリプト、未加工・加工データ、生成図、旧成果物、複数の発表資料、バックアップ、提出資料、一時保存データ、研究文書がリポジトリの最上位に混在していた。

<a id="final-target-structure"></a>

## 最終的な構成

直下の研究文書の現在の保存先は[配置と移動先の案内](../docs/REPOSITORY_ORGANIZATION.md)を参照する。現在の実行状況・計画は本フォルダー、研究概要・タイトル・問いは `01_research_design/`、手順参照は `docs/`、日付付き記録は `00_project_management/history/` に配置する。

以下は目標とする最終的な論理構成である。各研究段階の原資料、管理対象の設定、実装、再生成可能な生成物、確認済み成果物の保存先を示す。`[P]`は計画中を表し、図に載っているだけで実装済みと解釈してはならない。

```text
research/
├── 00_project_management/                 [G] repository policy, environment, and research study guide
├── 01_research_design/                    [G] questions, hypotheses, and analysis design
├── 02_literature/                         [G] evidence and directly linked references
│   ├── references/                        [G] inventory, paper registry, and BibTeX
│   └── extraction_tables/                 [G] structured evidence extraction
├── 03_data/
│   ├── raw/                               [L] immutable third-party snapshots
│   │   └── traffic_simulation/            [L] N03, OSM, JARTIC, census, and related sources
│   ├── processed/                         [R] governed intermediate datasets
│   │   └── traffic_simulation/            [R] boundaries, demand, SUMO networks, and audits
│   ├── synthetic/                         [R] generated research instances
│   └── metadata/                          [G] source registry and chronological acquisition records
├── 04_notebooks/                          [P] active, exploratory, and archived notebooks
├── 05_src/                                [G] implementation
│   ├── traffic_simulation/
│   │   ├── network/                       [G] boundary, OSM, and SUMO-network preparation
│   │   ├── demand/                        [G] governed synthetic delivery demand
│   │   ├── calibration/                   [G] JARTIC preparation and calibration
│   │   ├── simulation/                    [P] scenario construction and SUMO execution
│   │   ├── validation/                    [G] unit tests, fixtures, and governance checks
│   │   └── visualization/                 [G] review-map generation
├── 06_outputs/                            [G] reviewed figures, tables, maps, and reports
│   └── traffic_simulation/                [G] selected traffic-study deliverables
├── 07_presentations/                      [G] current presentation and cited assets
├── 08_documents/                          [G] manuscript and supplementary material
├── reproducibility/
│   ├── config/                            [G] versioned machine-readable settings
│   │   └── traffic_simulation/            [G] study area, demand, SUMO, and typemap policy
│   └── outputs/traffic_simulation/        [R] current regenerable runtime products
├── legacy/non_sumo_route_proxy_analysis/  [G] prior proxy data, code, figures, and audit package
├── docker/                                [G] isolated analysis and SUMO environments
├── compose.yaml                           [G] canonical service boundary
├── README.md                              [G] repository entry point and current status
└── LICENSE                                [G] repository license
```

Legend:

- `[G]`: Git-managed source, policy, metadata, test, or reviewed deliverable.
- `[L]`: local governed source data; excluded from Git and reacquired from its recorded source.
- `[R]`: regenerable artifact; excluded from Git unless explicitly promoted as a reviewed deliverable.
- `[P]`: planned location or module that is not yet evidence of implementation.

The intended artifact flow is:

```text
03_data/raw + 03_data/metadata + reproducibility/config
                         │
                         ▼
                      05_src
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      03_data/processed      reproducibility/outputs
              │                     │
              └──────────┬──────────┘
                         ▼
                  06_outputs / 08_documents
```

番号付きディレクトリは研究の進行段階を表す。`reproducibility/`は機械処理の実行範囲を示すもので、番号付きディレクトリ内の出典記録、実装、確認済み研究成果を置き換えない。

<a id="compact-path-inventory"></a>

## 主要な保存先の一覧

```text
00_project_management/
01_research_design/
02_literature/{quantum_routing,benchmarking_methodology,quantum_utility,references,extraction_tables}/
03_data/{raw/{population,charging,logistics,vehicle_specs,road_network},interim,processed,synthetic,metadata}/
04_notebooks/{active,exploratory,archived}/
05_src/{data_processing,literature_analysis,traffic_simulation,visualization}/
06_outputs/{figures/active,tables,maps,reports}/
07_presentations/{current,assets,references,archived_versions}/
08_documents/{manuscripts,abstracts,supplementary}/
reproducibility/{config,outputs/traffic_simulation}/
legacy/non_sumo_route_proxy_analysis/{data,src,outputs,reproducibility}/
docker/{analysis}/
compose.yaml
.dockerignore
90_archive/ (removed after adopting the latest-only policy)
99_quarantine/ (temporary review only; cleared after confirmation)
```

リポジトリ最上位には、`README.md`、`LICENSE`、版管理・コンテナー設定、番号付き研究ディレクトリ、現行交通シミュレーションの`reproducibility/`、統合した旧分析保管領域、分離した`docker/`環境を置く。現行の発表資料は`07_presentations/current/`に保存し、一時的な実行記録と過去の整理一覧は保持しない。

東京交通シミュレーションの拡張には専用の保存領域を使う。出典別の未加工入力は`03_data/raw/traffic_simulation/`、生成入力は`03_data/processed/traffic_simulation/`、出典記録は`03_data/metadata/traffic_simulation_sources.csv`、実装は`05_src/traffic_simulation/`、再現可能な実行成果物は`reproducibility/outputs/traffic_simulation/`、確認済み最終成果物は`06_outputs/traffic_simulation/`に置く。正本の保存先は`05_src/traffic_simulation/paths.py`で定義し、新規モジュールでは機器固有のパスや固定の親階層番号を使わない。固定済みの合成電気自動車配送問題の経路代理分析は`legacy/non_sumo_route_proxy_analysis/`に分離し、正式な交通シミュレーション入力として扱わない。

<a id="naming"></a>

## 命名規則

研究成果物には`NNN_YYYYMMDD_descriptive_file_name.ext`、版番号を含める場合は`NNN_YYYYMMDD_vNN_descriptive_file_name.ext`を使う。ファイル名は英小文字の単語を下線で区切る。外部データセットの同一性は来歴と改名対応表で保持する。版管理の内部ファイルと環境パッケージはこの命名規則の対象外とする。

<a id="retention"></a>

## 保存方針

現行ファイルと再現に必要なファイルは利用可能な状態で保持する。置換済みと確認された旧版、一時保存データ、一時的な実行記録、過去の整理一覧は削除する。科学的来歴、検証のまとめ、成果物一覧、現行の日本語改訂監査は、解釈や再現を支えるため保持する。
