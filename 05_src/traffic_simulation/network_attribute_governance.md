# 道路属性・外部データ対応・SUMOネットワーク品質管理規約

更新日：2026年7月22日
方針名：`report_then_gate_by_criticality`
適用対象：大田区を起点とする東京交通シミュレーション道路網

## 1. 目的と正本

本規約は、OSM道路属性の欠損、外部データによる補完、道路区間の対応付け、構造確認用・正式実験用SUMOネットワークの分離、停止条件を定める。欠損を隠さず、研究結果に使う道路の属性と来歴を第三者が追跡できることを目的とする。

方針の文章上の正本は本ファイル、機械可読設定の正本は`reproducibility/config/traffic_simulation/sumo_network.yml`とする。両者が矛盾する場合は正式変換を停止し、同じ変更で整合させる。実装順序と研究全体の工程は`implementation_plan.md`に記録する。

## 2. 基本原則

- OSM属性の欠損を一律の停止条件にしない。
- 欠損値、補完値、未解決値、矛盾値、不正値を全件記録する。
- 欠損値をSUMOまたはtypemapの既定値へ黙って渡さない。
- typemapから`speed`、`numLanes`、`oneway`を省略しても欠損検出にはならず、`netconvert`がimporter-levelまたはglobal defaultを適用し得るものとして扱う。特に未解決の`oneway`は一方向edgeとして生成され得る。
- `netconvert`へ渡す保持対象wayは、`lanes`、`maxspeed`、`oneway`の採用値と来歴を必ず持つ。生OSMでの欠損は許容しても、未解決のまま変換へ渡さない。
- 採用値ごとに出典、導出方法、基準日、信頼度、適用範囲を保存する。
- 道路形状と接続関係の基礎データには、日付固定したOSM PBFを使用する。
- DRM-DBおよびDRM-PFは使用しない。
- 外部データをOSM原本へ書き戻さず、OSM wayまたはSUMO edgeに対応する版管理済み補完表として保持する。
- 外部値の存在だけで採用せず、権威性、基準日、区間一致、定義、利用条件、対応付け信頼度を検査する。
- 古い外部データで新しいOSM属性を無条件に上書きしない。

## 3. 値の状態

各道路属性は、次の状態のいずれかを持つ。

| 状態 | 意味 |
|---|---|
| `observed` | 観測された交通状態。規制値や物理属性とは区別する |
| `authoritative_external` | 公的外部データから対応付けた値 |
| `explicit_osm` | OSMに明示された値 |
| `derived_osm_rule` | OSMの暗黙規則から導出した値 |
| `reviewed_manual` | 根拠資料を人が確認して採用した値 |
| `approved_assumption` | 正式に承認し、適用範囲と感度分析条件を持つ研究上の仮定 |
| `derived_validated_model` | 事前定義し、独立した検証記録を持つ補完モデルから導出した値 |
| `structural_placeholder` | 構造確認用ネットワークだけに使う技術的仮置き値 |
| `missing` | 入力に値が存在しない |
| `valid_but_unsupported` | 構文上有効だが現行規則では安全に解釈できない |
| `conditional` | 条件付きであり現行静的表現へ一意に変換できない |
| `directionally_asymmetric` | 方向別値が異なり現行の単一値表現へ変換できない |
| `unresolved` | 採用値が存在しない |
| `conflict` | 複数情報が矛盾し、採否が未決定 |
| `invalid` | 値または属性間関係が不正 |

`structural_placeholder`は実測値、推定値、正式な仮定値ではない。`approved_assumption`と`unresolved`も区別する。

## 4. ネットワークの分離

### 4.1 構造確認用ネットワーク

構造確認用ネットワークは、次の確認だけに使用する。

- 道路接続、方向性、孤立成分、行き止まり
- SUMO CLIによる読み込みと最小起動
- OSMとSUMO道路網の可視化比較
- 暫定経路と事後重要道路の抽出
- ジャンクション、橋梁、トンネル、高架、側道のレビュー対象抽出

非重要道路に限り、版管理された`structural_placeholder`を使用できる。適用したOSM way、属性、値、typemap版を全件記録する。構造確認用ネットワークから得た旅行時間、容量、配送評価、古典・QAOA比較を研究結果として使用しない。

低信頼の外部データ対応候補は、構造確認用ネットワークでも属性の上書きに使わない。OSM値または明示された`structural_placeholder`を使い、低信頼候補はレビュー情報としてだけ保持する。

### 4.2 正式実験用ネットワーク

