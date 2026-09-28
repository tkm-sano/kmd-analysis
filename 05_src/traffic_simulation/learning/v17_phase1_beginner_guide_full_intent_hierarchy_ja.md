<a id="whywhathowで理解する-v17属性解決-phase-1"></a>

# 理由・内容・方法で理解する v17属性解決工程 1

## 全設計意図・階層・プログラム構造を日本語で学ぶ版

## 初学者向け解説書

> 本版は、研究目的、正本、data、処理、成果物、検証、Phase、人の責任という全階層を示したうえで、プログラム内部の処理、データ型、検証、例外、ハッシュ、テストの関係を日本語中心で説明する。

---

# 0. この文書の読み方

本書は、v17属性解決のPhase 1を、すべて次の順序で説明する。

1. **理由：なぜ必要なのか**
2. **内容：何を作るのか**
3. **方法：どのように作るのか**

専門用語を先に並べるのではなく、まず必要性を理解し、その後に成果物と作業方法を説明する構成である。

本書の対象となる成果物は次の6つである。

1. 仕様同期表
2. v17 Configuration
3. JSON Schema
4. 登録簿群
5. 意味上の不変条件一覧
6. 差分レビュー報告書

---

# 0A. この解説書自体の位置付け

<a id="whyなぜ文書の位置付けを明示するのか"></a>

## 理由：なぜ文書の位置付けを明示するのか

本プロジェクトには、規範仕様書、成果物説明書、初心者向け解説書、設定、データ構造、登録簿、検証用データ、正解判定器、実装コード、検証報告書など、目的の異なる文書とファイルが存在する。

これらを同じ「仕様」として扱うと、次の混乱が起こる。

- 説明文が実装上の正式規則だと誤解される。
- コード例が実装済みの事実だと誤解される。
- 初心者向けのたとえが機械可読な定義より優先される。
- 現状説明と将来の要求が混ざる。
- v16の実行事実とv17の設計方針が混ざる。

そのため、この文書が何を決め、何を決めないかを先に固定する必要がある。

<a id="whatこの文書の役割"></a>

## 内容：この文書の役割

この文書は、**v17属性解決仕様とPhase 1成果物体系を理解するための解説書**である。

この文書が行うことは次である。

- 各設計判断の意図を説明する。
- 各成果物の階層上の位置を説明する。
- 上位目的と下位実装のつながりを説明する。
- 技術用語とプログラム構造を日本語で説明する。
- 理由・内容・方法で第三者へ説明できる形にする。
- どの層が何を保証するかを整理する。

この文書が行わないことは次である。

- v17の正式な列挙値や規則を新たに変更すること。
- 設定の代わりになること。
- ジェイソン形式 データ構造の代わりになること。
- 登録簿の代わりになること。
- 正式運用 コードが実装済みであると証明すること。
- 検証用データや正解判定器が合格済みであると証明すること。
- 属性解決の受入を承認すること。
- スーモネットワークの妥当性を承認すること。

<a id="howどの文書を正式な基準として読むか"></a>

## 方法：どの文書を正式な基準として読むか

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

<a id="whyなぜ研究全体から見るのか"></a>

## 理由：なぜ研究全体から見るのか

属性解決は、研究そのものの最終目的ではない。

属性解決だけを見ていると、なぜ未解決値を厳しく停止するのか、なぜハッシュ値や出典・来歴が必要なのか、なぜ正式と構造上のを分けるのかが分かりにくい。

最上位の研究目的から下位のデータ処理までをつなぐ必要がある。

<a id="what研究目的からデータまでの階層"></a>

## 内容：研究目的からデータまでの階層

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

例えば、属性解決に誤りがあると、スーモ 道路区間や車線が誤り、旅行時間や配送経路が変わり、最終的な手法比較も変わる。

<a id="how各層で問うべきこと"></a>

## 方法：各層で問うべきこと

| 層 | 主な問い |
|---|---|
| 研究目的 | 何を比較し、何を明らかにするのか。 |
| 実験設計 | 比較条件は公平で再現可能か。 |
| シミュレーション | 現実の交通条件をどこまで表現するか。 |
| スーモネットワーク | 道路区間、車線、接続は正しいか。 |
| 入力生成 | 属性解決器結果を損なわずスーモへ渡したか。 |
| 属性解決 | 値は何で、どの根拠で決めたか。 |
| 分類・正規化 | 入力をどの事例として認識したか。 |
| 原典 | 元データは何で、変更されていないか。 |

---

# 0C. システム処理の階層

<a id="whyなぜ処理階層を分けるのか"></a>

## 理由：なぜ処理階層を分けるのか

一つの処理が複数の責任を持つと、誤りの発生箇所と修正箇所が分からなくなる。

例えば、`oneway=-1`を誤って順方向へ出力した場合でも、原因は次のどこかにあり得る。

- オープンストリートマップ 属性タグの読込み
- 値の正規化
- direction rule
- 方向付き区間生成
- plain 拡張マークアップ形式への書出し
- スーモ 道路区間 識別子の対応付け

処理階層を分けることで、責任と検証点を固定する。

<a id="what処理パイプライン"></a>

## 内容：処理パイプライン

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

<a id="how各処理の責任境界"></a>

## 方法：各処理の責任境界

| 処理 | 責任 | 責任外 |
|---|---|---|
| Loader | ファイルを読み、原典値を保持する | 値の意味を決めない |
| Parser | 文字列を構文単位へ分ける | 採用値を決めない |
| Normalizer | 同義表記を標準値へ変える | 欠損を推定しない |
| Classifier | 事例と適用候補規則を決める | effective 値を決めない |
| 属性解決器 | 値、状態、由来、停止理由を決める | スーモ 拡張マークアップ形式を直接編集しない |
| 検証器 | 規則違反を検出する | 値を自動修正しない |
| Serializer | 検証済みdataを固定形式へ書く | 解決規則を再判断しない |
| 具体化処理 | 正式結果をスーモ入力へ反映する | 不足値を補わない |
| netconvert | 交通シミュレーターの道路網を生成する | 研究上の正式 eligibilityを決めない |
| Calibration | パラメーターを観測へ合わせる | 道路網 coding 誤りを隠さない |
| 検証 | 別dataで妥当性を確認する | コード 試験の代わりにならない |

---

# 0D. データモデルの階層

<a id="whyなぜデータ粒度を分けるのか"></a>

## 理由：なぜデータ粒度を分けるのか

「道路1本」という表現だけでは、方向、車線、車種、時間条件を正しく扱えない。

例えば同じオープンストリートマップ 道路地物でも、次が異なる可能性がある。

- 順方向と逆方向で速度が異なる。
- 車線ごとに通行可能車種が異なる。
- 配送だけが通行可能である。
- 特定時間だけ通行許可が変わる。

したがって、処理対象を段階的に細分化する。

<a id="whatデータ粒度の階層"></a>

## 内容：データ粒度の階層

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
| Source Dataset | 取得したオープンストリートマップ全体 |
| OSM Way | 原典のノード列と属性タグを持つ道路要素 |
| Source Way Interval | 交差点等で分割された原典上の区間 |
| 方向付き区間 | 原典を保ったまま走行方向を付けた区間 |
| Directional Lane | 走行方向から見た個別車線 |
| Vehicle・Scenario Tuple | 車種、時間、目的、permit等を加えた評価単位 |
| Resolution Record | 一つの属性に対する解決結果 |

<a id="how一件の道路が複数recordになる例"></a>

## 方法：一件の道路が複数記録になる例

```text
OSM Way 1001
  双方向
  forward 2 lanes
  backward 1 lane
  7 vehicle classes
  1 scenario context
  permission attribute
```

この場合、通行許可だけでも概念上は次の件数になる。

```text
3 lanes × 7 vehicle classes × 1 scenario = 21 tuples
```

さらに速度、車線 件数、方向等の別属性記録が存在する。

この細分化により、「道路としては解決済みだが、特定車線・特定車種だけ未解決」という状態を表現できる。

---

# 0E. 正本の階層

<a id="whyなぜ正式な基準を階層化するのか"></a>

## 理由：なぜ正式な基準を階層化するのか

同じ規則が文書、ヤムル形式、データ構造、コードに存在すると、どれを正しい基準とするかが問題になる。

例えば、仕様書では`rule_derived`、コードでは`derived_osm_rule`、データ構造では両方許可という状態では、v17の正式語彙が不明である。

そこで、判断・機械表現・検証・実装を階層化する。

<a id="whatauthority-hierarchy"></a>

## 内容：正本階層

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

注意点として、Generated Artifactは実行結果であり、規則の正しさを自分自身では証明しない。

<a id="how不一致が見つかった場合"></a>

## 方法：不一致が見つかった場合

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

<a id="whyなぜ成果物の種類を分けるのか"></a>

## 理由：なぜ成果物の種類を分けるのか

すべてのファイルを「成果物」とだけ呼ぶと、規則を定めるファイル、検査するファイル、実行結果を記録するファイルが混ざる。

成果物の種類によって、変更方法、確認方法、正式性が異なる。

<a id="what成果物の5分類"></a>

## 内容：成果物の5分類

### 1. 規範成果物

何を正しいとするかを定義する。

```text
v17規範仕様書
Decision Record
Registry
Semantic Invariant一覧
```

### 2. 実行選択成果物

今回の実行で何を有効にするかを定める。

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

<a id="how変更の扱い"></a>

## 方法：変更の扱い

| 成果物分類 | 変更時に必要なこと |
|---|---|
| 規範 | 承認、版更新、関連成果物同期 |
| 実行選択 | 実行 識別子更新、ハッシュ値記録 |
| 構造検査 | データ構造 版更新、検証用データ更新 |
| 試験・検証 | independent 確認、網羅率確認 |
| 実行生成 | 再実行し、直接手修正しない |

---

# 0G. 検証と受入の階層

<a id="whyなぜtestに通ったを一つにまとめないのか"></a>

## 理由：なぜ「試験に通った」を一つにまとめないのか

異なる検査は、異なる問いに答える。

`pytest`が通っても、全道路記録が解決済みとは限らない。

ジェイソン形式 データ構造が通っても、`oneway=-1`の方向が正しいとは限らない。

属性解決の受入が通っても、スーモ 接続や信号制御が正しいとは限らない。

<a id="what検証階層"></a>

## 内容：検証階層

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

<a id="how検査結果の言い方"></a>

## 方法：検査結果の言い方

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

<a id="0h-lifecycleとphaseの階層"></a>

# 0H. ライフサイクルと工程の階層

<a id="whyなぜphaseを分けるのか"></a>

## 理由：なぜ工程を分けるのか

規則を決める作業、正解を作る作業、コードを書く作業、全件実行する作業を同時に行うと、正式運用 コードが事実上の正解を作ってしまう。

上流取り決めを先に固定し、下流実装を後から合わせる必要がある。

<a id="whatlifecycle"></a>

## 内容：ライフサイクル

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

<a id="howphase-1の境界"></a>

## 方法：工程 1の境界

Phase 1で行う：

- 規則と語彙を一致させる。
- data 取り決めを固定する。
- 検査条件を固定する。
- リポジトリとの差を記録する。
- Phase 2の検証用データ対象を決める。

Phase 1では行わない：

- 正式運用 属性解決器の全面実装。
- full-population run。
- 未解決記録の解消。
- 正式 道路網承認。
- calibration。
- solver comparison。

---

# 0I. 人とプログラムの責任階層

<a id="whyなぜ人と機械の責任を分けるのか"></a>

## 理由：なぜ人と機械の責任を分けるのか

プログラムは、登録された規則を高速かつ一貫して適用できる。

しかし、どの規則を正式採用するか、どの証拠を十分とするか、研究目的に対して何件まで未解決を許すかは、人間の判断である。

逆に、人間が正式運用 出力を手作業で直すと、再現性が失われる。

<a id="what責任分担"></a>

## 内容：責任分担

| 主体 | 主な責任 |
|---|---|
| 仕様策定者 | 判断規則、境界、受入条件を定める |
| 登録簿管理者 | 正式語彙と規則 版を管理する |
| 検証用データ作成者 | 小さな入力事例を設計する |
| 正解判定器作成・確認者 | 正式運用 コードから独立した期待結果を承認する |
| 実装者 | 取り決めどおりにコードを書く |
| 検証器実装者 | 不変条件を機械検査へ落とす |
| 実行者 | 固定環境・コマンドで実行する |
| Reviewer | 仕様と成果物の整合を確認する |
| Acceptance承認者 | 判定基準結果と証拠を確認し、次工程を承認する |
| Program | 登録済み規則を適用し、結果と停止を記録する |

