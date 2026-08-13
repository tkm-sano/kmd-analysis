# Why・What・Howで理解する v17属性解決 Phase 1

## 全設計意図・階層・プログラム構造を日本語で学ぶ版

## 初学者向け解説書

> 本版は、研究目的、authority、data、処理、成果物、検証、Phase、人の責任という全階層を示したうえで、プログラム内部の処理、データ型、検証、例外、ハッシュ、テストの関係を日本語中心で説明する。

---

# 0. この文書の読み方

本書は、v17属性解決のPhase 1を、すべて次の順序で説明する。

1. **Why：なぜ必要なのか**
2. **What：何を作るのか**
3. **How：どのように作るのか**

専門用語を先に並べるのではなく、まず必要性を理解し、その後に成果物と作業方法を説明する構成である。

本書の対象となる成果物は次の6つである。

1. 仕様同期表
2. v17 Configuration
3. JSON Schema
4. Registry群
5. Semantic Invariant一覧
6. 差分レビュー報告書

---

# 0A. この解説書自体の位置付け

## Why：なぜ文書の位置付けを明示するのか

本プロジェクトには、規範仕様書、成果物説明書、初心者向け解説書、Configuration、Schema、Registry、fixture、oracle、実装code、検証報告書など、目的の異なる文書とfileが存在する。

これらを同じ「仕様」として扱うと、次の混乱が起こる。

- 説明文が実装上の正式ruleだと誤解される。
- code例が実装済みの事実だと誤解される。
- 初心者向けのたとえが機械可読な定義より優先される。
- 現状説明と将来の要求が混ざる。
- v16の実行事実とv17の設計方針が混ざる。

そのため、この文書が何を決め、何を決めないかを先に固定する必要がある。

## What：この文書の役割

この文書は、**v17属性解決仕様とPhase 1成果物体系を理解するための解説書**である。

この文書が行うことは次である。

- 各設計判断の意図を説明する。
- 各成果物の階層上の位置を説明する。
- 上位目的と下位実装のつながりを説明する。
- 技術用語とプログラム構造を日本語で説明する。
- Why・What・Howで第三者へ説明できる形にする。
- どの層が何を保証するかを整理する。

この文書が行わないことは次である。

- v17の正式なenumやruleを新たに変更すること。
- Configurationの代わりになること。
- JSON Schemaの代わりになること。
- Registryの代わりになること。
- production codeが実装済みであると証明すること。
- fixtureやoracleが合格済みであると証明すること。
- Attribute Resolution Acceptanceを承認すること。
- SUMOネットワークの妥当性を承認すること。

## How：どの文書を正式な基準として読むか

文書と成果物の位置付けは、次の順で理解する。

```text
正式な判断を確認したい
  → v17規範仕様書、承認済みdecision record

今回のrun設定を確認したい
  → v17 Configuration

許可されるfieldや型を確認したい
  → JSON Schema

許可されるrule・state・stop codeを確認したい
  → Registry

意味上の検査条件を確認したい
  → Semantic Invariant一覧

仕様とrepositoryの対応を確認したい
  → 仕様同期表

現在不足しているものを確認したい
  → 差分レビュー報告書

背景や意図を理解したい
  → 本解説書
```

---

# 0B. 最上位から見た研究全体の階層

## Why：なぜ研究全体から見るのか

属性解決は、研究そのものの最終目的ではない。

属性解決だけを見ていると、なぜ未解決値を厳しく停止するのか、なぜhashやprovenanceが必要なのか、なぜformalとstructuralを分けるのかが分かりにくい。

最上位の研究目的から下位のデータ処理までをつなぐ必要がある。

## What：研究目的からデータまでの階層

```text
第0層：研究目的
  実世界に近い交通・配送条件で、
  古典手法と量子・ハイブリッド手法を比較可能にする。

第1層：実験設計
  どの地域、車両、需要、時間、評価指標を使うか決める。

第2層：交通シミュレーションモデル
  道路、車線、速度、通行可否、信号、需要を表現する。

第3層：SUMOネットワーク
  junction、edge、lane、connection、TLSを構成する。

第4層：SUMO入力生成
  plain XML等へ方向、車線、速度、permissionを出力する。

第5層：属性解決
  OSM情報から正式な属性値、状態、由来を決める。

第6層：分類・正規化
  OSM tagを読み、表記を統一し、caseを分類する。

第7層：原典データ
  OSM Node、Way、Relation、Tag、境界、relation closure。
```

上位層は下位層の出力に依存する。

例えば、属性解決に誤りがあると、SUMO edgeやlaneが誤り、旅行時間や配送経路が変わり、最終的な手法比較も変わる。

## How：各層で問うべきこと

| 層 | 主な問い |
|---|---|
| 研究目的 | 何を比較し、何を明らかにするのか。 |
| 実験設計 | 比較条件は公平で再現可能か。 |
| シミュレーション | 現実の交通条件をどこまで表現するか。 |
| SUMOネットワーク | edge、lane、connectionは正しいか。 |
| 入力生成 | Resolver結果を損なわずSUMOへ渡したか。 |
| 属性解決 | 値は何で、どの根拠で決めたか。 |
| 分類・正規化 | 入力をどのcaseとして認識したか。 |
| 原典 | 元データは何で、変更されていないか。 |

---

# 0C. システム処理の階層

## Why：なぜ処理階層を分けるのか

一つの処理が複数の責任を持つと、誤りの発生箇所と修正箇所が分からなくなる。

例えば、`oneway=-1`を誤ってforwardへ出力した場合でも、原因は次のどこかにあり得る。

- OSM tagの読込み
- 値の正規化
- direction rule
- Directed Segment生成
- plain XMLへの書出し
- SUMO edge IDの対応付け

処理階層を分けることで、責任と検証点を固定する。

## What：処理パイプライン

```text
原典読込み層
  Loader

構文解釈層
  Parser

表記統一層
  Normalizer

case判定層
  Classifier

値決定層
  Resolver

意味検査層
  Semantic Validator

成果物固定層
  Serializer / Manifest Writer

SUMO入力生成層
  Permission Materializer / Plain XML Builder

SUMO変換層
  netconvert

ネットワーク統合検証層
  Network Integration Validator

交通モデル調整層
  Calibration

独立妥当性確認層
  Validation

研究実験層
  Scenario Execution / Solver Comparison
```

## How：各処理の責任境界

| 処理 | 責任 | 責任外 |
|---|---|---|
| Loader | fileを読み、原典値を保持する | 値の意味を決めない |
| Parser | 文字列を構文単位へ分ける | 採用値を決めない |
| Normalizer | 同義表記を標準値へ変える | 欠損を推定しない |
| Classifier | caseと適用候補ruleを決める | effective valueを決めない |
| Resolver | 値、状態、由来、停止理由を決める | SUMO XMLを直接編集しない |
| Validator | 規則違反を検出する | 値を自動修正しない |
| Serializer | 検証済みdataを固定形式へ書く | 解決ruleを再判断しない |
| Materializer | formal結果をSUMO入力へ反映する | 不足値を補わない |
| netconvert | SUMO networkを生成する | 研究上のformal eligibilityを決めない |
| Calibration | parameterを観測へ合わせる | network coding errorを隠さない |
| Validation | 別dataで妥当性を確認する | code testの代わりにならない |

---

# 0D. データモデルの階層

## Why：なぜデータ粒度を分けるのか

「道路1本」という表現だけでは、方向、車線、車種、時間条件を正しく扱えない。

例えば同じOSM Wayでも、次が異なる可能性がある。

- forwardとbackwardで速度が異なる。
- laneごとに通行可能車種が異なる。
- deliveryだけが通行可能である。
- 特定時間だけpermissionが変わる。

したがって、処理対象を段階的に細分化する。

## What：データ粒度の階層

```text
Source Dataset
  └─ OSM Node / Way / Relation
      └─ Source Way Interval
          └─ Directed Segment
              └─ Directional Lane
                  └─ Vehicle・Scenario Context Tuple
                      └─ Attribute Resolution Record
```

### 各階層の意味

| 階層 | 意味 |
|---|---|
| Source Dataset | 取得したOSM全体 |
| OSM Way | 原典のnode列とtagを持つ道路要素 |
| Source Way Interval | junction等で分割された原典上の区間 |
| Directed Segment | 原典を保ったまま走行方向を付けた区間 |
| Directional Lane | 走行方向から見た個別車線 |
| Vehicle・Scenario Tuple | 車種、時間、目的、permit等を加えた評価単位 |
| Resolution Record | 一つの属性に対する解決結果 |

## How：一件の道路が複数recordになる例

```text
OSM Way 1001
  双方向
  forward 2 lanes
  backward 1 lane
  7 vehicle classes
  1 scenario context
  permission attribute
```

この場合、permissionだけでも概念上は次の件数になる。

```text
3 lanes × 7 vehicle classes × 1 scenario = 21 tuples
```

さらにspeed、lane count、direction等の別属性recordが存在する。

この細分化により、「道路としては解決済みだが、特定lane・特定車種だけ未解決」という状態を表現できる。

---

# 0E. Authorityの階層

## Why：なぜ正式な基準を階層化するのか

同じ規則が文書、YAML、Schema、codeに存在すると、どれを正しい基準とするかが問題になる。

例えば、仕様書では`rule_derived`、codeでは`derived_osm_rule`、Schemaでは両方許可という状態では、v17の正式語彙が不明である。

そこで、判断・機械表現・検証・実装を階層化する。

## What：Authority hierarchy

```text
第1位：承認済みDecision Record
  何を採用するかという最終判断

第2位：Machine-readable Configuration・Registry
  今回のrunで有効な判断と正式語彙

第3位：JSON Schema・Semantic Invariant
  許可される構造と意味条件

第4位：規範仕様書
  判断の意味、条件、境界、背景

第5位：Fixture・Independent Oracle
  小さなcaseでの具体的期待結果

第6位：Production Code
  上位contractを実行する実装

第7位：Generated Artifact
  実行の結果として生成されたdata
```

注意点として、Generated Artifactは実行結果であり、ruleの正しさを自分自身では証明しない。

## How：不一致が見つかった場合

```text
codeとRegistryが違う
  → codeをRegistryへ合わせる。
  → codeの都合でRegistryを暗黙変更しない。

Schemaと仕様書が違う
  → Decision Recordを確認する。
  → 正式判断に合わせて両方を同期する。

Oracleとproduction出力が違う
  → production出力を正解扱いしない。
  → 仕様、Oracle、実装を独立reviewする。
```

---

# 0F. 成果物の階層

## Why：なぜ成果物の種類を分けるのか

すべてのfileを「成果物」とだけ呼ぶと、規則を定めるfile、検査するfile、実行結果を記録するfileが混ざる。

成果物の種類によって、変更方法、review方法、正式性が異なる。

## What：成果物の5分類

### 1. 規範成果物

何を正しいとするかを定義する。

```text
v17規範仕様書
Decision Record
Registry
Semantic Invariant一覧
```

### 2. 実行選択成果物

今回のrunで何を有効にするかを定める。

```text
v17 Configuration
Scenario Context
Environment Configuration
```

### 3. 構造検査成果物

data形式を定める。

```text
JSON Schema
Configuration Schema
Manifest Schema
```

### 4. 試験・検証成果物

規則どおり動くかを確認する。

```text
Fixture
Oracle
Validation Report
Coverage Report
Acceptance Artifact
```

### 5. 実行生成成果物

処理の結果として作られる。

```text
Classification Artifact
Resolution Artifact
Directed Segment Artifact
Permission Expectation
Plain XML
.net.xml
Build Manifest
```

## How：変更の扱い

| 成果物分類 | 変更時に必要なこと |
|---|---|
| 規範 | 承認、version更新、関連成果物同期 |
| 実行選択 | run ID更新、hash記録 |
| 構造検査 | Schema version更新、fixture更新 |
| 試験・検証 | independent review、coverage確認 |
| 実行生成 | 再実行し、直接手修正しない |

---

# 0G. 検証と受入の階層

## Why：なぜ「testに通った」を一つにまとめないのか

異なる検査は、異なる問いに答える。

`pytest`が通っても、全道路recordが解決済みとは限らない。

JSON Schemaが通っても、`oneway=-1`の方向が正しいとは限らない。

Attribute Resolution Acceptanceが通っても、SUMO connectionやTLSが正しいとは限らない。

## What：検証階層

```text
第1層：構文・形式検査
  JSON/YAMLが読めるか。
  型・enum・required fieldが正しいか。

第2層：意味検査
  field間、record間、集合、hashの条件が正しいか。

第3層：Unit Test
  小さなfunctionが期待どおり動くか。

第4層：Fixture・Oracle Test
  仕様case全体が独立した期待結果と一致するか。

第5層：Integration Test
  module間の接続が正しいか。

第6層：Full-population Accounting
  全入力が解決・除外として数えられているか。

第7層：Attribute Resolution Acceptance
  formal属性成果物を次工程へ渡せるか。

第8層：SUMO Network Integration Acceptance
  SUMO network構造が正しいか。

第9層：Calibration
  parameterを観測dataへ合わせられるか。

第10層：Independent Validation
  calibration未使用dataでも妥当か。

第11層：Research Experiment Readiness
  比較実験へ使用可能か。
```

## How：検査結果の言い方

避ける表現：

```text
テストが通ったのでネットワークは正しい。
```

適切な表現：

```text
JSON Schema validationは通過した。
Semantic validationは未実行である。
Attribute Resolution Acceptanceはnot_runである。
したがってformal networkの入力適格性は未承認である。
```

---

# 0H. LifecycleとPhaseの階層

## Why：なぜPhaseを分けるのか

規則を決める作業、正解を作る作業、codeを書く作業、全件実行する作業を同時に行うと、production codeが事実上の正解を作ってしまう。

上流contractを先に固定し、下流実装を後から合わせる必要がある。

## What：Lifecycle

```text
v16履歴固定
  ↓
v17規範仕様完成
  ↓
Phase 1：Authority Synchronization
  仕様同期表、Configuration、Schema、Registry、Invariant、差分レビュー
  ↓
Phase 2：Independent Fixtures and Oracles
  小さな入力と独立正解の固定
  ↓
Phase 3：State Contract Migration
  resolution_status / value_origin
  ↓
Phase 4：Directed Segment Integration
  ↓
Phase 5：Directional Lane Resolution
  ↓
Phase 6–9：Access・Conditional・Speed
  ↓
Phase 10：Formal Evidence Method
  ↓
Phase 11：Integration Test
  ↓
Phase 12：Full-population Run
  ↓
Phase 13：Stop Record Resolution
  ↓
Phase 14：Attribute Resolution Acceptance
  ↓
SUMO Network Integration
  ↓
Calibration・Validation
  ↓
Research Experiment
```