正式実験用ネットワークでは、全保持道路の`unresolved`、`conflict`、`invalid`および未検証`structural_placeholder`をゼロにする。採用値は、OSM明示値、公的外部値、OSM仕様から一意に導出した値、確認済み手動値、または独立した検証記録を持つ`derived_validated_model`のいずれかとし、全採用値の出典と導出方法を追跡可能にする。道路種別の代表値を置いただけの`structural_placeholder`を正式実験へ昇格させない。

重要道路に`approved_assumption`が残る場合は、適用理由と下限・基準・上限を事前に固定し、正式な結果確定前に感度分析を行う。`structural_placeholder`が残る重要道路を正式実験用ネットワークへ含めない。

構造確認用と正式実験用は、設定ID、出力ディレクトリ、manifest、ネットワークSHA-256を分離し、上書きまたは成果物の混在を禁止する。

## 5. 使用する外部データ

### 5.1 全国道路・街路交通情勢調査

車線数、道路幅員、交通量、旅行速度について、具体的な項目定義を確認した範囲で補完・較正候補に使用する。指定最高速度と一方通行は、箇所別基本表等の具体的なヘッダと定義書で該当項目を確認するまで候補状態に留め、採用値の根拠にしない。調査基本区間とOSM wayの対応付けを行い、調査年とOSM基準日の差、道路改良、規制変更を確認する。

### 5.2 JARTIC交通規制情報

各都道府県警察の交通規制データベースから変換された交通規制情報について、収録内容と利用条件を確認した上で、指定最高速度、一方通行、通行止め、車両通行止め、指定方向、時間帯・曜日・車種別規制の補完候補に使用する。

- JARTIC交通規制情報とリアルタイム交通情報を区別する。
- 法定速度だけが適用され、指定規制がない道路は最高速度データに現れない場合がある。
- データに存在しないことを「規制なし」の証明にしない。
- 月次原本を上書きせず保存し、取得日、対象月、版、SHA-256を記録する。
- 入力漏れ、誤り、規制実施時期とDB更新時期のずれを考慮する。

### 5.3 道路台帳

国、東京都、大田区等の道路管理者別に、最終配送経路、較正区間、独立検証区間、橋梁、トンネル、主要交差点その他の重要道路を個別確認するために使用する。幅員等を確認できても、記載のない法的規制を推測しない。

### 5.4 国土数値情報

国土数値情報N13道路データの2024年度版を、道路分類、幅員区分、道路状態、橋梁・トンネル・地上・高架等の立体関係と階層順を確認する補助データとして使用する。ノード・リンク構造の正本にはしない。幅員区分から正確な車線数を直接決定しない。

### 5.5 全国道路施設点検データベース

橋梁、トンネル、シェッド、大型カルバート等を特定し、構造上重要な道路を判定するために使用する。取得時点の提供範囲、基準日、利用規約を保存する。

### 5.6 空中写真

空中写真は、最終配送経路、較正区間、独立検証区間、または外部データとの対応付けが曖昧な重要道路に限り、次を補助的に確認するために使用する。

- 道路形状
- 中央分離帯
- 本線と側道
- 高架道路と地上道路の位置関係
- 橋梁、トンネル出入口、複雑交差点の物理構造

空中写真の解像度、撮影時点、遮蔽物、道路標示の可視性には限界がある。空中写真だけから指定最高速度、一方通行、通行禁止、時間帯・曜日・車種別規制、信号現示、正確な車線接続を確定しない。判読不能または曖昧な場合は確定値を作らず、`unresolved`、`conflict`または根拠を明示した`approved_assumption`として扱う。

空中写真は`visual_support`として記録し、自動的にOSM形状を上書きしない。提供元の条件により画像を保存できない場合は、URL、画像・タイルID、撮影日、閲覧日、解像度、表示範囲、判読内容、限界、確認者を保存する。

### 5.7 交通量と実走速度

JARTIC等の交通量と実走速度は、SUMOの交通需要設定、較正、独立検証に使用する。観測された実走速度を道路の`maxspeed`へ直接代入しない。

## 6. 属性別の確認規則

### 6.1 `oneway`

次の順で確認する。

1. OSM明示値
2. OSMの暗黙規則
3. 基準日と区間対応を確認した公的規制情報
4. 項目定義を確認した公的規制情報

一般道路で`oneway`が欠損し、暗黙の一方通行規則にも該当しない場合は、OSMデータ消費上の規則として双方向と解釈し、`derived_osm_rule`と記録する。実地確認済みとは扱わない。