<a id="how禁止する責任の混同"></a>

## 方法：禁止する責任の混同

- 正式運用 コードが正解判定器を生成しない。
- 実行者が出力ジェイソン形式を手で修正しない。
- 検証器が未解決値を自動補完しない。
- 道路種別の対応表が正式 通行許可の正本にならない。
- コード中の未登録if文が新しい規範規則にならない。
- 確認者の判断を記録なしで直接出力へ反映しない。

---

# 0J. 設計意図一覧

<a id="whyなぜ意図へidを付けるのか"></a>

## 理由：なぜ意図へ識別子を付けるのか

個別の規則だけを読むと、なぜその規則があるのかを見失いやすい。

設計意図を識別子化することで、複数の成果物や実装が同じ目的へ向いているか確認できる。

<a id="what主要な設計意図"></a>

## 内容：主要な設計意図

| 意図識別子 | 意図 | 主に関係する層・成果物 |
|---|---|---|
| INT-001 | 原典オープンストリートマップを不変に保つ | Loader、Directed Segment、hash |
| INT-002 | 方向情報を原典ノード順に結び付ける | Directed Segment、relation mapping |
| INT-003 | 値の状態と値の由来を分離する | Schema、State Registry、Resolver |
| INT-004 | 不明値を推測で正式へ入れない | Formal profile、Invariant、Acceptance |
| INT-005 | 開発用仮定と研究入力を分離する | Structural/Formal、Assumption Registry |
| INT-006 | 入力順に依存しない結果を得る | Access dominance、metamorphic test |
| INT-007 | 車線・方向の適用範囲を保持する | Target Scope、AccessRule |
| INT-008 | 規則競合を隠さず停止する | Stop Code、Resolver、Validator |
| INT-009 | 同じ入力・環境から同じ成果物を得る | Canonical JSON、hash、manifest |
| INT-010 | どの値がどの根拠から来たか追跡する | Provenance、Registry、Evidence |
| INT-011 | 仕様と実装の乖離を検出する | Traceability Matrix、Gap Review |
| INT-012 | コードを規範の唯一の保管場所にしない | Registry、Configuration、Schema |
| INT-013 | 正式運用 コードから独立した正解を持つ | Fixture、Oracle、Review |
| INT-014 | 属性成果物と交通シミュレーターの道路網承認を分離する | Acceptance hierarchy |
| INT-015 | ソフトウェア 試験と交通モデル妥当性を分離する | Test、Calibration、Validation |
| INT-016 | 母集団から記録が静かに消えるのを防ぐ | Population accounting、Exclusion Manifest |
| INT-017 | v16履歴を改変せずv17へ移行する | Transition、output directory、manifest |
| INT-018 | 各モジュールの責任を小さく保つ | Loader～Materializer architecture |
| INT-019 | 検査失敗時に原因と修正先を特定する | Finding、stop code、structured log |
| INT-020 | 次工程へ進める条件を機械判定可能にする | Acceptance Configuration、Artifact |

<a id="how意図を成果物へ対応付ける例"></a>

## 方法：意図を成果物へ対応付ける例

<a id="int-004不明値を推測でformalへ入れない"></a>

### INT-004：不明値を推測で正式へ入れない

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

# 0K. 六つの工程 1成果物の相互関係

<a id="whyなぜ六つを独立fileにしつつ連携させるのか"></a>

## 理由：なぜ六つを独立ファイルにしつつ連携させるのか

一つの巨大ファイルにすべてを書くと、機械処理しにくくなる。

完全に独立させると、用語や規則がずれる。

したがって、責任を分離しながら参照関係を明示する。

<a id="what参照関係"></a>

## 内容：参照関係

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

<a id="how循環を避ける"></a>

## 方法：循環を避ける

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

<a id="whyなぜ属性解決が必要なのか"></a>

## 理由：なぜ属性解決が必要なのか

オープンストリートマップの道路データには、次のような情報が含まれる。

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
- 複数の接続規則が互いに矛盾する。
- 値自体は正しいが、現在のプログラムでは扱えない。

これらを曖昧なままスーモへ変換すると、プログラムが暗黙に値を補ったり、実装順によって異なる結果を出したりする可能性がある。

したがって、スーモネットワークを作る前に、各属性について以下を明示する必要がある。

- 値が決まったか。
- 決まっていないか。
- どの根拠で決めたか。
- 仮定を使ったか。
- 正式な研究入力として使えるか。

<a id="what属性解決とは何か"></a>

## 内容：属性解決とは何か

属性解決とは、オープンストリートマップの入力を読み、各属性について次の情報を出力する処理である。

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

<a id="howどのように実現するのか"></a>

## 方法：どのように実現するのか

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


<a id="2-技術的背景osmからsumoへ何が変換されるのか"></a>

# 2. 技術的背景：オープンストリートマップからスーモへ何が変換されるのか

この章は、後続の6成果物を理解するための前提となる技術背景を説明する。ここで説明する内容は、v17の新しい規範を追加するものではなく、既存仕様で採用した構造がなぜ必要なのかを理解するための補足である。

<a id="whyなぜデータ変換の途中を明示する必要があるのか"></a>

## 理由：なぜデータ変換の途中を明示する必要があるのか

オープンストリートマップとスーモは、道路を表現する目的とデータ構造が異なる。

オープンストリートマップは、世界中の地理情報を共同編集するための地理データベースである。一方、スーモは、車両がどの方向へ、どの車線を通り、どの接続を経由できるかを計算する交通シミュレータである。

そのため、オープンストリートマップからスーモへの変換は、単純なファイル形式変換ではない。

実際には、次の判断を含む。

- 一つのオープンストリートマップ 道路地物から、何本の方向別道路区間を作るか。
- 総車線数を各方向へどう割り当てるか。
- 車線別接続をスーモ 車線へどう対応付けるか。
- 右左折制限をどの接続へ反映するか。
- 欠損した速度や通行許可をどう扱うか。
- 条件付き規制をどの時点・車種・目的に適用するか。

これらの判断を`netconvert`や道路種別の対応表へ暗黙に任せると、生成結果は得られても、研究者が「なぜその値になったか」を説明できない可能性がある。

したがって、オープンストリートマップとスーモの間に、判断内容を記録する属性解決器層を設ける必要がある。

<a id="whatosm側のデータ構造"></a>

## 内容：オープンストリートマップ側のデータ構造

オープンストリートマップの基本要素は次の3つである。

<a id="node"></a>

### ノード

緯度・経度を持つ点である。道路の形状点、交差点、信号、施設位置等に使用される。

<a id="way"></a>

### 道路地物

複数のノードを順番に並べた線または面である。道路の場合、このノードの並び順が`forward`方向の基準になる。

例えば、道路地物のノード列が次であるとする。

```text
Node A → Node B → Node C
```

このとき、オープンストリートマップにおける方向は次のように解釈する。

```text
forward  = A → B → C
backward = C → B → A
```

`oneway=-1`は、道路地物を構成するノード列を変更する指示ではなく、通行方向が`backward`だけであることを示す。

### 関係要素

複数のノード、道路地物、Relationを役割付きでまとめる要素である。交通ネットワークでは、右左折制限の`from`、`via`、`to`等に使用される。

### 属性タグ

ノード、道路地物、Relationに付与されるキー-値形式の属性である。

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

<a id="whatsumo側のデータ構造"></a>

## 内容：スーモ側のデータ構造

スーモの道路ネットワークは、主に次の要素から構成される。

### 交差点

道路の接続点である。オープンストリートマップ ノードと一対一とは限らず、変換時に統合・分割される場合がある。

<a id="edge"></a>

### 道路区間

一つの方向へ走行する道路区間である。スーモの道路区間は基本的に有向であり、双方向道路は通常、反対方向の道路区間を別々に持つ。

```text
OSMの双方向Way
    ↓
SUMOのforward edge
SUMOのbackward edge
```

<a id="lane"></a>

### 車線

道路区間に属する車線である。速度、通行可能vClass、長さ等を持つ。

### 接続

ある車線から別の車線へ進める関係である。道路が図形上つながっているだけでは、車両が実際に移動できるとは限らない。

### 信号制御の論理

信号制御の段階と、制御対象接続の対応である。接続が変われば、信号レビューもやり直す必要がある。

<a id="plain-xmlとnetxml"></a>

### 標準の拡張マークアップ形式と`.net.xml`

スーモでは、道路区間、ノード、接続等をplain 拡張マークアップ形式として記述し、`netconvert`で実行用の`.net.xml`を生成できる。

```text
plain XML
   ↓ netconvert
.net.xml
```

`.net.xml`には、交差点内部構造、接続、right-of-道路地物等の生成情報が含まれる。そのため、生成後の`.net.xml`を手作業で修正するのではなく、入力側のplain 拡張マークアップ形式や属性解決器結果を修正して再生成する必要がある。

<a id="whatresolverが担う中間表現"></a>

## 内容：属性解決器が担う中間表現

属性解決器は、オープンストリートマップ 出典とスーモ 具体化の間に置かれる。

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

属性解決器は、次の問いに答える。

- この値は決まったか。
- どの出典 属性タグを読んだか。
- どの規則を使ったか。
- 出典明示値か、規則導出値か、仮定値か。
- どの方向・車線・車種・時間に適用されるか。
- 不明または競合なら、なぜ停止したか。

この中間成果物があることで、スーモへ入る前の判断を単独で検証できる。

<a id="howdirected-segmentが方向を保持する仕組み"></a>

## 方法：方向付き区間が方向を保持する仕組み

オープンストリートマップ 道路地物をそのまま反転すると、方向別属性タグとの対応が崩れる可能性がある。

例えば次の属性タグがある。

```text
lanes:forward=2
lanes:backward=1
maxspeed:forward=50
maxspeed:backward=40
```

道路地物のノード順を反転してしまうと、`forward`と`backward`の意味も入れ替わる。そのため、v17では出典 道路地物を変更せず、方向を別の属性として表す。

```text
Directed Segment
= source Wayの一定区間 + source direction
```

例：

```text
ds:12345:0:4:forward
ds:12345:0:4:backward
```

この表現により、出典 道路地物 識別子、ノード列、方向別属性タグ、スーモ 道路区間の関係を追跡できる。

<a id="howlaneの順序を変換する仕組み"></a>

## 方法：車線の順序を変換する仕組み

オープンストリートマップの車線情報は、各走行方向から見た左から右の順序で解釈する。一方、スーモの車線 索引は右端を0として扱う。

そのため、属性解決器の車線 位置をスーモ 索引へ変換する必要がある。

```text
sumo_index = lane_count - 1 - lane_position
```

3車線の例：

| 属性解決器の車線 位置 | 意味 | SUMO index |
|---:|---|---:|
| 0 | 左端 | 2 |
| 1 | 中央 | 1 |
| 2 | 右端 | 0 |

この変換を明文化しないと、車線別通行許可が左右反転する危険がある。

<a id="howaccess-ruleを適用する仕組み"></a>

## 方法：接続 規則を適用する仕組み

接続処理では、最初に「どの組へ適用されるか」を決め、その後に「複数規則のどれが優先されるか」を決める。

### 適用対象の決定

```text
direction scope
lane scope
```

例えば`bus:lanes:forward`は、順方向方向の指定車線だけに適用する。

### 条件の評価

```text
vehicle
日時
目的
authorization・permit
```

<a id="複数ruleの比較"></a>

### 複数規則の比較

v17では、次の4軸を使用する。

```text
spatial
vehicle
temporal
purpose
```

すべての軸で同等以上に限定され、少なくとも一軸でより限定される規則を、より具体的な規則として扱う。

これは単純な「最後に書かれた規則を採用する」方式ではない。入力順を変えても結果が変わらないようにするためである。

<a id="howformalとstructuralを分ける理由"></a>

## 方法：正式と構造上のを分ける理由

道路ネットワークの開発では、欠損値があると処理を最後まで試せない場合がある。

そこで構造処理設定では、登録済みの仮定を使って、構造確認用道路網を作ることを許す。

例：

```text
総車線数=4
方向別車線数なし
→ structuralでは2+2と仮定可能
```

しかし、この2+2は出典から確認された値ではない。そのため正式処理設定では使用しない。

```text
structural
→ 実装・構造確認用
→ model_assumedを条件付きで許可

formal
→ 正式な研究入力候補
→ model_assumedを禁止
```

