# 版16道路属性の初期正式仕様案（履歴）

> **文書状態:** 一部採用後に置き換えられた提案履歴
> **対象:** 版16の正式用道路属性解決
> **基準日:** 2026年7月16日
> **実装可否:** 本文書を実装根拠として使用してはならない

承認済みの後続方針は
`10_approved_attribute_resolution_policy.md`および
`reproducibility/config/traffic_simulation/approved_attribute_resolution_policy_v17.yml`
に移した。本文書の4,500 kg車両案、一次元的なaccess優先順および未確定状態は、
当時の提案履歴としてのみ保持する。今後の実行順序は
`../attribute_resolution_execution_procedure.md`に定める。

## 目次

- [1. この文書の位置付け](#1-この文書の位置付け)
- [2. 一次資料で確認した事項](#2-一次資料で確認した事項)
- [3. 採用候補となる中核方針](#3-採用候補となる中核方針)
- [4. 基準シナリオ](#4-基準シナリオ)
- [5. 管理配送車両](#5-管理配送車両)
- [6. 解決状態と値の由来](#6-解決状態と値の由来)
- [7. 停止単位](#7-停止単位)
- [8. 元道路と方向付き区間](#8-元道路と方向付き区間)
- [9. 逆向き一方通行](#9-逆向き一方通行)
- [10. 方向別車線](#10-方向別車線)
- [11. 通行許可](#11-通行許可)
- [12. 条件付き規制](#12-条件付き規制)
- [13. 速度](#13-速度)
- [14. 既存契約からの変更](#14-既存契約からの変更)
- [15. 採用前に追加決定が必要な事項](#15-採用前に追加決定が必要な事項)
- [16. 採用判定](#16-採用判定)
- [17. 参照資料](#17-参照資料)

## 1. この文書の位置付け

本文書は、`attribute_resolution_decisions_to_finalize.md`に列挙した未決定事項に対する
初期案を整理する。研究上選択する基準シナリオと、OSM・法令・登録済み証拠から決まる
道路属性を区別する。

本文書の一部は後続の版17方針へ採用されたが、内容全体は正式仕様ではない。後続方針と
異なる値または規則を本文書から採用してはならない。既存の停止記録を本文書だけで
採用値へ変更してはならない。

## 2. 一次資料で確認した事項

- 内閣府の2026年祝日一覧では、7月16日は祝日ではない。7月の海の日は7月20日である。
- 2026年7月16日は木曜日である。
- 警察庁は、生活道路に関する新しい法定速度を2026年9月1日から適用するとしている。
- 警察庁は、中央線・車両通行帯がある一般道路、往復方向が構造分離された一般道路等を
  変更後も60 km/hとなる道路として区別している。
- 道路標識または道路標示による指定速度がある場合は、その指定速度が法定速度より
  優先される。
- OSMの`hgv`は大型貨物車向けの通行制限キーであり、多くの国では許容最大質量
  3.5トン超の貨物車を対象とする。ただし、日本での研究用対応は研究規則として
  明示的に固定する必要がある。
- SUMOの道路typeが持つ既定速度はシミュレーション設定値であり、OSM明示値、
  指定速度または法定速度の確認済み値とは区別する。

## 3. 採用候補となる中核方針

| 対象 | 採用候補 |
|---|---|
| 基準日時 | 2026年7月16日09:00から17:00、`Asia/Tokyo`、平日、非祝日 |
| 管理配送車両 | 最大積載量2,000 kg、車両総重量上限4,500 kgの研究用配送貨物車 |
| 解決記録 | 解決状態と値の由来を別フィールドにする |
| 停止単位 | 属性が影響する最小の管理単位で停止する |
| 方向モデル | 原典OSM Wayを不変に保持し、方向付き区間を派生成果物として生成する |
| `oneway=-1` | 元Wayは反転せず、逆方向の方向付き区間だけを生成する |
| 方向別車線 | 入力から数学的に一意となる場合だけ導出する |
| 通行許可 | 車線・方向・車種の具体的なタグから一般タグへ評価する |
| 条件付き規制 | 対応構文を限定し、運行時間中に結果が変化する場合は停止する |
| 速度 | 適用可能な公式証拠、OSM数値、法令導出の順に評価する |

## 4. 基準シナリオ

採用候補は次のとおりとする。

```yaml
scenario_profile_id: tokyo_delivery_v16
source_context:
  osm_snapshot_date: "2026-07-16"
simulation_period:
  timezone: "Asia/Tokyo"
  start_at: "2026-07-16T09:00:00+09:00"
  end_at: "2026-07-16T17:00:00+09:00"
  duration_minutes: 480
  day_type: weekday
  public_holiday: false
  school_holiday_condition: not_evaluated
```

学校休業日を参照する条件式は、`not_evaluated`を偽と解釈せず、対応不能として停止する。
タイムゾーン、開始・終了時刻、祝日暦または法令適用日が欠ける場合も停止する。

この基準シナリオは研究上の選択である。道路規制の意味や法令上の速度そのものを
研究上の選択として変更するものではない。

## 5. 管理配送車両

採用候補は次のとおりとする。

```yaml
vehicle_profile_id: managed_delivery_truck_v1
vehicle_role: managed_delivery_vehicle
trip_purpose: delivery
weight:
  maximum_weight_rating_kg: 4500
  unladen_weight_kg: 2500
  maximum_payload_kg: 2000
  actual_payload_policy: remaining_load
  actual_weight_formula: unladen_weight_kg + actual_payload_kg
hazardous_goods: false
permit_ids: []
```

本プロファイルは実在車両の諸元ではなく研究用モデル車両である。OSM access階層では、
本車両を`vehicle`、`motor_vehicle`、`goods`および研究上の`hgv`対応対象として
評価する。ただし、複数キーをすべて真として結合するのではなく、具体性の高い
適用可能なキーを選択する。

重量条件は次の値と比較する候補とする。

| OSM条件 | 比較候補 |
|---|---|
| `maxweight` | 当該時点の実重量 |
| `maxweightrating` | 車両総重量上限 |
| `maxaxleload` | 登録済み軸重 |
| `maxheight` | 登録済み車高 |
| `maxwidth` | 登録済み車幅 |
| `maxlength` | 登録済み車長 |

軸重、車高、車幅または車長を参照する規制があり、対応する車両入力がなければ停止する。

## 6. 解決状態と値の由来

解決状態と値の由来を分離する案を採用候補とする。

```yaml
resolution_status:
  - resolved
  - not_applicable
  - unresolved
  - conflict
  - unsupported
  - invalid

value_origin:
  - source_explicit
  - source_normalized
  - rule_derived
  - evidence_derived
  - model_assumed
```

正式用で値を採用できるのは、`resolution_status=resolved`かつ
`value_origin`が`source_explicit`、`source_normalized`、`rule_derived`または
`evidence_derived`の場合に限る。`model_assumed`は正式用で禁止する。

既存Schemaの`value_state`は状態と由来を一つの列挙型に含むため、この案を採用する
場合はSchema版を更新し、旧成果物との互換性と移行規則を定義する。

## 7. 停止単位

停止範囲と利用不能になる処理を別々に記録する案を採用候補とする。

```yaml
blocking_scope:
  - source_way
  - directed_segment
  - lane
  - connection
  - vehicle_profile
  - time_interval
  - attribute_only

blocked_capabilities:
  - topology
  - routing
  - travel_time
  - lane_capacity
  - lane_connection
  - formal_sumo_simulation
```

| 未解決属性 | 最小停止単位 | 停止する主要処理 |
|---|---|---|
| 走行方向 | 元道路 | topology、routing、formal SUMO simulation |
| 通行許可 | 方向付き区間と車両プロファイル | routing、formal SUMO simulation |
| 速度 | 方向付き区間 | travel time、routing、formal SUMO simulation |
| 方向別車線数 | 方向付き区間 | lane capacity、lane connection |
| 車線別規制 | 車線 | lane connection、formal SUMO simulation |
| 右左折規制 | 接続 | routing、formal SUMO simulation |
| 条件付き規制 | 区間、車両、時間区間 | routing、formal SUMO simulation |

一部機能に利用可能であっても、一件でも正式用阻害項目がある成果物は
`complete=false`とし、正式SUMO道路網の入力にはしない。

## 8. 元道路と方向付き区間

原典OSM Way、分割区間、方向付き区間を分ける案を採用候補とする。

```text
way/{osm_way_id}/segment/{4桁連番}/direction/{F|B}
```

- `F`は元Wayの構成点順と同じ走行方向を表す。
- `B`は元Wayの構成点順と逆の走行方向を表す。
- 通常一方通行と逆向き一方通行で識別子形式を変えない。
- SUMO edge IDは方向付き区間識別子から機械的に生成する。
- 元Way識別子、元構成点順、分割位置、走行構成点順および変換規則を道路対応履歴に
  保存する。

交差点等でWayを分割する具体的な分割規則は、採用前の追加決定事項とする。

## 9. 逆向き一方通行

生成方向は次の案を採用候補とする。

| `oneway` | 生成方向 |
|---|---|
| `yes`、`1`、`true` | `F`だけ |
| `-1`、`reverse` | `B`だけ |
| `no`、通常解釈で双方向となる欠損 | `F`と`B` |
| 不正値 | 生成せず停止 |

`oneway=-1`では原典Wayを書き換えず、`B`の方向付き区間だけを生成する。方向依存タグは
値を書き換えず、元Wayに対する方向、適用する方向付き区間、走行方向に対する意味を
来歴として記録する。

対応候補となる方向構文には、`:forward`、`:backward`、`:lanes:forward`、
`:lanes:backward`およびそれらと`:conditional`の組合せを含める。未知または曖昧な
方向構文は停止する。

右左折規制とバス向け規制の接続対応規則はまだ不足しているため、
`oneway=-1`の正式実装は開始しない。

## 10. 方向別車線

次の整合式を採用候補とする。

```text
lanes = lanes:forward + lanes:backward + lanes:both_ways
```

双方向道路では、二つ以上の独立した値から残りの一値が一意かつ非負に導ける場合だけ
算術導出を許可する。総数しかない場合の均等配分または最頻値補完は禁止する。

一方通行では、一般`lanes`を存在する方向付き区間の車線数として扱う候補とする。
`oneway=yes`では`F`、`oneway=-1`では`B`へ割り当てる。

版16正式用では、`lanes:both_ways`が正の値なら対応不能として停止する。欠損を
自動的に0とみなすかは、採用前の追加決定事項とする。

## 11. 通行許可

一般タグより具体的な車種・方向・車線タグを優先する方針を採用候補とする。ただし、
優先順位はタグ名の固定順位だけでなく、車線、方向、車種、条件付きという直交する
具体性軸を比較できる決定表として実装する。

基準シナリオでは、次のaccess値を候補とする。

| 値 | 基準シナリオの候補結果 |
|---|---|
| `yes`、`permissive`、`designated` | 通行可能 |
| `no`、`private` | 通行不可 |
| `permit` | 許可IDがないため通行不可 |
| `destination` | 制限区域内が目的地の場合だけ通行可能 |
| `delivery` | 制限区域内への配送の場合だけ通行可能 |
| `customers` | 対象顧客施設が目的地の場合だけ通行可能 |
| 未登録値 | 対応不能として停止 |

具体的な車種タグが一般`access`を上書きできる案を採用候補とする。同じ具体性で異なる
結果がある場合は、安全側への暗黙変換をせず競合停止とする。

目的地区域の境界、経路が区域内配送か通過かを判定する方法は追加決定事項とする。

## 12. 条件付き規制

版16で対応する構文を限定する案を採用候補とする。

対応候補:

- 曜日範囲
- 時計時刻範囲
- 日本の祝日
- 明示日付範囲
- 登録済み車種
- 重量比較
- 登録済み利用目的
- セミコロンで区切られた複数規則
- 論理積

対応不能として停止する候補:

- 学校休業日
- 日出・日没
- 天候
- 季節的な自然条件
- 明示的な論理和と否定
- 入れ子括弧
- 未登録トークン

評価は、無条件値の取得、構文解析、文脈代入、変化点列挙、全運行期間での結果比較、
同時適用規則の競合検査の順に行う。09:00から17:00の途中で結果が変化する場合は、
版16の静的正式道路網では停止する。同時に有効な規則が同じ結果なら採用候補とし、
異なる結果なら競合停止とする。

時刻境界の包含規則、夜間をまたぐ範囲、重量単位、省略単位、セミコロンの正式文法は
追加決定事項とする。添付案の`qest_conditional_v1`は識別子の意図が確認できないため、
正式なプロファイル識別子として採用しない。

## 13. 速度

速度候補は次の優先順位とする案を採用候補とする。

1. 区間、方向、期間が一致する道路標識または道路管理者の公式資料
2. OSMの方向別数値`maxspeed`
3. OSMの一般数値`maxspeed`
4. 適用日付き法令、確認済み道路状態、`maxspeed:type`等からの導出
5. 未解決停止

方向別数値があれば対応方向へ適用し、方向別数値がない場合だけ一般数値を各方向へ
適用する。`maxspeed:type=JP:urban`を固定速度へ直接変換しない。

版16の基準日は2026年7月16日であり、2026年9月1日施行の変更前である。ただし、
この事実だけから`JP:urban`を一律60 km/hへ変換しない。指定速度、当時の法令、
道路区分および車両固有規制を先に確認する。

SUMO typemapの既定速度は`model_assumed`とし、正式属性としての採用を禁止する。

## 14. 既存契約からの変更

この案を採用する場合、少なくとも次の既存契約を変更する。

| 対象 | 必要な変更 |
|---|---|
| 属性分類Schema | `value_state`を`resolution_status`と`value_origin`へ分離 |
| 失敗分類 | 提案された名称付き停止理由を既存の`RS###`または`AC###`へ対応付ける |
| 道路対応履歴 | 元Way、分割区間、方向付き区間、SUMO edgeの対応を追加 |
| 通行権限期待値 | 方向付き区間、車両、時間区間、目的地文脈を追加 |
| 設定ファイル | シナリオ、車両、条件式、速度規則の版付き設定を追加 |
| 意味整合検査 | 停止範囲、利用可能機能、状態と由来の組合せを検査 |
| 固定試験 | 新Schemaと新しい方向・条件・許可規則に合わせて独立正解を追加 |

添付案の`SCENARIO_*`、`VEHICLE_*`等の名称を、そのまま既存Schemaへ追加しては
ならない。既存の失敗コード体系は`RS###`、`AC###`等を要求するため、意味と
責任コンポーネントを決めた対応表が必要である。

## 15. 当時、採用前に追加決定が必要だった事項

| 識別子 | 追加決定 |
|---|---|
| `OPEN-PROP-001` | 研究用4,500 kg車両を日本のOSM`hgv`へ対応させる根拠と適用範囲 |
| `OPEN-PROP-002` | 実積載量が配送順序で変化する場合の道路進入時重量の計算時点 |
| `OPEN-PROP-003` | 軸重、車高、車幅、車長を使用する規制を全件停止で扱う範囲 |
| `OPEN-PROP-004` | 既存`value_state`成果物から新しい状態・由来フィールドへの移行 |
| `OPEN-PROP-005` | 名称付き停止理由と既存の安定した失敗コードの対応 |
| `OPEN-PROP-006` | OSM Wayを分割するノード、分割順、segment indexの決定規則 |
| `OPEN-PROP-007` | `lanes:both_ways`欠損を0として扱える条件 |
| `OPEN-PROP-008` | 通行許可の具体性を車線・方向・車種・条件間で比較する順序 |
| `OPEN-PROP-009` | `destination`、`delivery`、`customers`の対象区域と目的地一致判定 |
| `OPEN-PROP-010` | 条件式の境界包含、夜間範囲、単位、セミコロンの正式文法 |
| `OPEN-PROP-011` | 2026年7月16日に適用する日本速度規則の条項付き機械可読表 |
| `OPEN-PROP-012` | `JP:urban`導出に必要な道路状態の入手先と区間一致規則 |
| `OPEN-PROP-013` | `oneway=-1`を含む通常・バス向け右左折規制の接続変換 |
| `OPEN-PROP-014` | 複数via、ランプ、Uターン、分離道路を含む方向変換の対応範囲 |
| `OPEN-PROP-015` | 各規則のproduction実装と独立した正解成果物 |

## 16. 後続の採用判定

添付案は、版16の初期正式仕様を作るための具体的な採用候補として有用である。特に、
基準日時、研究用車両、原典Wayの不変保持、一意な車線導出、静的期間内で結果が
変化する条件の停止、速度証拠の優先順位は、既存方針を具体化している。

版17方針により、車両プロファイル、permissions authority、accessの4軸比較、
方向付き区間、方向別車線のformal除外および二軸値状態は方針固定となった。一方、
条件付き規制の完全な文法、許可台帳、日本速度規則、全production実装および独立fixtureは
未完了である。

```yaml
proposal_status: partially_adopted_and_superseded
normative_specification: false
implementation_allowed: false
v16_full_rerun_allowed: false
```

新規実装は版17の規範仕様と機械可読方針を使用する。

## 17. 参照資料

- [内閣府「国民の祝日について」](https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html)
- [警察庁「生活道路における自動車の法定速度が引き下げられます」](https://www.npa.go.jp/bureau/traffic/seikatsudouro/seikatsudoro.html)
- [OpenStreetMap Wiki `hgv`](https://wiki.openstreetmap.org/wiki/Key:hgv)
- [OpenStreetMap Wiki `maxweight`](https://wiki.openstreetmap.org/wiki/Key:maxweight)
- [OpenStreetMap Wiki access tags](https://wiki.openstreetmap.org/wiki/Key:access)
- [OpenStreetMap Wiki conditional restrictions](https://wiki.openstreetmap.org/wiki/Conditional_restrictions)
- [OpenStreetMap Wiki forward and backward](https://wiki.openstreetmap.org/wiki/Forward_%26_backward%2C_left_%26_right)
- [OpenStreetMap Wiki lanes](https://wiki.openstreetmap.org/wiki/Key:lanes)
- [SUMO edge type file](https://sumo.dlr.de/docs/SUMO_edge_type_file.html)