明示値は`yes`、`no`、`-1`をOSM上の有効値として識別する。ただし、`-1`は左右・方向依存タグを含む完全な安全変換が未実装であるため、現行版では原wayを変更せず`valid_but_unsupported`として停止する。明示値がない`junction=roundabout`と`highway=motorway`は暗黙の一方通行として`derived_osm_rule`を記録する。`highway=motorway_link`は一般に一方通行であることだけを根拠に自動決定せず、明示値がなければ`unresolved`とする。`oneway`に統計的な`structural_placeholder`を使用しない。複数タグまたは資料が矛盾する場合は`conflict`として停止する。

### 6.2 `lanes`

次を確認する。

1. `lanes:forward`、`lanes:backward`、`lanes:both_ways`等
2. OSMの`lanes`
3. 全国道路・街路交通情勢調査
4. 道路台帳
5. 対象を限定した空中写真による補助確認
6. 構造確認用の非重要道路だけに使用する`structural_placeholder`

`lanes`、方向別車線タグ、`oneway`、中央分離帯、道路形状の間に矛盾がないかを検査する。画像だけで正確な車線接続を確定しない。

構造確認用の補完候補は、固定した大田区OSM抽出の明示値について、道路種別と一方通行・双方向の組合せごとに車線数の一意な最頻値を計算する。標本数30以上、最頻値比率50%以上をともに満たす場合だけ`structural_placeholder`として採用し、同率最頻値、標本不足または比率不足は`unresolved`とする。近い道路種別へ自動的にフォールバックしない。30件と50%は真値ではなく、結果確認前に固定した本研究の運用基準である。

### 6.3 `maxspeed`

次を確認する。

1. OSM明示値
2. 方向別・条件付きタグ
3. JARTIC交通規制情報
4. 警察、道路管理者等の公的資料
5. 法令上の導出規則

`maxspeed:conditional`や複数値を直ちに不正値とせず、方向、時間帯、曜日、車種、条件、区間を確認する。法令から導出する場合は、法令の適用日、対象車種、道路状態の基準日を保存する。

構造確認用の補完候補は、固定した大田区OSM抽出の明示的な数値`maxspeed`について、道路種別ごとに一意な最頻値を計算する。標本数30以上、最頻値比率50%以上をともに満たす場合だけ`structural_placeholder`として採用し、同率最頻値、標本不足または比率不足は`unresolved`とする。近い道路種別へ自動的にフォールバックしない。この値は規制値の推定または東京に対する真値とは扱わず、正式実験へ使用しない。

上記の番号は確認順であり、無条件の上書き順位ではない。複数情報が競合する場合は、法的・管理上の権威性、基準日、区間一致、定義、ライセンス、対応付け信頼度を比較し、機械的に解消できなければ`conflict`とする。

## 7. 外部データとOSMの対応付け

単純な最近傍結合だけで決定しない。少なくとも次を組み合わせる。

- 道路中心線間距離
- 進行方向の差
- 区間重複率
- 路線名と路線番号
- 道路分類
- 立体階層
- 上下線、側道、本線、橋梁、トンネルの区分

対応状態は次に統一する。

| 状態 | 意味 |
|---|---|
| `high_confidence_auto` | 事前規則を満たす高信頼自動対応 |
| `needs_review` | 人手確認が必要 |
| `human_confirmed` | 人手確認済み |
| `human_rejected` | 人手で候補を棄却 |
| `unmatched` | 対応候補なし |
| `conflict` | 複数候補または情報が矛盾 |

高架道路と地上道路が重複する区間、上下線または側道の対応候補が競合する区間、複雑な交差点周辺、立体階層が一致しない区間、第1候補と第2候補の評価差が小さい区間は、自動対応付けの信頼度を低く設定する。

これらが最終配送経路、較正区間、独立検証区間、事前・事後重要道路に含まれる場合は人手確認を必須とする。それ以外は自動採用せず、未確認または低信頼として記録する。低信頼値を構造確認用ネットワークの属性へも採用しない。

対応記録には、候補ID、OSM way ID、外部区間ID、候補順位、中心線距離、方向差、重複率、名称・番号・分類・階層一致、risk reason、判定、理由、確認者、確認日、証拠参照を保存する。

## 8. 道路重要度

属性補完前に事前重要度を判定する。事前重要道路には次を含める。

- JARTIC観測道路
- 全国道路・街路交通情勢調査対象道路
- 主要道路
- 橋梁、トンネル、高架、主要交差点
- 較正区間と独立検証区間

構造確認用ネットワークで暫定配送経路を生成した後、事後重要度を判定する。事後重要道路には次を含める。