この分離により、「スーモが動いたこと」と「研究入力として正当であること」を区別できる。

---

<a id="3-技術的背景決定性provenance検証"></a>

# 3. 技術的背景：決定性・出典・来歴・検証

<a id="whyなぜ同じ入力から同じ結果を得る必要があるのか"></a>

## 理由：なぜ同じ入力から同じ結果を得る必要があるのか

研究で使用する道路網は、後から同じ条件で再生成できなければならない。

結果が次の要因で変わると、比較実験の信頼性が下がる。

- Python dictionaryや記録の処理順
- 規則の記載順
- 使用するデータ構造・登録簿の版
- 交通シミュレーターの版
- library version
- 入力ファイルの変更
- 手作業による出力修正

そのため、v17では決定性と再現性を別々に確認する。

### 決定性

同じ論理入力に対して、同じ判断を返す性質である。

例：独立した接続 記録の順番を変えても、最終通行許可が変わらない。

### 再現性

同じ入力、設定、環境、コマンドから、同じ成果物を再生成できる性質である。

<a id="whatprovenanceとは何か"></a>

## 内容：出典・来歴とは何か

出典・来歴は、値や成果物がどこから来たかを追跡する情報である。

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

`value_origin`は出典・来歴全体を置き換えるものではない。

```text
value_origin
→ 値の由来を分類する短い状態

provenance
→ どのsource・rule・処理から生成されたかを詳しく記録
```

<a id="whathashは何を保証するのか"></a>

## 内容：ハッシュ値は何を保証するのか

ハッシュ値は、ファイルやデータ内容から計算される固定長の識別値である。

内容が1文字でも変化すると、通常は異なるハッシュ値になる。

v17ではSHA-256を使用し、ジェイソン形式についてはRFC 8785に基づく正規化を行ってから計算する。

ジェイソン形式は、同じ意味でもキー順や数値表記が異なる場合がある。

```json
{"a":1,"b":2}
```

```json
{"b":2,"a":1}
```

意味は同じでもバイト列は異なる。正規化は、意味が同じジェイソン形式を同じバイト表現へそろえるために使う。

ハッシュ値は「内容が正しい」こと自体を保証しない。保証するのは、登録した内容から変化していないこと、または同じ内容を再生成できたことに近い。

<a id="whatvalidationverificationacceptanceの違い"></a>

## 内容：検証・実装検証・受入の違い

この研究では、複数の検査を分離する。

| 検査 | 主な問い |
|---|---|
| Schema validation | データの形は正しいか。 |
| Semantic validation | データの意味・関係は正しいか。 |
| Fixture/oracle test | 小さな既知事例で期待結果と一致するか。 |
| Full-population accounting | 全入力が処理・除外として数えられているか。 |
| 属性解決の受入 | 正式属性成果物を次工程へ渡せるか。 |
| 交通シミュレーターの道路網統合受入 | 交通シミュレーターの道路網へ正しく統合されたか。 |
| Calibration | 観測値へモデルを合わせられるか。 |
| Independent validation | 別データでも交通現象を再現できるか。 |

ソフトウェア 試験が通っただけでは、正式 道路網が承認されたことにはならない。

<a id="howfail-closedで処理する"></a>

## 方法：不確実な場合は拒否で処理する

不確実な場合は拒否とは、不明・未対応・競合がある場合に、推測して処理を続けず停止する方針である。

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

不確実な場合は拒否は処理成功率を下げる場合があるが、研究入力へ説明不能な値が混入することを防ぐ。

---

# 技術補章A：プログラムの言葉で見る属性解決

この補章では、これまで説明した属性解決を、実際のプログラムがどのような部品に分かれ、どのようなデータを受け渡すかという観点から説明する。

本文では可能な限り日本語を用いる。ただし、ジェイソン形式の項目名、Pythonのクラス名、設定ファイルのキーなどは、既存仕様と外部ツールとの互換性を保つため英語表記を残す。

本補章のコードは**説明用の例**であり、現在のリポジトリに同じクラス、関数、配置が実装済みであることを示すものではない。

---

## A-1. 技術用語を日本語へ置き換える

<a id="whyなぜ用語の対応が必要なのか"></a>

### 理由：なぜ用語の対応が必要なのか

ソフトウェア開発では、同じ概念が英語のまま使用されることが多い。

例えば、`record`、`field`、`schema`、`validator`という語を理解しないまま仕様書を読むと、実際に何を作るのかが分かりにくい。

一方、英語をすべて日本語へ置き換えると、既存コード、ジェイソン形式、ヤムル形式、スーモ、オープンストリートマップの公式用語と対応しなくなる。

そのため、本書では次の方針を採る。

> 説明文では日本語を主に使い、プログラム上の正式な識別子は英語を保持する。

<a id="what主要用語の対応表"></a>

### 内容：主要用語の対応表

| 英語・識別子 | 本書で使う日本語 | プログラム上の意味 |
|---|---|---|
| リポジトリ | リポジトリ、開発資産の保管場所 | コード、設定、試験、文書を版管理する場所 |
| 成果物 | 成果物、生成物 | 処理によって作られ保存されるファイル |
| 記録 | レコード、1件のデータ | ジェイソン形式 対象やコンマ区切り形式の1行に相当する単位 |
| 項目 | 項目 | 記録内のキーと値の組 |
| キー | キー、項目名 | `resolution_status`などの名前 |
| 値 | 値 | `resolved`などの内容 |
| 列挙値 | 列挙型、許可値一覧 | 使用可能な値を有限個に限定する仕組み |
| null | 値なし | 空文字や0とは異なる「値が存在しない」状態 |
| identifier / ID | 識別子 | 記録や規則を一意に区別する名前 |
| 版 | 版 | 仕様や登録簿の変更単位 |
| 設定 | 実行設定 | 今回の実行で使用する条件の集合 |
| データ構造 | 構造定義 | 項目、型、必須条件を定める規則 |
| 登録簿 | 登録簿 | 使用可能な正式語彙・規則・識別子の一覧 |
| 検証器 | 検証器 | データ構造や意味条件に違反していないか調べる処理 |
| 解析器 | 構文解析器 | 文字列を構造化データへ変換する処理 |
| normalizer | 正規化器 | 同じ意味の表記を統一する処理 |
| classifier | 分類器 | 入力がどの事例や規則対象かを判定する処理 |
| 属性解決器 | 解決器 | 最終的な属性値・状態・由来を決める処理 |
| serializer | 直列化器、書出し器 | Python 対象等をJSON/YAMLへ変換する処理 |
| deserializer | 読込み変換器 | JSON/YAMLをPython 対象等へ変換する処理 |
| 具体化処理 | 具体化器、入力生成器 | 解決結果からスーモ plain 拡張マークアップ形式等を生成する処理 |
| 成果物一覧 | 実行記録表 | 入力、版、コマンド、ハッシュ値、出力をまとめるファイル |
| 検証用データ | 固定試験入力 | 特定事例を再現する小規模な入力 |
| 正解判定器 | 期待結果 | 検証用データに対して正しいと事前定義した出力 |
| invariant | 不変条件 | 常に成立しなければならない意味上の条件 |
| 述語 | 判定条件 | 真／偽を返す条件式 |
| 範囲 | 適用範囲 | 規則が対象とする方向、車線等 |
| 領域 | 対象集合 | 車両、時間、目的等の規則対象集合 |
| exception | 例外 | 通常処理を続行できないプログラム上の異常 |
| 停止コード | 停止理由コード | データ上の未解決・競合等を表す正式な理由 |
| ハッシュ値 | 内容指紋 | ファイル内容から計算される固定長の値 |
| 正規化 | 正準化、標準形変換 | 同じ意味のデータを同じバイト列へそろえる処理 |
| 実行時間 | 実行時 | コードが実際に動いている時点 |
| production code | 本番処理コード | 全データを処理する正式なコード |
| 試験 | 試験 | 期待する動作を満たすか確認する処理 |
| 判定基準 | 受入関門 | 条件をすべて満たした場合だけ次工程へ進める判定 |

<a id="how実際の文書とcodeでどう表記するか"></a>

### 方法：実際の文書とコードでどう表記するか

説明文では次のように書く。

```text
解決器（Resolver）は、正規化済みの道路属性を受け取り、
解決状態（resolution_status）と値の由来（value_origin）を出力する。
```

コードでは既存仕様に合わせて英語識別子を使用する。

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

- 分類名、関数名、ジェイソン形式 キーは英語にする。
- comment、docstring、誤り説明は日本語で書く。
- 英語識別子の意味を仕様書と登録簿で日本語説明する。
- 略語だけで命名せず、意味が分かる名前を使う。

---

## A-2. プログラム全体を処理段階へ分ける

<a id="whyなぜ一つの大きな関数にしないのか"></a>

### 理由：なぜ一つの大きな関数にしないのか

すべての処理を一つの関数に書くと、次の問題が起こる。

- どこで値が変わったか分からない。
- オープンストリートマップの読込み失敗と規則競合を区別できない。
- 一つの修正が別の属性へ影響する。
- 検証用データで小さな処理だけを試験できない。
- 出典・来歴を記録しにくい。
- v16とv17の境界が曖昧になる。

そのため、入力から出力までを責任別の処理段階へ分割する。

<a id="what推奨する処理の流れ"></a>

### 内容：推奨する処理の流れ

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

<a id="how各段階の入力と出力"></a>

### 方法：各段階の入力と出力

| 段階 | 入力 | 主な処理 | 出力 |
|---|---|---|---|
| 入力読込み | オープンストリートマップ、設定、登録簿 | ファイルを安全に読む | raw object |
| 構文解析 | 属性タグ文字列 | 型・構文へ分解する | parsed value |
| 正規化 | parsed value | 表記を統一する | canonical value |
| 分類 | source observation | 事例と適用規則を判定 | classification record |
| 属性解決 | classification＋rule | 値、状態、由来を決定 | resolution record |
| 意味検証 | resolution artifact | 不変条件を検査 | validation result |
| 書出し | validated object | 正本 ジェイソン形式へ変換 | JSON artifact |
| 具体化 | formal artifact | plain 拡張マークアップ形式へ反映 | スーモ入力ファイル |
| スーモ変換 | plain XML | `netconvert`実行 | `.net.xml` |
| 統合検証 | `.net.xml` | 接続等を確認 | network acceptance result |

重要なのは、属性解決の完了とスーモネットワークの完成を別段階として扱うことである。

---

### 方法：各段階の入力と出力

<a id="whyなぜ辞書だけで扱わないのか"></a>

### 理由：なぜ辞書だけで扱わないのか

Pythonでは、ジェイソン形式をそのまま`dict`として扱える。

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

<a id="what列挙型とデータクラス"></a>

### 内容：列挙型とデータクラス

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

`frozen=True`は、作成後に記録を不用意に変更しにくくする指定である。

<a id="how作成時に検査する"></a>

### 方法：作成時に検査する

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

この関数は説明用である。実際にはジェイソン形式 データ構造による検査とSemantic 検証器による検査を分担させる。

---

#### データクラス

<a id="whyなぜ区別するのか"></a>

### 理由：なぜ区別するのか

プログラムでは、次の4つは異なる意味を持つ。

```text
null
""
0
fieldそのものがない
```

これらを混同すると、欠損なのか有効値なのか判断できなくなる。

<a id="whatそれぞれの意味"></a>

### 内容：それぞれの意味

| 表現 | 意味の例 |
|---|---|
| `null` | 項目は定義されているが、値は存在しない |
| `""` | 空の文字列という値が存在する |
| `0` | 数値0という有効値が存在する |
| 項目省略 | 記録形式に違反、または当該項目を出力していない |

例：

```json
{
  "lane_position": null,
  "stop_code": null,
  "rule_ids": []
}
```

- `lane_position: null`：この属性には車線位置が適用されない。
- `stop_code: null`：停止していない。
- `rule_ids: []`：規則 識別子の配列は存在するが、要素が0件である。

<a id="howschemaで区別する"></a>

### 方法：データ構造で区別する

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

<a id="whyなぜ3つへ分けるのか"></a>

### 理由：なぜ3つへ分けるのか

オープンストリートマップ 属性タグは基本的に文字列である。

例えば、次の値はすべて一方通行を示す可能性がある。

```text
yes
1
true
```

しかし、ファイルから文字列を読むこと、値が文法的に正しいか調べること、同じ意味の表記を統一することは別の責任である。

<a id="what三つの責任"></a>

### 内容：三つの責任

#### 読込み器