## How：Phase 1の境界

Phase 1で行う：

- 規則と語彙を一致させる。
- data contractを固定する。
- 検査条件を固定する。
- repositoryとの差を記録する。
- Phase 2のfixture対象を決める。

Phase 1では行わない：

- production Resolverの全面実装。
- full-population run。
- 未解決recordの解消。
- formal network承認。
- calibration。
- solver comparison。

---

# 0I. 人とプログラムの責任階層

## Why：なぜ人と機械の責任を分けるのか

プログラムは、登録されたruleを高速かつ一貫して適用できる。

しかし、どのruleを正式採用するか、どの証拠を十分とするか、研究目的に対して何件まで未解決を許すかは、人間の判断である。

逆に、人間がproduction outputを手作業で直すと、再現性が失われる。

## What：責任分担

| 主体 | 主な責任 |
|---|---|
| 仕様策定者 | 判断規則、境界、受入条件を定める |
| Registry管理者 | 正式語彙とrule versionを管理する |
| Fixture作成者 | 小さな入力caseを設計する |
| Oracle作成・review者 | production codeから独立した期待結果を承認する |
| 実装者 | contractどおりにcodeを書く |
| Validator実装者 | 不変条件を機械検査へ落とす |
| 実行者 | 固定環境・commandでrunする |
| Reviewer | 仕様と成果物の整合を確認する |
| Acceptance承認者 | gate結果と証拠を確認し、次工程を承認する |
| Program | 登録済みruleを適用し、結果と停止を記録する |

## How：禁止する責任の混同

- production codeがOracleを生成しない。
- 実行者が出力JSONを手で修正しない。
- Validatorが未解決値を自動補完しない。
- typemapがformal permission authorityにならない。
- code中の未登録if文が新しい規範ruleにならない。
- reviewerの判断をlogなしで直接outputへ反映しない。

---

# 0J. 設計意図一覧

## Why：なぜ意図へIDを付けるのか

個別のruleだけを読むと、なぜそのruleがあるのかを見失いやすい。

設計意図をID化することで、複数の成果物や実装が同じ目的へ向いているか確認できる。

## What：主要な設計意図

| 意図ID | 意図 | 主に関係する層・成果物 |
|---|---|---|
| INT-001 | 原典OSMを不変に保つ | Loader、Directed Segment、hash |
| INT-002 | 方向情報を原典node順に結び付ける | Directed Segment、relation mapping |
| INT-003 | 値の状態と値の由来を分離する | Schema、State Registry、Resolver |
| INT-004 | 不明値を推測でformalへ入れない | Formal profile、Invariant、Acceptance |
| INT-005 | 開発用仮定と研究入力を分離する | Structural/Formal、Assumption Registry |
| INT-006 | 入力順に依存しない結果を得る | Access dominance、metamorphic test |
| INT-007 | lane・directionの適用範囲を保持する | Target Scope、AccessRule |
| INT-008 | rule競合を隠さず停止する | Stop Code、Resolver、Validator |
| INT-009 | 同じ入力・環境から同じ成果物を得る | Canonical JSON、hash、manifest |
| INT-010 | どの値がどの根拠から来たか追跡する | Provenance、Registry、Evidence |
| INT-011 | 仕様と実装の乖離を検出する | Traceability Matrix、Gap Review |
| INT-012 | codeを規範の唯一の保管場所にしない | Registry、Configuration、Schema |
| INT-013 | production codeから独立した正解を持つ | Fixture、Oracle、Review |
| INT-014 | 属性成果物とSUMO network承認を分離する | Acceptance hierarchy |
| INT-015 | software testと交通モデル妥当性を分離する | Test、Calibration、Validation |
| INT-016 | 母集団からrecordが静かに消えるのを防ぐ | Population accounting、Exclusion Manifest |
| INT-017 | v16履歴を改変せずv17へ移行する | Transition、output directory、manifest |
| INT-018 | 各moduleの責任を小さく保つ | Loader～Materializer architecture |
| INT-019 | 検査失敗時に原因と修正先を特定する | Finding、stop code、structured log |
| INT-020 | 次工程へ進める条件を機械判定可能にする | Acceptance Configuration、Artifact |

## How：意図を成果物へ対応付ける例

### INT-004：不明値を推測でformalへ入れない

```text
規範仕様
  → formalではmodel_assumed禁止

Configuration
  → allow_model_assumed: false

Schema
  → formal＋model_assumedを拒否

Registry
  → model_assumed.formal_eligible=false

Semantic Invariant
  → formal artifact内件数が0

Fixture
  → formal assumed値を拒否するnegative case

差分レビュー
  → codeが仮定値をformalへ出す場合はCritical/Major finding

Acceptance
  → model_assumed_count = 0
```

このように、一つの意図が複数層で繰り返し保護される。

---

# 0K. 六つのPhase 1成果物の相互関係

## Why：なぜ六つを独立fileにしつつ連携させるのか

一つの巨大fileにすべてを書くと、機械処理しにくくなる。

完全に独立させると、用語やruleがずれる。

したがって、責任を分離しながら参照関係を明示する。

## What：参照関係

```text
仕様同期表
  各Requirement IDを起点に全成果物を横断する。

Configuration
  Schema・Registryのversionとhashを参照する。

JSON Schema
  recordのfieldとenumを検査する。

Registry
  enum、rule、stop code、assumptionの意味を提供する。

Semantic Invariant
  Schemaで扱えない関係条件を定義する。

差分レビュー
  上記成果物とrepository実装の不一致を記録する。
```

## How：循環を避ける

望ましい参照：

```text
Configuration → Registry version
Schema → enumの構造
Validator → Registry entry
Traceability → 全成果物のlocation
Gap Review → Requirement ID
```

避けるべき参照：

```text
Registryの正式値をproduction codeから自動抽出する。
Oracleをproduction outputから生成する。
Configurationの意味をcodeだけで定義する。
Schema enumとRegistry enumを別々に手入力し、同期確認しない。
```

---

# 1. v17属性解決とは何か

## Why：なぜ属性解決が必要なのか

OpenStreetMapの道路データには、次のような情報が含まれる。

- 一方通行かどうか
- 車線数
- 方向別車線数
- 制限速度
- 車種別の通行可否
- 曜日や時間帯による条件付き規制

しかし、すべての道路について完全な情報が存在するわけではない。

例えば、次のような状態がある。

- `oneway`が書かれていない。
- 総車線数はあるが、方向別車線数がない。
- 一般車の規制と配送車の規制が異なる。
- 平日の特定時間だけ通行できない。
- 複数のaccess規則が互いに矛盾する。
- 値自体は正しいが、現在のプログラムでは扱えない。

これらを曖昧なままSUMOへ変換すると、プログラムが暗黙に値を補ったり、実装順によって異なる結果を出したりする可能性がある。

したがって、SUMOネットワークを作る前に、各属性について以下を明示する必要がある。

- 値が決まったか。
- 決まっていないか。
- どの根拠で決めたか。
- 仮定を使ったか。
- 正式な研究入力として使えるか。

## What：属性解決とは何か

属性解決とは、OpenStreetMapの入力を読み、各属性について次の情報を出力する処理である。

```text
処理結果の状態
値の由来
決定した値
使用した規則
使用した証拠
停止理由
provenance
```

例えば、通常道路で`oneway`が欠損しており、登録済みの規則から双方向と判断した場合は、次のように記録する。

```text
resolution_status: resolved
value_origin: rule_derived
effective_value: no
rule_id: OSM_ONEWAY_ABSENT_DEFAULT_NO
```

一方、方向別車線数を決める正式な根拠がない場合は、次のように停止する。

```text
resolution_status: unresolved
value_origin: null
effective_value: null
stop_code: LANE_DIRECTIONAL_ALLOCATION_MISSING
```

## How：どのように実現するのか

属性解決を正しく実現するには、自然言語の仕様書だけでは不十分である。

仕様書に書かれた判断を、次の成果物へ分ける必要がある。

```text
人間が読む判断
    ↓
仕様同期表で反映先を整理
    ↓
Configurationで今回の設定を固定
    ↓
Schemaでデータ形式を検査
    ↓
Registryで正式な語彙と規則を管理
    ↓
Semantic Invariantで意味を検査
    ↓
差分レビューで既存repositoryとの違いを確認
```


# 2. 技術的背景：OSMからSUMOへ何が変換されるのか

この章は、後続の6成果物を理解するための前提となる技術背景を説明する。ここで説明する内容は、v17の新しい規範を追加するものではなく、既存仕様で採用した構造がなぜ必要なのかを理解するための補足である。

## Why：なぜデータ変換の途中を明示する必要があるのか

OpenStreetMapとSUMOは、道路を表現する目的とデータ構造が異なる。

OpenStreetMapは、世界中の地理情報を共同編集するための地理データベースである。一方、SUMOは、車両がどの方向へ、どの車線を通り、どの接続を経由できるかを計算する交通シミュレータである。

そのため、OpenStreetMapからSUMOへの変換は、単純なファイル形式変換ではない。

実際には、次の判断を含む。

- 一つのOSM Wayから、何本の方向別edgeを作るか。
- 総車線数を各方向へどう割り当てるか。
- lane別accessをSUMO laneへどう対応付けるか。
- turn restrictionをどの接続へ反映するか。
- 欠損した速度やpermissionをどう扱うか。
- 条件付き規制をどの時点・車種・目的に適用するか。

これらの判断を`netconvert`やtypemapへ暗黙に任せると、生成結果は得られても、研究者が「なぜその値になったか」を説明できない可能性がある。

したがって、OSMとSUMOの間に、判断内容を記録するResolver層を設ける必要がある。

## What：OSM側のデータ構造

OpenStreetMapの基本要素は次の3つである。

### Node

緯度・経度を持つ点である。道路の形状点、交差点、信号、施設位置等に使用される。

### Way

複数のNodeを順番に並べた線または面である。道路の場合、このNodeの並び順が`forward`方向の基準になる。

例えば、WayのNode列が次であるとする。

```text
Node A → Node B → Node C
```

このとき、OSMにおける方向は次のように解釈する。

```text
forward  = A → B → C
backward = C → B → A
```

`oneway=-1`は、Wayを構成するNode列を変更する指示ではなく、通行方向が`backward`だけであることを示す。

### Relation

複数のNode、Way、Relationを役割付きでまとめる要素である。交通ネットワークでは、turn restrictionの`from`、`via`、`to`等に使用される。

### Tag

Node、Way、Relationに付与されるkey-value形式の属性である。

例：

```text
highway=residential
oneway=yes
lanes=2
maxspeed=40
access=no
bus=yes
```

重要なのは、**タグがないこと**と、**タグに明示値があること**は異なるという点である。

例えば、`oneway`が存在しないことを、入力データ上で`oneway=no`と書かれていることと同一視してはならない。最終的な走行方向が同じになったとしても、由来が異なるためである。

```text
oneway=no が明示されている
→ source_explicit

onewayが欠損し、登録済み規則からnoを導出した
→ rule_derived
```

## What：SUMO側のデータ構造

SUMOの道路ネットワークは、主に次の要素から構成される。

### Junction

道路の接続点である。OSM Nodeと一対一とは限らず、変換時に統合・分割される場合がある。

### Edge

一つの方向へ走行する道路区間である。SUMOのedgeは基本的に有向であり、双方向道路は通常、反対方向のedgeを別々に持つ。

```text
OSMの双方向Way
    ↓
SUMOのforward edge
SUMOのbackward edge
```

### Lane

Edgeに属する車線である。速度、通行可能vClass、長さ等を持つ。

### Connection

あるlaneから別のlaneへ進める関係である。道路が図形上つながっているだけでは、車両が実際に移動できるとは限らない。

### Traffic Light Logic

信号制御のphaseと、制御対象connectionの対応である。connectionが変われば、信号レビューもやり直す必要がある。

### Plain XMLと`.net.xml`

SUMOでは、edge、node、connection等をplain XMLとして記述し、`netconvert`で実行用の`.net.xml`を生成できる。

```text
plain XML
   ↓ netconvert
.net.xml
```

`.net.xml`には、junction内部構造、connection、right-of-way等の生成情報が含まれる。そのため、生成後の`.net.xml`を手作業で修正するのではなく、入力側のplain XMLやResolver結果を修正して再生成する必要がある。

## What：Resolverが担う中間表現

Resolverは、OSM sourceとSUMO materializationの間に置かれる。

```text
OSM source
    ↓
分類
    ↓
属性解決 Resolver
    ↓
formal / structural attribute artifact
    ↓
Permission Materializer・plain XML生成
    ↓
netconvert
    ↓
SUMO network audit
```

Resolverは、次の問いに答える。

- この値は決まったか。
- どのsource tagを読んだか。
- どのruleを使ったか。
- source明示値か、規則導出値か、仮定値か。
- どの方向・lane・車種・時間に適用されるか。
- 不明または競合なら、なぜ停止したか。

この中間artifactがあることで、SUMOへ入る前の判断を単独で検証できる。

## How：Directed Segmentが方向を保持する仕組み

OSM Wayをそのまま反転すると、方向別tagとの対応が崩れる可能性がある。

例えば次のtagがある。

```text
lanes:forward=2
lanes:backward=1
maxspeed:forward=50
maxspeed:backward=40
```

WayのNode順を反転してしまうと、`forward`と`backward`の意味も入れ替わる。そのため、v17ではsource Wayを変更せず、方向を別の属性として表す。

```text
Directed Segment
= source Wayの一定区間 + source direction
```

例：

```text
ds:12345:0:4:forward
ds:12345:0:4:backward
```

この表現により、source Way ID、Node列、方向別tag、SUMO edgeの関係を追跡できる。

## How：laneの順序を変換する仕組み

OSMのlane情報は、各走行方向から見た左から右の順序で解釈する。一方、SUMOのlane indexは右端を0として扱う。

そのため、Resolverのlane positionをSUMO indexへ変換する必要がある。

```text
sumo_index = lane_count - 1 - lane_position
```

