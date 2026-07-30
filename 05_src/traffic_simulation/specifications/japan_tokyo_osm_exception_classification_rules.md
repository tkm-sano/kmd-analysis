# 日本・東京の道路属性例外分類規則

> **文書状態**: 実装済み分類規則
> **基準日**: 2026-07-30
> **対象**: 大田区v15全件試行で分離した307行
> **対象外**: 属性値の採用、法的判断の代替、v16正式属性解決

## 1. 目的

この文書は、OpenStreetMapの道路属性を日本・東京の配送車両シミュレーションへ
変換する前に、未対応表現、矛盾、条件付き規制を排他的に分類する規則を定める。
分類は「どの処理規則を必要とするか」を決めるだけであり、速度、車線数、通行可否を
採用しない。解決条件が満たされていない行は、分類後も停止を維持する。

機械可読な正本は
`reproducibility/config/traffic_simulation/resolver_exception_decision_table.yml`、
実装は
`05_src/traffic_simulation/network/classify_resolver_exceptions.py`である。

## 2. 日本・東京への適合方針

日本の交通規制は、道路標識・道路標示、車種、時間、道路構造などの条件に依存する。
警察庁は道路標識・道路標示を交通規制の表示手段として説明している。警視庁も東京の
最高速度について、現場の道路標識・道路標示に従うよう示している。このため、
OSMの抽象的な道路種別や単一タグから、東京の個別道路に適用される規制を推測しない。

特に、生活道路の法定速度は2026年9月1日に変更予定であり、同じ道路でも参照日と
道路構造によって適用規則が変わり得る。`maxspeed:type=JP:urban`だけから固定速度を
採用せず、少なくとも参照日、指定速度の有無、中央線・車両通行帯、往復方向の分離、
道路区分を確認できる証拠を要求する。

東京では通行禁止規制の除外や許可が個別の標章・許可証に依存する場合がある。
したがって、`private`、`permit`、条件付き通行規制を一般配送車両へ自動的に許可
しない。配送目的であることだけを根拠に通行可能とも判定しない。

根拠資料は次のとおりである。