ファイルから値を取得する。

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

<a id="how由来を保持する"></a>

### 方法：由来を保持する

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

<a id="whyなぜ分けるのか"></a>

### 理由：なぜ分けるのか

分類と解決を一つにすると、「どの事例と判断したか」と「どの値を採用したか」が混ざる。

例えば、`oneway`欠損道路を次のように分類する。

```text
分類：
ordinary road with missing oneway
```

その後、登録済み規則により次の値を解決する。

```text
解決値：
no
```

分類結果は、規則や値を将来変更しても比較可能なように保持する必要がある。

<a id="what分類器"></a>

### 内容：分類器

分類器は、入力がどの事例に属するかを判断する。

```python
@dataclass(frozen=True)
class ClassificationRecord:
    classification_record_id: str
    source_way_id: int
    attribute_name: str
    classification_code: str
    matched_rule_ids: tuple[str, ...]
```

<a id="what解決器"></a>

### 内容：解決器

解決器は、分類結果と登録簿を使い、値・状態・由来を決定する。

```python
def resolve_oneway(
    classification: ClassificationRecord,
    raw_value: str | None,
    rule_registry: "OnewayRuleRegistry",
) -> ResolutionRecord:
    ...
```

<a id="how分類投影を変えない"></a>

### 方法：分類投影を変えない

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

<a id="a-7-directed-segmentをオブジェクトとして表す"></a>

## A-7. 方向付き区間をオブジェクトとして表す

<a id="whyなぜwayを直接反転しないのか"></a>

### 理由：なぜ道路地物を直接反転しないのか

オープンストリートマップ 道路地物のノード順序は、方向別属性タグと関係の基準である。

道路地物を反転してしまうと、次の対応が壊れる可能性がある。

- `lanes:forward`
- `lanes:backward`
- `maxspeed:forward`
- `maxspeed:backward`
- 右左折制限
- 出典ファイルのハッシュ値
- 出典・来歴

そのため、出典 道路地物は変更せず、走行方向を別の対象として表す。

<a id="whatdirected-segmentの型"></a>

### 内容：方向付き区間の型

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

<a id="howonewayから生成する"></a>

### 理由：なぜ道路地物を直接反転しないのか

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

逆方向 形状をスーモへ出力するときは、走行順としてノード列を逆にしてよいが、出典 対象自体を変更してはならない。

```python
def traversal_nodes(segment: DirectedSegment) -> tuple[int, ...]:
    if segment.source_direction is SourceDirection.FORWARD:
        return segment.source_node_ids
    return tuple(reversed(segment.source_node_ids))
```

`source_node_ids`は原典順のまま保持し、`traversal_nodes`だけを必要時に計算する。

---

### 内容：方向付き区間の型

<a id="whyなぜruleをif文だけで書かないのか"></a>

### 理由：なぜ規則をif文だけで書かないのか

大量の`if`文へ規則を直接埋め込むと、優先順位、版、出典、検証用データとの対応を追跡しにくい。

```python
# 規則がcodeへ埋め込まれ、根拠やversionが分からない例
if highway == "residential" and oneway is None:
    oneway = "no"
```

v17では、規則の定義を登録簿に置き、コードは規則を評価する役割を担う。

<a id="whatrule-object"></a>

## A-8. 規則、判定条件、適用範囲

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

<a id="howregistryからruleを適用する"></a>

### 方法：登録簿から規則を適用する

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

規則の順序は、ファイルの偶然の並び順ではなく、登録簿で定義された優先順位に従う。

ただし接続 specificityのように部分順序で比較する規則では、単純な優先順位を使用しない。

---

# 規則がコードへ埋め込まれ、根拠や版が分からない例

<a id="whyなぜ単純な番号順では駄目なのか"></a>

### 理由：なぜ単純な番号順では駄目なのか

接続 規則は、方向、車線、車種、時刻、目的等の複数条件を持つ。

例えば、次の二つがある。

```text
Rule A:
すべてのmotor_vehicleを禁止

Rule B:
delivery車両を平日10時から12時だけ許可
```

Rule Bは車種と時間の両方で具体的である。

単純に「後に書かれた規則」や「番号が大きい規則」を選ぶと、入力順によって結果が変わる。

<a id="what適用範囲と意味軸"></a>

### 内容：適用範囲と意味軸

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

実際の時間集合は巨大になり得るため、実装では区間や述語で表す可能性がある。上記は概念説明用である。

<a id="how支配関係を判定する"></a>

### 方法：支配関係を判定する

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

支配されない規則だけを残す。

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

残った規則のeffectがすべて同じなら採用する。

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

<a id="a-10-json-schemaとpython検証器の役割分担"></a>

### 理由：なぜ単純な番号順では駄目なのか

<a id="whyなぜ両方必要なのか"></a>

### 理由：なぜ両方必要なのか

ジェイソン形式 データ構造はファイル単体の構造検査に適している。

PythonのSemantic 検証器は、複数記録、外部登録簿、ハッシュ値、入力と出力の関係を調べることに適している。

どちらか一方だけでは不十分である。

<a id="whatschemaで検査する内容"></a>

### 内容：データ構造で検査する内容

- 必須項目
- 文字列・数値・配列等の型
- 列挙値
- null許可
- 解決済み時の必須項目
- 正式時の`model_assumed`禁止
- 識別子の文字形式

<a id="whatsemantic-validatorで検査する内容"></a>

## A-10. ジェイソン形式データ構造とPython検証器の役割分担

- 出典 道路地物が不変か。
- `oneway=-1`から逆方向だけが生成されたか。
- 車線 件数の合計が一致するか。
- 登録簿参照が存在するか。
- 接続のmaximal 規則が正しいか。
- 母集団 equationが成立するか。
- 同一実行のハッシュ値が一致するか。

<a id="how検証結果を構造化する"></a>

### 方法：検証結果を構造化する

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

検証器は、単に`True`や`False`を返すだけでなく、どの条件が、どの記録で、なぜ失敗したかを記録する。

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

### 内容：データ構造で検査する内容

<a id="whyなぜ区別するのか-1"></a>

### 理由：なぜ区別するのか

すべての停止をPythonの例外だけで表すと、データの問題とコードの故障が混ざる。

例えば次はデータとして予想される停止である。

- 方向別車線数がない。
- 複数接続 規則が競合する。
- 条件付き構文が未対応である。

一方、次はプログラムの故障である。

- 存在するはずの変数が未定義。
- ジェイソン形式 ファイルを破損した状態で書き出した。
- 同じ記録 識別子を不正に2回生成した。

<a id="what二種類の失敗"></a>

### 内容：二種類の失敗

#### 業務・仕様上の停止

Resolution 記録へ記録する。

```text
resolution_status: unresolved
stop_code: LANE_DIRECTIONAL_ALLOCATION_MISSING
```

これは処理対象データの状態である。

#### プログラム例外

コードの継続が安全でない場合に送出する。

```python
class ResolverProgrammingError(RuntimeError):
    """仕様上想定しないプログラム内部の異常。"""
```

<a id="how境界で変換する"></a>

### 方法：境界で変換する

期待されるデータ停止は、できるだけ記録として返す。

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

登録簿欠落や不可能な内部状態は例外にする。

```python
if stop_code not in stop_code_registry:
    raise ResolverProgrammingError(
        f"未登録stop codeがcodeから出力された: {stop_code}"
    )
```

---

## A-12. 正準化とハッシュ

<a id="whyなぜ普通にjson保存するだけでは駄目なのか"></a>

### 理由：なぜ普通にジェイソン形式保存するだけでは駄目なのか

ジェイソン形式では、対象のキー順序や空白が異なっても意味は同じである。

```json
{"a":1,"b":2}
```

```json
{
  "b": 2,
  "a": 1
}
```

しかし、ファイルのバイト列は異なるため、そのままSHA-256を計算すると異なるハッシュ値になる。

同じ意味のデータから同じハッシュ値を得るには、標準形へ変換する必要がある。

<a id="what正準化"></a>

### 内容：正準化

正準化は、同じ意味のジェイソン形式を同じバイト列へそろえる処理である。

v17ではRFC 8785のジェイソン形式 Canonicalization Schemeを使用する方針である。

<a id="howhashを計算する"></a>

### 方法：ハッシュ値を計算する

説明用の疑似コードである。

```python
import hashlib


def sha256_canonical_json(value: object) -> str:
    canonical_bytes = rfc8785_dumps(value)
    return hashlib.sha256(canonical_bytes).hexdigest()
```

記録 識別子を作る際は、結果やtimestampのように後から変わる項目を含めず、同一性だけを対象にする。

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

ハッシュ値 項目自身を自分のハッシュ値計算対象へ入れると循環するため、含めてはならない。

---

## A-13. 設定ファイルをプログラムへ読み込む

<a id="whyなぜ設定をcodeから分離するのか"></a>

### 理由：なぜ設定をコードから分離するのか

条件をコードへ直接書くと、設定変更のたびにコード変更と再確認が必要になる。

また、過去実行でどの設定を使ったか追跡しにくい。

<a id="whatyaml設定の読込み"></a>

### 内容：ヤムル形式設定の読込み

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

<a id="how型へ変換して検査する"></a>

### 方法：型へ変換して検査する

```python
import yaml


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file)

    if not isinstance(loaded, dict):
        raise ValueError("Configurationのrootはobjectでなければならない。")

    return loaded
```

読込み後にデータ構造とSemantic 検証器を実行する。

```python
raw_config = load_yaml("sumo_network_v17.yml")
validate_json_schema(raw_config, configuration_schema)
config = parse_configuration(raw_config)
validate_configuration_semantics(config)
```

`yaml.safe_load`を使用し、安全でない任意対象生成を避ける。

---

<a id="a-14-serializerとmanifest"></a>

### 理由：なぜ設定をコードから分離するのか

<a id="whyなぜ出力方法を固定するのか"></a>

### 理由：なぜ出力方法を固定するのか

同じdataでも、書出し順、日時項目、浮動小数点表現等が異なるとハッシュ値が変わる。

また、ジェイソン形式だけを保存しても、どのコマンド・コード・設定で生成したか分からない。

<a id="what二種類の出力"></a>

### 内容：二種類の出力

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

<a id="how書出しを一か所へ集約する"></a>

### 方法：書出しを一か所へ集約する

```python
def write_canonical_json(path: str, value: object) -> str:
    canonical_bytes = rfc8785_dumps(value)

    with open(path, "wb") as file:
        file.write(canonical_bytes)

    return hashlib.sha256(canonical_bytes).hexdigest()
```

各処理が独自のジェイソン形式出力を行うのではなく、共通Serializerを使用する。

成果物一覧には次を記録する。

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

<a id="a-15-fixtureoracletestの実装"></a>

## A-15. 検証用データ・正解判定器・試験の実装

<a id="whyなぜ本番データだけで試験しないのか"></a>

### 理由：なぜ本番データだけで試験しないのか

本番データは件数が多く、複数の要因が同時に含まれる。

失敗した場合、どの規則が原因か切り分けにくい。

小さな検証用データでは、一つの規則だけを明示的に確認できる。

<a id="whatfixtureの例"></a>

### 内容：検証用データの例

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

<a id="whatoracleの例"></a>

### 内容：正解判定器の例

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

<a id="howtestを書く"></a>

### 方法：試験を書く

```python
def test_oneway_minus_one_generates_backward_only() -> None:
    fixture = load_fixture("DIR-ONEWAY-MINUS-001")
    oracle = load_oracle("DIR-ONEWAY-MINUS-001")

    actual = run_directed_segment_generator(fixture)

    assert actual == oracle["expected_directed_segments"]
```

ただし、正解判定器を正式運用 コードで自動生成してはならない。

期待結果は仕様と独立確認に基づいて作成する。

### 負の試験

正しい事例だけでなく、違反を正しく拒否することも確認する。

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

### 内容：正解判定器の例

<a id="whyなぜ配置を整理するのか"></a>

### 理由：なぜ配置を整理するのか

仕様、設定、登録簿、データ構造、検証用データ、コードが同じfolderへ混在すると、正本と実装の区別が難しくなる。

<a id="what概念的な配置例"></a>

### 内容：概念的な配置例

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

これは説明用の構造例であり、既存リポジトリの命名規則と整合させて調整する。

<a id="how分離の原則"></a>

### 方法：分離の原則