- 配送経路に採用された道路
- 複数シナリオで頻繁に使用された道路
- 属性変更が配送経路または評価値へ大きく影響する道路

非重要道路が暫定経路に使われた場合は事後重要道路へ昇格し、正式ネットワーク生成前に属性と対応付けを再検査する。

## 9. 停止・警告条件

### 9.1 即時停止

- 保持対象wayの`lanes`、`maxspeed`、`oneway`に採用値または必須来歴がない
- 不正な車線数、速度、方向値
- 属性間の矛盾
- 方向解釈の失敗
- 出典、理由、基準日、確認者のない手動値
- 検出された誤対応または立体階層の誤り
- 必要な欠損・矛盾・補完レポートを生成できない
- 設定と本規約の矛盾
- `vType`、`vehicle`、`flow`、`trip`の入力に`ignoring`、`custom1`、`custom2`または管理対象外のvClassがある
- `netconvert`ログに未知type、未知compound type、edge追加失敗、または明示的discardと照合できないedge除外がある
- 生成ネットワークのpermissionsがtypemapの基本permissionsを超える、または承認されていないdefault由来値がある

### 9.2 正式実験の停止

- 重要道路に`unresolved`、`conflict`、`invalid`が残る
- 低信頼対応を人手確認せず採用している
- 採用値の基準日または来歴がない
- 重要道路に`approved_assumption`が残るのに、必要な感度分析が未実施
- 正式ネットワークに`structural_placeholder`が残る
- 較正用と独立検証用の地点または期間が分離されていない

### 9.3 警告で継続可能

- 構造確認用ネットワークの非重要道路に`structural_placeholder`がある
- OSM規則により一般道路を双方向と解釈した
- 配送、較正、検証、重要道路に使われない周辺道路に欠損がある

警告で続行しても、欠損・補完レポートへの記録は省略しない。

## 10. ジャンクションと変換環境

- 日本の左側通行を`lefthand=true`で固定し、`netconvert`の右側通行defaultへ委ねない。OSMの一方通行方向自体は反転しない。
- PBFを固定版`osmium`でOSM XMLへ変換し、`netconvert`へPBFを直接渡さない。
- Pythonによる設定検証・前後処理は`analysis`、`netconvert`実行はdigest固定`sumo`サービスに分離する。
- ジャンクションヒューリスティックは10 mの候補生成だけに使用する。
- 正式変換は人手確認済み統合表から作成した`.nod.xml`だけを使用し、自動統合を無効にする。
- OSM信号位置を利用しても、実信号現示、サイクル、オフセットを再現したとは扱わない。
- internal linkを保持し、ランプ・ラウンドアバウトの追加推定を初期版では行わない。
- Uターンは行き止まりだけに許可し、孤立edgeを自動削除しない。
- `ignore-errors`を使用せず、入力・設定・変換エラーはfail-fastとする。
- `osm.lane-access=true`を固定し、way単位とlane単位のaccessタグを持つ小規模fixtureでSUMO 1.24.0の変換結果を検証する。
- `osm.annotate-defaults=true`を固定し、生成ネットワークと実行ログを監査する。ただし、注釈だけを欠損検出の代用にはしない。

SUMO入力で許可するvClassは`sumo_network.yml`の`vehicle_input_policy.allowed_vclasses`だけとする。permissionsを無視できる`ignoring`、研究上の意味を定義していない`custom1`と`custom2`、typemapで許可していない`evehicle`を禁止する。EV配送車は`vClass="delivery"`とSUMO battery deviceの組合せで表し、道路利用区分と電動パワートレインを分離する。入力XML上の直接指定だけでなく、各vehicle、flow、tripが参照するvTypeも解決して検査する。

ネットワークが管理する最大集合8クラスと、用途別に実際に生成する車両集合を区別する。配送経路用途は`delivery`と`truck`、初期背景交通用途は`passenger`、`taxi`、`bus`、`coach`、`delivery`、`truck`、`motorcycle`とする。`moped`は道路permissionsの管理集合には残すが、需要根拠を別途固定するまで背景交通として生成しない。用途別集合を分けても、同じ道路網で管理対象外vClassを許可しない原則は変えない。

OSM access規則は、`access`、`vehicle`、`motor_vehicle`、車種別、方向別、lane別の順に、広い規則から具体的な規則へ上書きして解決する。その後に研究対象集合との積集合を取り、最終permissionsを次で定義する。

```text
P_final = P_research_scope intersect P_OSM_resolved
```

