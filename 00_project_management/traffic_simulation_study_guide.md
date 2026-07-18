# Traffic Simulation Research Study Guide

更新日：2026年7月18日

## 目的

現在のSUMO道路網設計は、SUMOの操作だけでなく、次の五分野を組み合わせて理解する必要がある。

1. シミュレーションモデルのVerificationとValidation
2. SUMO・OSMのデータ仕様
3. ソフトウェアテストとデータ来歴
4. 再現可能な計算機実験
5. 感度分析と不確実性評価

この順序で学び、placeholderの制限、fixtureと正式実験の分離、設定の固定、代替条件の比較を、一つのV&Vと再現可能性の枠組みとして説明できることを目標とする。

## 1. VerificationとValidation

### 基礎資料

- Robert G. Sargent, [An Introduction to Verification and Validation of Simulation Models](https://informs-sim.org/wsc13papers/includes/files/027.pdf), Winter Simulation Conference 2013, [DOI](https://doi.org/10.1109/WSC.2013.6721430)
- NIST IR 8298, [A Summary of Industrial Verification, Validation, and Uncertainty Quantification Procedures](https://doi.org/10.6028/NIST.IR.8298)

NIST IR 8298の主対象は数値流体シミュレーションである。V&Vと不確実性評価の構成を学び、交通シミュレーションへ読み替える。

| 概念 | 本研究で確認すること |
|---|---|
| Conceptual model validity | OSMタグをSUMO属性へ変換する規則が研究目的に適合するか |
| Computerized model verification | Python前処理、validator、`netconvert`が固定仕様どおり動くか |
| Data validity | OSM、公的データ、補完値の品質と基準日が用途に十分か |
| Operational validity | 距離、旅行時間、交通量等が主張する現実対象と整合するか |

読了後は、次の四つを区別して説明できることを到達目標とする。

```text
仕様が研究目的に適切か
実装が仕様どおりか
入力データが用途に十分か
結果が主張する現実対象に対して妥当か
```

テストが通ることはVerificationの証拠にはなるが、東京交通に対するValidationの完了を意味しない。

## 2. SUMOの仕様

### 必読資料

- [SUMO edge type file](https://sumo.dlr.de/docs/SUMO_edge_type_file.html)
- [Importing Networks from OpenStreetMap](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html)
- [`netconvert` documentation](https://sumo.dlr.de/docs/netconvert.html)
- [`osmNetconvert.typ.xml` documentation](https://sumo.dlr.de/docs/OsmNetconvert.typ.xml.html)
- [Vehicle permissions](https://sumo.dlr.de/docs/Simulation/VehiclePermissions.html)

重点的に確認する設定とオプションは次のとおりである。

```text
priority
speed
numLanes
oneway
allow / disallow
--lefthand
--osm.lane-access
--osm.annotate-defaults
--output.original-names
--type-files
```

各項目について、OSM明示値、typemap値、importer-level default、global defaultのどれが採用されるかを区別する。オプションは固定SUMO 1.24.0の`netconvert --help`およびfixture実変換でも確認する。

SUMO標準typemapの公式性と東京への地域適合性を分ける。公式値を固定することは再現性を高めるが、東京で実証的に妥当であることを保証しない。

## 3. OSMの意味論

OSM Wikiは、OSMデータ消費時のタグの意味とコミュニティ慣習を確認する仕様資料として使用する。日本の法的規制やモデルの実証的妥当性を保証する資料とは扱わない。

### 必読資料

- [`access`](https://wiki.openstreetmap.org/wiki/Key:access)
- [`oneway`](https://wiki.openstreetmap.org/wiki/Key:oneway)
- [`lanes`](https://wiki.openstreetmap.org/wiki/Key:lanes)
- [`*:lanes`](https://wiki.openstreetmap.org/wiki/Key:*:lanes)
- [`maxspeed`](https://wiki.openstreetmap.org/wiki/Key:maxspeed)
- [`source:maxspeed`](https://wiki.openstreetmap.org/wiki/Key:source:maxspeed)

### 本研究への対応

`access`では、一般規則を個別規則で上書きする階層を確認する。

```text
access
→ vehicle
→ motor_vehicle
→ bus、delivery等の車種別規則
→ forward / backward
→ lane別規則
→ 研究対象vClass集合との積集合
```

`oneway`では`yes`、`no`、`-1`、roundaboutとmotorwayの暗黙規則、および暗黙値の解釈限界を確認する。曖昧な規則を多数派の方向へ統計補完しない。

`lanes`では、`lanes`が原則としてway全体の車線数であり、方向別情報を`lanes:forward`、`lanes:backward`、`lanes:both_ways`で表すことを確認する。`*:lanes`では`|`で区切られた値とOSM way方向、走行方向、左側通行の関係を確認する。

`maxspeed`では、方向別、lane別、車種別、条件付き値と単位を確認する。実走速度を法的な`maxspeed`へ直接代入しない。`source:maxspeed`は由来の候補であり、値そのものと分けて保存する。

## 4. テストとデータ来歴

### テスト設計

- pytest, [About fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html)

pytest fixture機能と、合成OSM XMLとしてのtest fixtureデータを区別する。

```text
test fixtureデータ
  way、tag、方向、lane、欠損等を含む合成入力

pytest fixture機能
  一時ディレクトリ、設定、入力、実行環境等をテストへ渡す仕組み
```

本研究の基本テストフローは次のとおりである。

```text
合成入力
→ 前処理
→ 変換前validator
→ digest固定SUMO 1.24.0のnetconvert
→ 生成XML解析
→ 期待値との完全比較
→ 変換後品質ゲート
```

欠損を拒否する前処理負例と、必須属性をmaterializeしたruntime正常系を分離する。

### データ来歴

- W3C, [PROV Overview](https://www.w3.org/TR/2013/NOTE-prov-overview-20130430/)

| PROV概念 | 本研究の例 |
|---|---|
| Entity | OSM PBF、元way、正規化OSM XML、SUMO edge、監査CSV |
| Activity | access解決、属性補完、`netconvert`実行、手動レビュー |
| Agent | 前処理プログラム、SUMO 1.24.0、確認者 |

各採用値について、少なくとも次を追跡する。

```yaml
adopted_value: 2
value_state: structural_placeholder
source_dataset: osm_geofabrik_kanto_20260716
source_attribute: lanes
derivation_method: local_unique_mode
group:
  highway: residential
  oneway_status: bidirectional
sample_size: 184
mode_share: 0.63
generated_by: preprocessing_version_x
validation_status: structural_only
```

例中の数値は形式説明用であり、現在の大田区集計結果ではない。

## 5. 再現可能な計算機実験

### 資料

- [ACM SIGSOFT Empirical Standards](https://www2.sigsoft.org/EmpiricalStandards/)
- [ACM SIGSIM PADS Artifact Evaluation](https://sigsim.acm.org/conf/pads/2026/blog/artifact-evaluation/)
- [ACM Artifact Review and Badging](https://reviewers.acm.org/training-course/artifact-review-and-badging)
- [IEEE Research Reproducibility](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/research-reproducibility/)

本研究で揃えるartifactは次のとおりである。

```text
日付固定OSM snapshotとSHA-256
地域設定
typemap
前処理コード
設定YAML
netconvertコマンド
SUMO版とコンテナdigest
fixtureと期待結果
validator出力
manifestとbuild summary
感度分析条件
```

設定を結果確認後に無記録で調整しない。基準設定、代替条件、評価指標、可能な範囲で判定閾値を先に固定し、成功と失敗の両方を記録する。

## 6. 感度分析と不確実性評価

### 資料

- [SALib documentation](https://salib.readthedocs.io/en/stable/)
- [SALib basics](https://salib.readthedocs.io/en/stable/user_guide/basics.html)

現在は、Sobol、Morris、FAST等の大規模な大域感度分析を直ちに導入しない。まず、研究結果へ影響する少数の離散的な設計条件について、事前固定したrobustness checkを行う。

```text
標準priority / 一様priority / 固定3段階priority
service permissionsの基準条件 / delivery除外
専用バス道路の保持 / 除外
track除外 / 明示的な自動車通行根拠があるtrackだけ保持
未解決属性で停止 / structural限定placeholder
```

不確実な連続パラメータが増え、相互作用を含む評価が研究質問に必要となった段階でSALibを検討する。感度分析は設定値の変化に対する結果依存性、ablation studyは構成要素を除いた場合の寄与として区別する。

## 推奨学習順序

| 段階 | 学習内容 | 到達目標 |
|---|---|---|
| 1 | SargentのV&V | Verification、Validation、data validity、operational validityを区別できる |
| 2 | SUMO edge type、OSM import、`netconvert` | 属性の採用源と欠損時挙動を説明できる |
| 3 | OSM access、oneway、lanes、maxspeed | OSMタグからSUMO permissionsまでの解釈順を説明できる |
| 4 | pytestとW3C PROV | fixture、期待結果、値の来歴を設計できる |
| 5 | ACM、IEEE、SALib | artifactと主要設定の頑健性評価を計画できる |

## 最小読書セット

時間が限られる場合は、次の六件を優先する。

1. [Sargent: An Introduction to Verification and Validation of Simulation Models](https://informs-sim.org/wsc13papers/includes/files/027.pdf)
2. [SUMO edge type file](https://sumo.dlr.de/docs/SUMO_edge_type_file.html)
3. [SUMO OpenStreetMap import](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html)
4. [OSM `access`](https://wiki.openstreetmap.org/wiki/Key:access)
5. [ACM SIGSOFT Empirical Standards](https://www2.sigsoft.org/EmpiricalStandards/)
6. [W3C PROV Overview](https://www.w3.org/TR/2013/NOTE-prov-overview-20130430/)

この六件を理解した後、現在の`priority`、permissions、placeholder、validator、fixtureおよび感度分析を、場当たり的な設定ではなく、シミュレーション研究のV&Vと再現可能性の構成要素として説明できることを確認する。