- `specifications`は人間向けの規範を置く。
- `configuration`は実行選択を置く。
- `schemas`は形式検査を置く。
- `registries`は正式語彙・規則を置く。
- `fixtures`は小規模入力と期待結果を置く。
- `src`は正式運用 コードを置く。
- `tests`は検証コードを置く。
- `artifacts`は生成物を置く。
- v16とv17を別ディレクトリにする。
- 構造上のと正式を別ディレクトリにする。

---

<a id="a-17-関数とmoduleの責任を小さくする"></a>

## A-17. 関数とモジュールの責任を小さくする

<a id="whyなぜ責任を小さくするのか"></a>

### 理由：なぜ責任を小さくするのか

一つの関数が読込み、正規化、規則選択、ファイル出力まで行うと、試験しにくくなる。

<a id="what望ましい関数の特徴"></a>

### 内容：望ましい関数の特徴

- 一つの目的だけを持つ。
- 入力と出力が明確である。
- 外部状態への依存を少なくする。
- 同じ入力なら同じ出力を返す。
- ファイル入出力と純粋な計算を分ける。

<a id="how純粋関数として書く"></a>

### 方法：純粋関数として書く

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

この関数はファイルを読まず、設定も変更せず、同じ入力に同じ出力を返すため試験しやすい。

```python
def test_sumo_lane_index() -> None:
    assert sumo_lane_index(3, 0) == 2
    assert sumo_lane_index(3, 1) == 1
    assert sumo_lane_index(3, 2) == 0
```

---

## A-18. 型検査・静的解析・実行時検査

<a id="whyなぜ複数の検査が必要なのか"></a>

### 理由：なぜ複数の検査が必要なのか

誤りには、コードを書く時点で見つけられるものと、実際のdataを読まなければ分からないものがある。

<a id="what検査の種類"></a>

### 内容：検査の種類

| 検査 | 対象 | 例 |
|---|---|---|
| 型検査 | コード内の型の整合 | `str`を期待する関数へ`int`を渡す |
| 静的解析 | コード品質・危険な書き方 | 未使用変数、到達不能コード |
| Unit Test | 小さな関数 | `oneway=-1`の方向集合 |
| Schema Validation | JSON/YAMLの形 | enum、required field |
| Semantic Validation | dataの意味 | lane count equation |
| Integration Test | モジュール間接続 | 属性解決器からSerializerまで |
| Runtime Fixture | 外部ツール含む実行 | plain 拡張マークアップ形式をスーモが読めるか |
| Acceptance Gate | 使用可能性 | 正式 成果物を次工程へ渡せるか |

<a id="how代表的なtoolの位置付け"></a>

### 方法：代表的なツールの位置付け

Python環境では、例えば次のツールを使える。

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

ただし、どのツールを採用するかはリポジトリの既存構成に合わせて決定する。

`pytest`がすべて通ったことは、属性解決の受入を意味しない。

---

<a id="a-19-日志監査記録日本語のerror-message"></a>

### 理由：なぜ複数の検査が必要なのか

<a id="whyなぜlogを残すのか"></a>

### 理由：なぜ記録を残すのか

処理が停止した場合、後から次を確認する必要がある。

- どの記録で停止したか。
- どの規則を評価したか。
- どの登録簿の版を使ったか。
- どの値同士が競合したか。
- どのコマンドで実行したか。

<a id="what構造化log"></a>

### 内容：構造化記録

人間向け文章だけでなく、機械的に検索可能な項目を持たせる。

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

<a id="how英語識別子と日本語説明を併記する"></a>

### 方法：英語識別子と日本語説明を併記する

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

programが判定に使う`stop_code`は英語の固定識別子とし、人間が読む説明は日本語にする。

---

<a id="a-20-phase-1で作るのはcodeそのものではなくcodeの契約である"></a>

### 理由：なぜ記録を残すのか

<a id="whyなぜphase-1で全面実装しないのか"></a>

### 内容：構造化記録

仕様、データ構造、登録簿が確定する前にコードを書くと、正式語彙やdata構造が途中で変わり、実装と検証用データを作り直す可能性が高い。

<a id="whatプログラム契約"></a>

### 内容：プログラム契約

Phase 1で固定するのは、モジュール間で受け渡すdataと判断規則である。

```text
どのfieldが必要か
どのenumを使うか
どのrule IDを使うか
どの条件を停止とするか
どのInvariantを検査するか
どの成果物を出力するか
```

これはプログラム用インターフェース契約やデータ契約に近い。

<a id="how契約を先にtest可能にする"></a>

### 方法：契約を先に試験可能にする

Phase 1では次を行う。

- データ構造 ファイルを作る。
- 登録簿 ファイルを作る。
- 不変条件 識別子を作る。
- 設定の参照先を固定する。
- 検証用データで必要になる事例を列挙する。
- 正式運用 コードの実装位置を仕様同期表へ記録する。

その後、Phase 2で正解判定器を固定し、Phase 3以降で実装する。

---

# 4. なぜ6つの成果物へ分けるのか

<a id="whyなぜ仕様書一つでは駄目なのか"></a>

## 理由：なぜ仕様書一つでは駄目なのか

仕様書は人間には読めるが、プログラムは仕様書の文章をそのまま実行できない。

例えば、仕様書に次の規則があるとする。

> 正式処理設定では`model_assumed`を使用してはならない。

この一文だけでは、次のことが決まっていない。

- 正式処理設定をどの設定で選ぶのか。
- `model_assumed`を正式な値としてどこに登録するのか。
- どのデータ項目へ格納するのか。
- 正式 記録に入った場合、どの検査で発見するのか。
- どの検証用データで動作確認するのか。
- 現在のコードが対応しているか。

一つの文を、設定・構造・語彙・意味検査・実装確認へ分解する必要がある。

<a id="what6成果物は何を担当するのか"></a>

## 内容：6成果物は何を担当するのか

| 成果物 | 担当する問い |
|---|---|
| 仕様同期表 | この規則はどこへ反映するのか。 |
| 設定 | 今回の実行では何を使うのか。 |
| JSON Schema | データの形は正しいか。 |
| 登録簿群 | 使用してよい正式な語彙・規則は何か。 |
| 意味上の不変条件一覧 | データの意味と関係は正しいか。 |
| 差分レビュー報告書 | 現在のリポジトリに何が足りないか。 |

<a id="howどのように使い分けるのか"></a>

## 方法：どのように使い分けるのか

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

<a id="configuration"></a>

### 設定

```yaml
profile_policy:
  formal:
    allow_model_assumed: false
```

<a id="schema"></a>

### データ構造

```text
profile=formal かつ value_origin=model_assumed を拒否する。
```

<a id="registry"></a>

### 登録簿

```yaml
value: model_assumed
formal_eligible: false
allowed_profiles:
  - structural
```

<a id="semantic-invariant"></a>

### 意味上の不変条件

```text
formal recordにmodel_assumedが1件も存在しない。
```

### 差分レビュー

```text
現在のserializerがformalにもmodel_assumedを出力するならMajor findingとする。
```

---

# 5. 6成果物の全体像

<a id="whyなぜ全体像を先に理解するのか"></a>

## 理由：なぜ全体像を先に理解するのか

6つを別々に作るだけでは、成果物同士が矛盾する可能性がある。

例えば、次のような状態は避けなければならない。

- 仕様書では`resolved`だが、データ構造では`complete`になっている。
- 設定では正式で仮定値を禁止しているが、登録簿では許可されている。
- 停止コードがコードにはあるが登録簿にはない。
- データ構造は更新されたが検証用データは旧形式である。

<a id="what全体の構造"></a>

## 内容：全体の構造

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

<a id="howどの順序で作るのか"></a>

## 方法：どの順序で作るのか

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
| 上位 | v17規範仕様書の要件 |
| 同位 | 設定、データ構造、登録簿、不変条件、差分レビュー |
| 下位 | Fixture、Oracle、Validator、Production Code、Evidence |
| 入力 | 規範仕様、リポジトリ現状、各成果物の保存先 |
| 出力 | 要件ごとの対応関係と進捗状態 |
| 保証すること | 仕様要求がどこへ反映されるか追跡できる |
| 保証しないこと | 実装が正しいこと、試験が合格したこと |
| 主な意図 | INT-011、INT-019 |

<a id="whyなぜ必要なのか"></a>

## 理由：なぜ必要なのか

仕様書には多くの必須規則がある。

しかし、各規則が次のどこに反映されるかを追跡できなければ、実装漏れが生じる。

- 設定
- データ構造
- 登録簿
- 検証器
- 検証用データ
- 正解判定器
- Production code

仕様同期表がない場合、次の問題が起こる。

- 仕様書だけが更新される。
- 同じ規則が複数ファイルで異なる意味になる。
- 検証用データがないままコードだけ完成する。
- 完成状況を第三者が判断できない。

<a id="技術的背景requirements-traceabilityとは何か"></a>

# 6. 成果物1：仕様同期表

仕様同期表は、ソフトウェア工学やシステム工学でいう要件 Traceability Matrixに相当する。

要求を次の方向へ追跡できるようにする。

```text
仕様要求 → 設計 → Schema・Registry → 実装 → Test → Evidence
```

逆方向にも追跡できる必要がある。

```text
Test失敗 → 対応する実装 → 対応するRequirement ID → 仕様上の根拠
```

この双方向追跡により、不要な実装、試験されていない要求、根拠のない規則を検出できる。

特にv17では、文書だけでなく複数のmachine-readable 成果物が正本を構成するため、単なる作業一覧ではなく、要求単位の対応表が必要になる。

<a id="what何を作るのか"></a>

## 内容：何を作るのか

仕様書の必須規則を1行ずつ登録する追跡可能性 行列を作る。

推奨ファイルは次である。

```text
05_src/traffic_simulation/specifications/
  v17_attribute_resolution_traceability_matrix.md
```

必要に応じてコンマ区切り形式も作る。

### 最低限必要な列

| 列 | 意味 |
|---|---|
| `requirement_id` | 規則の一意な識別子 |
| `specification_section` | 仕様書の場所 |
| `requirement_summary` | 規則の要約 |
| `configuration_location` | 設定上の場所 |
| `schema_location` | データ構造上の場所 |
| `registry_location` | 登録簿上の場所 |
| `validator_location` | 検証器上の場所 |
| `fixture_ids` | 対応検証用データ |
| `oracle_location` | 正解データの場所 |
| `production_location` | Production コードの場所 |
| `current_status` | 現在の状態 |
| `evidence` | 変更記録、ハッシュ値、試験結果 |
| `owner` | 担当者 |

<a id="要求idの例"></a>

### 要求識別子の例

```text
AR-STATE-xxx   状態・由来
AR-DIR-xxx     Directed Segment・oneway
AR-LANE-xxx    方向別車線
AR-SPEED-xxx   制限速度
AR-ACCESS-xxx  access
AR-COND-xxx    条件付き規制
AR-ACC-xxx     受入条件
```

<a id="howどのように作るのか"></a>

## 方法：どのように作るのか

<a id="step-1仕様書から必須文を抽出する"></a>

### 手順 1：仕様書から必須文を抽出する

例えば次の文を抽出する。

```text
v17 writerはvalue_stateを出力してはならない。
oneway=-1はbackwardのみを生成する。
formal profileはmodel_assumedを使用してはならない。
```

<a id="step-2一つの判定可能な要求へ分割する"></a>

### 手順 2：一つの判定可能な要求へ分割する

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

<a id="step-3反映先を記入する"></a>

### 手順 3：反映先を記入する

例：

| 項目 | 内容 |
|---|---|
| Requirement ID | `AR-DIR-004` |
| 要件 | `oneway=-1`は逆方向のみ生成する |
| 設定 | `direction_model` |
| データ構造 | `source_direction` |
| 登録簿 | `oneway_rule_registry` |
| 検証器 | Directed Segment lineage check |
| 検証用データ | `DIR-ONEWAY-MINUS-001` |
| Code | Directed Segment generator |
| 状態 | `partial` |

<a id="step-4状態を付ける"></a>

### 手順 4：状態を付ける

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
- 対象とする仕様書版とハッシュ値が記録されている。

---

<a id="7-成果物2v17-configuration"></a>

# 7. 成果物2：v17 設定

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 承認済み方針・決定記録 記録 |
| 同位 | Registry、Schema、Scenario Context、Environment Manifest |
| 下位 | Loader、属性解決器、検証器、具体化処理の実行 |
| 入力 | policy ID、profile、population、Schema/Registry version |
| 出力 | 一つの実行で有効な設定集合 |
| 保証すること | どの条件・版で実行したか固定する |
| 保証しないこと | 規則の意味そのもの、実装の正しさ |
| 主な意図 | INT-005、INT-009、INT-012、INT-017 |