個別タグによる例外を解決する前に全タグを単純な積集合へ入れない。未対応の条件付き規則または解釈不能な上書き関係は`unresolved`とする。前処理でway・方向・laneごとの期待permissionsを保存し、SUMO 1.24.0の生成結果と比較する。importerの結果が一致しない場合は、生成permissionsを期待集合との積集合へ縮小する決定的な後処理だけを許可し、typemapの基本集合を拡張しない。補正後はlane間およびedge間の接続可能性を再検査し、不一致が残れば停止する。

専用バス道路は背景交通用に保持し、現行v1では`bus`だけを許可する。OSMに配送例外が明示されていても、現行bus-only typemapへ後処理で`delivery`を追加しない。例外を採用する場合は、対応するgoverned compound type、根拠、fixtureおよび新しい設定版を先に作成する。

`access=no`、`vehicle=no`、`motor_vehicle=no`、`motorcar=no`、`hgv=no`、`bus=yes`、`delivery=yes`、`access:lanes`、`vehicle:lanes`を含むfixtureを用意し、way単位とlane単位の制約を別々に検証する。生成permissionsがtypemapの基本permissionsを拡張していないことを確認し、意図した縮小と一致しない場合は停止する。

2026年7月18日のfixture実変換では、未知bus compound、`bicycle`および`private`のpermissions追加、`motor_vehicle=no`の期待外処理、欠損属性へのdefault適用を確認したため不合格とした。`oneway`欠損wayは逆方向edgeなしで生成され、`osmDefaults`注釈にも`oneway`は記録されなかった。詳細は単一の時系列記録`03_data/metadata/acquisition/20260718_sumo_tokyo_motorized_typemap_design.md`に残す。この不一致を解決し、同じfixtureが合格するまで正式変換を許可しない。

fixtureは前処理負例とruntime正常系に分離する。必須属性欠損は前処理負例として`netconvert`前に拒否し、runtime正常系には`lanes`、`maxspeed`、`oneway`をすべてmaterializeする。runtime正常系では、way・方向・laneごとの期待permissions、方向edge、車線数、速度および追跡元OSM IDとの完全一致を要求する。管理対象外vClass、予期しない正逆方向edge、permissions不一致および未追跡edgeの許容件数はゼロとする。

### 10.1 設計判断、地域適合性、実装リスク、テスト入力の区別

次の項目を単一の「恣意性」尺度で順位付けしない。影響の大小は、作用経路に対応した感度分析前には確定しない。

| 項目 | 分類 | 現在の位置付け | 主に確認する影響 |
|---|---|---|---|
| SUMO標準`priority` | 地域適合性の制限を伴う設計判断 | SUMO 1.24.0へ固定するが、東京で実証的に較正された値ではない | 交差点通行権、停止、待ち時間、遅延、実現旅行時間 |
| 道路ホワイトリスト | 研究対象範囲の設計判断 | motorized-onlyの基準条件 | 接続成分、到達可能顧客、経路、距離 |
| vClass permissions | 車種別通行条件の設計判断 | 管理対象は8クラス。通常道路は8、motorwayはmopedを除く7、service compoundは2、専用バス道路は1クラス | 車種別利用可能edge、到達可能性、経路、距離 |
| 専用バス道路 | ネットワーク表現上の設計判断 | bus用に保持し、deliveryの進入を許可しない | 背景バス網、配送車の不正進入 |
| typemapでの属性省略 | 根拠付き値を要求する設計判断 | 方針自体は合理的だが、単独では欠損停止を保証しない | validatorと監査が機能する場合のfallback排除 |
| validator・監査未完成 | 実装・品質保証上のリスク | 高リスクであり正式buildを停止する | 誤速度、誤車線数、誤方向、過剰permissions |
| fixture数値 | 合成テスト入力 | 東京代表値ではないが、正式実験から隔離した挙動検査には適合する | 単位変換、単車線・複数車線、方向、欠損、access処理 |

標準`priority`の継承は研究者による結果確認後の個別調整を避け、再現性を高める。一方、上流標準typemapはドイツの市街地外道路向けとして説明されており、東京への地域適合性を保証しない。`priority`はright-of-wayへ影響するが、基準条件では`weights.priority-factor=0`を固定するため、静的な経路コストへpriorityペナルティを直接加えない。シミュレーションでは待ち時間と実現旅行時間が変わり得て、その実現旅行時間で再経路探索する場合には経路へ間接的に影響し得る。

### 10.2 設計感度分析

正式な結論前に、`sumo_network.yml`の`design_sensitivity`へ固定した条件を比較する。結果を確認してから都合のよい条件、指標、閾値を選ばない。