3車線の例：

| Resolverのlane position | 意味 | SUMO index |
|---:|---|---:|
| 0 | 左端 | 2 |
| 1 | 中央 | 1 |
| 2 | 右端 | 0 |

この変換を明文化しないと、lane別permissionが左右反転する危険がある。

## How：access ruleを適用する仕組み

access処理では、最初に「どのtupleへ適用されるか」を決め、その後に「複数ruleのどれが優先されるか」を決める。

### 適用対象の決定

```text
direction scope
lane scope
```

例えば`bus:lanes:forward`は、forward方向の指定laneだけに適用する。

### 条件の評価

```text
vehicle
日時
目的
authorization・permit
```

### 複数ruleの比較

v17では、次の4軸を使用する。

```text
spatial
vehicle
temporal
purpose
```

すべての軸で同等以上に限定され、少なくとも一軸でより限定されるruleを、より具体的なruleとして扱う。

これは単純な「最後に書かれたruleを採用する」方式ではない。入力順を変えても結果が変わらないようにするためである。

## How：formalとstructuralを分ける理由

道路ネットワークの開発では、欠損値があると処理を最後まで試せない場合がある。

そこでstructural profileでは、登録済みの仮定を使って、構造確認用networkを作ることを許す。

例：

```text
総車線数=4
方向別車線数なし
→ structuralでは2+2と仮定可能
```

しかし、この2+2はsourceから確認された値ではない。そのためformal profileでは使用しない。

```text
structural
→ 実装・構造確認用
→ model_assumedを条件付きで許可

formal
→ 正式な研究入力候補
→ model_assumedを禁止
```

この分離により、「SUMOが動いたこと」と「研究入力として正当であること」を区別できる。

---

# 3. 技術的背景：決定性・provenance・検証

## Why：なぜ同じ入力から同じ結果を得る必要があるのか

研究で使用するnetworkは、後から同じ条件で再生成できなければならない。

結果が次の要因で変わると、比較実験の信頼性が下がる。

- Python dictionaryやrecordの処理順
- ruleの記載順
- 使用するSchema・Registry version
- SUMO version
- library version
- 入力fileの変更
- 手作業による出力修正

そのため、v17では決定性と再現性を別々に確認する。

### 決定性

同じ論理入力に対して、同じ判断を返す性質である。

例：独立したaccess recordの順番を変えても、最終permissionが変わらない。

### 再現性

同じinput、configuration、environment、commandから、同じartifactを再生成できる性質である。

## What：provenanceとは何か

provenanceは、値やartifactがどこから来たかを追跡する情報である。

属性値については、例えば次を記録する。

```text
source Way ID
source tag
使用rule ID
使用evidence ID
生成software version
configuration hash
実行時刻
```

`value_origin`はprovenance全体を置き換えるものではない。

```text
value_origin
→ 値の由来を分類する短い状態

provenance
→ どのsource・rule・処理から生成されたかを詳しく記録
```

## What：hashは何を保証するのか

hashは、fileやデータ内容から計算される固定長の識別値である。

内容が1文字でも変化すると、通常は異なるhashになる。

v17ではSHA-256を使用し、JSONについてはRFC 8785に基づくcanonicalizationを行ってから計算する。

JSONは、同じ意味でもkey順や数値表記が異なる場合がある。

```json
{"a":1,"b":2}
```

```json
{"b":2,"a":1}
```

意味は同じでもbyte列は異なる。canonicalizationは、意味が同じJSONを同じbyte表現へそろえるために使う。

hashは「内容が正しい」こと自体を保証しない。保証するのは、登録した内容から変化していないこと、または同じ内容を再生成できたことに近い。

## What：validation・verification・acceptanceの違い

この研究では、複数の検査を分離する。

| 検査 | 主な問い |
|---|---|
| Schema validation | データの形は正しいか。 |
| Semantic validation | データの意味・関係は正しいか。 |
| Fixture/oracle test | 小さな既知caseで期待結果と一致するか。 |
| Full-population accounting | 全入力が処理・除外として数えられているか。 |
| Attribute Resolution Acceptance | formal属性artifactを次工程へ渡せるか。 |
| SUMO Network Integration Acceptance | SUMO networkへ正しく統合されたか。 |
| Calibration | 観測値へモデルを合わせられるか。 |
| Independent validation | 別データでも交通現象を再現できるか。 |

software testが通っただけでは、formal networkが承認されたことにはならない。

## How：fail-closedで処理する

fail-closedとは、不明・未対応・競合がある場合に、推測して処理を続けず停止する方針である。

例：

```text
未登録のoneway値
→ defaultへ置換しない
→ ONEWAY_VALUE_UNSUPPORTEDで停止
```

```text
複数の最大access ruleが異なる結果
→ 入力順で選ばない
→ ACCESS_SPECIFICITY_CONFLICTで停止
```

fail-closedは処理成功率を下げる場合があるが、研究入力へ説明不能な値が混入することを防ぐ。

---

# 技術補章A：プログラムの言葉で見る属性解決

この補章では、これまで説明した属性解決を、実際のプログラムがどのような部品に分かれ、どのようなデータを受け渡すかという観点から説明する。

本文では可能な限り日本語を用いる。ただし、JSONの項目名、Pythonのクラス名、設定ファイルのキーなどは、既存仕様と外部ツールとの互換性を保つため英語表記を残す。

本補章のコードは**説明用の例**であり、現在のrepositoryに同じクラス、関数、配置が実装済みであることを示すものではない。

---

## A-1. 技術用語を日本語へ置き換える

### Why：なぜ用語の対応が必要なのか

ソフトウェア開発では、同じ概念が英語のまま使用されることが多い。

例えば、`record`、`field`、`schema`、`validator`という語を理解しないまま仕様書を読むと、実際に何を作るのかが分かりにくい。

一方、英語をすべて日本語へ置き換えると、既存code、JSON、YAML、SUMO、OSMの公式用語と対応しなくなる。

そのため、本書では次の方針を採る。

> 説明文では日本語を主に使い、プログラム上の正式な識別子は英語を保持する。

### What：主要用語の対応表

| 英語・識別子 | 本書で使う日本語 | プログラム上の意味 |
|---|---|---|
| repository | リポジトリ、開発資産の保管場所 | code、設定、test、文書をversion管理する場所 |
| artifact | 成果物、生成物 | 処理によって作られ保存されるfile |
| record | レコード、1件のデータ | JSON objectやCSVの1行に相当する単位 |
| field | 項目 | record内のkeyとvalueの組 |
| key | キー、項目名 | `resolution_status`などの名前 |
| value | 値 | `resolved`などの内容 |
| enum | 列挙型、許可値一覧 | 使用可能な値を有限個に限定する仕組み |
| null | 値なし | 空文字や0とは異なる「値が存在しない」状態 |
| identifier / ID | 識別子 | recordやruleを一意に区別する名前 |
| version | 版 | 仕様やRegistryの変更単位 |
| configuration | 実行設定 | 今回のrunで使用する条件の集合 |
| schema | 構造定義 | field、型、必須条件を定める規則 |
| registry | 登録簿 | 使用可能な正式語彙・rule・IDの一覧 |
| validator | 検証器 | Schemaや意味条件に違反していないか調べる処理 |
| parser | 構文解析器 | 文字列を構造化データへ変換する処理 |
| normalizer | 正規化器 | 同じ意味の表記を統一する処理 |
| classifier | 分類器 | 入力がどのcaseやrule対象かを判定する処理 |
| resolver | 解決器 | 最終的な属性値・状態・由来を決める処理 |
| serializer | 直列化器、書出し器 | Python object等をJSON/YAMLへ変換する処理 |
| deserializer | 読込み変換器 | JSON/YAMLをPython object等へ変換する処理 |
| materializer | 具体化器、入力生成器 | 解決結果からSUMO plain XML等を生成する処理 |
| manifest | 実行記録表 | 入力、version、command、hash、出力をまとめるfile |
| fixture | 固定試験入力 | 特定caseを再現する小規模な入力 |
| oracle | 期待結果 | fixtureに対して正しいと事前定義した出力 |
| invariant | 不変条件 | 常に成立しなければならない意味上の条件 |
| predicate | 判定条件 | true／falseを返す条件式 |
| scope | 適用範囲 | ruleが対象とする方向、lane等 |
| domain | 対象集合 | vehicle、time、purpose等のrule対象集合 |
| exception | 例外 | 通常処理を続行できないプログラム上の異常 |
| stop code | 停止理由コード | データ上の未解決・競合等を表す正式な理由 |
| hash | 内容指紋 | file内容から計算される固定長の値 |
| canonicalization | 正準化、標準形変換 | 同じ意味のデータを同じbyte列へそろえる処理 |
| runtime | 実行時 | codeが実際に動いている時点 |
| production code | 本番処理コード | 全データを処理する正式なcode |
| test | 試験 | 期待する動作を満たすか確認する処理 |
| gate | 受入関門 | 条件をすべて満たした場合だけ次工程へ進める判定 |

### How：実際の文書とcodeでどう表記するか

説明文では次のように書く。

```text
解決器（Resolver）は、正規化済みの道路属性を受け取り、
解決状態（resolution_status）と値の由来（value_origin）を出力する。
```

codeでは既存仕様に合わせて英語識別子を使用する。

```python
resolution_status = "resolved"
value_origin = "rule_derived"
```

Pythonは日本語の変数名も技術的には使用できるが、本研究では推奨しない。

```python
# 技術的には動くが、外部仕様やtoolとの対応が悪くなる
解決状態 = "resolved"
```

推奨方針は次である。

- class名、関数名、JSON keyは英語にする。
- comment、docstring、error説明は日本語で書く。
- 英語識別子の意味を仕様書とRegistryで日本語説明する。
- 略語だけで命名せず、意味が分かる名前を使う。

---

## A-2. プログラム全体を処理段階へ分ける

### Why：なぜ一つの大きな関数にしないのか

すべての処理を一つの関数に書くと、次の問題が起こる。

- どこで値が変わったか分からない。
- OSMの読込み失敗とrule競合を区別できない。
- 一つの修正が別の属性へ影響する。
- fixtureで小さな処理だけを試験できない。
- provenanceを記録しにくい。
- v16とv17の境界が曖昧になる。

そのため、入力から出力までを責任別の処理段階へ分割する。

### What：推奨する処理の流れ

```text
1. 入力読込み
2. 構文解析
3. 正規化
4. 分類
5. 属性解決
6. 意味検証
7. JSON成果物への書出し
8. SUMO入力への具体化
9. netconvert実行
10. SUMOネットワーク統合検証
```

プログラム名に対応させると次のようになる。

```text
Loader
  ↓
Parser
  ↓
Normalizer
  ↓
Classifier
  ↓
Resolver
  ↓
Semantic Validator
  ↓
Serializer
  ↓
Permission Materializer
  ↓
netconvert
  ↓
Network Integration Validator
```

### How：各段階の入力と出力

| 段階 | 入力 | 主な処理 | 出力 |
|---|---|---|---|
| 入力読込み | OSM、設定、Registry | fileを安全に読む | raw object |
| 構文解析 | tag文字列 | 型・構文へ分解する | parsed value |
| 正規化 | parsed value | 表記を統一する | canonical value |
| 分類 | source observation | caseと適用ruleを判定 | classification record |
| 属性解決 | classification＋rule | 値、状態、由来を決定 | resolution record |
| 意味検証 | resolution artifact | 不変条件を検査 | validation result |
| 書出し | validated object | canonical JSONへ変換 | JSON artifact |
| 具体化 | formal artifact | plain XMLへ反映 | SUMO入力file |
| SUMO変換 | plain XML | `netconvert`実行 | `.net.xml` |
| 統合検証 | `.net.xml` | connection等を確認 | network acceptance result |

重要なのは、属性解決の完了とSUMOネットワークの完成を別段階として扱うことである。

---

## A-3. データをPythonの型として表す

### Why：なぜ辞書だけで扱わないのか

Pythonでは、JSONをそのまま`dict`として扱える。

```python
record = {
    "resolution_status": "resolved",
    "value_origin": "rule_derived",
}
```

しかし、すべてを自由な辞書にすると、項目名の打ち間違い、型の違い、必須項目の不足を実行前に見つけにくい。

```python
# 打ち間違いだが、辞書自体は作れてしまう
record["resoluton_status"] = "resolved"
```

そのため、プログラム内部では型を定義して扱う方が安全である。

### What：列挙型とデータクラス

#### 列挙型

列挙型は、許可する値を限定する型である。

```python
from enum import Enum


class ResolutionStatus(str, Enum):
    """属性解決の状態。"""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    CONFLICT = "conflict"
    INVALID = "invalid"
    VALID_BUT_UNSUPPORTED = "valid_but_unsupported"
```

`"finished"`のような未登録値を受け入れないために使用する。

#### 値の由来

```python
class ValueOrigin(str, Enum):
    """解決値がどの根拠から得られたか。"""

    SOURCE_EXPLICIT = "source_explicit"
    SOURCE_NORMALIZED = "source_normalized"
    RULE_DERIVED = "rule_derived"
    EVIDENCE_DERIVED = "evidence_derived"
    DERIVED_VALIDATED_MODEL = "derived_validated_model"
    MODEL_ASSUMED = "model_assumed"
```

#### データクラス

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResolutionRecord:
    """1件の属性解決結果。"""

    record_id: str
    profile: str
    source_way_id: int
    attribute_name: str
    resolution_status: ResolutionStatus
    value_origin: ValueOrigin | None
    effective_value: Any | None
    rule_ids: tuple[str, ...] = field(default_factory=tuple)
    stop_code: str | None = None
```

`frozen=True`は、作成後にrecordを不用意に変更しにくくする指定である。

### How：作成時に検査する

```python
def validate_record(record: ResolutionRecord) -> None:
    """状態と値の組合せを検査する。"""

    if record.resolution_status is ResolutionStatus.RESOLVED:
        if record.effective_value is None:
            raise ValueError("解決済みrecordには有効値が必要である。")
        if record.value_origin is None:
            raise ValueError("解決済みrecordには値の由来が必要である。")
        if record.stop_code is not None:
            raise ValueError("解決済みrecordに停止理由を設定してはならない。")
    else:
        if record.effective_value is not None:
            raise ValueError("未解決recordに有効値を設定してはならない。")
        if record.value_origin is not None:
            raise ValueError("未解決recordに値の由来を設定してはならない。")
        if record.stop_code is None:
            raise ValueError("未解決recordには停止理由が必要である。")