<a id="whyなぜ必要なのか-1"></a>

## 理由：なぜ必要なのか

仕様書は、v17で可能な規則全体を説明する。

一方、実際の実行では次を一意に決める必要がある。

- どの方針を使うか。
- どの母集団を使うか。
- 構造上のか正式か。
- どのデータ構造 版を使うか。
- どの登録簿の版を使うか。
- どの受入条件を使うか。
- どの交通シミュレーターの版を使うか。

これらをコード内へ直接書くと、実行ごとの設定が追跡できなくなる。

<a id="技術的背景宣言的configuration"></a>

## 技術的背景：宣言的設定

設定は、処理手順を直接書く命令型コードではなく、「どの方針・版・設定プロファイルを使うか」を宣言する成果物である。

宣言的に分離する利点は次である。

- コードを変更せず実行条件を切り替えられる。
- 実行条件をGitで比較できる。
- 実行後に同じ条件を再現できる。
- v16とv17を同じcodebaseで扱っても、設定を混同しにくい。
- 設定 ハッシュ値を成果物一覧へ記録できる。

ただし、設定へ規則の意味を重複して書くと、仕様書や登録簿との不一致が起きる。そのため設定は選択と参照に限定する。

<a id="what何を作るのか-1"></a>

## 内容：何を作るのか

今回の実行で有効な設定を記録するヤムル形式 ファイルを作る。

推奨ファイルは次である。

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

<a id="howどのように作るのか-1"></a>

## 方法：どのように作るのか

<a id="step-1v16を保存する"></a>

### 手順 1：v16を保存する

v16 設定は変更しない。

v17用に新しい設定 識別子と出力先を用意する。

<a id="step-2仕様書の選択項目を移す"></a>

### 手順 2：仕様書の選択項目を移す

次を設定へ移す。

- policy ID
- 設定プロファイル
- Schema version
- 登録簿参照
- direction model
- lane rule
- access rule
- acceptance threshold

<a id="step-3registryを参照する"></a>

### 手順 3：登録簿を参照する

設定へ規則本文を重複して書かず、保存先、版、ハッシュ値を記録する。

```yaml
registries:
  stop_codes:
    path: ...
    version: ...
    sha256: ...
```

<a id="step-4configuration自体を検査する"></a>

### 手順 4：設定自体を検査する

設定 データ構造とSemantic 検証器を通す。

<a id="configurationに書かないもの"></a>

### 設定に書かないもの

- `oneway=-1`の詳細な意味論
- 停止コードの修正方法
- 検証用データの期待出力
- 接続 dominanceの長い説明

これらは仕様書や登録簿が担当する。

### 完了条件

- v17専用設定 識別子がある。
- v16を変更していない。
- 構造上のと正式が区別されている。
- データ構造と登録簿の版が指定されている。
- 受入条件が機械可読である。
- 設定自身が検証を通る。

---

<a id="8-成果物3json-schema"></a>

# 8. 成果物3：ジェイソン形式 データ構造

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | v17データ契約、正式列挙値 |
| 同位 | Registry、Semantic Invariant |
| 下位 | JSON/YAML成果物、Serializer、データ構造 検証器 |
| 入力 | 必須項目、型、列挙値、条件付き必須規則 |
| 出力 | 有効 / 不正と構造エラー |
| 保証すること | dataの形式と基本組合せが正しい |
| 保証しないこと | 道路方向、集合包含、母集団等の意味的正しさ |
| 主な意図 | INT-003、INT-012、INT-019 |

<a id="whyなぜ必要なのか-2"></a>

## 理由：なぜ必要なのか

プログラムがジェイソン形式を出力しても、項目の不足や型の誤りがある可能性がある。

例えば、次の記録は問題である。

```json
{
  "resolution_status": "finished",
  "value_origin": "probably",
  "effective_value": null
}
```

`finished`や`probably`はv17で認められた値ではない。

また、`resolved`なのに値がない、正式なのに仮定値がある、といった不正も検出する必要がある。

## 技術的背景：構文検査と意味検査の境界

ジェイソン形式 データ構造は、ジェイソン形式 documentが定められた契約に従っているかを検査する。

主な機能は次である。

- `type`：文字列、数値、対象、array等を制約する。
- `required`：必須項目を指定する。
- `enum`：許可する有限値を指定する。
- `pattern`：識別子等の文字列形式を制約する。
- `minimum`・`maximum`：数値範囲を制約する。
- `if`・`then`・`else`：項目間の条件付き制約を定義する。
- `oneOf`・`anyOf`・`allOf`：複数データ構造の組合せを定義する。

一方、ジェイソン形式 データ構造は基本的に一つのdocument構造を検査する仕組みである。複数記録間の集合関係、外部登録簿参照、出典 成果物とのハッシュ値照合等は、通常のデータ構造だけでは十分に扱えない。

そのため、データ構造 検証とSemantic 検証を別の層にする。

<a id="what何を作るのか-2"></a>

## 内容：何を作るのか

データの構造と基本的な組合せを検査するジェイソン形式 データ構造群を作る。

最低限、次のデータ構造が必要である。

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

<a id="代表的なenum"></a>

### 代表的な列挙値

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

<a id="howどのように作るのか-2"></a>

## 方法：どのように作るのか

<a id="step-1必須fieldを定義する"></a>

### 手順 1：必須項目を定義する

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

<a id="step-2型とenumを定義する"></a>

### 手順 2：型と列挙値を定義する

- 文字列か。
- 数値か。
- 配列か。
- nullを許すか。
- 使用可能な値は何か。

<a id="step-3cross-field条件を定義する"></a>

## 方法：どのように作るのか

<a id="resolvedの場合"></a>

#### 解決済みの場合

```text
effective_value != null
value_origin != null
stop_code == null
```

<a id="non-resolvedの場合"></a>

### 手順 2：型と列挙値を定義する

```text
effective_value == null
value_origin == null
stop_code != null
```

<a id="formalの場合"></a>

#### 正式の場合

```text
value_origin != model_assumed
assumption_ids = []
```

<a id="step-4正例と負例をtestする"></a>

### 手順 4：正例と負例を試験する

正しい検証用データは通過し、誤った検証用データは失敗しなければならない。

<a id="schemaで確認しないもの"></a>

### データ構造で確認しないもの

次は意味上の不変条件で確認する。

- `oneway=-1`が逆方向だけか。
- 出典 道路地物が変更されていないか。
- 総車線数と方向別車線数が一致するか。
- 接続 規則の優先関係が正しいか。
- 母集団件数が一致するか。
- 同じ実行を2回行ってハッシュ値が一致するか。

### 完了条件

- 正しい検証用データが通る。
- 誤った検証用データが失敗する。
- 列挙値が仕様書・設定・登録簿と一致する。
- v17 出力に`value_state`がない。
- データ構造では表現できない条件が意味上の不変条件へ移されている。

---

<a id="9-成果物4registry群"></a>

# 9. 成果物4：登録簿群

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 承認済み決定記録 記録・規範仕様 |
| 同位 | Configuration、Schema、Semantic Invariant |
| 下位 | Parser、Normalizer、Classifier、Resolver、Validator |
| 入力 | 正式語彙、規則、停止コード、概念体系、仮定 |
| 出力 | 版付きの機械可読な正式登録簿 |
| 保証すること | 使用可能な値と規則の意味が一意である |
| 保証しないこと | コードが正しく規則を適用したこと |
| 主な意図 | INT-008、INT-010、INT-012、INT-019 |

<a id="whyなぜ必要なのか-3"></a>

## 理由：なぜ必要なのか

正式な値や規則をコードへ直接書くだけでは、次が分からない。

- その値は正式に承認されているか。
- どの版で追加されたか。
- どの検証用データで検査されるか。
- 廃止された値か。
- どの意味を持つか。
- 修正可能な停止理由か。

登録簿がないと、コード中の文字列が事実上の仕様になってしまう。

<a id="技術的背景controlled-vocabularyontologydecision-table"></a>

# 9. 成果物4：登録簿群

登録簿群には、技術的には複数種類の情報が含まれる。

## 階層上の位置付け

許可された有限の用語集合である。

例：

```text
resolved
unresolved
conflict
```

## 理由：なぜ必要なのか

概念間の包含・親子・対応関係を表す。

例：

```text
delivery ⊂ motor_vehicle
bus ⊂ psv
```

接続 specificityでは、単に文字列が長いかではなく、この集合関係を使う。

<a id="decision-table"></a>

## 技術的背景：統制語彙・概念体系・決定表

条件と結果の対応を明示する表である。

例：

```text
oneway=yes → forward
oneway=no  → forward + backward
oneway=-1  → backward
```

### 統制語彙

停止理由を分類する体系である。停止コードごとにtrigger、状況、確認要否、remediationを持つ。

これらをコードから分離することで、規則の確認、版管理、検証用データ被覆の確認が可能になる。

<a id="what何を作るのか-3"></a>

## 内容：何を作るのか

使用可能な正式語彙、規則、停止コード、概念体系、仮定を管理する機械可読な辞書を作る。

<a id="必須registry"></a>

### 必須登録簿

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

<a id="例stop-code-registry"></a>

### 不具合分類

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

<a id="例oneway-rule-registry"></a>

## 内容：何を作るのか

```yaml
rule_id: OSM_ONEWAY_ABSENT_DEFAULT_NO
predicate: ordinary road and oneway is absent
canonical_value: "no"
value_origin: rule_derived
```

<a id="howどのように作るのか-3"></a>

## 方法：どのように作るのか

<a id="step-1正式語彙を抽出する"></a>

### 手順 1：正式語彙を抽出する

仕様書、既存ヤムル形式、コード、検証用データから次を集める。

- 列挙値
- rule ID
- 停止コード
- assumption ID
- access value
- 車種

<a id="step-2重複と別名を整理する"></a>

### 手順 2：重複と別名を整理する

例：

```text
derived_osm_rule
rule_derived
```

v17ではどちらを正式名称にするか決める。

<a id="step-3各entryへ意味を付ける"></a>

### 手順 3：各入口へ意味を付ける

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

<a id="step-4configurationから参照する"></a>

### 手順 4：設定から参照する

設定には登録簿の保存先、版、ハッシュ値を記録する。

<a id="step-5未登録値を拒否する"></a>

### 手順 5：未登録値を拒否する

検証器は、登録簿にない状態、規則、停止コードを正式 阻害要因として扱う。

### 完了条件

- 仕様書に登場する正式識別子がすべて登録されている。
- コードだけに存在する未登録値がない。
- deprecated 値の扱いが分かる。
- 停止コードと検証用データが対応している。
- 設定が登録簿の版を一意に指定する。
- 未登録値を検証器が拒否する。

---

<a id="10-成果物5semantic-invariant一覧"></a>

# 10. 成果物5：意味上の不変条件一覧

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 規範仕様の意味上の要求 |
| 同位 | JSON Schema、Registry、Fixture |
| 下位 | Semantic Validator、Validation Report、Acceptance Gate |
| 入力 | 項目間、記録間、集合、ハッシュ値、母集団の条件 |
| 出力 | 判定可能な不変条件 識別子と失敗時処理 |
| 保証すること | 何を意味的に検査するかが明確である |
| 保証しないこと | 検証器 コードが実装・実行済みであること |
| 主な意図 | INT-002、INT-004、INT-006、INT-009、INT-016 |

<a id="whyなぜ必要なのか-4"></a>

## 理由：なぜ必要なのか

データ構造はデータの形を検査できるが、処理の意味までは十分に検査できない。

例えば次は、データ構造だけでは判断しにくい。

```text
oneway=-1ならbackwardだけを生成する。
総車線数は方向別車線数の合計と一致する。
recordの順序を変えてもaccess結果は変わらない。
input件数はgovernedとexcludedの合計である。
```

これらは、複数項目、複数記録、入力と出力の関係を確認する必要がある。

<a id="技術的背景invariantproperty-based-testmetamorphic-test"></a>

# 10. 成果物5：意味上の不変条件一覧

意味上の不変条件は、特定の入力例だけでなく、すべての適用対象で成立すべき性質を表す。

例：

```text
formal recordにはmodel_assumedが存在しない。
```

この性質は、個別の検証用データだけでなく、母集団全体 成果物全体でも検査できる。

## 階層上の位置付け

多数の入力に対して共通する性質を検査する。

例：

```text
すべてのrecord_idは再計算したhashと一致する。
```