| 要因 | 基準条件 | 代替条件 | 主指標 |
|---|---|---|---|
| `priority` | SUMO 1.24.0標準値 | 全typeを1、固定した3段階階層 | 交差点待ち時間、停止回数、旅行時間、遅延 |
| service permissions | 現在の管理対象allow | deliveryを除外 | delivery利用可能edge、到達可能顧客、経路距離 |
| 専用バス道路 | bus専用で保持 | ネットワークから除外 | bus利用可能edge、配送車進入違反、接続成分 |
| `track` | 除外 | 明示的なmotor_vehicle根拠があるものだけ保持 | 接続成分、到達可能顧客、経路距離 |
| 未解決属性 | 変換前停止 | structural profile限定の明示的placeholder | fallback混入、方向差、容量差、旅行時間差 |

各指標`M`について、基準値が0でなければ`abs(M_alternative - M_baseline) / abs(M_baseline)`を相対変化として報告する。基準値が0の場合は相対変化を未定義とし、絶対差を報告する。「影響が小さい」と判定する数値閾値は、根拠とともに結果確認前に別途登録する。閾値が未登録の間は、相対変化が小さいという合否判定を行わない。

### 10.3 計算機実験における設定の固定・検証方針

本研究は、すべての設定値に唯一の正解が存在するとは仮定しない。公式実装の既定値、標準ベンチマーク、先行研究、対象データからの導出値、または研究目的に基づいて事前定義した値から基準設定を選び、採用理由、版、適用範囲および代替条件を開示する。基準設定に求めるのは東京に対する真値であることではなく、第三者が同じ条件を再構成でき、研究上の仮定と観測値を区別できることである。

今回のXMLおよびSUMOネットワーク設定には、次の手順を適用する。

1. 研究目的と評価対象を定義する。
2. 基準設定、比較する代替設定、評価指標および判定閾値を、主要結果の確認前に固定する。
3. 設定ファイル、入力、前処理、コマンド、ソフトウェア版、seed、実行環境および出力評価方法を保存する。
4. Verificationにより、実装が意図した仕様どおり動くことを自動テストとvalidatorで確認する。
5. Validationにより、研究で主張する現実対象をモデルが必要な範囲で表現しているかを独立した資料または観測と比較する。
6. 結果への影響が大きい可能性があり、自然な値が一意でなく、研究者判断を含み、結論を変え得る設定に限定して感度分析またはrobustness checkを行う。
7. 基準条件と事前登録した代替条件の結果を、都合のよい条件だけ選ばず報告する。

VerificationとValidationを混同しない。前者には、速度単位変換、車線数、方向、道路ホワイトリスト、vClass permissions、未解決属性の停止、fixtureの正式実験からの隔離を含める。後者には、道路延長・道路種別構成・接続性、主要道路の分類、配送地点の到達可能性、および主要地点間の距離・旅行時間が極端に不自然でないことの確認を含める。テストが通ることだけを、東京交通の再現性の証拠とはしない。

本研究の現段階の主張は「東京の公開データを基礎として構成した固定的な評価ネットワーク」に限定する。「東京交通を忠実に再現した」と主張する場合は、車線数・速度分布、交通量、旅行時間、渋滞遅延等について、較正用データと独立検証用データを分離した追加Validationを要求する。

感度分析は設定値を変えたときの結果依存性を調べるものとし、ablation studyは構成要素を除いたときの寄与を調べるものとして区別する。道路ホワイトリスト、配送車permissionsおよび`priority`は前者の主要対象とする。fixtureのIDや合成座標は正式実験へ入らないため感度分析の対象とせず、意図した境界条件を検査できることをVerificationで示す。validatorの有無を比較する場合は性能条件ではなく、品質保証機構の必要性を確認するablationとして扱う。

記録の分担は次のとおりとする。

| 場所 | 記録内容 |
|---|---|
| 論文本文 | 結論に重要な基準設定、採用理由、主要な感度分析および妥当性の制限 |
| 論文付録 | 設定一覧、代替条件、追加結果および詳細な品質指標 |
| リポジトリ | XML、機械可読設定、コード、validator、fixture、manifestおよび来歴 |
| README | 必要環境、再実行手順、正本への導線および現在の実装状態 |

この方針は、設定の恣意性をゼロと主張するものではない。設定選択を追跡可能にし、実装誤りを検出し、主要な判断に対する結果の頑健性と研究主張の適用範囲を示すためのものである。

## 11. 感度分析と古典・QAOA比較

重要道路に`approved_assumption`が残る場合は、下限・基準・上限を事前固定し、配送経路、総走行距離、所要時間、制約充足率、シナリオ充足率、古典手法とQiskit Aer QAOAの比較結果への影響を確認する。