- [警察庁「交通規制の目的」](https://www.npa.go.jp/bureau/traffic/seibi2/kisei/mokuteki/regulation/regulation.html)
- [警察庁「生活道路における自動車の法定速度」](https://www.npa.go.jp/bureau/traffic/seikatsudouro/seikatsudoro.html)
- [警視庁「最高速度規制の見直しについて」](https://www.keishicho.metro.tokyo.lg.jp/kotsu/doro/kisei_minaoshi.html)
- [警視庁「通行禁止道路の許可申請について」](https://www.keishicho.metro.tokyo.lg.jp/tetsuzuki/kotsu/tsuko_kyoka.html)
- [OpenStreetMap Wiki `oneway`](https://wiki.openstreetmap.org/wiki/JA:Key:oneway)
- [OpenStreetMap Wiki `maxspeed:type`](https://wiki.openstreetmap.org/wiki/Key:maxspeed:type)
- [OpenStreetMap Wiki `maxspeed:advisory`](https://wiki.openstreetmap.org/wiki/Key:maxspeed:advisory)
- [OpenStreetMap Wiki 条件付き規制](https://wiki.openstreetmap.org/wiki/Conditional_restrictions)
- [OpenStreetMap Wiki 通行制限](https://wiki.openstreetmap.org/wiki/Access_tags)
- [OpenStreetMap Wiki `lanes:both_ways`](https://wiki.openstreetmap.org/wiki/Key:lanes:both_ways)

## 3. 規則

### 3.1 通行方向と車線

| 規則識別子 | 一致条件 | 分類後の扱い |
|---|---|---|
| `EXC-ONEWAY-001` | `oneway=-1`を安全に方向変換できない停止行 | OSM Wayと逆向きの一方通行という地図表現として保持し、形状だけを反転しない。方向別車線、速度、権限、右左折規制を同時に変換する規則が完成するまで停止する。 |
| `EXC-LANES-001` | `lanes:both_ways`、または総数を伴わない方向別車線表現 | 中央共用車線と前後方向車線を同一視しない。全体数との整合と方向別用途を確認できるまで停止する。 |
| `EXC-LANES-002` | 総車線数と方向別車線数が矛盾 | 多数決や片方の優先で解消せず、権威ある追加証拠を要求する。 |

### 3.2 最高速度

| 規則識別子 | 一致条件 | 分類後の扱い |
|---|---|---|
| `EXC-SPEED-001` | `maxspeed=50;40` | 二つの値が方向、時間、車種、区間のいずれを表すか不明なため、単一値へ縮約しない。 |
| `EXC-SPEED-002` | `maxspeed:type=JP:urban` | 日本向けの地図表現として分類するが、参照日と適用道路状態を検証するまで数値化しない。 |
| `EXC-SPEED-003` | `maxspeed:advisory=40` | 勧告速度として分類し、法的な最高速度の代用にしない。`maxspeed`が併記されても両者を別属性として保持する。 |

### 3.3 通行可能車種と通行条件

| 規則識別子 | 一致条件 | 分類後の扱い |
|---|---|---|
| `EXC-PERM-001` | 双方向道路の車線配分が未解決 | 方向・車線ごとの権限を生成せず、車線配分の解決を先に要求する。 |
| `EXC-PERM-002` | `hgv:conditional` | 評価日時、祝日暦、車両区分、重量等の条件を登録できるまで停止する。 |
| `EXC-PERM-003` | `motorcycle` | 二輪車規制を配送用自動車へ転用せず、統制対象の二輪車クラスだけへ対応付ける。 |
| `EXC-PERM-004` | `motor_vehicle:conditional` | 自動車全般への条件として保持し、条件評価の文脈が完全になるまで停止する。 |
| `EXC-PERM-005` | `psv` | バスとタクシーを暗黙に同一クラスへ展開せず、研究対象車種との対応規則を要求する。 |
| `EXC-PERM-006` | `goods:conditional`と`vehicle:conditional` | 貨物用途と車両全般の条件を別々に保持し、優先順位と条件の積集合を定義するまで停止する。 |
| `EXC-PERM-007` | `access=private` | 配送車両に一般許可があると推定せず、個別許可または対象除外の根拠を要求する。 |
| `EXC-PERM-008` | `goods`と`motor_vehicle:conditional` | 貨物用途の無条件規制と自動車全般の条件付き規制を別々に評価する。 |
| `EXC-PERM-009` | `goods`と`vehicle:conditional` | 貨物用途と車両全般の適用範囲を統合規則なしに縮約しない。 |
| `EXC-PERM-010` | `psv:lanes` | 区切り数、空要素、方向、車線数を検証してから車線別権限へ変換する。 |
| `EXC-PERM-011` | `access=destination` | 通過交通の制限として保持し、配送先との経路文脈なしに全面許可または全面禁止へ変換しない。 |
| `EXC-PERM-012` | `hgv=destination` | 大型貨物車の車種定義と配送先文脈を要求し、一般貨物車へ拡張しない。 |
| `EXC-PERM-013` | `goods:conditional` | 貨物用途、積載量等の条件、評価時点を解釈できるまで停止する。 |
| `EXC-PERM-014` | `access=permit` | 研究内の配送車両が許可を保有すると仮定せず、許可状態を入力として登録するまで停止する。 |

## 4. 排他的照合

照合キーは属性、値状態、失敗コード、導出方法、および必要な場合のOSMタグ部分集合
である。入力行が0個または2個以上の規則へ一致した場合、処理は失敗して出力を
公開しない。未知の日本向け速度種別、未知の車種キー、壊れたタグJSONも同様に停止する。

大田区v15の307行は固定SHA-256の停止記録から選択し、全行がちょうど一つの規則へ
一致することを自動試験で確認する。ただし、この合格は307行の値が解決済みである
ことを意味しない。分類済み・解決保留という状態であり、正式道路網の阻害は残る。

## 5. 試験と変更管理

通常例、異常例、境界例は
`05_src/traffic_simulation/validation/fixtures/resolver_exception_rules/cases.json`、
実装から独立した正解結果は同フォルダの`oracle.json`に固定する。

規則の変更は、根拠資料、適用日、決定表、固定データ、独立正解、実装、全件照合の
順に行う。法令改正やOSM表現変更があっても、過去の参照日に対する結果を黙って
書き換えず、新しい規則版として固定する。