## 理由：なぜ必要なのか

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

検証用データは具体例の検査、不変条件は一般性質の検査と考えると理解しやすい。

<a id="what何を作るのか-4"></a>

## 内容：何を作るのか

常に成立すべき意味上の条件を、1件ずつ判定可能な形で記録する。

推奨ファイルは次である。

```text
05_src/traffic_simulation/specifications/
  v17_semantic_invariants.md
```

必要に応じてヤムル形式版も作る。

<a id="invariantの基本構造"></a>

### 不変条件の基本構造

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

<a id="howどのように作るのか-4"></a>

## 方法：どのように作るのか

<a id="step-1仕様書から関係条件を抽出する"></a>

### 手順 1：仕様書から関係条件を抽出する

特に次を探す。

- 〜の場合、〜でなければならない。
- 合計が一致しなければならない。
- 前後で変化してはならない。
- すべての記録を数えなければならない。
- 同じ入力なら同じ結果でなければならない。

<a id="step-2truefalseで判定できる形にする"></a>

### 手順 2：真／偽で判定できる形にする

悪い例：

```text
方向を適切に処理する。
```

良い例：

```text
canonical_oneway=-1の場合、generated direction setは{backward}と一致する。
```

<a id="step-3失敗時の処理を決める"></a>

### 手順 3：失敗時の処理を決める

- resolution status
- 停止コード
- severity
- review required
- remediation

<a id="step-4fixtureとvalidatorを対応付ける"></a>

### 手順 4：検証用データと検証器を対応付ける

不変条件だけを書いて終わらせず、どの試験で確認するかを決める。

<a id="主なinvariant群"></a>

### 主な不変条件群

#### 状態

- 解決済みなら値と出発地がある。
- non-解決済みなら値と出発地はnullである。
- 正式には`model_assumed`がない。

#### 方向

- `oneway=-1`は逆方向だけである。
- 出典 道路地物は変更されない。
- 順方向と逆方向は同じ出典 intervalを参照する。

#### 車線

- 総車線数と方向別車線数の和が一致する。
- 車線 vector長と車線数が一致する。
- 正式でeven splitを使わない。

#### 状態

- 方向／車線 範囲外へ規則を適用しない。
- dominated 規則がmaximal setに残らない。
- 異なるmaximal effectがあれば停止する。
- 記録順を変えても結果が変わらない。

#### 母集団

- `input = governed + excluded`
- 具体化 欠落を除外として数えない。
- omitted 道路区間の元組を分母から消さない。

#### 再現性

- 必要ハッシュ値が存在する。
- 同じ環境・入力・コマンドで2回実行したハッシュ値が一致する。

### 完了条件

- 仕様書の意味的要求が一覧化されている。
- 各条件が真／偽で判定できる。
- 失敗時の処理が決まっている。
- 検証用データと検証器が対応している。
- データ構造との役割分担が明確である。
- Acceptance Gateが参照する不変条件が分かる。

---

# 11. 成果物6：差分レビュー報告書

## 階層上の位置付け

| 観点 | 位置付け |
|---|---|
| 上位 | 仕様同期表とv17規範仕様 |
| 同位 | Current Specification、Phase Completion Record |
| 下位 | 修正PR、担当割当、後続Phase計画 |
| 入力 | リポジトリのファイル・コード・試験・成果物現状 |
| 出力 | Finding、Severity、Target Phase、Owner、Evidence |
| 保証すること | 仕様と現状の差が可視化される |
| 保証しないこと | 差分が修正済みであること |
| 主な意図 | INT-011、INT-017、INT-019 |

<a id="whyなぜ必要なのか-5"></a>

## 理由：なぜ必要なのか

v17仕様書が完成しても、リポジトリ内の実装やファイルは自動的には更新されない。

現在のリポジトリには次のような状態が残っている可能性がある。

- v16の`value_state`だけを使っている。
- `resolution_status`と`value_origin`が未実装である。
- 方向付き区間 生成器はあるが正式運用へ接続されていない。
- 接続 utilityはあるが車線 範囲に対応していない。
- 停止コード 登録簿がない。
- Acceptance条件が文書にしかない。

したがって、仕様と現状の差を明示的に調べる必要がある。

# 11. 成果物6：差分レビュー報告書

差分レビューは、通常の文章校正ではなく、旧版から新版へのmigration 隔たり analysisである。

確認対象は、単なるファイルの有無だけではない。

- データ モデルの差
- 列挙値・項目名の差
- 正本の差
- 規則 優先順位の差
- 実装 wiringの差
- 検証用データ・正解判定器被覆の差
- 実行時間 根拠の差

例えば、方向付き区間 生成器の関数が存在しても、正式運用 処理工程から呼ばれていなければ「実装済み」とは扱えない。

```text
utility exists
≠ production integrated
≠ runtime verified
≠ accepted
```

差分レビューでは、この状態を分けて記録する必要がある。

<a id="what何を作るのか-5"></a>

## 内容：何を作るのか

仕様書とリポジトリの不一致を1件ずつ記録する報告書を作る。

推奨ファイルは次である。

```text
05_src/traffic_simulation/
  v17_authority_synchronization_review.md
```

<a id="findingの基本項目"></a>

### 確認事項の基本項目

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
| `missing_artifact` | 必要ファイルがない |
| `missing_field` | 必須項目がない |
| `legacy_only` | v16形式しかない |
| `enum_conflict` | 列挙値が仕様と違う |
| `semantic_conflict` | 処理の意味が仕様と違う |
| `unregistered_rule` | 未登録規則を使用している |
| `fixture_gap` | 検証用データがない |
| `oracle_gap` | 正解判定器がない |
| `validator_gap` | 意味検査がない |
| `evidence_gap` | ハッシュ値や成果物一覧がない |
| `documentation_only` | 文書だけで機械成果物がない |

<a id="howどのように作るのか-5"></a>

## 方法：どのように作るのか

<a id="step-1仕様同期表を基準にrepositoryを調べる"></a>

### 手順 1：仕様同期表を基準にリポジトリを調べる

各要件 識別子について、実際のファイル、関数、データ構造、検証用データを探す。

<a id="step-2一致しない項目をfindingにする"></a>

### 手順 2：一致しない項目を確認事項にする

例：

```text
Finding ID: FIND-STATE-001
Requirement: AR-STATE-003
Current: serializerがvalue_stateを出力している
Required: v17 writerはvalue_stateを出力しない
Severity: Major
Target Phase: Phase 3
```

<a id="step-3重要度を付ける"></a>

### 手順 3：重要度を付ける

### 手順 1：仕様同期表を基準にリポジトリを調べる

結果や原典を壊す可能性がある。

- v16成果物を書き換える。
- 出典 オープンストリートマップを直接編集する。
- 正式へ仮定値を入れる。
- `oneway=-1`を誤方向へ生成する。
- 証拠なしで受入済みとする。

### 手順 2：一致しない項目を確認事項にする

実装前に解消または計画が必要である。

- データ構造と登録簿が一致しない。
- 停止コードが未登録である。
- 状態 取り決めが移行されていない。
- Semantic 検証器がない。

### 手順 3：重要度を付ける

結果を直接壊さないが、第三者の理解や管理を難しくする。

- namingが統一されていない。
- 説明が不足する。
- ファイル 保存先が整理されていない。

<a id="step-4phaseを割り当てる"></a>

#### 重大

Phase 1で直すものと、Phase 2以降で実装するものを分ける。

<a id="step-5修正後に再レビューする"></a>

### 手順 5：修正後に再レビューする

初回レビューだけで終わらず、Phase 1の修正後にCriticalとPhase 1対象Majorがゼロか確認する。

### 完了条件

- 未解決Criticalがゼロである。
- Phase 1対象Majorがゼロである。
- 後続Phaseへ送る項目にownerと対象 段階がある。
- v16とv17の境界が明記されている。
- 修正した変更記録とハッシュ値が記録されている。

---

### 手順 4：工程を割り当てる

<a id="whyなぜphase-1を設けるのか"></a>

### 手順 5：修正後に再レビューする

仕様書完成直後に正式運用 コードを変更すると、次の問題が起こる。

- 実装者が自然言語を別々に解釈する。
- データ構造とコードがずれる。
- 試験の正解を正式運用 コードから作ってしまう。
- 途中で用語や規則 識別子が変更される。
- v16とv17の成果物が混ざる。

Phase 1は、実装前に「全員が同じ規則を参照する状態」を作る工程である。

<a id="whatphase-1で完成するもの"></a>

### 完了条件

Phase 1完了時には次が存在する。

- 全必須規則を追跡できる仕様同期表
- v17 Configuration
- 必須ジェイソン形式 データ構造
- 正式な登録簿群
- 意味上の不変条件一覧
- リポジトリとの差分レビュー
- v16とv17の明確な分離
- Phase 2で作る検証用データ・正解判定器の対象一覧

<a id="howphase-1を進める方法"></a>

# 12. 工程 1全体

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

## 内容：工程 1で完成するもの

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

## 方法：工程 1を進める方法

<a id="whyなぜすぐfull-runをしないのか"></a>

## 理由：なぜすぐ全体 実行をしないのか

設定、データ構造、登録簿が揃っても、実装が正しいとは限らない。

まず、小さな入力と独立した正解を使って、規則どおりに動くことを確認する必要がある。

<a id="what次に作るもの"></a>

## 内容：次に作るもの

Phase 2では次を作る。

- independent fixture
- production-independent oracle
- 検証用データ author・確認者記録
- stop-code coverage
- metamorphic test

その後、Phase 3以降で正式運用 コードを変更する。

<a id="how次へ進む順序"></a>

## 方法：次へ進む順序

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

## 理由：なぜすぐ全体実行をしないのか

<a id="whyなぜ区別が必要なのか"></a>

## 理由：なぜ区別が必要なのか

「仕様体系が完成したこと」と「正式運用実装が完成したこと」を混同すると、未検証の道路網を研究へ使う危険がある。

<a id="what未完成のままでよいもの"></a>

## 内容：未完成のままでよいもの

Phase 1終了時点では、次は未完成でよい。

- 正式運用 コードの全面v17対応
- 検証用データ・正解判定器の実行成功
- `oneway=-1`の正式運用統合
- directional lane resolver
- access resolver
- conditional parser
- full-population run
- 配送地点 記録の全解消
- 属性解決の受入
- 通行許可の具体化処理
- formal SUMO network
- 較正
- independent validation

<a id="how未完成項目を管理するのか"></a>

## 方法：未完成項目を管理するのか

差分レビューに次を記録する。

- Finding ID
- 対応要件 識別子
- Target Phase
- Owner
- 完了条件
- 根拠

「後で行う」だけではなく、どのPhaseで何をもって完了とするかを固定する。

---

<a id="15-よくある質問をwhywhathowで整理する"></a>

# 15. よくある質問を理由・内容・方法で整理する

## Q1. なぜ仕様書だけでは駄目なのか

<a id="why"></a>

### 理由

プログラムは自然言語の規則を直接検査・実行できないためである。

<a id="what"></a>

### 内容

仕様を設定、データ構造、登録簿、不変条件へ分解する。

<a id="how"></a>

### 方法

仕様同期表で、各規則の反映先を一つずつ指定する。

---

<a id="q2-json-schemaとsemantic-invariantは何が違うのか"></a>

## Q2. ジェイソン形式 データ構造と意味上の不変条件は何が違うのか

<a id="why-1"></a>

### 理由

形式の正しさと意味の正しさは別だからである。

<a id="what-1"></a>

### 内容

- データ構造：項目、型、列挙値、null等を検査する。
- 不変条件：方向、合計、集合、順序、母集団等を検査する。

<a id="how-1"></a>

### 方法

データ構造で表現できない条件を意味上の不変条件一覧へ明示的に移す。

---

<a id="q3-registryは単なる用語集なのか"></a>

## Q3. 登録簿は単なる用語集なのか

<a id="why-2"></a>

### 理由

正式な語彙や規則をコードから独立して管理する必要があるためである。

<a id="what-2"></a>

### 内容

状態、出発地、停止コード、一方通行 規則、車両 概念体系等を管理する。

<a id="how-2"></a>

### 方法

設定から版とハッシュ値を指定し、未登録値を検証器で拒否する。

---

## Q4. 仕様同期表と差分レビューは何が違うのか

<a id="why-3"></a>

### 理由

規則の配置と、現在の不足は別の情報だからである。

<a id="what-3"></a>

### 内容