古典手法とQAOAには、同じ道路ネットワーク、車線数、速度上限、一方通行、需要、環境条件、出発時刻、地点間コスト、乱数条件を与える。一方にだけ外部補完、経路救済、再計算を適用しない。

## 12. 保存する来歴と品質指標

OSM、外部データ、空中写真参照、typemap、設定、補完表、SUMOネットワークについて、取得日、基準日、版、URL、ライセンス、SHA-256を保存する。

属性ごとに、way数だけでなく道路延長、道路種別、重要度、配送経路利用回数、route-weighted distanceに占める各状態の割合を集計する。少なくとも次を出力する。

- 欠損、補完、未解決、矛盾、不正の全件表
- 外部データ対応候補と対応状態
- `structural_placeholder`適用表
- 事前・事後重要道路表
- 人手レビュー表
- 構造確認用・正式実験用manifest
- 入力、設定、typemap、補完表、出力ネットワークのSHA-256

## 13. 現在確認されているOSM属性状況

### 13.1 分析対象と再現方法

2026年7月16日スナップショットの大田区取得BBOXについて、正式なアクセス権解決前の初期自動車系道路候補を事前集計した。分析コード、テスト、機械可読な定義は次のとおりである。

- 分析コード：`05_src/traffic_simulation/network/analyze_osm_attributes.py`
- テスト：`05_src/traffic_simulation/validation/test_analyze_osm_attributes.py`
- 定義：`reproducibility/config/traffic_simulation/sumo_network.yml`の`osm_attribute_baseline_audit`
- 入力：`03_data/processed/traffic_simulation/road_network/osm_extracts/osm_ota_ward_20260716.osm.pbf`
- 入力SHA-256：`10d554a13e89b815ca416c272d23d9477d52e312fa3d299f466fb3c01cf9d041`
- 出力：`03_data/processed/traffic_simulation/validation/ota_ward_20260716_osm_attribute_baseline.json`（生成物のためGit管理外）
- 使用ツール：`osmium version 1.15.0`

実行コマンドは次のとおりである。

```bash
docker compose run --rm analysis \
  python -m traffic_simulation.network.analyze_osm_attributes --overwrite

docker compose run --rm analysis \
  python -m pytest \
  05_src/traffic_simulation/validation/test_analyze_osm_attributes.py -q
```

コードは、まず`osmium tags-filter`で`highway`タグを持つwayを抽出し、`osmium export`でLineStringのGeoJSON sequenceへ変換する。その後、設定に固定した次の14種類だけを候補にする。

`motorway`、`motorway_link`、`trunk`、`trunk_link`、`primary`、`primary_link`、`secondary`、`secondary_link`、`tertiary`、`tertiary_link`、`residential`、`unclassified`、`living_street`、`service`

単純形式の有効値は次のように判定する。この判定は正式な属性解決ではなく、明示タグの基礎的な充足状況を測るための厳格な基準である。

- `lanes`：1以上の整数文字列
- `maxspeed`：単位を伴わない1以上の数値文字列。km/hとして扱う
- `oneway`：`yes`、`no`、`-1`のいずれか
- タグがないか空文字なら`missing`、タグがあって上記形式に合わなければ`invalid`
- この基礎集計では`missing`と`invalid`を合わせて`unresolved`と呼ぶ

道路延長はGeoJSONの各LineStringについて隣接座標間のHaversine距離を合計した。地球半径は6,371,008.8 mに固定した。way数と延長を併記することで、短い生活道路が多数を占める場合にway数だけで欠損影響を過大評価しないようにした。

### 13.2 集計結果

対象は26,201 way、概算延長3,053.925 kmであった。

| 属性 | 欠損・不正way | 割合 | 対象延長割合 |
|---|---:|---:|---:|
| `lanes` | 22,630 | 86.37% | 76.96% |
| `maxspeed` | 23,128 | 88.27% | 78.39% |
| `oneway` | 19,753 | 75.39% | 65.48% |
| いずれか未解決 | 24,823 | 94.74% | 未集計 |
| 3属性すべてが単純形式で有効 | 1,378 | 5.26% | 未集計 |

`maxspeed`の内訳は欠損23,119 way、不正9 wayであり、不正値は複数値を含む`50;40`であった。他の2属性はこの単純形式判定における不正値がなく、表の値はすべて欠損である。

未解決属性の組合せは次のとおりである。

