# OSMからSUMO道路ネットワークを生成するための学習兼仕様書

> **文書状態**：Draft
> **版**：0.2-draft
> **改稿日**：2026-07-22
> **対象**：OpenStreetMap（OSM）からSUMO道路ネットワークを生成し、古典最適化とQAOAの比較実験に利用する研究工程
> **主対象読者**：OSM、SUMO、XMLおよび交通ネットワーク生成の実装経験が十分でない実装者
> **文書の役割**：基礎概念を学ぶための説明と、再現可能な実装・検証に必要な仕様上の原則を一つの流れで示す

## 目次

- [1．この文書の目的](#1この文書の目的)
- [2．研究全体における位置付け](#2研究全体における位置付け)
- [3．最初に理解する全体像](#3最初に理解する全体像)
- [第I部　道路データの基礎](#第i部道路データの基礎)
- [第II部　SUMOの基礎](#第ii部sumoの基礎)
- [第III部　今回の生成システム](#第iii部今回の生成システム)
  - [14．Resolver](#14resolver)
  - [15．Provisional Build](#15provisional-build)
  - [16．PermissionとvClass](#16permissionとvclass)
  - [17．Permission Materializer](#17permission-materializer)
  - [18．ConnectionとConnection Permission](#18connectionとconnection-permission)
  - [19．TLS Review](#19tls-review)
  - [20．Final Build](#20final-build)
  - [21．Post-build Audit](#21post-build-audit)
- [第IV部　実装を始めるときに理解する内容](#第iv部実装を始めるときに理解する内容)
- [第V部　検証を始めるときに理解する内容](#第v部検証を始めるときに理解する内容)
- [第VI部　最初の実践手順](#第vi部最初の実践手順)

## 1．この文書の目的

この文書は、OSMの道路データからSUMOで使用する道路ネットワークを生成する工程を、基礎概念、実装責任、検証方法の順に理解できるように整理した学習兼仕様書である。

本研究では、生成した道路ネットワーク上で配送車両を走行させ、同一の配送問題を古典最適化とQAOAへ与えて比較する。したがって、道路ネットワークの生成方法が実装者ごとに異なる場合、最適化手法以外の差が研究結果へ混入する。例えば、同じ道路を一方の実装者が1車線、別の実装者が2車線として生成すると、道路容量、車線変更、旅行時間および経路選択が変化し得る。この状態では、最適化手法の差ではなく、道路設定の差を比較することになる。

本書が目指す完成状態は、対象範囲内の入力について、別々の実装者が同じ入力、設定および実行環境から、同じ意味を持つ出力または同じ停止理由を得られる状態である。具体的には、次の条件を満たす必要がある。

* 適格な入力に対しては、同じ道路方向、車線構成、速度、通行権限、接続関係および信号構造を持つネットワークが生成される。
* 不適格な入力に対しては、実装者が推測で処理を継続せず、規定されたFailure Codeと停止理由を返す。
* 各属性値について、入力値、採用値、判断根拠、適用規則およびレビュー履歴を追跡できる。
* 最終生成物について、生成処理とは独立した検査により、仕様への適合を確認できる。
* 研究結果について、使用した入力、設定、コード、実行環境および出力を再現できる。

すべての将来ケースを自動処理することは完成条件ではない。現在の仕様で一意に判断できないケースを明示的に停止させ、未対応範囲として記録することも、再現可能性を確保するための正しい動作である。

### 1.1 本書が扱う範囲

本書は、固定したOSMスナップショットを入力し、道路属性を解釈し、SUMOの道路構造へ変換し、最終ネットワークが仕様どおりに生成されたことを確認するまでを扱う。具体的には、OSM属性の解釈、`netconvert`による構造生成、`lane`・`connection`の通行権限、信号リンクとの構造的対応、成果物の来歴管理およびPost-build Auditを対象とする。

本書は、交通需要の生成、信号時間の実データ較正、運転挙動パラメータの較正、配送需要モデル、古典最適化およびQAOAのアルゴリズム設計を直接の仕様対象としない。これらは、承認済み道路ネットワークを入力として扱う後続工程である。

### 1.2 説明と規範の区別

本書には、初学者が概念を理解するための説明と、実装を拘束する規範が共存する。実装上の必須条件は、要件ID、`MUST`、`MUST NOT`、Failure Code、Schema、Readiness Gateおよび受入基準によって明示する。背景説明や例示だけを根拠として、実装者が新しい補完規則や例外処理を追加してはならない。

> **規範性の原則**
> 本書の説明文は設計意図を理解するためのものである。実装を直接拘束する規則は、規範語、要件ID、機械可読な設定・Schema、および承認済みの対応表によって特定する。

### 1.3 本書を読む際の前提

本書は、OSMファイル、XML、SUMOの`edge`や`lane`を初めて扱う読者を想定している。そのため、前半では基礎概念を説明し、後半では仕様、実装、試験および受入判定へ進む。既に基礎知識を持つ読者は、第III部から読み始めてもよい。

## 2．研究全体における位置付け

道路ネットワーク生成は、本研究の最終目的ではない。古典最適化とQAOAを比較するための実験環境を準備する工程である。

研究全体は、概ね次の順序で進む。

```text
現実の道路情報
        ↓
OpenStreetMapの道路データ
        ↓
道路属性の解釈と確認
        ↓
SUMO道路ネットワークの生成
        ↓
道路構造と通行条件の検証
        ↓
交通需要と信号制御の追加
        ↓
交通状態の較正と独立検証
        ↓
配送問題インスタンスの生成
        ↓
古典最適化とQAOAの比較
```

本書が主に扱う範囲は、OpenStreetMapの道路データを取得してから、研究で利用可能なSUMO道路ネットワークであることを確認するまでである。

道路ネットワークに誤りがあると、次の結果が変化する。

* 道路の車線数が変わると、道路容量や渋滞状態が変化する。
* 最高速度が変わると、経路ごとの旅行時間が変化する。
* 一方通行が逆になると、経路の到達可能性が変化する。
* 通行権限が誤っていると、配送車が現実には通れない道路を利用する。
* Connectionが誤っていると、右左折や交差点通過の可否が変化する。
* 信号との対応が誤っていると、交差点の交通状態が不自然になる。

したがって、道路ネットワーク生成仕様は、古典最適化とQAOAへ同じ実験条件を与えるための基盤として位置付ける。

### 2.1 OSMとSUMOの関係

OSMとSUMOは、同じ道路を扱うが役割が異なる。

* OSMは、現実世界の道路、交差点、道路種別、通行規制などを共同編集型の地理データとして記録する**入力データ源**である。
* SUMOは、車両、経路、交通需要、信号制御などを与えて交通流を計算する**交通シミュレータ**である。
* `netconvert`は、OSMの記述をSUMOが走行計算に使用できる道路ネットワークへ変換するツールである。

したがって、OSMファイルをSUMOがそのまま走行に使用するわけではない。両者の関係は、次のように表せる。

```text
現実世界の道路
        ↓ 観測・編集
OSMデータ
  位置、形状、道路種別、明示された属性・規制
        ↓ Resolver・設定・レビュー
研究上採用する道路の意味
  方向、車線、速度、通行権限、来歴
        ↓ netconvert・Permission Materializer・TLS Review
SUMO道路ネットワーク
  junction、edge、lane、connection、traffic light logic
        ↓ 需要・車両・信号時間を追加
SUMOシミュレーション
  車両軌跡、旅行時間、渋滞、エネルギー等
```

#### 2.1.1 OSMは現実そのものではない

OSMは現実の道路について得られた記述であり、道路管理者の完全な台帳や、時々刻々変化する交通状態そのものではない。道路ごとに情報量が異なり、次の状態を含み得る。

* `lanes`、`maxspeed`、`oneway`、`access`などの属性が欠けている。
* タグ同士が矛盾している。
* 条件付き規制が、現在のResolverでは解釈できない形式で記録されている。
* 実際の工事、規制変更、信号運用などが取得日以後に変化している。
* 道路形状は存在しても、交通量、待ち行列、実旅行時間は記録されていない。

このため、OSMに道路が存在することは、その道路を無条件でSUMOへ採用できることを意味しない。また、OSMに属性がないことは、現実の道路に車線数や速度規制がないことを意味しない。

本研究では、取得日とSHA-256を固定したOSMを入力スナップショットとして扱う。欠損や矛盾は、仕様で認めた導出・補完規則を適用するか、解釈不能として停止する。実装者の都度判断で値を追加しない。

#### 2.1.2 SUMO道路網はOSMの単純な複製ではない

SUMOは車両を走行させるため、OSMより明示的なネットワーク構造を必要とする。主要な概念の対応は次のとおりである。

| OSM側の概念 | SUMO側の概念 | 関係 |
|---|---|---|
| `node` | `junction`、edge形状点等 | すべてのOSM nodeがSUMO junctionになるわけではない |
| `way` | 1本以上の`edge` | 一方通行方向、交差点分割、内部処理により複数edgeになり得る |
| `lanes`等のタグ | `lane` | 方向別車線数と車線順序を解釈して生成する |
| `access`等のタグ | lane・connectionの`allow`/`disallow` | 車種別・方向別・車線別の規則へ変換する |
| way同士の接続 | `connection` | 交差点で可能なlane間移動として明示する |
| `restriction` relation | connectionの禁止・制限 | relationの解釈と変換結果を検証する必要がある |
| `highway=traffic_signals`等 | signalized junction・TLS link | 信号位置だけで実際の現示やサイクルが分かるわけではない |

この対応は一対一ではない。例えば、一つのOSM wayが交差点で複数のSUMO edgeへ分割されることがある。反対に、形状整理やjunction処理によって、複数のOSM要素が一つのSUMO構造に影響することもある。このため、OSM IDとSUMO要素の来歴対応を保存し、座標の近さやSUMO edge IDの見た目だけで対応を推測してはならない。

#### 2.1.3 変換時に追加される判断

SUMO道路網の生成時には、OSMに明示された事実だけでなく、研究設定または変換処理による判断が加わる。

* 研究対象として保持する道路種別と除外する道路種別
* 欠損した車線数や速度を補完できる条件
* 日本の左側通行とlane indexの対応
* 車種ごとの通行可能性
* junctionの分割または統合
* lane間connectionとturn restriction
* 信号交差点とTLS linkの構造
* 内部edge、形状点、行き止まり等のSUMO固有表現

これらはOSMの事実と同一ではないため、出典を次のように区別する。

| 区分 | 例 |
|---|---|
| OSM明示値 | `lanes=2`、`oneway=yes`、`maxspeed=40` |
| OSMからの機械的導出 | 明示された方向別タグから求めた方向ごとの車線数 |
| 研究上の補完・仮定 | 許可された道路クラス別補完値、対象vClass集合 |
| SUMO変換結果 | 分割後edge、lane index、connection、internal edge |
| 人による確認結果 | junction統合、TLS link対応、重要道路の採否 |

最終的な`net.xml`だけを見ても、この区分は完全には復元できない。そのため、Resolver監査、permission期待値、provenance、設定、manifestおよびレビュー記録を`net.xml`と一緒に保存する。

#### 2.1.4 SUMOへ変換できることと妥当であることは別である

`netconvert`が終了コード0で`net.xml`を生成しても、その道路網が東京の交通を妥当に表しているとは限らない。

検査は少なくとも二段階に分ける。

1. **Verification:** 設定した方向、車線数、速度、permissions、connection、信号構造が、仕様どおりSUMOへ変換されたかを確認する。
2. **Validation:** 生成したネットワークへ需要や信号時間を与えた結果が、独立した交通量、速度、旅行時間等の観測と十分に整合するかを確認する。

OSMとSUMOの対応確認は主にVerificationである。東京の交通状態としての妥当性は、道路交通センサス、JARTIC、警視庁交通量等を別の観測根拠として用いるValidationで評価する。OSMだけを根拠に交通容量、需要量、渋滞、信号時間の正しさを主張しない。

#### 2.1.5 本研究の最適化との関係

OSMは、古典最適化やQAOAへ直接与える配送問題ではない。SUMO道路ネットワーク上で出発地・顧客・充電地点間の道路経路と交通条件を評価し、その結果から固定された旅行時間、距離、エネルギー等のコストを作る。その共通コストを用いて、古典手法とQAOAを比較する。

```text
OSM由来の道路情報
        ↓ 統制された変換と検証
承認済みSUMO道路ネットワーク
        ↓ 共通の需要・信号・車両条件
道路経路、旅行時間、距離、エネルギー
        ↓ 固定インスタンス化
古典最適化とQAOAへ同じ配送問題を入力
```

したがって、OSMからSUMOへの変換規則が変わると、配送コストと最適経路も変わり得る。`formal_accepted`ネットワークを変更した場合は、それ以前に作成したコスト行列、較正結果、配送インスタンスおよび古典・QAOA比較結果を、そのまま有効とは扱わない。

### 2.2 シミュレータとしてのSUMOの分析上の位置付け

本研究におけるSUMOは、現実の東京をそのまま保存したデータでも、配送順序を決める最適化ソルバーでもない。道路、交通需要、信号、車両、運転挙動等の仮定を入力し、その条件下で交通状態がどのように推移するかを計算する**交通マイクロシミュレータ**である。

分析上は、SUMOを次の三つの間に置く。

```text
現実から取得した入力・観測
  OSM、N03、JARTIC、道路交通センサス等
        ↓ 入力整備・較正・検証
SUMO交通モデル
  道路網、需要、信号、車両、運転挙動
        ↓ 同一条件でシナリオ実行
分析用出力
  旅行時間、距離、軌跡、待ち時間、エネルギー等
        ↓
配送評価・シナリオ比較
```

したがって、SUMOは**観測データと研究上の比較結果をつなぐモデル層**である。入力データに存在しない情報を無条件に事実として生成するものではない。

#### 2.2.1 SUMOへ入力するもの

SUMO実行時には、複数の入力層を明示的に組み合わせる。

| 入力層 | 内容 | 本研究での主な根拠 |
|---|---|---|
| 道路構造 | junction、edge、lane、connection、通行方向 | OSMを中心に統制変換したformalネットワーク |
| 道路属性 | 速度、permissions、車線数等 | OSM明示値、統制された導出・補完、レビュー |
| 交通需要 | 車両の出発地、目的地、出発時刻、台数 | 交通観測・人口・貨物流動等から別途構築 |
| 信号制御 | signalized junction、phase、duration、offset | OSM信号位置、構造レビュー、較正用資料 |
| 車両 | 車種、寸法、加減速、追従、エネルギー特性 | SUMO設定、車両仕様、較正・感度分析 |
| 運転挙動 | 追従、車線変更、反応等 | 固定基準値と明示した感度シナリオ |
| 環境条件 | 天候、事故、規制、充電条件等 | 観測または事前登録したシナリオ仮定 |
| 実行条件 | seed、時間範囲、warm-up、出力間隔 | 実験計画で固定 |

OSMはこのうち道路構造・道路属性の主要原典であるが、SUMOモデル全体の唯一の入力ではない。例えば、JARTICの観測速度は交通状態の較正・検証に用いるものであり、OSMの法的な`maxspeed`と同じ変数として無条件に置換しない。

#### 2.2.2 SUMO内部で計算されるもの

SUMOは、入力された条件と選択したモデルに従って、時刻ごとの車両状態を更新する。

* 車両がどのedge、lane、connectionを通過するか。
* 先行車や信号に応じて、速度と加減速がどう変化するか。
* 車線変更、合流、待ち行列がどこで生じるか。
* 各車両の出発、到着、停止、遅延がいつ発生するか。
* 採用したエネルギーモデルの下で、消費エネルギーがどう変化するか。

これらは入力とモデルから計算された**シミュレーション値**であり、現実に観測された値とは区別する。出力表には、観測値、較正値、シミュレーション値、シナリオ仮定値の区分を保持する。

#### 2.2.3 本研究でSUMOが担う四つの役割

1. **道路経路への対応:** 最適化手法が扱う顧客間移動をformalネットワーク上の道路経路へ変換し、一方通行、右左折、道路接続、通行可能車種を反映する。
2. **共通コストの生成:** 固定した交通条件で距離、旅行時間、エネルギー等を計算し、古典手法とQAOAへ同一の配送問題インスタンスとして与える。
3. **配送計画の共通走行評価:** 両手法が生成した配送計画を同じSUMO条件へ戻し、旅行時間、遅延、エネルギー、配送完了量等を比較する。
4. **シナリオ比較:** 交通需要、信号、事故、天候、車両特性、運転挙動等を事前登録した範囲で変更し、他の条件を固定して影響を比較する。

```text
共通の配送問題
    ├── 古典最適化 ── 配送計画A ─┐
    └── QAOA       ── 配送計画B ─┤
                                  ↓
                         同一SUMO環境で走行
                                  ↓
                     運用・社会的指標を比較
```

ソルバーごとに別の道路網、交通条件またはseedを使用しない。道路条件を変える実験では、その変更を独立したシナリオ因子として両手法へ共通適用する。

#### 2.2.4 SUMOが担わない役割

SUMOは、次の役割を担わない。

* OSM属性が現実に正しいかを自動的に保証すること。
* 東京の交通需要や信号時間を、根拠なしに確定すること。
* 配送の訪問順序を古典最適化またはQAOAとして解くこと。
* QAOAの回路深さ、測定回数、最適化反復等の計算資源を評価すること。
* 較正・独立Validationなしに、現実の交通を正確に予測すること。
* シナリオ外の地域、時間帯、需要水準へ結果を自動的に一般化すること。

古典手法とQAOAの計算時間、解品質、制約充足、QUBO規模、回路指標等はソルバー側の記録から評価する。一方、旅行時間、距離、エネルギー、配送完了量等はSUMO側の共通走行評価から取得する。二つの評価系を混同しない。

#### 2.2.5 静的配送問題と動的SUMO交通の違い

本研究の配送最適化がfrozen-instance designであっても、SUMO内の車両状態が時間変化しないという意味ではない。

* **静的・frozen配送問題:** 最適化開始後に注文、顧客、車両、コスト行列等を更新せず、同じ問題インスタンスを各ソルバーへ与える。
* **SUMO内の動的交通:** 固定されたシナリオの中で、車両位置、速度、待ち行列、信号状態、旅行時間等がシミュレーション時刻とともに変化する。

既知の時間帯別条件を事前に固定してSUMOで時間発展させることは、frozen-instance designと矛盾しない。ただし、実行中に新しく観測された事故、注文、故障等を受けて配送計画をオンライン再最適化することは、現在の評価範囲に含めない。

#### 2.2.6 分析結果を正式利用できる条件

SUMO出力を正式な研究結果へ使用する前に、少なくとも次の順序を満たす。

```text
道路網Verification
        ↓
formalネットワーク受入
        ↓
交通需要・信号・車両条件の固定
        ↓
観測データによる較正
        ↓
較正に未使用のデータによるValidation
        ↓
正式シナリオとseedの事前固定
        ↓
配送計画の共通SUMO走行評価
```

道路網が生成できただけのstructural出力は、旅行時間、容量、エネルギー、配送性能の評価へ使用しない。較正に使用した観測値と同じデータだけでValidation済みとはしない。

#### 2.2.7 SUMO結果から主張できる範囲

SUMOから直接得られるのは、「固定・開示したモデルとシナリオの下で計算された結果」である。例えば、次の形式で述べる。

> 承認済み大田区ネットワーク、固定需要、固定信号条件、指定車両モデルおよび指定seedの下で、配送計画Aは配送計画Bよりシミュレーション旅行時間が短かった。

次のように、モデルの適用範囲を超えて一般化してはならない。

> QAOAは東京の実配送で常に旅行時間を短縮する。

現実への主張には、入力データの代表性、較正、独立Validation、複数seed、複数需要・交通シナリオ、および不確実性評価が必要である。SUMOの役割は比較条件を統制することであり、モデル化仮定を消去することではない。

---

## 3．最初に理解する全体像

道路ネットワークは、一回の変換処理だけで完成するわけではない。

本研究では、次のように複数の工程へ分けて生成する。

```text
固定されたOSMファイル
        ↓
Resolver
        ↓
意味を整理した道路属性と期待permissions
        ↓
Provisional Build
        ↓
暫定的なSUMO edge・lane・connection
        ↓
Permission Materializer
        ↓
通行権限を反映したSUMO要素
        ↓
TLS Review
        ↓
信号との構造的な対応を確認
        ↓
Final Build
        ↓
formal.net.xml
        ↓
Post-build Audit
        ↓
研究で正式利用できるかを判定
```

各工程を分ける理由は、異なる種類の判断を一つのプログラムへ混在させないためである。

* Resolverは、OSMに書かれた情報が何を意味するかを判断する。
* Provisional Buildは、OSMを暫定的なSUMO構造へ変換する。
* Materializerは、OSM上の期待値を実際のSUMO要素へ設定する。
* TLS Reviewは、道路変更後も信号との対応が壊れていないか確認する。
* Final Buildは、承認済みの入力から最終ネットワークを生成する。
* Post-build Auditは、最終結果が仕様どおりかを独立して確認する。

### 3.1 各機能は何をするものか

各機能は、一つの巨大な変換プログラムを構成する内部処理ではなく、入力、出力、停止条件を持つ独立した責任単位として扱う。前工程の出力を後工程が受け取り、後工程が前工程の判断を暗黙に変更しないようにする。

| 機能 | 主な役割 | 主な入力 | 主な出力 |
|---|---|---|---|
| Resolver | OSM属性の意味を解決し、研究上の採用値と期待permissionsを決める | 固定OSM XML、typemap、研究設定、criticality | 正規化OSM、属性監査、補完記録、permission期待値 |
| Provisional Build | OSMから暫定的なSUMO構造を生成する | Resolver確認済みOSM、暫定変換設定 | 暫定node、edge、lane、connection、TLS構造、provenance |
| Permission Materializer | lane・connectionごとの期待permissionsをSUMO plain XMLへ反映する | permission期待値、暫定plain XML、provenance | permissions反映済みedge・connection XML |
| TLS Review | 確定したconnectionと信号リンク・現示文字列の構造対応を確認する | permissions反映後のconnection、暫定TLS情報 | レビュー済みconnection、TLS XML、review manifest |
| Final Build | 承認済みplain XMLから正式候補`net.xml`を生成する | node、edge、connection、TLS XML、固定設定 | `formal_candidate`の`net.xml`、実行ログ、build manifest |
| Post-build Audit | 最終出力を独立に検査し、正式利用の可否を判定する | `formal_candidate`の`net.xml`、期待値、provenance、ログ | 監査結果、品質指標、合否判定、停止理由 |

詳細は第14章から第21章で説明する。最初に理解すべき要点は、Resolverが期待値を決め、Materializerがその期待値をSUMO要素へ反映し、Post-build Auditが結果を独立に照合するという分離である。

### 3.2 責任の読み分け方

機能を分ける理由は、判断の所在と失敗原因を明確にするためである。

* OSM属性の解釈誤りはResolverで修正する。
* OSM wayとSUMO laneの対応誤りはprovenanceまたはMaterializerで修正する。
* connectionと信号linkの対応誤りはTLS Reviewで修正する。
* 変換コマンドや環境の不一致はFinal Buildで修正する。
* 最終出力と期待値の不一致はPost-build Auditが検出する。

この分離により、後工程が都合のよい値へ無記録で修正することを防ぎ、同じ入力と設定から同じ判断と停止理由を再現できる。

---

### 3.3 ネットワーク成果物の状態

道路ネットワークは、生成された時点で直ちに研究へ使用できるわけではない。本書では、成果物の状態を次の三段階に区別する。

| 状態 | 定義 | 使用可能な目的 |
|---|---|---|
| `provisional` | OSMから暫定的に生成され、構造確認と対応付けに使用するネットワークである。 | `edge`・`lane`・`connection`の確認、provenanceの作成、MaterializerおよびTLS Reviewの入力に限定する。 |
| `formal_candidate` | 承認済み入力からFinal Buildが生成した正式利用候補である。 | Post-build Auditおよび受入判定に限定し、研究結果の算出には使用しない。 |
| `formal_accepted` | Post-build Auditに合格し、受入記録が作成された正式ネットワークである。 | 交通需要の追加、較正、配送コスト生成および古典最適化とQAOAの比較に使用できる。 |

`provisional`または`formal_candidate`の成果物を、ファイル名だけを変更して`formal_accepted`として扱ってはならない。状態遷移は、必要な入力hash、レビュー、監査結果および承認記録によって証明する。

### 3.4 判断根拠の優先順位

道路属性の値を決定する際は、根拠の種類を混同してはならない。本書では、少なくとも次の順序で判断根拠を区別する。

1. OSMに有効な値が明示され、他のタグと矛盾しない場合は、その値を`explicit_valid`として採用する。
2. 複数の明示情報から値を一意に導出できる場合は、導出規則を記録して`derived_unambiguous`として採用する。
3. 承認済みの外部資料または人手レビューで確定した場合は、資料、対象範囲、確認者および確認日を記録して`reviewed_external`として採用する。
4. 研究上承認された補完規則を適用する場合は、規則ID、適用条件および影響範囲を記録する。
5. 以上の根拠で一意に決定できない場合は、`unresolved`として停止する。

`typemap`の既定値は、現実の道路属性を証明する根拠ではない。構造生成のために使用する場合は、その値が構造確認専用であることを`structural_placeholder`として明示し、正式ネットワークへの混入をReadiness Gateで禁止する。

### 3.5 主要成果物と責任

各工程の成果物は、用途と責任を明確にして保存する。

| 成果物 | 主な内容 | 作成責任 | 正式利用の条件 |
|---|---|---|---|
| `sumo_network.yml` | 対象範囲、固定値、許可状態、管理対象vClass、Readiness Gateを記録する。 | 仕様管理者 | 承認済みID、版およびSHA-256が記録されている。 |
| 正規化OSM | Resolverが採用した属性を、元のOSMとの対応を保って表す。 | Resolver | 属性監査と一対一に追跡できる。 |
| 属性監査 | 元値、採用値、状態、規則ID、根拠および停止理由を記録する。 | Resolver | Schemaへ適合し、未解決項目が分類されている。 |
| permission期待値 | OSM Way、方向、車線位置ごとの期待vClass集合を記録する。 | Resolver | JSON Schemaへ適合し、設定IDとhashが一致する。 |
| provenance | OSM要素からSUMOの`edge`・`lane`・`connection`への対応を記録する。 | Provisional Build | 対応方法と曖昧性の有無が記録されている。 |
| Materializer Audit | 適用先、適用前後の値、規則および結果を記録する。 | Permission Materializer | すべての変更が追跡可能である。 |
| TLS review manifest | `connection`と`linkIndex`の対応、入力hash、判断および未解決事項を記録する。 | TLS Review | 対象入力のhashと一致し、状態が`reviewed`である。 |
| build manifest | 入力、設定、コード、環境、コマンド、ログおよび出力を結び付ける。 | Final Build | 必須項目が揃い、出力hashと一致する。 |
| post-build audit | 仕様適合性、品質指標、Failure Codeおよび受入可否を記録する。 | Post-build Audit | すべてのBLOCKING項目が解消されている。 |


### 3.6 用語と表記の規則

本書では、OSMおよびSUMOのデータ要素をコード表記で示し、処理工程と成果物を固有名として示す。

| 種類 | 表記例 | 意味 |
|---|---|---|
| OSM要素 | `node`、`way`、`tag`、`relation` | OSMデータモデル上の要素である。 |
| SUMO要素 | `junction`、`edge`、`lane`、`connection` | SUMO道路ネットワーク上の要素である。 |
| SUMO属性 | `allow`、`disallow`、`linkIndex` | XML内で機械的に解釈される属性である。 |
| 車両クラス | `vClass`、`passenger`、`delivery` | SUMOが車両の通行可能性を表す分類である。 |
| 処理工程 | Resolver、Provisional Build、Permission Materializer、TLS Review、Final Build、Post-build Audit | 本研究で責任を分離した処理単位である。 |
| 来歴情報 | provenance、manifest、Audit | 対応関係、処理全体の来歴、個別判断の記録を表す。 |

本文中の「permission」は、`lane`または`connection`を通行できる`vClass`集合を表す総称である。OSMの`access`タグ体系とSUMOの`vClass`体系は同一ではないため、両者を直接同一視しない。

## 第I部　道路データの基礎


### この章群で理解すること

第4章から第9章では、OSMデータを読むために必要な最小限のデータ構造を学ぶ。ここで重要なのは、画面に表示された地図画像と、プログラムが処理する地理データを区別することである。地図画像は人が場所を理解するための表現であるのに対し、OSMファイルは、位置、接続順序、道路種別、車線数および通行規制を、識別子と属性によって記述した構造化データである。

この章群では、次の関係を順番に理解する。

```text
ファイル
  └─ データを保存する単位である。
       ↓
XML
  └─ データの構造を要素と属性で記述する形式である。
       ↓
OSMファイル
  └─ 特定地域のOSMデータを保存した入力スナップショットである。
       ↓
node・way・tag・relation
  └─ 点、線、属性および複数要素間の関係を表す。
```

各概念の役割は次のとおりである。

| 概念 | 初学者向けの説明 | 本研究で理解する必要がある理由 |
|---|---|---|
| ファイル | データを保存し、別の処理へ受け渡すための単位である。 | 同じファイル名でも内容が異なる可能性があるため、SHA-256によって使用した実体を固定する必要がある。 |
| XML | 要素の入れ子構造と属性によってデータを表す記述形式である。 | OSMとSUMOはいずれもXMLを使用するが、要素の意味と構造が異なるため、形式が同じであることとデータモデルが同じであることを混同してはならない。 |
| OSM | 現実の道路に関する共同編集型の地理データベースである。 | 道路形状や属性の主要な入力源になる一方、欠損、矛盾、更新時点の差があるため、そのまま正解とは扱えない。 |
| `node` | 緯度・経度を持つ一点であり、道路形状点や信号位置等を表す。 | `way`の形状と方向は`node`の並びから構成されるため、方向判定の根拠になる。 |
| `way` | 複数の`node`を順番に参照して作る線状要素である。 | 一つの道路区間に見えても、SUMOでは方向別または交差点別に複数の`edge`へ変換され得る。 |
| `tag` | `way`や`node`へ意味を付与するキーと値の組である。 | `highway`、`lanes`、`maxspeed`、`oneway`、`access`等が道路属性の解釈根拠になる。 |
| `relation` | 複数のOSM要素の役割と関係をまとめる要素である。 | 右左折禁止や行政界のように、単一の`way`や`tag`だけでは表せない規則を扱うために必要である。 |

例えば、三つの`node`を順番に参照する一つの`way`へ、`highway=residential`、`lanes=2`、`oneway=yes`という`tag`が付いている場合、データ上は「指定された方向へ進む生活道路であり、車線数が2である」と解釈する候補になる。ただし、この記述だけで、交差点付近の付加車線、時間帯規制、実際の交通量または道路工事の状態まで分かるわけではない。OSMから読み取れる事実と、研究側が追加する仮定を分離することが、この章群の中心的な学習目標である。


### 4．ファイルとは何か

ファイルとは、コンピュータ上に保存されたデータのまとまりである。

同じ道路情報でも、目的によって異なる形式のファイルが使用される。

例えば、今回の処理では次の形式を扱う。

| 形式         | 主な役割                             |
| ---------- | -------------------------------- |
| `.osm.pbf` | 大規模なOpenStreetMapデータを小さい容量で保存する。 |
| `.osm.xml` | OpenStreetMapの内容を人が確認できる形式で表す。   |
| `.yml`     | 研究で使用する設定値や方針を保存する。              |
| `.json`    | プログラム間で構造化された情報を受け渡す。            |
| `.csv`     | 道路ごとの判断や監査結果を表形式で保存する。           |
| `.net.xml` | SUMOが車両走行に使用する道路ネットワークを保存する。     |

ファイル名が同じでも、中身が変更されている場合がある。そのため、後述するSHA-256を使って、実際に使用したファイル内容を識別する。

---

### 5．XMLとは何か

XMLは、山括弧を使って構造化されたデータを記述する形式である。

例えば、次はOSMのTagを表すXMLである。

```xml
<tag k="lanes" v="2"/>
```

この一行には次の要素がある。

* `<tag ... />`全体をXML要素と呼ぶ。
* `k`と`v`をXML属性と呼ぶ。
* `k="lanes"`は、項目名が車線数であることを表す。
* `v="2"`は、項目の値が2であることを表す。

XMLは文章ではなく、プログラムが読み取れる構造化データである。

OSMとSUMOはいずれもXMLを使用するが、同じ要素名や構造を使用するわけではない。OSM用XMLとSUMO用XMLは別のデータ形式である。

---

### 6．OpenStreetMapとは何か

OpenStreetMapは、道路、建物、駅、信号、行政界などを記録する地理データベースである。一般にOSMと呼ばれる。

OpenStreetMapの画面に表示される地図画像を直接シミュレーションへ取り込むわけではない。

本研究で使用するのは、道路の位置、形状、種類、車線数、速度、通行条件などが保存された数値・文字データである。

OSMは多くの情報を持つ一方、すべての道路についてすべての属性が記録されているわけではない。属性の欠損、矛盾、複雑な条件付き規制があるため、SUMOへ変換する前に処理規則を定める必要がある。

---

### 7．OSMファイルとは何か

OSMファイルは、OpenStreetMapのデータベースから、特定地域の情報を取り出したファイルである。

今回の研究では、関東地方のOSMデータから東京都大田区周辺を抽出することを想定する。

```text
関東地方のOSM PBF
        ↓
大田区行政界で地域を抽出
        ↓
大田区周辺のOSM XML
```

`.osm.pbf`は保存と地域抽出に適しているが、人が直接読むことには向いていない。

`.osm.xml`はテキスト形式であり、道路を構成するNode、Way、Tagを確認できる。

研究では、元となるPBFと抽出後のXMLの両方を保存し、それぞれのSHA-256を記録する。

---

### 8．`node`、`way`、`tag`とは何か

#### 8.1 `node`

Nodeは、地図上の一点を表す。

```xml
<node id="1001" lat="35.5610" lon="139.7160"/>
```

このNodeは、IDが1001であり、指定された緯度と経度に存在する点を表す。

Nodeは道路形状を作る点として使用されるほか、信号機や交差点を表す場合もある。

#### 8.2 `way`

Wayは、複数のNodeを順番に結んだ線である。道路は通常Wayとして記録される。

```xml
<way id="2001">
  <nd ref="1001"/>
  <nd ref="1002"/>
  <nd ref="1003"/>
</way>
```

このWayは、Node 1001、1002、1003の順に延びる線を表す。

Nodeの並び順は、道路方向を解釈する基準になる。

```text
forward方向
1001 → 1002 → 1003

backward方向
1003 → 1002 → 1001
```

#### 8.3 `tag`

Tagは、WayやNodeに追加する属性である。

```xml
<tag k="highway" v="residential"/>
<tag k="lanes" v="2"/>
<tag k="maxspeed" v="40"/>
<tag k="oneway" v="yes"/>
```

この例では、生活道路であり、車線数が2本、最高速度が40 km/h、WayのNode順方向へ進む一方通行であることを表す。

ただし、実際には次の注意が必要である。

* `oneway`がない場合でも、道路種別やroundaboutによって暗黙に一方通行となる場合がある。
* `lanes`は原則として自動車交通に使用する総車線数を表すが、交差点付近の付加車線などが十分に記録されていない可能性がある。
* access系Tagは交通量ではなく、主に法的な通行可能性を表す。
* 条件付き規制や方向別・車線別規制は、単純なTagより複雑である。

---

### 9．`relation`とは何か

Relationは、複数のNodeやWayの関係を表すOSM要素である。

例えば、次の情報に使用される。

* 右折禁止や左折禁止を表す。
* 行政界を表す。
* バス路線を表す。
* 複数の道路要素からなる複雑な関係を表す。

最初はNode、Way、Tagの理解を優先してよい。ただし、正式な道路ネットワークで右左折規制を扱う場合、Relationの解釈も必要になる。

---

## 第II部　SUMOの基礎


### この章群で理解すること

第10章から第13章では、OSMに記録された道路情報が、SUMOで車両を走行させるためのネットワークへどのように変換されるかを学ぶ。SUMOは地図を表示するためのソフトウェアではなく、車両がどの道路区間と車線を通り、交差点でどの方向へ移動し、信号によっていつ停止または進行するかを計算する交通シミュレータである。

OSMとSUMOの主要要素は一対一には対応しない。概念上の変換関係は次のとおりである。

```text
OSM way
  └─ 道路の形状と属性を表す。
       ↓ netconvert・typemap・研究規則
SUMO edge
  └─ 一方向の道路区間を表す。
       ↓
SUMO lane
  └─ edge内の個別車線を表す。
       ↓ connection
次のedge・laneへ移動する。
       ↓ TLS
信号制御対象の移動に状態を割り当てる。
```

各概念の役割は次のとおりである。

| 概念 | 初学者向けの説明 | 誤りが研究へ与える影響 |
|---|---|---|
| SUMO | 車両、道路、経路、需要および信号を入力し、交通流を時間発展として計算するシミュレータである。 | SUMO上の道路構造が誤っていると、旅行時間、到達可能性、渋滞および配送コストが変化する。 |
| `junction` | 交差点、合流点、分岐点または道路端を表すネットワーク上の節点である。 | 不適切な統合や分割があると、本来接続しない道路が接続されたり、必要な移動が失われたりする。 |
| `edge` | 一方向へ進む道路区間であり、経路探索の基本単位になる。 | 方向や分割位置が誤ると、一方通行、距離、速度および経路選択が変わる。 |
| `lane` | `edge`内にある個別車線であり、速度、幅、通行可能車種等を持つ。 | 車線数やpermissionが誤ると、道路容量、車線変更および配送車の通行可能性が変わる。 |
| `connection` | 一つの`lane`から別の`lane`へ移動できる関係である。 | 右左折、直進、合流または分岐の可否が誤ると、道路網全体の到達可能性が変わる。 |
| TLS | 信号制御対象の`connection`と信号状態を対応させる仕組みである。 | `linkIndex`やphaseの対応が誤ると、異なる方向が同時に青になるなど、交差点挙動が不正になる。 |
| `netconvert` | OSMやplain XMLをSUMOの`net.xml`へ変換するプログラムである。 | 終了コード0であっても、採用された既定値や構造が研究仕様と一致するとは限らないため、別途検査が必要である。 |
| typemap | OSM道路種別をSUMO道路種別へ対応付ける設定である。 | 欠損属性へ既定値を補う可能性があるため、OSM明示値と研究上の補完値を区別しなければならない。 |

`edge`と`lane`の関係は、道路区間とその内部車線の関係である。双方向道路は通常、方向別に二つの`edge`として表され、各`edge`が一つ以上の`lane`を持つ。さらに、交差点を越えて次の道路へ進むためには`connection`が必要である。この階層を理解すると、「道路が存在すること」「その道路を特定車種が通れること」「交差点で次の道路へ移動できること」が別々の条件であると分かる。

本研究では、`net.xml`が生成されたことを完成条件とはしない。OSM上の意味が、`edge`、`lane`、`connection`およびTLSへ仕様どおり反映されていることを検査し、その後に正式利用の可否を判定する。


### 10．SUMOとは何か

SUMOは、道路上で車両を動かす交通シミュレーターである。正式名称はSimulation of Urban MObilityである。

SUMOを使用すると、次の現象を扱える。

* 車両を指定された経路で走行させられる。
* 車両が信号で停止する状況を表現できる。
* 車線変更や交差点通過を表現できる。
* 道路混雑や旅行時間を計算できる。
* 一般交通と配送車両を同じ道路上で動かせる。

OSMが現実の道路に関する元データであるのに対し、SUMOは車両を動かすシミュレーション環境である。

---

### 11．SUMOで道路を表す要素

#### 11.1 `junction`

Junctionは、交差点や道路の端点を表す。

OSMのNodeと似た役割を持つが、変換時に複数のNodeが統合されたり、別のJunctionへ変換されたりする場合がある。

#### 11.2 `edge`

Edgeは、一方向の道路区間を表す。

OSMでは、一つのWayで双方向道路を表すことがある。一方、SUMOでは方向別にEdgeを分ける。

```text
OSM

A ───── B
一つの双方向Way
```

```text
SUMO

A ───→ B
A ←─── B
```

一つのOSM Wayが、交差点や属性変化によって複数のEdgeへ分割される場合もある。

#### 11.3 `lane`

Laneは、Edgeの中に存在する個別車線である。

片方向2車線の場合、一つのEdgeの中に二つのLaneが存在する。

SUMOでは、進行方向から見た右端の車線を原則としてLane index 0とする。

```text
進行方向から見て左側　Lane 1
進行方向から見て右側　Lane 0
```

日本は左側通行であるため、「外側車線」「走行車線」といった日常語だけで対応を判断してはならない。仕様では、進行方向から見た左右とLane indexの関係を明示する必要がある。

#### 11.4 `connection`

Connectionは、あるLaneから別のLaneへ移動できる関係を表す。

例えば、交差点の進入車線から、直進先、左折先、右折先へ進める関係を表す。

道路が地図上で接していても、右左折禁止や車線別進行方向によってConnectionが存在しない場合がある。

#### 11.5 TLS

TLSはTraffic Light Systemの略であり、SUMOにおける信号制御を表す。

TLSでは、信号制御対象となるConnectionと、青・黄・赤の信号状態を対応させる。

---

### 12．netconvertとnet.xml

`netconvert`は、OSMなどの道路データをSUMO道路ネットワークへ変換するプログラムである。

```text
OSMファイル
     ↓
netconvert
     ↓
SUMOのnet.xml
```

`net.xml`には、Junction、Edge、Lane、Connection、TLS、速度、通行可能車種などが記録される。

ただし、完成した`net.xml`は相互に依存する情報を多く含むため、原則として直接手作業で編集しない。

道路属性やConnectionを変更する場合は、編集可能なplain XMLである`.nod.xml`、`.edg.xml`、`.con.xml`、`.tll.xml`などを修正し、`netconvert`を再実行する。

---

### 13．typemapとは何か

typemapは、OSMの道路種別をSUMOの道路種別へ変換するための設定である。

例えば、OSMの`highway=residential`を、SUMOでどの速度、優先度、車線数、通行可能車種を持つ道路として扱うかを定義できる。

typemapは便利である一方、OSMに属性がない場合に既定値を自動的に与える可能性がある。

そのため、本研究では次を区別する。

* OSMに明示された値を採用したのか。
* OSM情報から一意に導出したのか。
* typemapの既定値を使用したのか。
* 研究側の補完規則を使用したのか。
* 人手レビューまたは外部資料で確定したのか。

typemapの値を無条件に現実の道路属性とみなしてはならない。

---

## 第III部　今回の生成システム


### この章群で理解すること

第14章から第21章では、OSMをSUMOへ変換する処理を、責任の異なる複数工程へ分離する理由を学ぶ。この分離の目的は、属性の解釈、SUMO要素への対応付け、交差点移動の確定、信号構造の確認、最終生成および完成後の検査を、一つのプログラム内で無記録に混在させないことである。

工程全体は次の関係を持つ。

```text
Resolver
  └─ OSM上で採用すべき意味と停止理由を決める。
       ↓
Provisional Build
  └─ 対応先を確認するための暫定SUMO構造を作る。
       ↓
Permission Materializer
  └─ Resolverの期待値をedge・lane・connectionへ反映する。
       ↓
Connection処理
  └─ 交差点等で許されるlane間移動を確定する。
       ↓
TLS Review
  └─ connectionと信号リンク・phaseの構造対応を確認する。
       ↓
Final Build
  └─ 承認済み入力だけから正式候補net.xmlを生成する。
       ↓
Post-build Audit
  └─ 生成処理とは別に、完成物と期待値を照合する。
```

各工程の中心的な問いは次のとおりである。

| 工程 | 中心的な問い | その工程で行ってはならないこと |
|---|---|---|
| Resolver | OSM上の値と規制を、研究ではどの意味として採用するか。 | SUMOの生成結果に合わせて解釈を変えたり、根拠のない補完を行ったりしてはならない。 |
| Provisional Build | OSM要素が、どのSUMO構造へ変換されるか。 | 暫定出力を正式な交通評価や最適化比較へ使用してはならない。 |
| Permission Materializer | 確定済みの期待permissionを、どの`edge`、`lane`または`connection`へ設定するか。 | OSMタグの意味を独自に再解釈してはならない。 |
| Connection処理 | どの車線からどの車線へ移動でき、どの`vClass`がその移動を利用できるか。 | 地図上で近いことだけを根拠に、新しい移動を推測して追加してはならない。 |
| TLS Review | 信号制御対象の`connection`と`linkIndex`、phase stateが整合しているか。 | 実信号データがない状態で現実の信号時間を推定してはならない。 |
| Final Build | 承認済みの入力と固定環境から、同じ正式候補を再生成できるか。 | 新しい補完、属性解釈、permission変更または手作業修正を行ってはならない。 |
| Post-build Audit | 最終`net.xml`が期待値、品質条件および来歴条件を満たすか。 | 検出した問題を監査中に自動修正してはならない。 |

ResolverとMaterializerは特に混同しやすい。Resolverは「OSM `way`のforward方向左端車線では`bus`を許可する」のように、OSM上で期待される意味を決める。一方、Materializerは、その期待値に対応するSUMO `edge`の方向と`lane index`をprovenanceから特定し、plain XMLへ設定する。前者は意味の決定であり、後者は対応先への適用である。

`connection`とTLSも別の責任を持つ。`connection`は車線間の移動可能性を定義し、TLSは信号制御対象となった移動へ時間ごとの状態を割り当てる。したがって、`connection`集合が変化した場合、過去のTLS Reviewは無効になる。文字列の長さだけが一致していても、`linkIndex`の順序が異なれば、別の進行方向を青にする可能性があるためである。

Final BuildとPost-build Auditを分ける理由は、生成処理が自らの誤りを同じロジックで見逃すことを防ぐためである。Final Buildは承認済み材料を組み立てる工程であり、Post-build Auditは完成物を読み直して期待値と比較する工程である。両者を通過して初めて、成果物を`formal_candidate`から`formal_accepted`へ移行できる。


### 14．Resolver

#### 14.1 Resolverの役割

Resolverは、OSMの道路情報を読み、研究で採用する値または停止理由を決める処理である。

#### 14.2 入力

Resolverは、次の入力集合を一つの処理単位として受け取る。

* 固定されたOSM XMLと、その取得元、取得日時およびSHA-256を受け取る。
* 承認済みの`sumo_network.yml`、typemap、Schemaおよび規則表を受け取る。
* 対象とする`vClass`集合と、道路重要度区分（criticality）を受け取る。
* 外部資料または人手レビューを使用する場合は、対象OSM要素、根拠資料、確認者、確認日および承認状態を含むレビュー記録を受け取る。

入力の一部が欠けている場合や、設定IDとSHA-256が一致しない場合は、属性解釈を開始せずに停止する。

#### 14.3 出力

Resolverは、少なくとも次の成果物を出力する。

* 各OSM `way`について、採用した道路方向、車線数、速度および通行条件を記録する。
* 各値について、元値、採用値、値の状態、適用規則IDおよび根拠を記録する。
* OSM `way`、方向および車線位置ごとの期待`vClass`集合を、permission期待値として出力する。
* 未解決、矛盾、未対応形式または条件付き規制について、Failure Codeと停止理由を出力する。
* 後工程が入力の同一性を確認できるように、設定ID、Schema版および入力SHA-256を出力へ埋め込む。

#### 14.4 Resolverを独立させる理由

OSMには、明示値、欠損値、矛盾値、未対応形式および条件付き値が混在する。これらを`netconvert`やtypemapへ直接委ねると、既定値が採用された箇所と理由を後から識別できない可能性がある。

Resolverを独立させることで、SUMO構造を生成する前に、OSM上で採用すべき意味と停止すべきケースを確定できる。また、属性解釈の試験を、SUMO要素への対応付けやXML書込みから分離できる。

#### 14.5 責任範囲外の処理

Resolverは、SUMOの`edge` ID、`lane index`または`connection`への対応付けを行わない。Resolverが決めるのは、OSM `way`上で採用すべき属性値と期待通行権限である。

Resolverは、欠損値をその場の判断で補完せず、外部資料の内容を無記録で転記せず、Provisional Buildの結果に合わせて期待値を変更しない。SUMO要素への対応はprovenanceとPermission Materializerの責任である。

#### 14.6 値の状態

属性値には、採用値だけでなく、どのように決定したかを示す状態を付ける。

| 状態                       | 意味                         |
| ------------------------ | -------------------------- |
| `explicit_valid`         | OSMに有効な値が明示されていた。          |
| `derived_unambiguous`    | OSM情報から一意に値を導出できた。         |
| `missing`                | 必要な情報が存在しなかった。             |
| `valid_but_unsupported`  | OSM上は有効だが、現在の処理では解釈できなかった。 |
| `conflicting`            | 複数の情報が矛盾していた。              |
| `conditional`            | 時間帯や条件によって値が変化する。          |
| `structural_placeholder` | 構造確認だけに使用する暫定値である。         |
| `reviewed_external`      | 外部資料または人手レビューで確定した。        |
| `unresolved`             | 現在の仕様では値を決定できなかった。         |

同じ40 km/hでも、OSM明示値と推定値では研究上の信頼性が異なるため、状態を保存する。

---

### 15．Provisional Build

#### 15.1 Provisional Buildの役割

Provisional Buildは、Resolverが確認したOSMと固定された暫定変換設定から、SUMOの`junction`、`edge`、`lane`、`connection`およびTLS候補を生成する工程である。目的は、OSM上の期待値を適用する対象となるSUMO構造を可視化し、OSM要素とのprovenanceを確立することである。

#### 15.2 入力

Provisional Buildは、少なくとも次の入力を使用する。

* Resolverが確認した正規化OSMと属性監査を使用する。
* 構造生成に必要なtypemap、`netconvert`設定および対象地域設定を使用する。
* 使用するSUMO版、依存環境およびコンテナdigestを固定する。
* 構造確認専用の既定値を使用する場合は、その項目、値、適用範囲および`structural_placeholder`状態を明示する。

#### 15.3 出力

Provisional Buildは、少なくとも次の成果物を出力する。

* 暫定的な`node`、`edge`、`connection`およびTLSのplain XMLを出力する。
* OSM `way`と生成されたSUMO `edge`の対応候補をprovenanceとして出力する。
* `edge`の方向、分割、`lane`数および`connection`候補を後工程が検査できる形式で出力する。
* 実行コマンド、SUMO環境、入力SHA-256、Warningおよび出力SHA-256を暫定build manifestへ記録する。

#### 15.4 暫定構造を生成する理由

Resolverが扱う主単位はOSM `way`であるが、通行権限を設定する主単位はSUMOの`lane`および`connection`である。一つのOSM `way`から生成される`edge`数、方向、分割位置および`lane index`は、実際の変換結果を確認しなければ確定できない。

このため、属性解釈とSUMO要素への適用の間にProvisional Buildを置き、OSM上の期待値をどのSUMO要素へ適用するかを検査可能にする。

#### 15.5 利用制限と技術検証事項

Provisional Buildの出力状態は`provisional`であり、旅行時間、渋滞、配送性能、較正、古典最適化またはQAOAの正式評価に使用してはならない。

OSMの元IDをplain XMLと`net.xml`へどのように保持できるか、`lane index`がどの条件で安定するか、および使用する`netconvert`オプションがどの構造変更を生むかは、固定したSUMO版でRuntime Testを行って確定する。技術検証が完了していない挙動を仕様上の事実として扱わない。

### 16．Permissionと`vClass`

Permissionは、SUMOの`lane`または`connection`を通行できる車両クラスの集合を表す。本書では、通行可能集合を`expected_vclasses`として明示し、必要に応じてXMLの`allow`または`disallow`へ変換する。

SUMOでは車両の用途や種類を`vClass`で表す。本研究が初期対象とする候補は次のとおりである。

| `vClass` | 本書での意味 |
|---|---|
| `passenger` | 一般乗用車を表す。 |
| `taxi` | タクシーを表す。 |
| `bus` | 路線バスを表す。 |
| `coach` | 長距離バス等を表す。 |
| `delivery` | 配送車を表す。 |
| `truck` | 貨物トラックを表す。 |
| `motorcycle` | オートバイを表す。 |

OSMの`access`、`vehicle`、`motor_vehicle`、`bus`などのタグ体系と、SUMOの`vClass`体系は同一ではない。したがって、OSMタグをSUMO `vClass`へ変換する対応表を研究側で定義し、規則IDとともに版管理する。

```text
OSMの交通モード・access情報
        ↓ 承認済み対応規則
研究上の期待通行集合
        ↓ Permission Materializer
SUMOのlane・connection permission
```

対応規則は、少なくとも次を定義する。

* どのOSMタグが、どの`vClass`へ影響するかを定義する。
* 一般タグ、方向別タグ、車線別タグおよび条件付きタグの優先順位を定義する。
* `yes`、`no`、`designated`、`destination`、`private`等の値を、研究対象でどのように扱うかを定義する。
* 未対応値、矛盾値および条件付き規制を検出した場合のFailure Codeを定義する。
* 出力する`vClass`集合の順序を固定し、同じ集合が同じ文字列として出力されるようにする。

例えば、`motor_vehicle=yes`を受け取った場合でも、管理対象のすべての`vClass`を自動的に許可してよいとは限らない。どの`vClass`を含めるかは、承認済み対応表に基づいて決定する。対応表に規則がない場合は、実装者が意味を推測せずに停止する。

### 17．Permission Materializer

#### 17.1 Permission Materializerの役割

Permission Materializerは、Resolverが確定したpermission期待値を、provenanceに基づいてSUMOのplain XML上の`edge`、`lane`および`connection`へ反映する工程である。OSM上の規則を再解釈する工程ではなく、承認済み期待値とSUMO要素の対応を検査し、適用結果を記録する工程である。

#### 17.2 入力

Permission Materializerは、少なくとも次の入力を使用する。

* Resolverが生成したpermission期待値と、そのSchema版、設定IDおよびSHA-256を使用する。
* Provisional Buildが生成したplain XMLとprovenanceを使用する。
* OSM方向とSUMO `edge`方向を対応付ける承認済み規則を使用する。
* OSM上の車線位置とSUMO `lane index`を対応付ける承認済み規則を使用する。
* 管理対象`vClass`集合、出力順序、Failure Codeおよび検査順序を`sumo_network.yml`から読み込む。

入力間で設定ID、Schema版またはSHA-256が一致しない場合は、対応付けを開始せずに停止する。

#### 17.3 Resolverとの責任分離

| 観点 | Resolver | Permission Materializer |
|---|---|---|
| 主な問い | OSM上の規則をどの値と通行集合として解釈するか。 | 確定した値と通行集合を、どのSUMO要素へ適用するか。 |
| 主な単位 | OSM `way`、方向、OSM上の車線位置 | SUMO `edge`、`lane index`、`connection` |
| 判断内容 | 属性値、値の状態、期待`vClass`集合 | 対応先、適用可否、適用前後の値 |
| 禁止事項 | SUMO IDや変換結果に合わせて期待値を変更しない。 | OSMタグを独自に再解釈しない。 |

例えば、Resolverが「OSM `way` 2001のforward方向の左端車線では`bus`だけを許可する」と決めた場合、Permission Materializerはprovenanceから対応するSUMO `lane`を特定し、期待集合と一致するpermissionを設定する。

#### 17.4 `edge`方向の対応付け

Materializerは、承認済みの方向判定規則に従って、各SUMO `edge`がOSM `way`のforward方向またはbackward方向のどちらに対応するかを一意に決定する。

方向判定では、OSM `way`のNode列、SUMO `edge`の端点、provenanceおよび座標系を使用する。`edge` IDの接頭辞、負号、文字列形式または座標の見た目だけを根拠としてはならない。複数候補が同じ優先順位で残る場合は、`ambiguous_edge_direction`として停止する。

#### 17.5 車線位置の対応付け

本研究では、OSM側の車線位置`p`を各進行方向から見て左端を0として数え、SUMO側では右端の`lane index`を0として数える。期待車線数と実車線数がともに`n`であり、両者が一対一に対応すると検証できた場合に限り、次の式を適用する。

```text
sumo_index = n - 1 - p
```

付加車線、専用車線、車線の統合・分割、異なる車線順序または車線数不一致が存在する場合は、この式を機械的に適用してはならない。対応を一意に決定できない場合は、規定されたFailure Codeで停止する。

#### 17.6 処理手順

Permission Materializerは、次の順序で処理する。

1. 入力JSONとXMLを読み込み、Schema適合性を検査する。
2. 設定ID、Schema版、入力SHA-256およびprovenanceの整合を検査する。
3. 管理対象`vClass`以外の値が存在しないことを検査する。
4. OSM `way`とSUMO `edge`を対応付ける。
5. 各SUMO `edge`のOSM方向を決定する。
6. 期待車線数と実車線数を比較する。
7. OSMの車線位置とSUMO `lane index`を対応付ける。
8. 期待permissionを`lane`へ設定する。
9. `edge`または`lane`の除外に伴う`connection`への影響を処理する。
10. TLS Reviewの再実施が必要かを判定する。
11. すべての検査、適用、削除および停止をMaterializer Auditへ記録する。
12. すべての処理が成功した場合だけ、一時ファイルを正式な中間成果物へ原子的に置き換える。

#### 17.7 出力

Permission Materializerは、少なくとも次の成果物を出力する。

* permissionを反映した`edge`・`lane`および`connection`のplain XMLを出力する。
* 各期待値について、対応したSUMO要素、適用前後の値、規則IDおよび結果をMaterializer Auditへ記録する。
* 適用件数、未適用件数、削除件数、WarningおよびFailure Codeをbuild summaryへ記録する。
* TLS Reviewを再実施すべき`connection`集合と、その入力SHA-256を出力する。

#### 17.8 曖昧性が残る場合の処理

`edge`方向、車線位置、期待permissionの適用先または`connection`への影響を一意に決定できない場合は、近い候補や多数決で処理を継続してはならない。正式な中間XMLを更新せず、規定されたFailure Code、候補一覧、比較証拠および停止箇所をAuditへ記録する。

### 18．`connection`と`connection permission`

#### 18.1 `connection`の定義と役割

`connection`は、あるSUMO `lane`から交差点、合流部または分岐部を通って、別のSUMO `lane`へ移動できる関係を表す。`edge`が一方向の道路区間を表し、`lane`がその区間内の個別車線を表すのに対し、`connection`は道路区間間の移動可能性を表す。

```text
進入edgeのlane
        ↓
交差点内のconnection
        ↓
退出edgeのlane
```

道路が地図上で接していても、対応する`connection`がなければSUMO車両はその方向へ移動できない。反対に、現実には禁止された移動の`connection`が存在すると、車両が誤った右左折、進入、合流または転回を行う。

#### 18.2 入力

`connection`処理は、少なくとも次の入力を使用する。

* Provisional Buildが生成したlane-to-lane `connection`候補を使用する。
* from `edge`、from `lane`、to `edge`およびto `lane`の識別子を使用する。
* OSMの`restriction` relation、方向情報および適用対象車種を使用する。
* Resolverが生成した各`lane`の期待`vClass`集合を使用する。
* Permission Materializerが確認した`edge`・`lane` provenanceを使用する。
* `connection`固有の`allow`、`disallow`またはその他の規制が存在する場合は、その規則と優先順位を使用する。

#### 18.3 決定事項

`connection`処理は、各候補について次を決定する。

* `connection`候補を保持するか削除するかを決定する。
* どのfrom `lane`からどのto `lane`へ接続するかを決定する。
* その`connection`を通行できる`vClass`集合を決定する。
* 信号制御対象である場合は、TLS Reviewへ渡すcontrolled `connection`として記録する。

明示的な`connection`固有規制がない場合に限り、本研究では`connection`の期待`vClass`集合を、from `lane`とto `lane`の期待集合の共通部分として計算する。

```text
expected_connection_vclasses
    = expected_from_lane_vclasses
      ∩ expected_to_lane_vclasses
```

例えば、from `lane`が`bus`と`taxi`を許可し、to `lane`が`bus`と`delivery`を許可する場合、共通部分は`bus`だけである。

この共通部分規則は、本研究が採用する設計規則であり、SUMOの一般的な自動推論規則として扱ってはならない。`connection`固有の規制が存在する場合は、承認済みの優先順位に従って適用する。規制同士が矛盾し、一意に解決できない場合は停止する。

#### 18.4 出力

`connection`処理は、少なくとも次の成果物を出力する。

* 保持したlane-to-lane `connection`を出力する。
* 各`connection`の期待`vClass`集合を出力する。
* 削除した`connection`、削除理由および根拠規則を記録する。
* from/to `lane`との対応とprovenanceを記録する。
* OSM `restriction`または研究規則への参照を記録する。
* TLS Reviewへ渡すcontrolled `connection`候補と入力SHA-256を出力する。

#### 18.5 独立確認が必要な理由

`lane` permissionが正しくても、`connection`が誤っていれば道路網全体の到達可能性は正しくならない。例えば、配送車が進入`lane`と退出`lane`の両方を通行できても、その間の右折が禁止されていれば、経路として利用できない。

また、`lane`の除外やpermission変更によって`connection`集合が変わると、TLSの`linkIndex`との対応も変わり得る。このため、`connection`を確定した後にTLS Reviewを実施する。

#### 18.6 禁止事項と停止条件

`connection`処理は、OSMまたはProvisional Buildに根拠がない右左折を、地図上の見た目だけで新規生成してはならない。座標が近い`lane`同士を推測で接続せず、Provisional Buildが生成した候補とprovenanceを使用する。

次のいずれかに該当する場合は停止する。

* from/to `edge`または`lane`が存在しない。
* OSM `restriction`と生成`connection`が矛盾する。
* `connection` permissionを一意に決定できない。
* permission適用後に不正な参照が残る。
* controlled `connection`をTLS `linkIndex`へ一意に対応付けられない。

### 19．TLS Review

#### 19.1 TLS Reviewの役割

TLS Reviewは、permission適用後に確定した`connection`集合と、SUMOの信号リンクおよびphase stateとの構造的対応を確認する工程である。

SUMOでは、信号制御される各`connection`へ`linkIndex`を割り当て、各phaseの`state`文字列の位置によって、そのリンクを赤、黄、青等のどの状態にするか表す。したがって、`connection`の削除、追加または並び順の変更がある場合は、過去のTLS対応をそのまま再利用できない。

#### 19.2 入力

TLS Reviewは、少なくとも次の入力を使用する。

* permission適用後に確定した`connection`集合を使用する。
* Provisional Buildが生成した暫定TLS情報を使用する。
* signalized `junction`の識別子を使用する。
* `connection`と`linkIndex`の対応候補を使用する。
* phase、`duration`、`state`等を含むTLS logicを使用する。
* 入力`connection`、TLS情報、設定およびSchemaのSHA-256を使用する。

#### 19.3 構造検査項目

TLS Reviewは、少なくとも次の構造条件を検査する。

* 各`linkIndex`が、現在存在する正しいcontrolled `connection`を参照している。
* 各controlled `connection`に必要な`linkIndex`が一意に存在する。
* `linkIndex`が重複せず、許可された範囲内にある。
* 各phaseの`state`文字列長が、制御対象リンク数と一致する。
* 削除された`connection`をTLSが参照していない。
* `connection`集合または並び順が変更された場合、過去のレビュー状態が無効化されている。
* review manifestの入力SHA-256が、現在の`connection`およびTLS入力と一致する。

controlled `connection`が4本ある場合、各phaseの`state`は4文字でなければならない。ただし、文字数が一致していても並び順が誤っていれば、別の進行方向を青にする。したがって、文字列長だけでなく、各文字位置と`connection`・`linkIndex`の対応を確認する。

#### 19.4 出力

TLS Reviewは、少なくとも次の成果物を出力する。

* レビュー済み`connection` XMLを出力する。
* レビュー済みTLS XMLを出力する。
* `connection`、`linkIndex`およびphase state位置の対応表を出力する。
* 対象入力のSHA-256を含むreview manifestを出力する。
* レビュアー、レビュー日時、判断、根拠および未解決事項を記録する。
* 合否、Failure Codeおよび再レビュー条件を記録する。

`connection`集合、並び順、TLS logicまたは入力SHA-256が後から変化した場合は、以前のレビュー結果を自動的に無効とする。

#### 19.5 交通モデルとしての妥当性との境界

構造的なTLS検証に合格しても、東京の実際の信号制御を再現しているとは限らない。実信号との一致については、後続の交通モデル構築・較正工程で、信号サイクル、青時間配分、交差点間offsetおよび時間帯別制御を独立した観測資料と比較する。

したがって、TLS Review済みとは、「信号データが現在のSUMO構造と矛盾していない」ことを意味し、「東京の実信号運用を再現している」ことを意味しない。

#### 19.6 禁止事項と停止条件

TLS Reviewは、レビュー中に都合のよい`connection`を追加せず、実信号データがない状態で信号時間を推定しない。構造を修正する必要がある場合は、`connection`工程へ戻り、修正後の入力でTLS Reviewを再実施する。

次のいずれかに該当する場合は停止する。

* controlled `connection`に`linkIndex`がない、重複する、または対応が曖昧である。
* phase `state`長が制御対象リンク数と一致しない。
* TLSが存在しない`connection`を参照する。
* review manifestと入力SHA-256が一致しない。
* 構造上の未解決事項が残る。

### 20．Final Build

#### 20.1 Final Buildの役割

Final Buildは、承認済みのplain XML、設定および実行環境から、`formal_candidate`状態の`formal.net.xml`を再現可能な手順で生成する工程である。

Final Buildは、新しい道路属性の解釈、補完、permission変更、`connection`追加またはTLS対応変更を行わない。上流で承認された判断を、固定環境で同一の成果物へ組み立てることだけを責任とする。

#### 20.2 入力

Final Buildは、少なくとも次の入力を使用する。

* 承認済みのnode XMLを使用する。
* Permission Materializerが生成したpermission反映済みedge XMLを使用する。
* TLS Reviewが承認したconnection XMLとTLS XMLを使用する。
* 固定されたtypemap、`netconvert`設定、XSDおよび`sumo_network.yml`を使用する。
* 各入力の承認記録、状態、Schema版およびSHA-256を使用する。
* SUMO、`netconvert`、PROJその他の依存関係を含む、digest固定コンテナを使用する。
* コードのcommit IDと、完全な実行コマンドを生成する設定を使用する。

入力の一部だけを新しい版へ差し替えてはならない。設定ID、Schema版、入力SHA-256およびreview manifestが、同一buildとして整合することをReadiness Gateで確認する。

#### 20.3 処理手順

Final Buildは、次の順序で処理する。

1. すべての入力、設定、承認状態、Schema版およびSHA-256を検査する。
2. Readiness Gateが合格していることを検査する。
3. 固定コンテナ内のSUMO、`netconvert`、PROJおよび依存環境の識別情報を取得する。
4. 設定から完全な`netconvert`コマンドを生成し、manifestへ記録する。
5. 一時出力先を使用して`netconvert`をfail-fastで実行する。
6. 終了コード、標準出力、標準エラーおよびWarningを保存する。
7. 生成された`net.xml`を固定XSDと固定SUMOで読み込み検査する。
8. 出力と付随成果物のSHA-256を計算する。
9. build manifestとbuild summaryを生成する。
10. すべての必須処理が成功した場合だけ、一時出力を`formal.net.xml`へ原子的に置き換える。
11. 生成物の状態を`formal_candidate`として記録し、Post-build Auditへ渡す。

#### 20.4 出力

Final Buildは、少なくとも次の成果物を出力する。

* `formal_candidate`状態の`formal.net.xml`を出力する。
* 完全な実行ログ、終了コード、標準出力および標準エラーを出力する。
* 入力、設定、コード、環境、コマンド、レビュー記録および出力を結ぶbuild manifestを出力する。
* Warning一覧、分類状態、件数およびBLOCKING判定を出力する。
* すべての成果物のSHA-256一覧を出力する。
* Post-build Auditへ渡すbuild summaryを出力する。

生成直後の`formal.net.xml`は正式利用候補であり、研究結果の算出には使用しない。Post-build Auditに合格し、対象SHA-256を含む受入判断が記録された後だけ、状態を`formal_accepted`へ変更できる。

#### 20.5 固定対象

再現可能性を確保するため、少なくとも次を固定または記録する。

* SUMOと`netconvert`の版を固定する。
* コンテナimageのdigestを固定する。
* PROJその他の依存環境の版を固定する。
* typemap、XSD、Schemaおよび設定ファイルのSHA-256を固定する。
* コードのcommit IDを記録する。
* 実行コマンド、全オプションおよび環境変数を記録する。
* すべての入力ファイルと出力ファイルのSHA-256を記録する。

#### 20.6 禁止事項と停止条件

Final Buildでは、新しい補完、道路属性の再解釈、permission変更、`connection`追加、TLS対応変更または人手による一時オプション追加を行ってはならない。

入力不整合、未承認入力、Readiness Gate不合格、環境情報欠損、`netconvert`失敗、XSD不適合、固定SUMOでの読込み失敗または未分類の停止対象Warningがある場合は、`formal_candidate`を成功成果物として公開しない。既存の承認済み成果物を上書きせず、Failure Codeと停止理由をbuild manifestへ記録する。

完成した`net.xml`を直接修正してはならない。問題がある場合は、原因となった上流のplain XML、設定、規則またはレビューへ戻り、Final Buildを再実行する。

### 21．Post-build Audit

#### 21.1 Post-build Auditの役割

Post-build Auditは、Final Buildが生成した`formal_candidate`状態の`formal.net.xml`を、生成処理とは独立した観点から検査し、`formal_accepted`として受け入れられるかを判定する工程である。

Final Buildが「指定入力から成果物を生成する」機能であるのに対し、Post-build Auditは「生成物が期待値、構造条件、来歴条件および受入基準を満たすかを判定する」機能である。生成処理と検査処理を分離することで、同じ実装誤りを自己検査で見逃す危険を低減する。

#### 21.2 入力

Post-build Auditは、少なくとも次の入力を使用する。

* Final Buildが生成した`formal.net.xml`を使用する。
* build manifest、build summary、実行ログおよびWarning一覧を使用する。
* Resolverの属性監査とpermission期待値を使用する。
* OSM要素からSUMOの`edge`、`lane`および`connection`へのprovenanceを使用する。
* Materializer Auditを使用する。
* TLS review manifestと対応表を使用する。
* 事前に固定した構造ゲート、品質ゲート、Failure Codeおよび受入基準を使用する。
* 固定XSD、固定SUMO実行環境および成果物のSHA-256を使用する。

#### 21.3 検査項目

Post-build Auditは、少なくとも次の仕様適合性を検査する。

* 期待した`edge`と`lane`が存在し、想定外の要素が追加されていない。
* 各`lane`のpermissionがpermission期待値と一致する。
* 管理対象外の`vClass`が存在しない。
* 各`connection`の存在、from/to対応およびpermissionが期待値と一致する。
* TLSとcontrolled `connection`、`linkIndex`およびphase state位置の対応が一致する。
* `formal.net.xml`が固定XSDへ適合し、固定SUMOで正常に読み込める。
* 未分類WarningおよびBLOCKING Warningが残っていない。

Post-build Auditは、少なくとも次の構造品質と来歴を検査する。

* 一方通行方向、日本の左側通行および`lane index`対応が期待どおりである。
* 孤立成分、切断、到達不能および行政界端の接続が、事前に固定した品質ゲートを満たす。
* OSM `way`からSUMOの`edge`、`lane`および`connection`まで追跡できる。
* 入力、設定、コード、環境および出力のSHA-256がbuild manifestと一致する。
* `net.xml`生成後に無記録の編集が行われていない。
* `structural_placeholder`が正式候補へ残っていない。

#### 21.4 出力

Post-build Auditは、少なくとも次の成果物を出力する。

* 検査項目ごとの合否、測定値、閾値および根拠を出力する。
* `node`、`edge`、`lane`、`connection`、TLS、孤立成分および到達可能性の品質指標を出力する。
* permission、provenance、Materializer AuditおよびTLS review manifestの照合結果を出力する。
* Warning、除外、不一致および未解決事項の一覧を出力する。
* Failure Code、停止理由および原因工程の候補を出力する。
* `formal_accepted`としての受入可否を出力する。
* 監査対象`net.xml`とすべての根拠ファイルのSHA-256を出力する。
* 合格時は、対象SHA-256、受入日時および承認者を含むacceptance recordを出力する。

#### 21.5 VerificationとValidationの境界

Post-build Auditは主としてVerificationであり、仕様どおりの道路ネットワークが生成されたかを確認する。東京の実交通量、速度、旅行時間、渋滞または信号運用を十分に再現できるかは、需要と信号時間を追加した後のValidationで評価する。

したがって、Post-build Auditへの合格だけを根拠として、「東京の交通を再現した」と主張してはならない。主張できるのは、固定した仕様、入力および環境に対して、道路ネットワークが受入基準を満たしたことである。

#### 21.6 禁止事項と不合格時の扱い

Post-build Auditは、検出した問題をその場で自動修正しない。不一致を発見した場合は、Resolver、Provisional Build、Permission Materializer、TLS ReviewまたはFinal Buildのどこに原因があるかを記録し、上流工程を修正して再生成する。

監査中に`net.xml`を直接変更した場合、そのファイルはbuild manifestと一致しなくなるため、正式成果物として扱わない。修正は必ず原因となった上流入力、設定または規則へ反映し、Final BuildとPost-build Auditを再実行する。

## 第IV部　実装を始めるときに理解する内容


### この章群で理解すること

第22章から第33章では、処理の考え方を、別の実装者が同じように実装・試験できる形へ変換するための基礎を学ぶ。再現可能な研究では、コードだけを保存しても不十分である。コードが満たすべき規則、入出力形式、変更履歴、各実行の来歴、個別判断および停止理由を、相互に対応付けて保存する必要がある。

この章群の概念は次の関係を持つ。

```text
仕様
  └─ 実装が満たすべき動作と停止条件を定義する。
       ↓
JSON Schema・設定ファイル
  └─ 入出力形式と機械可読な固定値を定義する。
       ↓
実装・テスト・バージョン管理
  └─ 仕様をコード化し、変更履歴を残す。
       ↓
Manifest
  └─ 一回の実行で何を使用し、何が生成されたかを記録する。
       ↓
Audit
  └─ 個別のway・edge・lane・connectionをどう判断したか記録する。
       ↓
Failure Code
  └─ 処理を継続できない理由を一意に表す。
```

各概念の役割は次のとおりである。

| 概念 | 役割 | 単独では保証できないこと |
|---|---|---|
| 仕様 | 入力条件、必須動作、禁止動作、出力、停止条件および検査証拠を定義する。 | 仕様を書いただけでは、実装が実際に従っていることは保証できない。 |
| JSON Schema | JSONの必須項目、型、許容値および未知項目の可否を検査する。 | 車線数の計算方法や規則の優先順位など、意味上の処理手順は定義できない。 |
| バージョン管理 | コード、仕様、設定およびテストの変更履歴と対応関係を保存する。 | 実行時にどの入力ファイルや環境を使用したかは、commit IDだけでは特定できない。 |
| Manifest | 一回の実行全体について、入力、設定、環境、コマンド、出力および結果を記録する。 | 各道路属性をどの規則で決めたかという個別判断は、Manifestだけでは十分に表せない。 |
| Audit | 各OSM要素またはSUMO要素について、元値、採用値、根拠、規則IDおよび適用結果を記録する。 | 実行環境全体や全成果物の対応は、Auditだけでは把握しにくい。 |
| Failure Code | 停止理由を機械的に識別し、実装間で同じ失敗を同じ名称として扱う。 | Failure Codeだけでは、どの入力や比較証拠によって停止したかは説明できないため、Auditと併用する必要がある。 |

仕様は、自然言語による説明だけではなく、観測可能な動作へ分解する必要がある。例えば、「方向を適切に判定する」という記述では、使用する入力、比較順序、許容差、複数候補が残った場合の停止条件が分からない。実装可能な仕様では、同じ入力に対して異なる実装者が同じ方向または同じFailure Codeを返せるように、判断規則と検査順序を固定する。

JSON Schemaと仕様の違いも重要である。JSON Schemaは、`direction`が文字列であり、`forward`または`backward`のどちらかであることを検査できる。しかし、どの条件で`forward`を選ぶかは判断できない。その判断は規範仕様に記述し、Schemaは判断結果を正しい形式で受け渡すために用いる。

ManifestとAuditは記録の粒度が異なる。Manifestは「この実行が、どのOSM、設定、コード、SUMO環境およびコマンドから、どの成果物を生成したか」を示す。Auditは「OSM `way` 2001の欠損車線数を、どの規則と根拠によって何車線として扱ったか」を示す。研究結果を再現し、問題原因を追跡するには両方が必要である。

Failure Codeと検査順序を固定する理由は、失敗も再現対象だからである。一つの入力に複数の欠陥がある場合、実装によって最初に検出する問題が異なると、同じ入力から異なる停止理由が返る。そこで、Schema、設定、対応付け、方向、車線、permission、connection、TLSという検査順序を定め、最初に報告するFailure Codeまたは複数コードの並び順を固定する。


### 22．プログラムと仕様の関係

仕様書は、現在のコードが何をしているかを説明する文書ではない。

仕様書は、コードが何をしなければならないかを定義する文書である。

```text
仕様
＝ 正しい動作を定義する。

実装
＝ 仕様をプログラムとして実現する。

試験
＝ 実装が仕様を満たすか確認する。
```

既存コードと仕様が異なる場合、既存コードを自動的に正しいものとして扱ってはならない。

まず仕様上どちらが正しいかを判断し、その後に実装または仕様を修正する。

---

### 23．要件の書き方

実装可能な要件は、目的だけでなく、入力条件、必須動作、正常出力、停止条件および観測可能な証拠を持つ必要がある。少なくとも次の項目を記載する。

```text
要件ID：
PM-REQ-021

目的：
OSM Wayに対応するSUMO Edgeの方向を、実装者の推測で決めることを防止する。

適用条件：
同一のOSM Wayに対応するSUMO Edge候補が一つ以上存在する。

入力：
OSM WayのNode列、SUMO Edgeのfrom/to Junction、provenance、座標系情報。

必須動作：
Materializerは、承認済みの方向判定規則を順番どおりに適用し、
各EdgeのOSM方向をforwardまたはbackwardのいずれか一つに決定しなければならない。

正常出力：
Edge ID、OSM Way ID、決定方向、適用規則IDおよび比較証拠を出力する。

停止条件：
複数の方向候補が同じ優先順位で残り、一意に決定できない。

Failure Code：
PM004 ambiguous_edge_direction

副作用：
停止時は正式出力XMLを更新せず、一時ファイルを破棄する。

監査情報：
比較した端点、座標系、候補方向、距離、許容差および適用規則を記録する。

対応テスト：
PM-TEST-021-A
PM-TEST-021-B
PM-TEST-021-C
```

要件では、「適切に処理する」「必要に応じて判断する」「十分に近い場合」といった、実装者によって解釈が変わる表現を使用しない。距離、許容差、優先順位、停止条件、出力順序および丸め規則は、機械的に判定できる形で定義する。

一つの要件に複数の責任を詰め込まない。例えば、方向判定、車線対応、permission適用および監査出力は、失敗原因と試験方法が異なるため、原則として別の要件IDへ分割する。

### 24．MUST、MUST NOT、MAY

仕様書では、規則の強さを区別する。

* `MUST`は、適用条件を満たす場合に必ず実施する動作を表す。
* `MUST NOT`は、適用条件を満たす場合に実施してはならない動作を表す。
* `MAY`は、明示された条件と記録要件を満たす場合に選択できる動作を表す。

例えば、次の要件は必須動作である。

```text
PM-REQ-031:
Materializerは、期待Lane数と実Lane数が一致することを確認しなければならない。
```

次の要件は禁止動作である。

```text
PM-REQ-032:
Materializerは、Lane数不一致を推測値で補正してはならない。
```

`MAY`を使用する場合も、実装者の自由判断を意味しない。選択可能な条件、選択結果を記録する場所、および選択によって変化する成果物を仕様化する必要がある。

説明文、コメント、サンプルコードと規範要件が矛盾する場合は、承認済みの要件ID、機械可読設定、Schemaおよび対応表を優先する。矛盾自体は仕様欠陥として記録し、無記録で解釈してはならない。

### 25．JSONとは何か

JSONは、プログラム間で構造化されたデータを受け渡す形式である。

例えば、permission expectationを次のように表現できる。

```json
{
  "osm_way_id": "2001",
  "direction": "forward",
  "lane_position": 0,
  "expected_vclasses": ["bus", "taxi"]
}
```

この例では次を表す。

* `osm_way_id`は対象となるOSM Wayを表す。
* `direction`はOSMのforward方向を表す。
* `lane_position`はOSM上の車線位置を表す。
* `expected_vclasses`は期待される車両クラスの配列である。

---

### 26．JSON Schema

JSON Schemaは、JSONに必要な項目、型、許容値を機械的に検査するための規則である。

例えば次を確認できる。

* `osm_way_id`が必ず存在している。
* `direction`が`forward`または`backward`である。
* `lane_position`が0以上の整数である。
* `expected_vclasses`が文字列の配列である。
* 未知の項目が追加されていない。

JSON Schemaは計算方法を定義しない。

```text
規範仕様書
＝ 何をどのように判断するかを定義する。

JSON Schema
＝ 入力と出力をどの形式で渡すかを定義する。
```

---

### 27．設定ファイル

`sumo_network.yml`は、承認済みの設定値をプログラムが読み取れる形で保存する。

例えば次を記録する。

* 対象地域を記録する。
* 使用するSUMO版を記録する。
* 管理対象vClassを記録する。
* 許可する属性状態を記録する。
* typemapの場所とSHA-256を記録する。
* readiness gateの条件を記録する。

長い説明や処理の理由はMarkdown仕様書に書き、YAMLには機械が使用する値と対応要件IDを保存する。

---

### 28．バージョン管理

実装を始める際は、コードと仕様の変更履歴を保存する必要がある。

Gitなどのバージョン管理を使用すると、次を確認できる。

* いつコードが変更されたかを確認できる。
* 誰がどの箇所を変更したかを確認できる。
* 変更前の状態へ戻せる。
* 仕様変更と実装変更を対応させられる。
* 特定の研究結果がどのコード版から生成されたかを確認できる。

コードのcommit IDは、Build Manifestへ記録する。

---

### 29．SHA-256とコンテナdigest

SHA-256は、ファイル内容から計算される識別値である。

内容が変われば、通常は異なる値になる。

次の確認に使用する。

* 入力OSMが変更されていないことを確認する。
* typemapが承認済み版と一致することを確認する。
* JSON Schemaが承認済み版と一致することを確認する。
* TLS Review対象のConnection集合が変化していないことを確認する。

同じ意味のXMLでも改行や属性順が異なればSHA-256は変わる。

そのため、次を区別する。

* 意味的決定性は、Edge、Lane、permissionなどの意味が一致することを表す。
* バイト決定性は、ファイル内容が文字単位で一致することを表す。

初期段階では意味的決定性を必須とし、必要な場合にcanonical serializationを定義してバイト決定性を追加する。

---

### 30．Manifest

Manifestは、一回の処理で使用した入力、環境、コマンド、出力をまとめた記録である。

例えば次を保存する。

* 入力ファイル名とSHA-256を保存する。
* 設定ファイルのIDとバージョンを保存する。
* コードのcommit IDを保存する。
* SUMOと依存ライブラリのバージョンを保存する。
* コンテナdigestを保存する。
* 実行コマンドを保存する。
* 出力ファイル名とSHA-256を保存する。
* 実行結果とFailure Codeを保存する。

Manifestは、「この成果物を何から作ったか」を証明する記録である。

---

### 31．Audit

Auditは、道路、Lane、Connectionごとの判断内容を保存する記録である。

例えば次を保存する。

```text
OSM Way ID：2001
元の車線数：欠損
採用車線数：2
値の状態：structural_placeholder
適用規則：LANE-RULE-004
```

Manifestが実行全体を記録するのに対し、Auditは個別判断の内容を記録する。

```text
Manifest
＝ 何を使用して処理全体を実行したかを示す。

Audit
＝ 各道路や車線をどう判断したかを示す。
```

---

### 32．Failure Codeと検査順序

Failure Codeは、処理を停止した理由を一意に表す。

```text
PM003 missing_orig_id
PM004 ambiguous_edge_direction
PM005 lane_count_mismatch
PM006 unknown_vclass
```

一つの入力に複数の問題がある場合、どの問題を先に報告するかを固定しなければ、実装ごとに停止理由が変わる。

そのため、検査順序も仕様化する。

```text
1．ファイルを読み込む。
2．JSON SchemaまたはXML Schemaを検査する。
3．schema versionを検査する。
4．config IDとSHA-256を検査する。
5．全体の前提条件を検査する。
6．Edge Mappingを行う。
7．Edge Directionを判定する。
8．Lane Mappingを行う。
9．Permissionを反映する。
10．Connectionを処理する。
11．TLS Reviewへ引き継ぐ。
```

複数エラーを一度に報告する場合は、エラーコードの並び順も固定する。

---

### 33．原子的書込み

原子的書込みとは、出力ファイルを途中状態のまま正式ファイルとして残さない書込み方法である。

例えば、直接`formal.net.xml`へ書き込み、処理途中で停止すると、不完全なファイルが残る可能性がある。

安全な方法では、最初に一時ファイルへ書き込み、すべての処理が成功した後に正式なファイル名へ置き換える。

これにより、途中まで生成されたファイルを誤って研究へ使用することを防ぐ。

---

## 第V部　検証を始めるときに理解する内容


### この章群で理解すること

第34章から第42章では、生成システムが正しく動くことと、生成されたモデルが研究目的に対して妥当であることを、どのように分けて確認するかを学ぶ。また、テスト用入力であるFixture、期待結果であるOracle、要件とテストの対応、および次工程へ進めるかを判定するReadiness Gateの関係を理解する。

検証の基本構造は次のとおりである。

```text
要件
  └─ 実装が満たすべき動作を定義する。
       ↓
Fixture
  └─ 特定の要件を確認するための固定入力を与える。
       ↓
Oracle
  └─ その入力に対する期待出力または期待停止理由を定義する。
       ↓
テスト実行
  └─ 実装結果とOracleを比較する。
       ↓
Verification
  └─ 仕様どおりに作られているかを判定する。
       ↓
Readiness Gate
  └─ 必要な成果物と検査が揃ったかを判定する。
       ↓
Validation
  └─ 研究目的に必要な現実を十分に表すかを独立データで評価する。
```

各概念の違いは次のとおりである。

| 概念 | 答える問い | 具体例 |
|---|---|---|
| Verification | 仕様で決めたものを正しく実装・生成できたか。 | `oneway=-1`を規則どおり反転し、Lane数不一致で指定Failure Codeを返すかを確認する。 |
| Validation | 生成したモデルが研究目的に必要な現実を十分に表現しているか。 | 独立した道路資料、交通量、速度または旅行時間と比較し、東京の交通条件として妥当かを確認する。 |
| Fixture | 一つまたは少数の要件を検査するために固定した小規模入力である。 | 2車線道路、Way分割、未知`vClass`、TLS link不一致等を最小構成で表す。 |
| Oracle | Fixtureに対して正しいと事前に定めた出力または停止理由である。 | 期待XML、期待JSON、期待Audit、期待Failure Codeおよび出力ファイルの有無を定める。 |
| テスト | 実装を実行し、実結果をOracleや性質と比較する手続である。 | 単体、統合、Runtime、回帰の各テストを目的に応じて使い分ける。 |
| Readiness Gate | 必要な入力、検査、承認およびhash整合が揃った場合だけ、次工程への移行を認める規則である。 | 未解決属性、BLOCKING Warning、未承認TLS Reviewまたは`structural_placeholder`が残る場合、Final Buildを開始させない。 |

VerificationとValidationは、対象と根拠が異なる。仕様で「OSMの`oneway=-1`はNode順と逆方向の`edge`として生成する」と定めた場合、その規則どおりに生成されたかを確認するのがVerificationである。一方、そのOSM記述自体が現実の道路方向と一致しているかを、道路管理資料や現地確認等で評価するのがValidationである。Verificationに合格しても、入力またはモデル化方針が現実に適しているとは限らない。

Fixtureを小さく作る理由は、失敗原因を限定するためである。大田区全体のOSMでLane Mappingのテストを行うと、道路分割、複雑なrelation、欠損タグ、信号構造等が同時に影響し、どの要件が原因で失敗したか特定しにくい。確認したい条件だけを含む最小入力を用いることで、一つの要件と一つの期待結果を対応付けられる。

Oracleは実装とは独立に作成する必要がある。実装コードを実行して得た出力を、そのまま期待結果として保存すると、実装の誤りを正解として固定する可能性がある。Oracleは仕様から導出し、必要に応じて手計算、Schema検査、固定SUMOによる読込みおよび第三者レビューによって確認する。

Readiness Gateは、テストの合否一覧を人が眺めるだけのチェックリストではない。次工程の開始条件を機械的に判定する統制点である。例えば、ResolverとMaterializerが成功していても、TLS Reviewのhashが現在の`connection`集合と一致しなければ、Final Buildへ進めてはならない。これにより、不完全または旧版の中間成果物が正式ネットワークへ混入することを防ぐ。


### 34．VerificationとValidation

VerificationとValidationは異なる。

#### Verification

Verificationは、仕様や設計どおりに実装されているかを確認する。

例えば次を確認する。

* `oneway=-1`を規則どおり反転しているかを確認する。
* Lane数不一致で指定Failure Codeを返すかを確認する。
* 指定Laneへ期待permissionが設定されるかを確認する。
* 同じ入力から同じ意味的出力が得られるかを確認する。

Verificationの問いは、次である。

> 作ろうと決めたものを、正しく作れているか。

#### Validation

Validationは、作ったモデルが研究目的に対して現実を十分に表現しているかを確認する。

例えば次を確認する。

* 生成された道路方向が現実と一致するかを確認する。
* 車線数や速度が現地条件と一致するかを確認する。
* 交通量や旅行時間が観測値に近いかを確認する。
* 信号設定が対象時間帯の交通を表現できるかを確認する。

Validationの問いは、次である。

> 研究目的に必要な現実を、十分に表現できているか。

本仕様書が主に扱うのは道路ネットワーク生成のVerificationである。交通量や渋滞のValidationは、後続の交通モデル工程で扱う。

---

### 35．テストの種類

#### 35.1 単体テスト

単体テストは、一つの関数や小さな処理単位を確認する。

例えば次を確認する。

* `yes`を一方通行として解析できるかを確認する。
* `40 mph`を規則どおり変換できるかを確認する。
* 未知vClassを検出できるかを確認する。
* vClassの出力順を固定できるかを確認する。

#### 35.2 統合テスト

統合テストは、複数の処理を接続したときに正しく動くかを確認する。

例えば次を確認する。

* Resolver出力をMaterializerが読み取れるかを確認する。
* Edge削除に伴ってConnectionが削除されるかを確認する。
* Connection変更によってTLS Reviewがinvalidatedになるかを確認する。

#### 35.3 Runtime Test

Runtime Testは、固定版SUMOを実際に使用して外部挙動を確認する。

例えば次を確認する。

* 出力XMLがSUMO XSDへ適合するかを確認する。
* `netconvert`が正常終了するかを確認する。
* SUMOが生成`net.xml`を読み込めるかを確認する。
* SUMO 1.24.0でLane indexや元ID保持が想定どおりかを確認する。

#### 35.4 回帰テスト

回帰テストは、コード変更によって過去に正しかった動作が壊れていないかを確認する。

承認済みfixtureを毎回実行し、期待結果との差を確認する。

---

### 36．Fixture

Fixtureは、特定要件を確認するために作成する、小さく固定された入力データである。

大田区全体のOSMをテストに使用すると、入力が複雑すぎて問題原因を特定しにくい。

Fixtureでは、確認したい条件だけを含める。

例えば次を作る。

* 一つのOSM Wayが一つのSUMO Edgeになるケースを作る。
* 一つのWayが複数Edgeへ分割されるケースを作る。
* Lane数が一致しないケースを作る。
* 一部Laneだけがバス専用になるケースを作る。
* Edge内の全Laneが通行不能になるケースを作る。
* Connection変更でTLS Reviewが無効になるケースを作る。

Fixtureは正常、境界、異常の三種類へ分ける。

---

### 37．Oracle

Oracleは、Fixtureに対して期待する正解である。

Oracleには次を含められる。

* 期待するXMLを含める。
* 期待するJSONを含める。
* 期待するAuditを含める。
* 期待するFailure Codeを含める。
* 出力ファイルを残すかどうかを含める。

Oracleを実装コードから生成してはならない。

実装とOracleに同じ誤りが入ると、誤った動作でもテストが合格するためである。

Oracleは仕様に基づいて独立に作成し、Schema検査、SUMO XSD検査、固定SUMOでの読込み、独立レビューを行う。

---

### 38．正常・境界・異常テスト

一つの要件について、可能な限り三種類のテストを用意する。

例えばLane Mapping要件では、次のように設計する。

#### 正常テスト

期待Lane数とSUMO Lane数が一致し、正しいLaneへpermissionが設定されることを確認する。

#### 境界テスト

1 Lane、空のvClass集合、最小座標差など、境界条件で規則どおり動くことを確認する。

#### 異常テスト

期待Lane数とSUMO Lane数が一致しない場合に、指定Failure Codeで停止することを確認する。

正常ケースだけでは、入力が壊れている場合に安全に停止できることを確認できない。

---

### 39．要件・試験対応表

要件・試験対応表は、各要件がどのテストによって確認されるかを管理する。

| 要件ID       | 要件内容           | テストID         | Fixture     | 期待結果        |
| ---------- | -------------- | ------------- | ----------- | ----------- |
| PM-REQ-021 | Edge方向を一意に決定する | PM-TEST-021-A | PM-FX-021-A | forwardを返す  |
| PM-REQ-021 | Edge方向を一意に決定する | PM-TEST-021-B | PM-FX-021-B | backwardを返す |
| PM-REQ-021 | Edge方向を一意に決定する | PM-TEST-021-C | PM-FX-021-C | PM004で停止する  |

対応表を使うことで、テストのない`MUST`を検出できる。

---

### 40．Readiness Gate

Readiness Gateは、必要な成果物、検査および承認が揃っている場合だけ、次の工程への状態遷移を認める判定規則である。単なるチェックリストではなく、後工程の実行可否を機械的に決める入口条件として実装する。

例えば、Final Buildを開始する前に、少なくとも次の条件をすべて満たす必要がある。

* Resolverの処理が成功し、属性監査に未分類の`unresolved`が残っていない。
* 正式利用を停止させる`formal blocker`がゼロである。`formal blocker`とは、未解決属性、Schema不適合、hash不一致、未承認レビューまたはBLOCKING Warningなど、正式利用を禁止する状態である。
* permission期待値が承認済みJSON Schemaへ適合している。
* Permission Materializerが成功し、適用件数、未適用件数および削除件数が監査記録と一致している。
* 必要なTLS Reviewが`reviewed`であり、review manifestの入力hashが現在の`connection`およびTLS入力と一致している。
* すべての入力、設定、Schema、typemapおよび実行環境の識別子とSHA-256が、承認済み値と一致している。
* `structural_placeholder`がFinal Buildの入力に残っていない。構造確認専用値を正式候補へ持ち込んではならない。

一つでも満たさない場合、Final Buildは開始しない。Readiness Gateの判定結果は、合否だけでなく、確認した条件、参照した成果物、hash、時刻およびFailure Codeを記録する。

Readiness Gateは、不完全な中間成果物が正式結果へ混入することを防ぎ、成果物の状態を`provisional`から`formal_candidate`へ無根拠に昇格させないために必要である。

### 41．Warningの扱い

すべてのWarningを同じように扱う必要はない。

Warningは次のように分類する。

* `BLOCKING`は、正式利用を停止させる問題である。
* `ACKNOWLEDGED`は、内容を確認し、理由を記録したうえで許容する警告である。
* `INFORMATIONAL`は、結果へ影響しない情報通知である。

未分類のWarningが残る場合は、`formal_accepted`としてはならない。

SUMO版が変更された場合は、過去に承認したWarningも再確認する。

---

### 42．独立検査

生成処理と検査処理を同じロジックへ依存させすぎると、同じ誤りを見逃す可能性がある。

例えば、MaterializerとPost-build Auditが同じ関数でpermissionを計算すると、その関数に誤りがあっても両者が一致してしまう。

そのため、可能な範囲で次を分離する。

* Materializerは値を設定する。
* Post-build Auditは最終出力を読み取り、期待値と比較する。
* Oracleは実装とは独立に作成する。
* 重要Fixtureは別の観点からレビューする。

完全に別実装へする必要があるかは、重要度と工数を考えて決める。

---

## 第VI部　最初の実践手順

### 43．最初の練習用OSM

最初は大田区全体を使用せず、一本の道路だけを扱う。

```xml
<osm version="0.6">
  <node id="10" lat="35.0000" lon="139.0000"/>
  <node id="11" lat="35.0001" lon="139.0001"/>

  <way id="1">
    <nd ref="10"/>
    <nd ref="11"/>
    <tag k="highway" v="residential"/>
    <tag k="oneway" v="yes"/>
    <tag k="lanes" v="2"/>
    <tag k="maxspeed" v="40"/>
  </way>
</osm>
```

この例について次を確認する。

1. Node 10と11が道路位置を表している。
2. Way 1がNode 10から11へ延びている。
3. `oneway=yes`なのでNode順方向だけに通行できる。
4. 車線数は2本である。
5. 最高速度は40 km/hである。
6. SUMOでは一方向Edgeが作られる。
7. Edge内には2本のLaneが作られる。
8. Lane index 0と1の位置関係を確認する。
9. Permission未指定時のbaselineを確認する。

---

### 44．最初の正常Fixture

次の条件を持つFixtureを作る。

```text
OSM Way：1本
方向：oneway=yes
期待Lane数：2
期待vClass：passenger、delivery
期待結果：二つのLaneへpermissionが設定される
```

確認する内容は次である。

* Resolverが正しいexpectationを生成する。
* Provisional Buildが一方向Edgeと2 Laneを生成する。
* Materializerが二つのLaneへpermissionを設定する。
* Final Buildが成功する。
* Post-build Auditが不一致ゼロを返す。

---

### 45．最初の異常Fixture

正常Fixtureから`lanes=2`の期待値と、SUMO側の実Lane数を意図的に不一致にする。

```text
期待Lane数：2
SUMO実Lane数：1
```

期待結果を次のように定義する。

```text
Failure Code：PM005 lane_count_mismatch
出力XML：正式出力を生成しない
Audit：期待Lane数と実Lane数を記録する
formal_blocker：true
```

このFixtureによって、実装が判断不能な状態を推測で処理せず、正しく停止することを確認する。

---

### 46．最初の実装順序

最初から全機能を実装しない。

次の順序で小さく進める。

1. OSM XMLを読み込む処理を実装する。
2. Node、Way、Tagを取得する処理を実装する。
3. `oneway=yes`と`lanes=2`を解析する処理を実装する。
4. Resolverの最小expectation JSONを出力する。
5. JSON Schemaでexpectationを検査する。
6. 単一WayのProvisional Buildを実行する。
7. OSM WayとSUMO Edgeを対応付ける。
8. Lane数が一致することを検査する。
9. Laneへpermissionを設定する。
10. 正常Fixtureと異常Fixtureを実行する。
11. 固定SUMOでFinal Buildを行う。
12. Post-build Auditで最終結果を確認する。

---

### 47．学習上の完成条件

実装開始前には、少なくとも次の内容を自分の言葉で説明できる必要がある。

* OSMファイルは地図画像ではなく、道路の位置、形状、属性および関係を保持する構造化データである。
* XMLの要素、属性および親子構造が、OSMとSUMOでどのように用いられるかを説明できる。
* OSMの`node`、`way`、`tag`および`relation`の関係を説明できる。
* OSMの`way`とSUMOの`edge`が一対一に対応しない理由を説明できる。
* SUMOの`junction`、`edge`、`lane`、`connection`およびTLSの役割を説明できる。
* `typemap`の既定値は、現実の道路属性を証明する値ではないことを説明できる。
* ResolverがOSM上の期待値を決定し、Permission Materializerがその期待値をSUMO要素へ反映するという責任分離を説明できる。
* `provisional`、`formal_candidate`および`formal_accepted`の違いと、各状態で許可される用途を説明できる。

検証開始前には、少なくとも次の内容を説明できる必要がある。

* Verificationは仕様への適合を確認し、Validationは研究目的に対する現実表現の十分性を確認する。
* 単体テスト、統合テスト、Runtime Testおよび回帰テストが、それぞれ異なる失敗を検出する。
* Fixtureは固定した試験入力であり、Oracleは仕様から独立に定義した期待結果である。
* Manifestは処理全体の来歴を記録し、Auditは個別の判断と変更を記録する。
* Failure Codeと検査順序を固定しなければ、同じ不適格入力でも実装ごとに異なる停止理由が返り得る。
* JSON Schemaはデータ構造を検査するが、属性の計算規則や採用根拠を定義しない。
* Readiness Gateは、未承認または不完全な中間成果物が後工程へ進むことを防ぐ。
* Post-build Auditは検査を行う工程であり、検出した不一致をその場で自動修正してはならない。

### 48．実装上の完成条件

対象範囲について、次の条件をすべて満たす状態を実装完成とする。

* 同じ適格入力、設定、コードおよび実行環境から、同じ意味的出力が得られる。
* 不適格入力は、規定された検査順序に従い、同じFailure Codeと停止理由で終了する。
* 失敗時に途中状態のファイルを正式成果物として残さず、既存の承認済み成果物を破損しない。
* すべての入力、設定、Schema、コード、実行環境、コマンド、ログおよび出力をbuild manifestから追跡できる。
* 各道路属性、`lane` permission、`connection`およびTLS対応の判断をAuditとprovenanceから追跡できる。
* すべての`MUST`および`MUST NOT`に対応する試験が存在し、要件・試験対応表に未対応要件がない。
* すべてのFailure Codeに対応する異常Fixtureが存在する。
* Oracleが実装コードから独立して作成され、承認済み版として固定されている。
* 固定したSUMO環境によるRuntime Testに合格している。
* Post-build AuditでBLOCKING不一致がゼロであり、未分類Warningが存在しない。
* `formal_accepted`への受入判断が、対象`net.xml`のSHA-256とともに記録されている。

「大田区全体のネットワークが一度生成できた」ことだけでは、実装完成とはみなさない。完成の判定対象は、成功結果だけでなく、失敗時の停止、来歴、独立検査および再実行可能性を含む。

### 49．本書の使い方

本書は、基礎概念から正式ネットワークの受入までを段階的に学べるように構成している。

第一段階では、第4章から第13章までを読み、OSM、XML、`node`、`way`、`tag`、SUMO、`edge`および`lane`の関係を理解する。この段階では、実際のOSMファイルと小さなXML例を開き、用語を実データと対応させる。

第二段階では、第14章から第21章までを読み、Resolver、Provisional Build、Permission Materializer、Connection処理、TLS Review、Final BuildおよびPost-build Auditの責任境界を理解する。この段階では、各工程の入力と出力を一枚のデータフロー図として描ける状態を目指す。

第三段階では、第22章から第33章までを読み、規範要件、JSON Schema、設定管理、バージョン管理、Manifest、Audit、Failure Codeおよび原子的書込みを理解する。この段階では、一つの要件を要件ID、停止条件、監査情報および対応テストまで含めて記述する。

第四段階では、第34章から第42章までを読み、Verification、Validation、Fixture、Oracle、テスト、Readiness Gate、Warning分類および独立検査を理解する。この段階では、正常・境界・異常Fixtureを一組設計する。

最後に、第43章以降の単一道路Fixtureを実際に作成し、OSM入力、Resolver、Provisional Build、Permission Materializer、Final BuildおよびPost-build Auditを一度通して実行する。この小さな実験で、成功時の成果物と失敗時の停止記録を確認した後に、大田区全体のネットワーク生成へ進む。