```

この関数は説明用である。実際にはJSON Schemaによる検査とSemantic Validatorによる検査を分担させる。

---

## A-4. `null`、空文字、0、項目省略の違い

### Why：なぜ区別するのか

プログラムでは、次の4つは異なる意味を持つ。

```text
null
""
0
fieldそのものがない
```

これらを混同すると、欠損なのか有効値なのか判断できなくなる。

### What：それぞれの意味

| 表現 | 意味の例 |
|---|---|
| `null` | 項目は定義されているが、値は存在しない |
| `""` | 空の文字列という値が存在する |
| `0` | 数値0という有効値が存在する |
| 項目省略 | record形式に違反、または当該項目を出力していない |

例：

```json
{
  "lane_position": null,
  "stop_code": null,
  "rule_ids": []
}
```

- `lane_position: null`：この属性にはlane位置が適用されない。
- `stop_code: null`：停止していない。
- `rule_ids: []`：rule IDの配列は存在するが、要素が0件である。

### How：Schemaで区別する

```json
{
  "type": "object",
  "required": [
    "lane_position",
    "stop_code",
    "rule_ids"
  ],
  "properties": {
    "lane_position": {
      "type": ["integer", "null"]
    },
    "stop_code": {
      "type": ["string", "null"]
    },
    "rule_ids": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

「適用されないためnull」と「出力漏れ」を分けるため、項目自体は`required`に含める。

---

## A-5. 読込み器・構文解析器・正規化器

### Why：なぜ3つへ分けるのか

OSM tagは基本的に文字列である。

例えば、次の値はすべて一方通行を示す可能性がある。

```text
yes
1
true
```

しかし、fileから文字列を読むこと、値が文法的に正しいか調べること、同じ意味の表記を統一することは別の責任である。

### What：三つの責任

#### 読込み器

fileから値を取得する。

```python
raw_value = way.tags.get("oneway")
```

#### 構文解析器

文字列として解釈可能か確認する。

```python
def parse_oneway(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    return raw_value.strip().lower()
```

#### 正規化器

同じ意味の表記を標準値へそろえる。

```python
ONEWAY_NORMALIZATION = {
    "yes": "yes",
    "1": "yes",
    "true": "yes",
    "no": "no",
    "0": "no",
    "false": "no",
    "-1": "-1",
    "reverse": "-1",
}


def normalize_oneway(parsed_value: str | None) -> str | None:
    if parsed_value is None:
        return None

    try:
        return ONEWAY_NORMALIZATION[parsed_value]
    except KeyError as exc:
        raise UnsupportedOnewayValue(parsed_value) from exc
```

### How：由来を保持する

明示値`yes`と、`1`を`yes`へ変換した値は、最終値が同じでも由来が異なる。

```python
def normalize_with_origin(raw_value: str) -> tuple[str, ValueOrigin]:
    normalized = ONEWAY_NORMALIZATION[raw_value]

    if normalized == raw_value:
        return normalized, ValueOrigin.SOURCE_EXPLICIT

    return normalized, ValueOrigin.SOURCE_NORMALIZED
```

値だけでなく、どの処理を通ったかも出力する。

---

## A-6. 分類器と解決器の違い

### Why：なぜ分けるのか

分類と解決を一つにすると、「どのcaseと判断したか」と「どの値を採用したか」が混ざる。

例えば、`oneway`欠損道路を次のように分類する。

```text
分類：
ordinary road with missing oneway
```

その後、登録済みruleにより次の値を解決する。

```text
解決値：
no
```

分類結果は、ruleや値を将来変更しても比較可能なように保持する必要がある。

### What：分類器

分類器は、入力がどのcaseに属するかを判断する。

```python
@dataclass(frozen=True)
class ClassificationRecord:
    classification_record_id: str
    source_way_id: int
    attribute_name: str
    classification_code: str
    matched_rule_ids: tuple[str, ...]
```

### What：解決器

解決器は、分類結果とRegistryを使い、値・状態・由来を決定する。

```python
def resolve_oneway(
    classification: ClassificationRecord,
    raw_value: str | None,
    rule_registry: "OnewayRuleRegistry",
) -> ResolutionRecord:
    ...
```

### How：分類投影を変えない

解決前後で分類結果が変わっていないことを確認する。

```python
before_hash = hash_classification_projection(classifications)
after_hash = hash_classification_projection(
    extract_classifications(resolution_artifact)
)

if before_hash != after_hash:
    raise ClassificationProjectionChangedError
```

これにより、値解決処理が分類結果を暗黙に書き換えることを防ぐ。

---

## A-7. Directed Segmentをオブジェクトとして表す

### Why：なぜWayを直接反転しないのか

OSM Wayのnode順序は、方向別tagとrelationの基準である。

Wayを反転してしまうと、次の対応が壊れる可能性がある。

- `lanes:forward`
- `lanes:backward`
- `maxspeed:forward`
- `maxspeed:backward`
- turn restriction
- source hash
- provenance

そのため、source Wayは変更せず、走行方向を別のobjectとして表す。

### What：Directed Segmentの型

```python
from enum import Enum


class SourceDirection(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass(frozen=True)
class DirectedSegment:
    directed_segment_id: str
    source_way_id: int
    source_start_index: int
    source_end_index: int
    source_direction: SourceDirection
    source_node_ids: tuple[int, ...]
```

### How：`oneway`から生成する

```python
def generate_directions(canonical_oneway: str) -> tuple[SourceDirection, ...]:
    match canonical_oneway:
        case "yes":
            return (SourceDirection.FORWARD,)
        case "no":
            return (
                SourceDirection.FORWARD,
                SourceDirection.BACKWARD,
            )
        case "-1":
            return (SourceDirection.BACKWARD,)
        case _:
            raise ValueError(
                f"未対応のoneway値である: {canonical_oneway}"
            )
```

backward geometryをSUMOへ出力するときは、走行順としてnode列を逆にしてよいが、source object自体を変更してはならない。

```python
def traversal_nodes(segment: DirectedSegment) -> tuple[int, ...]:
    if segment.source_direction is SourceDirection.FORWARD:
        return segment.source_node_ids
    return tuple(reversed(segment.source_node_ids))
```

`source_node_ids`は原典順のまま保持し、`traversal_nodes`だけを必要時に計算する。

---

## A-8. Rule、判定条件、適用範囲

### Why：なぜruleをif文だけで書かないのか

大量の`if`文へ規則を直接埋め込むと、優先順位、version、出典、fixtureとの対応を追跡しにくい。

```python
# 規則がcodeへ埋め込まれ、根拠やversionが分からない例
if highway == "residential" and oneway is None:
    oneway = "no"
```

v17では、ruleの定義をRegistryに置き、codeはruleを評価する役割を担う。

### What：Rule object

```python
@dataclass(frozen=True)
class OnewayRule:
    rule_id: str
    priority: int
    predicate_name: str
    effective_value: str
    value_origin: ValueOrigin
```

`predicate_name`は、どの判定関数を使用するかを登録する名前である。

### How：Registryからruleを適用する

```python
from collections.abc import Callable

Predicate = Callable[[dict], bool]


def apply_first_matching_rule(
    context: dict,
    rules: tuple[OnewayRule, ...],
    predicates: dict[str, Predicate],
) -> OnewayRule | None:
    ordered_rules = sorted(rules, key=lambda rule: rule.priority)

    for rule in ordered_rules:
        predicate = predicates[rule.predicate_name]
        if predicate(context):
            return rule

    return None
```

規則の順序は、fileの偶然の並び順ではなく、Registryで定義されたpriorityに従う。

ただしaccess specificityのように部分順序で比較する規則では、単純なpriorityを使用しない。

---

## A-9. Access Ruleを集合として比較する

### Why：なぜ単純な番号順では駄目なのか

access ruleは、方向、lane、車種、時刻、目的等の複数条件を持つ。

例えば、次の二つがある。

```text
Rule A:
すべてのmotor_vehicleを禁止

Rule B:
delivery車両を平日10時から12時だけ許可
```

Rule Bは車種と時間の両方で具体的である。

単純に「後に書かれたrule」や「番号が大きいrule」を選ぶと、入力順によって結果が変わる。

### What：適用範囲と意味軸

```python
@dataclass(frozen=True)
class TargetScope:
    directions: frozenset[SourceDirection]
    lane_positions: frozenset[int] | None  # Noneは全lane


@dataclass(frozen=True)
class AccessRule:
    rule_id: str
    target_scope: TargetScope
    spatial_domain: frozenset[str]
    vehicle_domain: frozenset[str]
    temporal_domain: frozenset[str]
    purpose_domain: frozenset[str]
    effect: str  # allowed / denied
```

実際の時間集合は巨大になり得るため、実装では区間やpredicateで表す可能性がある。上記は概念説明用である。

### How：支配関係を判定する

Rule AがRule Bより具体的である条件を、集合の包含として表す。

```python
def is_subset_or_equal(left: frozenset, right: frozenset) -> bool:
    return left.issubset(right)


def dominates(a: AccessRule, b: AccessRule) -> bool:
    comparisons = (
        scope_is_narrower_or_equal(a.target_scope, b.target_scope),
        a.spatial_domain.issubset(b.spatial_domain),
        a.vehicle_domain.issubset(b.vehicle_domain),
        a.temporal_domain.issubset(b.temporal_domain),
        a.purpose_domain.issubset(b.purpose_domain),
    )

    if not all(comparisons):
        return False

    return at_least_one_strictly_narrower(a, b)
```

支配されないruleだけを残す。

```python
def maximal_rules(rules: tuple[AccessRule, ...]) -> tuple[AccessRule, ...]:
    return tuple(
        candidate
        for candidate in rules
        if not any(
            other.rule_id != candidate.rule_id
            and dominates(other, candidate)
            for other in rules
        )
    )
```

残ったruleのeffectがすべて同じなら採用する。

異なる場合は推測せず停止する。

```python
def combine_maximal_rules(
    rules: tuple[AccessRule, ...],
) -> str:
    effects = {rule.effect for rule in rules}

    if len(effects) == 1:
        return effects.pop()

    raise AccessSpecificityConflict(
        stop_code="ACCESS_SPECIFICITY_CONFLICT",
        rule_ids=tuple(rule.rule_id for rule in rules),
    )
```

---

## A-10. JSON SchemaとPython検証器の役割分担

### Why：なぜ両方必要なのか

JSON Schemaはfile単体の構造検査に適している。

PythonのSemantic Validatorは、複数record、外部Registry、hash、入力と出力の関係を調べることに適している。

どちらか一方だけでは不十分である。

### What：Schemaで検査する内容

- 必須field
- 文字列・数値・配列等の型
- enum
- null許可
- resolved時の必須項目
- formal時の`model_assumed`禁止
- IDの文字形式

### What：Semantic Validatorで検査する内容

- source Wayが不変か。
- `oneway=-1`からbackwardだけが生成されたか。
- lane countの合計が一致するか。
- Registry参照が存在するか。
- accessのmaximal ruleが正しいか。
- population equationが成立するか。
- 同一runのhashが一致するか。

### How：検証結果を構造化する

```python
@dataclass(frozen=True)
class ValidationFinding:
    invariant_id: str
    passed: bool
    severity: str
    message_ja: str
    record_ids: tuple[str, ...] = ()
    stop_code: str | None = None
```

検証器は、単に`True`や`False`を返すだけでなく、どの条件が、どのrecordで、なぜ失敗したかを記録する。

```python
def validate_formal_origin(
    records: tuple[ResolutionRecord, ...],
) -> tuple[ValidationFinding, ...]:
    findings = []

    for record in records:
        if (
            record.profile == "formal"
            and record.value_origin is ValueOrigin.MODEL_ASSUMED
        ):
            findings.append(
                ValidationFinding(
                    invariant_id="INV-STATE-FORMAL-001",
                    passed=False,
                    severity="critical",
                    message_ja=(
                        "formal recordにmodel_assumedが含まれている。"
                    ),
                    record_ids=(record.record_id,),
                    stop_code="FORMAL_MODEL_ASSUMED_PROHIBITED",
                )
            )

    return tuple(findings)
```

---

## A-11. Stop Codeとプログラム例外の違い

### Why：なぜ区別するのか

すべての停止をPythonの例外だけで表すと、データの問題とcodeの故障が混ざる。

例えば次はデータとして予想される停止である。

- 方向別車線数がない。
- 複数access ruleが競合する。
- conditional構文が未対応である。

一方、次はプログラムの故障である。

- 存在するはずの変数が未定義。
- JSON fileを破損した状態で書き出した。
- 同じrecord IDを不正に2回生成した。

### What：二種類の失敗

#### 業務・仕様上の停止

Resolution Recordへ記録する。

```text
resolution_status: unresolved
stop_code: LANE_DIRECTIONAL_ALLOCATION_MISSING
```

これは処理対象データの状態である。

#### プログラム例外

codeの継続が安全でない場合に送出する。

```python
class ResolverProgrammingError(RuntimeError):
    """仕様上想定しないプログラム内部の異常。"""
```

### How：境界で変換する

期待されるデータ停止は、できるだけrecordとして返す。

```python
def unresolved_record(
    *,
    record_id: str,
    stop_code: str,
) -> ResolutionRecord:
    return ResolutionRecord(
        record_id=record_id,
        profile="formal",
        source_way_id=0,
        attribute_name="lanes",
        resolution_status=ResolutionStatus.UNRESOLVED,
        value_origin=None,
        effective_value=None,
        stop_code=stop_code,
    )
```

Registry欠落や不可能な内部状態は例外にする。

```python
if stop_code not in stop_code_registry:
    raise ResolverProgrammingError(
        f"未登録stop codeがcodeから出力された: {stop_code}"
    )
```

---

## A-12. 正準化とハッシュ

### Why：なぜ普通にJSON保存するだけでは駄目なのか

JSONでは、objectのkey順序や空白が異なっても意味は同じである。

```json
{"a":1,"b":2}
```

```json
{
  "b": 2,
  "a": 1
}
```

しかし、fileのbyte列は異なるため、そのままSHA-256を計算すると異なるhashになる。

同じ意味のデータから同じhashを得るには、標準形へ変換する必要がある。

### What：正準化

正準化は、同じ意味のJSONを同じbyte列へそろえる処理である。

v17ではRFC 8785のJSON Canonicalization Schemeを使用する方針である。

### How：hashを計算する

説明用の疑似コードである。

```python
import hashlib


def sha256_canonical_json(value: object) -> str:
    canonical_bytes = rfc8785_dumps(value)
    return hashlib.sha256(canonical_bytes).hexdigest()
```

record IDを作る際は、結果やtimestampのように後から変わるfieldを含めず、identityだけを対象にする。

```python
record_key = {
    "configuration_id": configuration_id,
    "population_version": population_version,
    "profile": profile,
    "source_way_id": source_way_id,
    "directed_segment_id": directed_segment_id,
    "lane_position": lane_position,
    "vehicle_class": vehicle_class,
    "attribute_name": attribute_name,
}

record_id = sha256_canonical_json(record_key)
```

hash field自身を自分のhash計算対象へ入れると循環するため、含めてはならない。

---

## A-13. 設定ファイルをプログラムへ読み込む

### Why：なぜ設定をcodeから分離するのか

条件をcodeへ直接書くと、設定変更のたびにcode変更と再reviewが必要になる。

また、過去runでどの設定を使ったか追跡しにくい。

### What：YAML設定の読込み

例：

```yaml
configuration_id: ota_ward_sumo_network_v17

profile_policy:
  formal:
    allow_model_assumed: false

registries:
  stop_codes:
    path: registries/stop_codes_v17.yml
    version: 17
    sha256: "..."
```

### How：型へ変換して検査する

```python
import yaml


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file)

    if not isinstance(loaded, dict):
        raise ValueError("Configurationのrootはobjectでなければならない。")

    return loaded
```

読込み後にSchemaとSemantic Validatorを実行する。

```python
raw_config = load_yaml("sumo_network_v17.yml")
validate_json_schema(raw_config, configuration_schema)
config = parse_configuration(raw_config)
validate_configuration_semantics(config)
```

`yaml.safe_load`を使用し、安全でない任意object生成を避ける。

---

## A-14. SerializerとManifest

### Why：なぜ出力方法を固定するのか

同じdataでも、書出し順、日時field、浮動小数点表現等が異なるとhashが変わる。

また、JSONだけを保存しても、どのcommand・code・設定で生成したか分からない。

### What：二種類の出力

#### データ成果物

```text
attribute_resolution_formal.json
directed_segments.json
permission_expectations.json
```

#### 実行記録

```text
build_manifest.json
validation_report.json
acceptance_result.json
```

### How：書出しを一か所へ集約する

```python
def write_canonical_json(path: str, value: object) -> str:
    canonical_bytes = rfc8785_dumps(value)

    with open(path, "wb") as file:
        file.write(canonical_bytes)

    return hashlib.sha256(canonical_bytes).hexdigest()
```

各処理が独自のJSON出力を行うのではなく、共通Serializerを使用する。

Manifestには次を記録する。

```python
manifest = {
    "source_commit": git_commit,
    "dirty_tree": dirty_tree,
    "configuration_hash": configuration_hash,
    "schema_hash": schema_hash,
    "registry_hashes": registry_hashes,
    "input_hashes": input_hashes,
    "command": command,
    "sumo_version": sumo_version,
    "python_version": python_version,
    "exit_code": exit_code,
    "output_hashes": output_hashes,
}
```

---

## A-15. Fixture・Oracle・Testの実装

### Why：なぜ本番データだけで試験しないのか

本番データは件数が多く、複数の要因が同時に含まれる。

失敗した場合、どの規則が原因か切り分けにくい。

小さなfixtureでは、一つの規則だけを明示的に確認できる。

### What：Fixtureの例

```json
{
  "fixture_id": "DIR-ONEWAY-MINUS-001",
  "source_way": {
    "id": 1001,
    "node_ids": [10, 20, 30],
    "tags": {
      "highway": "residential",
      "oneway": "-1"
    }
  }
}
```

### What：Oracleの例

```json
{
  "fixture_id": "DIR-ONEWAY-MINUS-001",
  "expected_directed_segments": [
    {
      "source_way_id": 1001,
      "source_direction": "backward"
    }
  ],
  "expected_stop_codes": []
}
```

### How：testを書く

```python
def test_oneway_minus_one_generates_backward_only() -> None:
    fixture = load_fixture("DIR-ONEWAY-MINUS-001")
    oracle = load_oracle("DIR-ONEWAY-MINUS-001")

    actual = run_directed_segment_generator(fixture)

    assert actual == oracle["expected_directed_segments"]
```

ただし、Oracleをproduction codeで自動生成してはならない。

期待結果は仕様と独立reviewに基づいて作成する。

### 負の試験

正しいcaseだけでなく、違反を正しく拒否することも確認する。

```python
def test_formal_record_rejects_model_assumed() -> None:
    record = make_record(
        profile="formal",
        resolution_status="resolved",
        value_origin="model_assumed",
    )

    with pytest.raises(SchemaValidationError):
        validate_record_schema(record)
```

---

## A-16. Repositoryの推奨構造

### Why：なぜ配置を整理するのか

仕様、設定、Registry、Schema、fixture、codeが同じfolderへ混在すると、authorityと実装の区別が難しくなる。

### What：概念的な配置例

```text
traffic_simulation/
├── specifications/
│   ├── attribute_resolution_policy_v17.md
│   ├── traceability_matrix_v17.md
│   └── semantic_invariants_v17.md
│
├── configuration/
│   └── sumo_network_v17.yml
│
├── schemas/
│   ├── resolution_record_v17.schema.json
│   ├── directed_segment_v17.schema.json
│   └── acceptance_v17.schema.json
│
├── registries/
│   ├── state_origin_v17.yml
│   ├── stop_codes_v17.yml
│   ├── oneway_rules_v17.yml
│   ├── access_values_v17.yml
│   └── vehicle_ontology_v17.yml
│
├── fixtures/
│   ├── inputs/
│   ├── oracles/
│   └── review/
│
├── src/
│   ├── loader/
│   ├── parser/
│   ├── normalizer/
│   ├── classifier/
│   ├── resolver/
│   ├── validator/
│   ├── serializer/
│   └── materializer/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── metamorphic/
│
└── artifacts/
    ├── v16/
    └── v17/
        ├── structural/
        └── formal/
```

これは説明用の構造例であり、既存repositoryの命名規則と整合させて調整する。

### How：分離の原則

- `specifications`は人間向けの規範を置く。
- `configuration`はrun選択を置く。
- `schemas`は形式検査を置く。
- `registries`は正式語彙・ruleを置く。
- `fixtures`は小規模入力と期待結果を置く。
- `src`はproduction codeを置く。
- `tests`は検証codeを置く。
- `artifacts`は生成物を置く。
- v16とv17を別directoryにする。
- structuralとformalを別directoryにする。

---

## A-17. 関数とmoduleの責任を小さくする

### Why：なぜ責任を小さくするのか

一つの関数が読込み、正規化、rule選択、file出力まで行うと、testしにくくなる。

### What：望ましい関数の特徴

- 一つの目的だけを持つ。
- 入力と出力が明確である。
- 外部状態への依存を少なくする。
- 同じ入力なら同じ出力を返す。
- file入出力と純粋な計算を分ける。

### How：純粋関数として書く

望ましい例：

```python
def sumo_lane_index(
    lane_count: int,
    lane_position: int,
) -> int:
    """OSM基準のlane位置をSUMO indexへ変換する。"""

    if lane_count <= 0:
        raise ValueError("lane_countは正の整数でなければならない。")

    if not 0 <= lane_position < lane_count:
        raise ValueError("lane_positionが範囲外である。")

    return lane_count - 1 - lane_position
```

この関数はfileを読まず、設定も変更せず、同じ入力に同じ出力を返すためtestしやすい。

```python
def test_sumo_lane_index() -> None:
    assert sumo_lane_index(3, 0) == 2
    assert sumo_lane_index(3, 1) == 1
    assert sumo_lane_index(3, 2) == 0
```

---

## A-18. 型検査・静的解析・実行時検査

### Why：なぜ複数の検査が必要なのか

誤りには、codeを書く時点で見つけられるものと、実際のdataを読まなければ分からないものがある。

### What：検査の種類

| 検査 | 対象 | 例 |
|---|---|---|
| 型検査 | code内の型の整合 | `str`を期待する関数へ`int`を渡す |
| 静的解析 | code品質・危険な書き方 | 未使用変数、到達不能code |
| Unit Test | 小さな関数 | `oneway=-1`の方向集合 |
| Schema Validation | JSON/YAMLの形 | enum、required field |
| Semantic Validation | dataの意味 | lane count equation |
| Integration Test | module間接続 | ResolverからSerializerまで |
| Runtime Fixture | 外部tool含む実行 | plain XMLをSUMOが読めるか |
| Acceptance Gate | 使用可能性 | formal artifactを次工程へ渡せるか |

### How：代表的なtoolの位置付け

Python環境では、例えば次のtoolを使える。

```text
mypy / pyright
  → 型検査

ruff
  → 静的解析、書式、よくある誤り

pytest
  → Unit Test、Integration Test

jsonschema
  → JSON Schema validation
```

ただし、どのtoolを採用するかはrepositoryの既存構成に合わせて決定する。

`pytest`がすべて通ったことは、Attribute Resolution Acceptanceを意味しない。

---

## A-19. 日志・監査記録・日本語のerror message

### Why：なぜlogを残すのか

処理が停止した場合、後から次を確認する必要がある。

- どのrecordで停止したか。
- どのruleを評価したか。
- どのRegistry versionを使ったか。
- どの値同士が競合したか。
- どのcommandで実行したか。

### What：構造化log

人間向け文章だけでなく、機械的に検索可能なfieldを持たせる。

```json
{
  "level": "ERROR",
  "event": "attribute_resolution_stopped",
  "record_id": "...",
  "attribute_name": "access",
  "stop_code": "ACCESS_SPECIFICITY_CONFLICT",
  "rule_ids": ["RULE-A", "RULE-B"],
  "message_ja": "同程度に具体的な規則が異なる通行結果を要求した。"
}
```

### How：英語識別子と日本語説明を併記する

```python
logger.error(
    "attribute_resolution_stopped",
    extra={
        "record_id": record.record_id,
        "stop_code": stop_code,
        "message_ja": "方向別車線数を正式に決定できない。",
    },
)
```

programが判定に使う`stop_code`は英語の固定IDとし、人間が読む説明は日本語にする。

---

## A-20. Phase 1で作るのはcodeそのものではなくcodeの契約である

### Why：なぜPhase 1で全面実装しないのか

仕様、Schema、Registryが確定する前にcodeを書くと、正式語彙やdata構造が途中で変わり、実装とfixtureを作り直す可能性が高い。

### What：プログラム契約

Phase 1で固定するのは、module間で受け渡すdataと判断規則である。

```text
どのfieldが必要か
どのenumを使うか
どのrule IDを使うか
どの条件を停止とするか
どのInvariantを検査するか
どの成果物を出力するか
```

これはAPI契約やデータ契約に近い。

### How：契約を先にtest可能にする

Phase 1では次を行う。

- Schema fileを作る。
- Registry fileを作る。
- Invariant IDを作る。
- Configurationの参照先を固定する。
- fixtureで必要になるcaseを列挙する。
- production codeの実装位置を仕様同期表へ記録する。

その後、Phase 2でOracleを固定し、Phase 3以降で実装する。

---

# 4. なぜ6つの成果物へ分けるのか

## Why：なぜ仕様書一つでは駄目なのか

仕様書は人間には読めるが、プログラムは仕様書の文章をそのまま実行できない。

例えば、仕様書に次の規則があるとする。

> formal profileでは`model_assumed`を使用してはならない。

この一文だけでは、次のことが決まっていない。

- formal profileをどの設定で選ぶのか。
- `model_assumed`を正式な値としてどこに登録するのか。
- どのデータfieldへ格納するのか。
- formal recordに入った場合、どの検査で発見するのか。
- どのfixtureで動作確認するのか。
- 現在のcodeが対応しているか。

一つの文を、設定・構造・語彙・意味検査・実装確認へ分解する必要がある。

## What：6成果物は何を担当するのか

| 成果物 | 担当する問い |
|---|---|
| 仕様同期表 | この規則はどこへ反映するのか。 |
| Configuration | 今回のrunでは何を使うのか。 |
| JSON Schema | データの形は正しいか。 |
| Registry群 | 使用してよい正式な語彙・規則は何か。 |
| Semantic Invariant一覧 | データの意味と関係は正しいか。 |
| 差分レビュー報告書 | 現在のrepositoryに何が足りないか。 |

## How：どのように使い分けるのか

同じ規則を例にすると、次のように分かれる。

### 規則

```text
formal profileではmodel_assumedを禁止する。
```

### 仕様同期表

```text
Requirement ID: AR-STATE-010
Configuration: profile_policy.formal
Schema: formal record conditional
Registry: value_origin registry
Validator: formal eligibility invariant
Fixture: STATE-FORMAL-ASSUMED-001
Code: serializer / resolver
```

### Configuration

```yaml
profile_policy:
  formal:
    allow_model_assumed: false
```

### Schema

```text
profile=formal かつ value_origin=model_assumed を拒否する。
```

### Registry

```yaml
value: model_assumed
formal_eligible: false
allowed_profiles:
  - structural
```

### Semantic Invariant

```text
formal recordにmodel_assumedが1件も存在しない。
```

### 差分レビュー

```text
現在のserializerがformalにもmodel_assumedを出力するならMajor findingとする。
```

---

# 5. 6成果物の全体像

## Why：なぜ全体像を先に理解するのか

6つを別々に作るだけでは、成果物同士が矛盾する可能性がある。

例えば、次のような状態は避けなければならない。

- 仕様書では`resolved`だが、Schemaでは`complete`になっている。
- Configurationではformalで仮定値を禁止しているが、Registryでは許可されている。
- stop codeがcodeにはあるがRegistryにはない。
- Schemaは更新されたがfixtureは旧形式である。

## What：全体の構造

```text
v17規範仕様書
  │
  ├─ 1. 仕様同期表
  ├─ 2. v17 Configuration
  ├─ 3. JSON Schema
  ├─ 4. Registry群
  ├─ 5. Semantic Invariant一覧
  └─ 6. 差分レビュー報告書
          │
          ↓
     Phase 1 完了
          │
          ↓
     fixture・oracle作成
          │
          ↓
     production実装
```

## How：どの順序で作るのか

実際の順序は次である。

```text
1. 仕様同期表の初版を作る
2. repositoryの差分を初回調査する
3. Configurationを作る
4. JSON Schemaを作る
5. Registry群を作る
6. Semantic Invariant一覧を作る
7. 用語と規則を再同期する
8. 差分レビューを更新する
9. 仕様同期表を最終更新する
10. Phase 1完了を判定する
```

差分レビューは成果物番号では6番であるが、作業では最初と最後の2回使用する。

---

# 6. 成果物1：仕様同期表

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | v17規範仕様書のRequirement |
| 同位 | Configuration、Schema、Registry、Invariant、差分レビュー |
| 下位 | Fixture、Oracle、Validator、Production Code、Evidence |
| 入力 | 規範仕様、repository現状、各成果物のpath |
| 出力 | Requirementごとの対応関係と進捗状態 |
| 保証すること | 仕様要求がどこへ反映されるか追跡できる |
| 保証しないこと | 実装が正しいこと、testが合格したこと |
| 主な意図 | INT-011、INT-019 |

## Why：なぜ必要なのか

仕様書には多くの必須規則がある。

しかし、各規則が次のどこに反映されるかを追跡できなければ、実装漏れが生じる。

- Configuration
- Schema
- Registry
- Validator
- Fixture
- Oracle
- Production code

仕様同期表がない場合、次の問題が起こる。

- 仕様書だけが更新される。
- 同じ規則が複数fileで異なる意味になる。
- fixtureがないままcodeだけ完成する。
- 完成状況を第三者が判断できない。

## 技術的背景：Requirements Traceabilityとは何か

仕様同期表は、ソフトウェア工学やシステム工学でいうRequirements Traceability Matrixに相当する。

要求を次の方向へ追跡できるようにする。

```text
仕様要求 → 設計 → Schema・Registry → 実装 → Test → Evidence
```

逆方向にも追跡できる必要がある。

```text
Test失敗 → 対応する実装 → 対応するRequirement ID → 仕様上の根拠
```

この双方向追跡により、不要な実装、testされていない要求、根拠のないruleを検出できる。

特にv17では、文書だけでなく複数のmachine-readable artifactがauthorityを構成するため、単なる作業一覧ではなく、要求単位の対応表が必要になる。

## What：何を作るのか

仕様書の必須規則を1行ずつ登録するtraceability matrixを作る。

推奨fileは次である。

```text
05_src/traffic_simulation/specifications/
  v17_attribute_resolution_traceability_matrix.md
```

必要に応じてCSVも作る。

### 最低限必要な列

| 列 | 意味 |
|---|---|
| `requirement_id` | 規則の一意なID |
| `specification_section` | 仕様書の場所 |
| `requirement_summary` | 規則の要約 |
| `configuration_location` | Configuration上の場所 |
| `schema_location` | Schema上の場所 |
| `registry_location` | Registry上の場所 |
| `validator_location` | Validator上の場所 |
| `fixture_ids` | 対応fixture |
| `oracle_location` | 正解データの場所 |
| `production_location` | Production codeの場所 |
| `current_status` | 現在の状態 |
| `evidence` | commit、hash、test結果 |
| `owner` | 担当者 |

### 要求IDの例

```text
AR-STATE-xxx   状態・由来
AR-DIR-xxx     Directed Segment・oneway
AR-LANE-xxx    方向別車線
AR-SPEED-xxx   制限速度
AR-ACCESS-xxx  access
AR-COND-xxx    条件付き規制
AR-ACC-xxx     受入条件
```

## How：どのように作るのか

### Step 1：仕様書から必須文を抽出する

例えば次の文を抽出する。

```text
v17 writerはvalue_stateを出力してはならない。
oneway=-1はbackwardのみを生成する。
formal profileはmodel_assumedを使用してはならない。
```

### Step 2：一つの判定可能な要求へ分割する

悪い例：

```text
状態を適切に管理する。
```

良い例：

```text
AR-STATE-001:
v17 writerはresolution_statusを出力する。

AR-STATE-002:
v17 writerはvalue_originを出力する。

AR-STATE-003:
v17 writerはvalue_stateを出力しない。
```

### Step 3：反映先を記入する

例：

| 項目 | 内容 |
|---|---|
| Requirement ID | `AR-DIR-004` |
| Requirement | `oneway=-1`はbackwardのみ生成する |
| Configuration | `direction_model` |
| Schema | `source_direction` |
| Registry | `oneway_rule_registry` |
| Validator | Directed Segment lineage check |
| Fixture | `DIR-ONEWAY-MINUS-001` |
| Code | Directed Segment generator |
| Status | `partial` |

### Step 4：状態を付ける

| 状態 | 意味 |
|---|---|
| `not_assessed` | 未確認 |
| `missing` | 成果物がない |
| `conflicting` | 仕様と矛盾する |
| `partial` | 一部だけ対応 |
| `aligned` | 一致している |
| `not_applicable` | 反映不要 |
| `blocked` | 上流判断待ち |

### 完了条件

- 仕様書の必須規則がすべて登録されている。
- 各規則の反映先が分かる。
- `missing`や`conflicting`が差分レビューに転記されている。
- 対象とする仕様書versionとhashが記録されている。

---

# 7. 成果物2：v17 Configuration

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 承認済みpolicy・Decision Record |
| 同位 | Registry、Schema、Scenario Context、Environment Manifest |
| 下位 | Loader、Resolver、Validator、Materializerの実行 |
| 入力 | policy ID、profile、population、Schema/Registry version |
| 出力 | 一つのrunで有効な設定集合 |
| 保証すること | どの条件・versionで実行したか固定する |
| 保証しないこと | ruleの意味そのもの、実装の正しさ |
| 主な意図 | INT-005、INT-009、INT-012、INT-017 |

## Why：なぜ必要なのか

仕様書は、v17で可能な規則全体を説明する。

一方、実際のrunでは次を一意に決める必要がある。

- どのpolicyを使うか。
- どのpopulationを使うか。
- structuralかformalか。
- どのSchema versionを使うか。
- どのRegistry versionを使うか。
- どのacceptance条件を使うか。
- どのSUMO versionを使うか。

これらをcode内へ直接書くと、runごとの設定が追跡できなくなる。

## 技術的背景：宣言的Configuration

Configurationは、処理手順を直接書く命令型codeではなく、「どのpolicy・version・profileを使うか」を宣言するartifactである。

宣言的に分離する利点は次である。

- codeを変更せずrun条件を切り替えられる。
- run条件をGitで比較できる。
- 実行後に同じ条件を再現できる。
- v16とv17を同じcodebaseで扱っても、設定を混同しにくい。
- Configuration hashをmanifestへ記録できる。

ただし、Configurationへ規則の意味を重複して書くと、仕様書やRegistryとの不一致が起きる。そのためConfigurationは選択と参照に限定する。

## What：何を作るのか

今回のrunで有効な設定を記録するYAML fileを作る。

推奨fileは次である。

```text
reproducibility/config/traffic_simulation/
  sumo_network_v17.yml
```

### 主な設定内容

```yaml
configuration_id: ota_ward_sumo_network_v17
policy_id: ota_ward_attribute_resolution_policy_v17
population_version: ota_ward_relation_closure_v16
schema_version: 17
```

```yaml
profile_policy:
  structural:
    allow_model_assumed: true
    eligible_for_attribute_resolution_acceptance: false

  formal:
    allow_model_assumed: false
    eligible_for_attribute_resolution_acceptance: true
```

```yaml
direction_model:
  representation: directed_segment
  preserve_source_way: true
  allow_source_way_reversal: false
```

```yaml
access_resolution:
  target_scope_dimensions:
    - direction
    - lane

  specificity_axes:
    - spatial
    - vehicle
    - temporal
    - purpose
```

## How：どのように作るのか

### Step 1：v16を保存する

v16 Configurationは変更しない。

v17用に新しいconfiguration IDと出力先を用意する。

### Step 2：仕様書の選択項目を移す

次をConfigurationへ移す。

- policy ID
- profile
- Schema version
- Registry参照
- direction model
- lane rule
- access rule
- acceptance threshold

### Step 3：Registryを参照する

Configurationへ規則本文を重複して書かず、path、version、hashを記録する。

```yaml
registries:
  stop_codes:
    path: ...
    version: ...
    sha256: ...
```

### Step 4：Configuration自体を検査する

Configuration SchemaとSemantic Validatorを通す。

### Configurationに書かないもの

- `oneway=-1`の詳細な意味論
- stop codeの修正方法
- fixtureの期待出力
- access dominanceの長い説明

これらは仕様書やRegistryが担当する。

### 完了条件

- v17専用configuration IDがある。
- v16を変更していない。
- structuralとformalが区別されている。
- SchemaとRegistryのversionが指定されている。
- acceptance条件が機械可読である。
- Configuration自身がvalidationを通る。

---

# 8. 成果物3：JSON Schema

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | v17データ契約、正式enum |
| 同位 | Registry、Semantic Invariant |
| 下位 | JSON/YAML成果物、Serializer、Schema Validator |
| 入力 | 必須field、型、enum、条件付き必須規則 |
| 出力 | valid / invalidと構造エラー |
| 保証すること | dataの形式と基本組合せが正しい |
| 保証しないこと | 道路方向、集合包含、母集団等の意味的正しさ |
| 主な意図 | INT-003、INT-012、INT-019 |

## Why：なぜ必要なのか

プログラムがJSONを出力しても、fieldの不足や型の誤りがある可能性がある。

例えば、次のrecordは問題である。

```json
{
  "resolution_status": "finished",
  "value_origin": "probably",
  "effective_value": null
}
```

`finished`や`probably`はv17で認められた値ではない。

また、`resolved`なのに値がない、formalなのに仮定値がある、といった不正も検出する必要がある。

## 技術的背景：構文検査と意味検査の境界

JSON Schemaは、JSON documentが定められた契約に従っているかを検査する。

主な機能は次である。

- `type`：文字列、数値、object、array等を制約する。
- `required`：必須fieldを指定する。
- `enum`：許可する有限値を指定する。
- `pattern`：ID等の文字列形式を制約する。
- `minimum`・`maximum`：数値範囲を制約する。
- `if`・`then`・`else`：field間の条件付き制約を定義する。
- `oneOf`・`anyOf`・`allOf`：複数Schemaの組合せを定義する。

一方、JSON Schemaは基本的に一つのdocument構造を検査する仕組みである。複数record間の集合関係、外部Registry参照、source artifactとのhash照合等は、通常のSchemaだけでは十分に扱えない。

そのため、Schema validationとSemantic validationを別のlayerにする。

## What：何を作るのか

データの構造と基本的な組合せを検査するJSON Schema群を作る。

最低限、次のSchemaが必要である。

```text
attribute_resolution_record_v17.schema.json
directed_segment_v17.schema.json
access_rule_v17.schema.json
exclusion_manifest_v17.schema.json
materialization_omission_v17.schema.json
environment_build_manifest_v17.schema.json
attribute_resolution_acceptance_v17.schema.json
sumo_network_v17.schema.json
```

### 代表的なenum

```text
resolution_status:
- resolved
- unresolved
- conflict
- invalid
- valid_but_unsupported
```

```text
value_origin:
- source_explicit
- source_normalized
- rule_derived
- evidence_derived
- derived_validated_model
- model_assumed
- null
```

## How：どのように作るのか

### Step 1：必須fieldを定義する

例：

```text
profile
record_id
source_way_id
directed_segment_id
resolution_status
value_origin
effective_value
stop_code
provenance
```

### Step 2：型とenumを定義する

- 文字列か。
- 数値か。
- 配列か。
- nullを許すか。
- 使用可能な値は何か。

### Step 3：cross-field条件を定義する

#### resolvedの場合

```text
effective_value != null
value_origin != null
stop_code == null
```

#### non-resolvedの場合

```text
effective_value == null
value_origin == null
stop_code != null
```

#### formalの場合

```text
value_origin != model_assumed
assumption_ids = []
```

### Step 4：正例と負例をtestする

正しいfixtureは通過し、誤ったfixtureは失敗しなければならない。

### Schemaで確認しないもの

次はSemantic Invariantで確認する。

- `oneway=-1`がbackwardだけか。
- source Wayが変更されていないか。
- 総車線数と方向別車線数が一致するか。
- access ruleの優先関係が正しいか。
- population件数が一致するか。
- 同じrunを2回行ってhashが一致するか。

### 完了条件

- 正しいfixtureが通る。
- 誤ったfixtureが失敗する。
- enumが仕様書・Configuration・Registryと一致する。
- v17 outputに`value_state`がない。
- Schemaでは表現できない条件がSemantic Invariantへ移されている。

---

# 9. 成果物4：Registry群

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 承認済みDecision Record・規範仕様 |
| 同位 | Configuration、Schema、Semantic Invariant |
| 下位 | Parser、Normalizer、Classifier、Resolver、Validator |
| 入力 | 正式語彙、rule、stop code、ontology、assumption |
| 出力 | version付きの機械可読な正式登録簿 |
| 保証すること | 使用可能な値とruleの意味が一意である |
| 保証しないこと | codeが正しくruleを適用したこと |
| 主な意図 | INT-008、INT-010、INT-012、INT-019 |

## Why：なぜ必要なのか

正式な値や規則をcodeへ直接書くだけでは、次が分からない。

- その値は正式に承認されているか。
- どのversionで追加されたか。
- どのfixtureで検査されるか。
- 廃止された値か。
- どの意味を持つか。
- 修正可能な停止理由か。

Registryがないと、code中の文字列が事実上の仕様になってしまう。

## 技術的背景：Controlled Vocabulary・Ontology・Decision Table

Registry群には、技術的には複数種類の情報が含まれる。

### Controlled Vocabulary

許可された有限の用語集合である。

例：

```text
resolved
unresolved
conflict
```

### Ontology

概念間の包含・親子・対応関係を表す。

例：

```text
delivery ⊂ motor_vehicle
bus ⊂ psv
```

access specificityでは、単に文字列が長いかではなく、この集合関係を使う。

### Decision Table

条件と結果の対応を明示する表である。

例：

```text
oneway=yes → forward
oneway=no  → forward + backward
oneway=-1  → backward
```

### Error Taxonomy

停止理由を分類する体系である。stop codeごとにtrigger、status、review要否、remediationを持つ。

これらをcodeから分離することで、規則のreview、version管理、fixture被覆の確認が可能になる。

## What：何を作るのか

使用可能な正式語彙、rule、stop code、ontology、assumptionを管理する機械可読な辞書を作る。

### 必須Registry

1. State／Origin Registry
2. Stop-code Registry
3. Oneway Rule Registry
4. Vehicle Ontology Registry
5. Access-value Registry
6. Conditional Grammar Registry
7. Assumption Registry
8. Japan Speed-rule Registry
9. Evidence Method Registry
10. Exclusion Rule Registry

### 例：Stop-code Registry

```yaml
stop_code: LANE_DIRECTIONAL_ALLOCATION_MISSING
trigger_condition: formal profileで方向別車線数を決定できない
resolution_status: unresolved
review_required: true
permitted_remediation:
  - explicit directional lane evidenceを追加
fixture_ids:
  - LANE-FORMAL-MISSING-001
```

### 例：Oneway Rule Registry

```yaml
rule_id: OSM_ONEWAY_ABSENT_DEFAULT_NO
predicate: ordinary road and oneway is absent
canonical_value: "no"
value_origin: rule_derived
```

## How：どのように作るのか

### Step 1：正式語彙を抽出する

仕様書、既存YAML、code、fixtureから次を集める。

- enum
- rule ID
- stop code
- assumption ID
- access value
- vehicle class

### Step 2：重複と別名を整理する

例：

```text
derived_osm_rule
rule_derived
```

v17ではどちらを正式名称にするか決める。

### Step 3：各entryへ意味を付ける

最低限、次を記録する。

```text
ID
意味
適用条件
許可profile
停止時の処理
fixture ID
承認者
version
```

### Step 4：Configurationから参照する

ConfigurationにはRegistryのpath、version、hashを記録する。

### Step 5：未登録値を拒否する

Validatorは、Registryにないstate、rule、stop codeをformal blockerとして扱う。

### 完了条件

- 仕様書に登場する正式IDがすべて登録されている。
- codeだけに存在する未登録値がない。
- deprecated valueの扱いが分かる。
- stop codeとfixtureが対応している。
- ConfigurationがRegistry versionを一意に指定する。
- 未登録値をValidatorが拒否する。

---

# 10. 成果物5：Semantic Invariant一覧

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 規範仕様の意味上の要求 |
| 同位 | JSON Schema、Registry、Fixture |
| 下位 | Semantic Validator、Validation Report、Acceptance Gate |
| 入力 | field間、record間、集合、hash、母集団の条件 |
| 出力 | 判定可能なInvariant IDと失敗時処理 |
| 保証すること | 何を意味的に検査するかが明確である |
| 保証しないこと | Validator codeが実装・実行済みであること |
| 主な意図 | INT-002、INT-004、INT-006、INT-009、INT-016 |

## Why：なぜ必要なのか

Schemaはデータの形を検査できるが、処理の意味までは十分に検査できない。

例えば次は、Schemaだけでは判断しにくい。

```text
oneway=-1ならbackwardだけを生成する。
総車線数は方向別車線数の合計と一致する。
recordの順序を変えてもaccess結果は変わらない。
input件数はgovernedとexcludedの合計である。
```

これらは、複数field、複数record、入力と出力の関係を確認する必要がある。

## 技術的背景：Invariant・Property-based Test・Metamorphic Test

Semantic Invariantは、特定の入力例だけでなく、すべての適用対象で成立すべき性質を表す。

例：

```text
formal recordにはmodel_assumedが存在しない。
```

この性質は、個別のfixtureだけでなく、full-population artifact全体でも検査できる。

### Property-basedな考え方

多数の入力に対して共通する性質を検査する。

例：

```text
すべてのrecord_idは再計算したhashと一致する。
```

### Metamorphicな考え方

入力を意味が変わらない形で変換したとき、出力がどう変わるべきかを検査する。

例：

```text
独立recordの並び順だけを変更する
→ 最終access結果は変わらない
```

```text
同じ入力を同じ環境で再実行する
→ canonical output hashは一致する
```

Fixtureは具体例の検査、Invariantは一般性質の検査と考えると理解しやすい。

## What：何を作るのか

常に成立すべき意味上の条件を、1件ずつ判定可能な形で記録する。

推奨fileは次である。

```text
05_src/traffic_simulation/specifications/
  v17_semantic_invariants.md
```

必要に応じてYAML版も作る。

### Invariantの基本構造

```yaml
invariant_id:
name:
scope:
precondition:
assertion:
failure_status:
stop_code:
severity:
fixture_ids:
validator_location:
```

### 例

```yaml
invariant_id: INV-DIR-004
name: oneway_minus_one_generates_backward_only
precondition:
  canonical_oneway: "-1"
assertion:
  generated_directions:
    - backward
failure_status: conflict
stop_code: DIRECTED_SEGMENT_LINEAGE_INVALID
fixture_ids:
  - DIR-ONEWAY-MINUS-001
```

## How：どのように作るのか

### Step 1：仕様書から関係条件を抽出する

特に次を探す。

- 〜の場合、〜でなければならない。
- 合計が一致しなければならない。
- 前後で変化してはならない。
- すべてのrecordを数えなければならない。
- 同じ入力なら同じ結果でなければならない。

### Step 2：true／falseで判定できる形にする

悪い例：

```text
方向を適切に処理する。
```

良い例：

```text
canonical_oneway=-1の場合、generated direction setは{backward}と一致する。
```

### Step 3：失敗時の処理を決める

- resolution status
- stop code
- severity
- review required
- remediation

### Step 4：fixtureとValidatorを対応付ける

Invariantだけを書いて終わらせず、どのtestで確認するかを決める。

### 主なInvariant群

#### 状態

- resolvedならvalueとoriginがある。
- non-resolvedならvalueとoriginはnullである。
- formalには`model_assumed`がない。

#### 方向

- `oneway=-1`はbackwardだけである。
- source Wayは変更されない。
- forwardとbackwardは同じsource intervalを参照する。

#### 車線

- 総車線数と方向別車線数の和が一致する。
- lane vector長と車線数が一致する。
- formalでeven splitを使わない。

#### Access

- direction／lane scope外へruleを適用しない。
- dominated ruleがmaximal setに残らない。
- 異なるmaximal effectがあれば停止する。
- record順を変えても結果が変わらない。

#### 母集団

- `input = governed + excluded`
- materialization omissionをexclusionとして数えない。
- omitted edgeの元tupleを分母から消さない。

#### 再現性

- 必要hashが存在する。
- 同じ環境・入力・commandで2回実行したhashが一致する。

### 完了条件

- 仕様書の意味的要求が一覧化されている。
- 各条件がtrue／falseで判定できる。
- 失敗時の処理が決まっている。
- fixtureとValidatorが対応している。
- Schemaとの役割分担が明確である。
- Acceptance Gateが参照するInvariantが分かる。

---

# 11. 成果物6：差分レビュー報告書

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 仕様同期表とv17規範仕様 |
| 同位 | Current Specification、Phase Completion Record |
| 下位 | 修正PR、担当割当、後続Phase計画 |
| 入力 | repositoryのfile・code・test・artifact現状 |
| 出力 | Finding、Severity、Target Phase、Owner、Evidence |
| 保証すること | 仕様と現状の差が可視化される |
| 保証しないこと | 差分が修正済みであること |
| 主な意図 | INT-011、INT-017、INT-019 |

## Why：なぜ必要なのか

v17仕様書が完成しても、repository内の実装やfileは自動的には更新されない。

現在のrepositoryには次のような状態が残っている可能性がある。

- v16の`value_state`だけを使っている。
- `resolution_status`と`value_origin`が未実装である。
- Directed Segment generatorはあるがproductionへ接続されていない。
- access utilityはあるがlane scopeに対応していない。
- stop code Registryがない。
- Acceptance条件が文書にしかない。

したがって、仕様と現状の差を明示的に調べる必要がある。

## 技術的背景：Gap AnalysisとMigration Review

差分レビューは、通常の文章校正ではなく、旧versionから新versionへのmigration gap analysisである。

確認対象は、単なるfileの有無だけではない。

- Data modelの差
- enum・field名の差
- authorityの差
- rule priorityの差
- implementation wiringの差
- fixture・oracle被覆の差
- runtime evidenceの差

例えば、Directed Segment generatorの関数が存在しても、production pipelineから呼ばれていなければ「実装済み」とは扱えない。

```text
utility exists
≠ production integrated
≠ runtime verified
≠ accepted
```

差分レビューでは、この状態を分けて記録する必要がある。

## What：何を作るのか

仕様書とrepositoryの不一致を1件ずつ記録する報告書を作る。

推奨fileは次である。

```text
05_src/traffic_simulation/
  v17_authority_synchronization_review.md
```

### Findingの基本項目

```text
finding_id
requirement_id
category
repository_location
current_behavior
required_behavior
impact
severity
recommended_action
target_phase
owner
status
evidence
```

### 差分の種類

| 種類 | 意味 |
|---|---|
| `missing_artifact` | 必要fileがない |
| `missing_field` | 必須fieldがない |
| `legacy_only` | v16形式しかない |
| `enum_conflict` | enumが仕様と違う |
| `semantic_conflict` | 処理の意味が仕様と違う |
| `unregistered_rule` | 未登録ruleを使用している |
| `fixture_gap` | fixtureがない |
| `oracle_gap` | oracleがない |
| `validator_gap` | 意味検査がない |
| `evidence_gap` | hashやmanifestがない |
| `documentation_only` | 文書だけで機械成果物がない |

## How：どのように作るのか

### Step 1：仕様同期表を基準にrepositoryを調べる

各Requirement IDについて、実際のfile、function、Schema、fixtureを探す。

### Step 2：一致しない項目をFindingにする

例：

```text
Finding ID: FIND-STATE-001
Requirement: AR-STATE-003
Current: serializerがvalue_stateを出力している
Required: v17 writerはvalue_stateを出力しない
Severity: Major
Target Phase: Phase 3
```

### Step 3：重要度を付ける

#### Critical

結果や原典を壊す可能性がある。

- v16成果物を書き換える。
- source OSMを直接編集する。
- formalへ仮定値を入れる。
- `oneway=-1`を誤方向へ生成する。
- 証拠なしでacceptedとする。

#### Major

実装前に解消または計画が必要である。

- SchemaとRegistryが一致しない。
- stop codeが未登録である。
- state contractが移行されていない。
- Semantic Validatorがない。

#### Minor

結果を直接壊さないが、第三者の理解や管理を難しくする。

- namingが統一されていない。
- 説明が不足する。
- file pathが整理されていない。

### Step 4：Phaseを割り当てる

Phase 1で直すものと、Phase 2以降で実装するものを分ける。

### Step 5：修正後に再レビューする

初回レビューだけで終わらず、Phase 1の修正後にCriticalとPhase 1対象Majorがゼロか確認する。

### 完了条件

- 未解決Criticalがゼロである。
- Phase 1対象Majorがゼロである。
- 後続Phaseへ送る項目にownerとtarget phaseがある。
- v16とv17の境界が明記されている。
- 修正したcommitとhashが記録されている。

---

# 12. Phase 1全体

## Why：なぜPhase 1を設けるのか

仕様書完成直後にproduction codeを変更すると、次の問題が起こる。

- 実装者が自然言語を別々に解釈する。
- Schemaとcodeがずれる。
- testの正解をproduction codeから作ってしまう。
- 途中で用語やrule IDが変更される。
- v16とv17の成果物が混ざる。

Phase 1は、実装前に「全員が同じ規則を参照する状態」を作る工程である。

## What：Phase 1で完成するもの

Phase 1完了時には次が存在する。

- 全必須規則を追跡できる仕様同期表
- v17 Configuration
- 必須JSON Schema
- 正式なRegistry群
- Semantic Invariant一覧
- repositoryとの差分レビュー
- v16とv17の明確な分離
- Phase 2で作るfixture・oracleの対象一覧

## How：Phase 1を進める方法

### 作業順

```text
1. 仕様同期表を作る
2. 初回差分レビューを行う
3. Configurationを作る
4. Schemaを作る
5. Registryを作る
6. Semantic Invariantを作る
7. 用語・enum・rule IDを再同期する
8. 差分レビューを更新する
9. 仕様同期表を最終化する
10. Phase 1完了判定を行う
```

### Phase 1完了チェック

```text
[ ] 仕様の必須規則が仕様同期表に登録されている
[ ] v17 Configurationが存在する
[ ] Configurationがvalidationを通る
[ ] 必須JSON Schemaが存在する
[ ] Registry群が存在する
[ ] Semantic Invariant一覧が存在する
[ ] 未解決Critical findingがゼロである
[ ] Phase 1対象Major findingがゼロである
[ ] v16成果物を変更していない
[ ] v17出力先がv16と分かれている
[ ] 仕様・Configuration・Schema・Registryの語彙が一致する
[ ] Phase 2で作るfixture・oracleの対象が決まっている
[ ] 各成果物のversionとSHA-256が記録されている
```

---

# 13. Phase 1後の次段階

## Why：なぜすぐfull runをしないのか

Configuration、Schema、Registryが揃っても、実装が正しいとは限らない。

まず、小さな入力と独立した正解を使って、規則どおりに動くことを確認する必要がある。

## What：次に作るもの

Phase 2では次を作る。

- independent fixture
- production-independent oracle
- fixture author・reviewer記録
- stop-code coverage
- metamorphic test

その後、Phase 3以降でproduction codeを変更する。

## How：次へ進む順序

```text
Phase 2:
fixture・oracleを固定する

Phase 3:
resolution_status／value_originへ移行する

Phase 4:
Directed Segmentをproductionへ統合する

Phase 5:
directional laneを実装する

Phase 6以降:
access、conditional、speedを統合する

その後:
full-population run
stop record解消
Attribute Resolution Acceptance
```

---

# 14. Phase 1でまだ完成しないもの

## Why：なぜ区別が必要なのか

「仕様体系が完成したこと」と「production実装が完成したこと」を混同すると、未検証のnetworkを研究へ使う危険がある。

## What：未完成のままでよいもの

Phase 1終了時点では、次は未完成でよい。

- production codeの全面v17対応
- fixture・oracleの実行成功
- `oneway=-1`のproduction統合
- directional lane resolver
- access resolver
- conditional parser
- full-population run
- stop recordの全解消
- Attribute Resolution Acceptance
- Permission Materializer
- formal SUMO network
- calibration
- independent validation

## How：未完成項目を管理するのか

差分レビューに次を記録する。

- Finding ID
- 対応Requirement ID
- Target Phase
- Owner
- 完了条件
- Evidence

「後で行う」だけではなく、どのPhaseで何をもって完了とするかを固定する。

---

# 15. よくある質問をWhy・What・Howで整理する

## Q1. なぜ仕様書だけでは駄目なのか

### Why

プログラムは自然言語の規則を直接検査・実行できないためである。

### What

仕様をConfiguration、Schema、Registry、Invariantへ分解する。

### How

仕様同期表で、各規則の反映先を一つずつ指定する。

---

## Q2. JSON SchemaとSemantic Invariantは何が違うのか

### Why

形式の正しさと意味の正しさは別だからである。

### What

- Schema：field、型、enum、null等を検査する。
- Invariant：方向、合計、集合、順序、母集団等を検査する。

### How

Schemaで表現できない条件をSemantic Invariant一覧へ明示的に移す。

---

## Q3. Registryは単なる用語集なのか

### Why

正式な語彙やruleをcodeから独立して管理する必要があるためである。

### What

state、origin、stop code、oneway rule、vehicle ontology等を管理する。

### How

Configurationからversionとhashを指定し、未登録値をValidatorで拒否する。

---

## Q4. 仕様同期表と差分レビューは何が違うのか

### Why

規則の配置と、現在の不足は別の情報だからである。

### What

- 仕様同期表：規則がどこへ反映されるべきか。
- 差分レビュー：現状が規則とどこで異なるか。

### How

仕様同期表を基準にrepositoryを調べ、不一致を差分レビューへ登録する。

---

## Q5. Phase 1が終われば実装完了なのか

### Why

Phase 1は実装の前提をそろえる段階だからである。

### What

完成するのはauthorityの構造と実装計画である。

### How

Phase 2でfixture・oracleを固定し、Phase 3以降でcodeを変更する。

---

# 16. 用語集

## Configuration

### Why

runごとに使用する規則やversionを固定するために必要である。

### What

policy、profile、Schema、Registry、acceptance条件を指定するYAML等である。

### How

v16と分離したv17 configuration IDを作り、参照先のversionとhashを記録する。

## JSON Schema

### Why

field不足や型・enumの誤りを機械的に発見するために必要である。

### What

JSONデータの構造規則である。

### How

正例と負例を作り、正例だけが通ることを確認する。

## Registry

### Why

正式な語彙や規則をcodeから独立して管理するために必要である。

### What

state、rule、stop code等の機械可読辞書である。

### How

各entryにID、意味、適用条件、version、fixtureを付ける。

## Semantic Invariant

### Why

Schemaでは検査できない意味上の関係を確認するために必要である。

### What

常に成立すべき条件である。

### How

一つの条件をtrue／falseで判定できる形へ分解する。

## Fixture

### Why

小さく固定された入力で規則を確実に確認するために必要である。

### What

特定caseを再現するtest用入力である。

### How

normal、boundary、negative caseを用意する。

## Oracle

### Why

production codeとは独立した正解が必要だからである。

### What

fixtureに対して期待される出力である。

### How

production codeを使わずに作成し、第三者reviewを記録する。

## Formal

### Why

正式な研究入力と開発用仮定を分けるために必要である。

### What

研究結果に使用可能なprofileである。

### How

`model_assumed`、未解決、競合等を禁止する。

## Structural

### Why

正式値が揃う前でも構造開発を進めるために必要である。

### What

開発・構造確認用profileである。

### How

登録済みの仮定だけを許可し、研究結果には使用しない。

---


# 技術補章B：プログラム用語の日本語早見表

| プログラム上の表記 | 日本語での説明 |
|---|---|
| `class` | データと処理をまとめる型の設計 |
| `instance` | classから作られた具体的なobject |
| `function` | 入力を受けて処理し、出力を返す処理単位 |
| `method` | classに属するfunction |
| `module` | 関連するclassやfunctionをまとめたPython file |
| `package` | 複数moduleをまとめた単位 |
| `interface` | module間で守る入力・出力の約束 |
| `API` | 他のmoduleやtoolから呼び出すための操作契約 |
| `type` | 値の種類 |
| `str` | 文字列 |
| `int` | 整数 |
| `float` | 小数を含む数値 |
| `bool` | trueまたはfalse |
| `list` | 順序を持つ可変の配列 |
| `tuple` | 順序を持つ固定的な配列 |
| `set` | 重複しない値の集合 |
| `frozenset` | 変更できない集合 |
| `dict` | keyとvalueの対応表 |
| `None` | Python上の値なし。JSONの`null`に対応する |
| `raise` | 例外を発生させる |
| `try / except` | 例外を捕捉し処理する |
| `return` | functionから値を返す |
| `yield` | 値を順番に生成する |
| `assert` | test等で条件成立を確認する |
| `immutable` | 作成後に変更しない性質 |
| `mutable` | 作成後に変更可能な性質 |
| `dependency` | 処理が利用する外部moduleやtool |
| `side effect` | file書込み等、戻り値以外に外部状態を変える作用 |
| `pure function` | 同じ入力に同じ出力を返し、外部状態を変えないfunction |
| `serialization` | objectをJSON等の保存形式へ変換すること |
| `deserialization` | JSON等をobjectへ戻すこと |
| `validation` | 定義済みの条件に適合するか確認すること |
| `migration` | 旧形式のdataを新形式へ移行すること |
| `backward compatibility` | 旧形式を新しいprogramでも読める性質 |
| `deprecated` | 廃止予定で新規使用を避ける状態 |
| `deterministic` | 同じ入力から同じ結果になる性質 |
| `idempotent` | 同じ操作を繰り返しても結果が変わらない性質 |
| `unit test` | 一つのfunction等を対象とする小規模試験 |
| `integration test` | 複数moduleの接続を対象とする試験 |
| `regression test` | 過去に動いていた機能が壊れていないか確認する試験 |
| `metamorphic test` | 入力を規則的に変えた際の出力関係を確認する試験 |
| `coverage` | testが対象caseをどの程度確認しているか |
| `commit` | repositoryへ記録した変更単位 |
| `branch` | 並行して変更を進める開発線 |
| `pull request` | 変更内容をreviewして統合する単位 |
| `CI` | commitやPRごとにtestを自動実行する仕組み |

## 日本語を使う場所と英語を残す場所

### 日本語を優先する場所

- 仕様本文
- comment
- docstring
- review報告
- errorの人間向け説明
- fixtureのcase説明
- acceptance reportの説明文

### 英語の固定識別子を残す場所

- JSON key
- YAML key
- class名・関数名
- stop code
- rule ID
- enum value
- file名
- SUMO・OSMの正式なtag名

この分け方により、説明は日本語で理解しやすくしながら、codeと外部仕様の対応関係を維持できる。

---

# 17. 技術的背景の参照先

この章は、解説書で扱った技術概念を確認するための参照先を示す。規範的な決定はv17属性解決仕様書を優先し、外部資料は背景理解に使用する。

## OpenStreetMap

- `oneway=-1`  
  https://wiki.openstreetmap.org/wiki/Tag%3Aoneway%3D-1

- forward／backwardの方向  
  https://wiki.openstreetmap.org/wiki/Forward

- `lanes:forward`／`lanes:backward`  
  https://wiki.openstreetmap.org/wiki/Key%3Alanes%3Aforward

- lane別tag  
  https://wiki.openstreetmap.org/wiki/Key%3A%2A%3Alanes

- access tag  
  https://wiki.openstreetmap.org/wiki/Access_tags

- conditional restriction  
  https://wiki.openstreetmap.org/wiki/Conditional_restrictions

## SUMO

- OpenStreetMapからのimport  
  https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html

- PlainXML  
  https://sumo.dlr.de/docs/Networks/PlainXML.html

- netconvert  
  https://sumo.dlr.de/docs/netconvert.html

## データ契約と再現性

- JSON Schemaのenum  
  https://json-schema.org/understanding-json-schema/reference/enum

- JSON Schemaの条件付きvalidation  
  https://json-schema.org/understanding-json-schema/reference/conditionals

- RFC 8785 JSON Canonicalization Scheme  
  https://www.rfc-editor.org/rfc/rfc8785.html

- W3C PROV-O  
  https://www.w3.org/TR/prov-o/

- Workflow Run RO-Crate  
  https://www.researchobject.org/workflow-run-crate/

## モデル・シミュレーションの検証

- FHWA Traffic Analysis Toolbox：Error Checking  
  https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter4.htm

- FHWA Traffic Analysis Toolbox：Calibration  
  https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm

- NASA-STD-7009B  
  https://standards.nasa.gov/node/263

---

# 17A. 一つの道路が全階層を通る例

## 例1：通常道路で`oneway`が欠損している

### 原典層

```text
Way ID: 1001
highway=residential
oneway: 欠損
```

意図：

- 原典欠損を勝手に`oneway=no`へ書き換えない。
- 欠損だった事実を保持する。

### 正規化・分類層

```text
raw_value: null
classification_code: ordinary_road_missing_oneway
```

意図：

- 「値がない」ことと「noと明示されている」ことを分ける。

### Registry層

```text
rule_id: OSM_ONEWAY_ABSENT_DEFAULT_NO
effective_value: no
value_origin: rule_derived
```

意図：

- code内の暗黙defaultではなく、正式ruleで導出する。

### Resolver層

```text
resolution_status: resolved
value_origin: rule_derived
effective_value: no
```

意図：

- 最終値と根拠を同時に保存する。

### Directed Segment層

```text
forward
backward
```

意図：

- 双方向を二つの走行方向として明示する。

### Validator層

確認すること：

- source Wayが変更されていない。
- rule IDがRegistryにある。
- forward/backwardの2件が生成された。
-同じ入力から同じIDが得られる。

### Materializer層

forwardとbackwardに対応するplain XML edge候補を出力する。

ここでは新しいdirection判断を行わない。

---

## 例2：`oneway=-1`

### 原典層

```text
Way node order: 10 → 20 → 30
oneway=-1
```

### 意図

- source Wayは反転しない。
- 走行方向だけをbackwardとして表す。
- `forward`／`backward` tagの基準を壊さない。

### Directed Segment

```text
source_node_ids: [10, 20, 30]
source_direction: backward
traversal order: [30, 20, 10]
```

### 各成果物の関与

| 成果物 | 関与 |
|---|---|
| 仕様同期表 | `oneway=-1`要求の全反映先を追跡 |
| Configuration | Directed Segment modelを有効化 |
| Schema | direction enumとID形式を検査 |
| Registry | `-1`の正規化ruleを提供 |
| Invariant | backwardのみ生成、source不変を検査 |
| 差分レビュー | productionがWay反転する場合にFinding化 |

---

## 例3：formalで方向別車線数が不足する

### 原典

```text
oneway=no
lanes=4
lanes:forward 欠損
lanes:backward 欠損
```

### Structural profile

登録条件を満たす場合、次を許可できる。

```text
forward=2
backward=2
value_origin=model_assumed
assumption_id=BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1
```

目的：

- topologyやMaterializer開発を進める。

使用禁止：

- calibration
- travel-time評価
- solver比較
- formal network承認

### Formal profile

```text
resolution_status=unresolved
stop_code=LANE_DIRECTIONAL_ALLOCATION_MISSING
```

目的：

- 根拠のない均等分割を研究入力へ入れない。

### 階層上の意味

```text
同じ原典
  ↓
profileという実行選択が異なる
  ↓
許可されるvalue_originが異なる
  ↓
結果artifactと使用可能範囲が異なる
```

---

## 例4：Access Ruleが競合する

### 適用候補

```text
Rule A: deliveryを許可
Rule B: deliveryを禁止
```

両者が同じlane、direction、vehicle、time、purposeへ適用され、どちらも相手を支配しない場合：

```text
resolution_status=conflict
stop_code=ACCESS_SPECIFICITY_CONFLICT
```

### 意図

- file順で一方を選ばない。
- first-matchやlast-matchを独立rule間へ誤用しない。
- 競合ruleとprovenanceを保存する。
- reviewerが新ruleまたはevidenceを登録し、全体を再実行する。

---

# 17B. 全階層を第三者へ説明するための要約

## Why

OpenStreetMapの道路情報は欠損・方向差・車線差・条件付き規制を含むため、そのままSUMOへ変換すると、暗黙の仮定や実装順によって研究結果が変わる可能性がある。

## What

そこで、原典を不変に保ちながら、各方向・車線・車種・scenarioについて、値、解決状態、値の由来、適用rule、停止理由を記録する属性解決層を設ける。

その判断を一貫して実行・検証するため、Phase 1では次の6成果物を作る。

```text
仕様同期表
Configuration
JSON Schema
Registry
Semantic Invariant
差分レビュー
```

## How

```text
上位の研究目的
  ↓
規範仕様で判断を定める
  ↓
Phase 1成果物で機械可読なcontractへ分解する
  ↓
Fixture・Oracleで独立した正解を固定する
  ↓
Production Codeをcontractへ合わせる
  ↓
Full-population Runを行う
  ↓
Attribute Resolution Acceptanceを通す
  ↓
SUMO Network Integrationを検証する
  ↓
Calibration・Validation後に研究実験へ使う
```

この階層を守ることにより、仕様、実装、入力、出力、検証、研究結果の因果関係を第三者が追跡できる。

---

# 18. 最終まとめ

## Why

v17仕様書だけでは、実装・検査・追跡を一意に行えないためである。

## What

Phase 1では、次の6成果物を作る。

```text
仕様同期表
Configuration
JSON Schema
Registry群
Semantic Invariant一覧
差分レビュー報告書
```

## How

次の順序で進める。

```text
仕様要求を分解する
→ 現状との差を確認する
→ Configurationを固定する
→ Schemaで形式を固定する
→ Registryで語彙を固定する
→ Invariantで意味を固定する
→ 差分を再確認する
→ Phase 1完了を判定する
```

Phase 1とは、簡潔にいえば次の工程である。

> 正しい実装を始める前に、仕様・設定・データ形式・正式語彙・意味検査・現状差分を一致させる工程である。