| 未解決属性 | way数 | 割合 |
|---|---:|---:|
| `lanes,maxspeed,oneway` | 17,838 | 68.08% |
| `lanes,maxspeed` | 3,848 | 14.69% |
| なし | 1,378 | 5.26% |
| `maxspeed` | 826 | 3.15% |
| `oneway` | 751 | 2.87% |
| `maxspeed,oneway` | 616 | 2.35% |
| `lanes,oneway` | 548 | 2.09% |
| `lanes` | 396 | 1.51% |

少なくとも1属性が未解決となった割合は、`service`で99.80%、`residential`で99.73%、`unclassified`で98.64%、`tertiary`で82.38%、`primary`で36.30%、`trunk`で33.67%であった。主要道路ほど明示属性が比較的多い一方、候補全体の大部分を占める生活・サービス道路では少ない。

関連タグも別途数えた。`lanes`がない一方で方向別車線タグがあるwayは2、`width`があるwayは213、`lane_markings`があるwayは884であった。`maxspeed`がない一方で`maxspeed:type`または`maxspeed:advisory`等の速度関連タグがあるwayは13であった。これらは自動的な補完値ではなく、次段階の解釈・矛盾検査の候補である。`oneway`がない`motorway`・`motorway_link`および`junction=roundabout`は0 wayであった。

### 13.3 解釈上の制限

- この値は「道路の94.74%が使用不能」という意味ではない。OSM暗黙規則、外部データ、人手レビュー、構造確認用placeholderをまだ適用していない。
- 対象は初期道路種別による候補であり、`access`、`motor_vehicle`、`vehicle`、SUMO vClassによる最終的な通行可否を解決していない。
- 大田区行政界そのものではなく、行政界の取得BBOXに交差する完全なwayを対象とするため、区外部分を含む。
- 集計単位はOSM wayであり、道路名単位、実道路区間単位、SUMO edge単位ではない。1本の道路が複数wayに分割される場合がある。
- Haversine延長は地表面上の概算であり、投影座標による測地精密計算やSUMO変換後edge長とは一致しない。
- `50;40`、条件付き速度、方向別属性は情報がないのではなく、単一値へ未解決である。正式処理では直ちに棄却せず内容をレビューする。
- 母集団、判定規則、入力PBF、コードのいずれかを変更した集計値を比較する場合は、設定版とmethod versionを更新し、同じ結果として混在させない。

## 14. 実装前の未確定事項

次はコード実装またはデータ取得前に、設定として追加固定する。

- 自動対応付けの評価式と高・低信頼閾値
- 第1候補と第2候補の競合判定閾値
- 主要道路と頻繁使用道路の機械判定条件
- `structural_placeholder`の具体値と適用対象
- 重要道路に残る`approved_assumption`の感度分析範囲
- 外部データ別の基準日競合規則
- 構造確認用・正式実験用の出力命名規則の完全なスキーマ

未確定値をPythonコードへ暗黙に埋め込まない。決定時は本規約と`sumo_network.yml`の版を同時に更新する。

## 15. 参照先

- SUMO OSM import: <https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html>
- OSM `oneway`: <https://wiki.openstreetmap.org/wiki/Key:oneway>
- OSM `access`: <https://wiki.openstreetmap.org/wiki/Key:access>
- OSM `lanes`: <https://wiki.openstreetmap.org/wiki/Key:lanes>
- OSM `maxspeed`: <https://wiki.openstreetmap.org/wiki/Key:maxspeed>
- NeurIPS Paper Checklist: <https://neurips.cc/public/guides/PaperChecklist>
- ACM Artifact Review and Badging: <https://reviewers.acm.org/training-course/artifact-review-and-badging>
- IEEE Research Reproducibility: <https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/research-reproducibility/>
- IEEE 1012 System, Software, and Hardware Verification and Validation: <https://standards.ieee.org/ieee/1012/7324/>
- ACM SIGSOFT Empirical Standards: <https://www2.sigsoft.org/EmpiricalStandards/about/>
- JARTICオープンデータ: <https://www.jartic.or.jp/service/opendata/>
- JARTIC交通規制情報説明書: <https://www.jartic.or.jp/d/opendata/typeD_kisei_73.pdf>
- 令和3年度全国道路・街路交通情勢調査: <https://www.mlit.go.jp/road/census/r3/index.html>
- 国土数値情報N13道路データ: <https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N13-2024.html>
- 全国道路施設点検データベース: <https://road-structures-map.mlit.go.jp/>
- 大田区道路台帳: <https://www.city.ota.tokyo.jp/seikatsu/sumaimachinami/douro_kouen_kasen/douro/dourodaicho.html>