- 仕様同期表：規則がどこへ反映されるべきか。
- 差分レビュー：現状が規則とどこで異なるか。

<a id="how-3"></a>

### 方法

仕様同期表を基準にリポジトリを調べ、不一致を差分レビューへ登録する。

---

### 理由

<a id="why-4"></a>

### 理由

Phase 1は実装の前提をそろえる段階だからである。

<a id="what-4"></a>

### 内容

完成するのは正本の構造と実装計画である。

<a id="how-4"></a>

### 方法

Phase 2で検証用データ・正解判定器を固定し、Phase 3以降でコードを変更する。

---

# 16. 用語集

<a id="configuration-1"></a>

## 設定

<a id="why-5"></a>

### 理由

実行ごとに使用する規則や版を固定するために必要である。

<a id="what-5"></a>

### 内容

方針、設定プロファイル、データ構造、登録簿、受入条件を指定するヤムル形式等である。

<a id="how-5"></a>

### 方法

v16と分離したv17 設定 識別子を作り、参照先の版とハッシュ値を記録する。

<a id="json-schema"></a>

## ジェイソン形式 データ構造

<a id="why-6"></a>

### 理由

項目不足や型・列挙値の誤りを機械的に発見するために必要である。

<a id="what-6"></a>

### 内容

ジェイソン形式データの構造規則である。

<a id="how-6"></a>

### 方法

正例と負例を作り、正例だけが通ることを確認する。

<a id="registry-1"></a>

## 登録簿

<a id="why-7"></a>

### 理由

正式な語彙や規則をコードから独立して管理するために必要である。

<a id="what-7"></a>

### 内容

状態、規則、停止コード等の機械可読辞書である。

<a id="how-7"></a>

### 方法

各入口に識別子、意味、適用条件、版、検証用データを付ける。

<a id="semantic-invariant-1"></a>

## 意味上の不変条件

<a id="why-8"></a>

### 理由

データ構造では検査できない意味上の関係を確認するために必要である。

<a id="what-8"></a>

### 内容

常に成立すべき条件である。

<a id="how-8"></a>

### 方法

一つの条件を真／偽で判定できる形へ分解する。

<a id="fixture"></a>

## 検証用データ

<a id="why-9"></a>

### 理由

小さく固定された入力で規則を確実に確認するために必要である。

<a id="what-9"></a>

### 内容

特定事例を再現する試験用入力である。

<a id="how-9"></a>

### 方法

normal、境界、負 事例を用意する。

<a id="oracle"></a>

## 正解判定器

<a id="why-10"></a>

### 理由

正式運用 コードとは独立した正解が必要だからである。

<a id="what-10"></a>

### 内容

検証用データに対して期待される出力である。

<a id="how-10"></a>

### 方法

正式運用 コードを使わずに作成し、第三者確認を記録する。

<a id="formal"></a>

## 正式

<a id="why-11"></a>

### 理由

正式な研究入力と開発用仮定を分けるために必要である。

<a id="what-11"></a>

### 内容

研究結果に使用可能な設定プロファイルである。

<a id="how-11"></a>

### 方法

`model_assumed`、未解決、競合等を禁止する。

<a id="structural"></a>

## 構造上の

<a id="why-12"></a>

### 理由

正式値が揃う前でも構造開発を進めるために必要である。

<a id="what-12"></a>

### 内容

開発・構造確認用設定プロファイルである。

<a id="how-12"></a>

### 方法

登録済みの仮定だけを許可し、研究結果には使用しない。

---


# 技術補章B：プログラム用語の日本語早見表

| プログラム上の表記 | 日本語での説明 |
|---|---|
| `class` | データと処理をまとめる型の設計 |
| `instance` | 分類から作られた具体的な対象 |
| `function` | 入力を受けて処理し、出力を返す処理単位 |
| `method` | 分類に属する関数 |
| `module` | 関連する分類や関数をまとめたPython ファイル |
| `package` | 複数モジュールをまとめた単位 |
| `interface` | モジュール間で守る入力・出力の約束 |
| `API` | 他のモジュールやツールから呼び出すための操作契約 |
| `type` | 値の種類 |
| `str` | 文字列 |
| `int` | 整数 |
| `float` | 小数を含む数値 |
| `bool` | 真または偽 |
| `list` | 順序を持つ可変の配列 |
| `tuple` | 順序を持つ固定的な配列 |
| `set` | 重複しない値の集合 |
| `frozenset` | 変更できない集合 |
| `dict` | キーと値の対応表 |
| `None` | Python上の値なし。ジェイソン形式の`null`に対応する |
| `raise` | 例外を発生させる |
| `try / except` | 例外を捕捉し処理する |
| `return` | 関数から値を返す |
| `yield` | 値を順番に生成する |
| `assert` | 試験等で条件成立を確認する |
| `immutable` | 作成後に変更しない性質 |
| `mutable` | 作成後に変更可能な性質 |
| `dependency` | 処理が利用する外部モジュールやツール |
| `side effect` | ファイル書込み等、戻り値以外に外部状態を変える作用 |
| `pure function` | 同じ入力に同じ出力を返し、外部状態を変えない関数 |
| `serialization` | 対象をジェイソン形式等の保存形式へ変換すること |
| `deserialization` | ジェイソン形式等を対象へ戻すこと |
| `validation` | 定義済みの条件に適合するか確認すること |
| `migration` | 旧形式のdataを新形式へ移行すること |
| `backward compatibility` | 旧形式を新しいprogramでも読める性質 |
| `deprecated` | 廃止予定で新規使用を避ける状態 |
| `deterministic` | 同じ入力から同じ結果になる性質 |
| `idempotent` | 同じ操作を繰り返しても結果が変わらない性質 |
| `unit test` | 一つの関数等を対象とする小規模試験 |
| `integration test` | 複数モジュールの接続を対象とする試験 |
| `regression test` | 過去に動いていた機能が壊れていないか確認する試験 |
| `metamorphic test` | 入力を規則的に変えた際の出力関係を確認する試験 |
| `coverage` | 試験が対象事例をどの程度確認しているか |
| `commit` | リポジトリへ記録した変更単位 |
| `branch` | 並行して変更を進める開発線 |
| `pull request` | 変更内容を確認して統合する単位 |
| `CI` | 変更記録やPRごとに試験を自動実行する仕組み |

## 日本語を使う場所と英語を残す場所

### 日本語を優先する場所

- 仕様本文
- comment
- docstring
- 確認報告
- 誤りの人間向け説明
- 検証用データの事例説明
- 受入 報告の説明文

### 英語の固定識別子を残す場所

- JSON key
- YAML key
- 分類名・関数名
- 停止コード
- rule ID
- enum value
- ファイル名
- スーモ・オープンストリートマップの正式な属性タグ名

この分け方により、説明は日本語で理解しやすくしながら、コードと外部仕様の対応関係を維持できる。

---

# 17. 技術的背景の参照先

この章は、解説書で扱った技術概念を確認するための参照先を示す。規範的な決定はv17属性解決仕様書を優先し、外部資料は背景理解に使用する。

<a id="openstreetmap"></a>

## オープンストリートマップ

- `oneway=-1`  
  https://wiki.openstreetmap.org/wiki/Tag%3Aoneway%3D-1

- 順方向／逆方向の方向\
  https://wiki.openstreetmap.org/wiki/Forward

- `lanes:forward`／`lanes:backward`  
  https://wiki.openstreetmap.org/wiki/Key%3Alanes%3Aforward

- 車線別属性タグ\
  https://wiki.openstreetmap.org/wiki/Key%3A%2A%3Alanes

- access tag  
  https://wiki.openstreetmap.org/wiki/Access_tags

- conditional restriction  
  https://wiki.openstreetmap.org/wiki/Conditional_restrictions

<a id="sumo"></a>

## スーモ

- オープンストリートマップからの取込み\
  https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html

- PlainXML  
  https://sumo.dlr.de/docs/Networks/PlainXML.html

- netconvert  
  https://sumo.dlr.de/docs/netconvert.html

## データ契約と再現性

- ジェイソン形式 データ構造の列挙値\
  https://json-schema.org/understanding-json-schema/reference/enum

- ジェイソン形式 データ構造の条件付き検証\
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

## データ契約と再現性

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

- 「値がない」ことと「いいえと明示されている」ことを分ける。

<a id="registry層"></a>

### 登録簿層

```text
rule_id: OSM_ONEWAY_ABSENT_DEFAULT_NO
effective_value: no
value_origin: rule_derived
```

意図：

- コード内の暗黙既定値ではなく、正式規則で導出する。

<a id="resolver層"></a>

### 属性解決器層

```text
resolution_status: resolved
value_origin: rule_derived
effective_value: no
```

意図：

- 最終値と根拠を同時に保存する。

<a id="directed-segment層"></a>

### 方向付き区間層

```text
forward
backward
```

意図：

- 双方向を二つの走行方向として明示する。

<a id="validator層"></a>

### 検証器層

確認すること：

- 出典 道路地物が変更されていない。
- 規則 識別子が登録簿にある。
- forward/backwardの2件が生成された。
-同じ入力から同じ識別子が得られる。

<a id="materializer層"></a>

### 具体化処理層

順方向と逆方向に対応するplain 拡張マークアップ形式 道路区間候補を出力する。

ここでは新しい方向判断を行わない。

---

### 方向付き区間層

### 原典層

```text
Way node order: 10 → 20 → 30
oneway=-1
```

### 意図

- 出典 道路地物は反転しない。
- 走行方向だけを逆方向として表す。
- `forward`／`backward` 属性タグの基準を壊さない。

<a id="directed-segment"></a>

### 方向付き区間

```text
source_node_ids: [10, 20, 30]
source_direction: backward
traversal order: [30, 20, 10]
```

### 各成果物の関与

| 成果物 | 関与 |
|---|---|
| 仕様同期表 | `oneway=-1`要求の全反映先を追跡 |
| 設定 | 方向付き区間 モデルを有効化 |
| データ構造 | 方向 列挙値と識別子形式を検査 |
| 登録簿 | `-1`の正規化規則を提供 |
| 不変条件 | 逆方向のみ生成、出典不変を検査 |
| 差分レビュー | 正式運用が道路地物反転する場合に確認事項化 |

---

<a id="例3formalで方向別車線数が不足する"></a>

## 例3：正式で方向別車線数が不足する

### 原典

```text
oneway=no
lanes=4
lanes:forward 欠損
lanes:backward 欠損
```

<a id="structural-profile"></a>

### 構造上の 設定プロファイル

登録条件を満たす場合、次を許可できる。

```text
forward=2
backward=2
value_origin=model_assumed
assumption_id=BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1
```

目的：

- 接続構造や具体化処理開発を進める。

使用禁止：

- 較正
- 移動時間評価
- 求解器比較
- 正式 道路網承認

<a id="formal-profile"></a>

### 正式 設定プロファイル

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

### 構造処理設定

### 適用候補

```text
Rule A: deliveryを許可
Rule B: deliveryを禁止
```

両者が同じ車線、方向、車両、時間、目的へ適用され、どちらも相手を支配しない場合：

```text
resolution_status=conflict
stop_code=ACCESS_SPECIFICITY_CONFLICT
```

### 意図

- ファイル順で一方を選ばない。
- first-matchやlast-matchを独立規則間へ誤用しない。
- 競合規則と出典・来歴を保存する。
- 確認者が新規則または根拠を登録し、全体を再実行する。

---

# 17B. 全階層を第三者へ説明するための要約

<a id="why-13"></a>

## 理由

オープンストリートマップの道路情報は欠損・方向差・車線差・条件付き規制を含むため、そのままスーモへ変換すると、暗黙の仮定や実装順によって研究結果が変わる可能性がある。

<a id="what-13"></a>

## 内容

そこで、原典を不変に保ちながら、各方向・車線・車種・想定条件について、値、解決状態、値の由来、適用規則、停止理由を記録する属性解決層を設ける。

その判断を一貫して実行・検証するため、Phase 1では次の6成果物を作る。

```text
仕様同期表
Configuration
JSON Schema
Registry
Semantic Invariant
差分レビュー
```

<a id="how-13"></a>

## 方法

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

<a id="why-14"></a>

## 理由

v17仕様書だけでは、実装・検査・追跡を一意に行えないためである。

<a id="what-14"></a>

## 内容

Phase 1では、次の6成果物を作る。

```text
仕様同期表
Configuration
JSON Schema
Registry群
Semantic Invariant一覧
差分レビュー報告書
```

<a id="how-14"></a>

## 方法

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
