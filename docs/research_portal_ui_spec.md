<a id="研究可視化ポータル-ui仕様書"></a>

# 研究可視化ポータル 画面仕様書

文書状態: Draft  
調査基準日: 2026-08-28  
関連研究仕様: [research_portal_research_spec.md](research_portal_research_spec.md)

<a id="1-uiの目的"></a>

## 1. 画面の目的

利用者が最初の画面で研究の中心線、現在地、計画済み領域、blocked要因を識別し、ノードをクリックして詳細Drawerから変数、仮説、根拠まで追跡できる画面を提供する。

画面は研究内容を解釈・補完しない。表示内容、表示名、状況、関係、根拠、初期表示は研究ポータル 登録簿を唯一の入力とする。

## 2. 情報アーキテクチャ

初期版は単一ページアプリを想定し、次の領域で構成する。

```text
App shell
├─ Header
│  ├─ research title
│  ├─ Registry updated/reviewed state
│  ├─ global search
│  └─ help / legend
├─ Context bar
│  ├─ current stage summary
│  ├─ status counts
│  └─ active filters / reset
├─ Main canvas
│  ├─ one-map graph
│  ├─ minimap / zoom controls
│  └─ selection / path highlight
├─ Filter panel（desktop）/ bottom sheet（mobile）
└─ Detail Drawer
   ├─ node or relation detail
   ├─ variables / parameters / hypotheses
   ├─ blockers / readiness
   └─ Evidence / provenance
```

ルートをページ分割する場合も、`/` を一枚地図、`/node/:id` と `/relation/:id` をdeep リンクとし、詳細ページへ遷移して地図の文脈を失わせない。初期版では比較表やデータ台帳の独立ページを必須としない。

## 3. 一枚地図

### 3.1 デフォルト構成

初期表示は左から右へ次の主系列を配置する。

```text
Open Data
→ Baseline Model
→ Common Delivery Instance
→ [Baseline | Classical | Qiskit Aer QAOA]
→ [Computation Time | Delivery Fulfillment]
→ Future Analyses
```

Future Analysesは次を折りたたみ群として持つ。

- quantum bit scale
- 量子計算 computationから電池 性能への外部 モデル
- 母集団 / 世帯等から配送 demand変化を推論するstatistical モデル
- final delivery demand fulfillment
- Urban Society / Economy

研究仕様で定義したsubgraphは、群 ノードの展開、breadcrumb、または「焦点」操作で表示する。初期表示で全変数を展開して可読性を失わせない。

<a id="32-layout"></a>

### 3.2 配置

- 主系列は固定順位を登録簿 表示で指定し、毎回大きく並び替わらない。
- 同一順位の比較手法は基準、古典計算、Qiskit Aer 量子近似最適化アルゴリズムの順に縦配置する。
- current/in_progressの中心経路をviewport中央に置く。
- 将来 subgraphは現行経路の右側または下段に隔離し、境界背景を変える。
- グラフ 配置が失敗した場合も、登録簿順のaccessible list 表示を提供する。
- ノード位置を利用者が一時移動できても、登録簿または共有配置へ自動保存しない。

<a id="33-node表現"></a>

### 3.3 ノード表現

ノードは色だけに依存せず、shape/icon、border、状況 badge、表示名で区別する。

| 状況 | 推奨表現 |
|---|---|
| `implemented` | solid border、check badge |
| `in_progress` | accent solid border、progress badge |
| `planned` | dashed border、薄いfill、`Planned` badge |
| `blocked` | 太い警告border、block icon、`Blocked` badge |
| `unknown` | dotted border、question icon、`Unknown` badge |

`readiness: not_accepted` は状況色とは別に、ノード下部へ `Not accepted for research use` の小badgeを表示する。実装済みでもnot 受入済みになり得るため、上書きしない。

ノード kindは小iconまたは形状で区別する。例: データセット=database、モデル=hexagon、手法=rounded rectangle、評価指標=circle、外部 モデル=double border、hypothesis=diamond、課題=octagon。iconには常にaccessible nameを付ける。

<a id="34-planned--hypothesis--external-model"></a>

### 3.4 計画済み / 仮説 / 外部モデル

- 計画済み ノード・関係は破線を基本とする。
- hypothesis 関係は破線に `Hypothesis` 表示名を付け、矢印だけで因果確定に見せない。
- 外部 モデルは二重枠または外部接続iconを使い、内部実装モデルと区別する。
- リポジトリに定量モデルがない場合、Drawer先頭に「モデル未構築」「定量結果なし」を表示する。
- Future Analyses領域全体に `Planned / not current evidence` の見出しを置く。

<a id="35-relation表現"></a>

### 3.5 関係表現

- 実装済み・現行の確定関係: solid line
- in progress: solid line + progress marker
- planned: dashed line
- blocked: warning-colored interrupted line
- hypothesis: dashed line + diamond marker + text label
- `compares_with`: 双方向または共通比較brace
- `blocked_by`: 課題から対象へ向かう警告線
- 道路区間 hover/focus時に関係 種類、状況、短い説明を表示する。
- 関係の根拠は道路区間 clickで関係 Drawerを開いて確認する。

<a id="36-graph操作"></a>

### 3.6 グラフ操作

- single click / Enter: ノード選択とDrawer表示
- double clickまたは専用button: 群展開・焦点
- Escape: Drawerを閉じ、直前のノードへ焦点を戻す
- zoom in/out/reset、fit to view
- pan、minimap
- upstream / downstream highlight
- 「根拠までの保存先」「現在地までの保存先」「blocked原因」をhighlight
- URL queryまたは保存先でselected ノード、表示、filtersを共有可能にする
- ブラウザー back/forwardで選択状態を復元する

## 4. Headerと文脈 bar

Headerには次を表示する。

- 研究名
- Registry `updated_at`
- `reviewed_by` / `reviewed_at`。不明の場合は不明と表示する
- 登録簿 検証状態
- global search
- legend / help

Context barには次を表示する。

- 現行 stage名と短い要約
- 実装済み / in_progress / 計画済み / blocked / 不明件数
- not 受入済み件数
- active filter chips
- filter reset

更新日を「研究データの観測日」と誤読させないため、`Registry updated` と表記する。

<a id="5-検索filterview"></a>

## 5. 検索・絞り込み・表示

### 5.1 検索対象

- ノード 識別子、日英表示名、まとめ
- 変数 / パラメーター名とsymbol
- hypothesis、issue、blocker
- 根拠 表示名とリポジトリ 保存先
- 属性タグ

検索結果は地図上でhighlightし、kind、状況、該当項目を表示する。検索索引も登録簿から生成し、根拠本文を全文検索して未登録内容を表示しない。

<a id="52-filter"></a>

### 5.2 絞り込み

- 状況
- 準備状況
- node kind
- nature: repository grounded / design / hypothesis / external model
- research stage
- Evidence availability / Evidence role
- current / future
- 阻害要因有無
- 属性タグ

絞り込みでノードが消える場合、選択ノードの親子関係が理解できるようghost connectorまたは「N ノード hidden」を表示する。blocked/unknownを既定値で隠してはならない。

<a id="53-preset-view"></a>

### 5.3 preset 表示

- `Research Overview`: 中心線と将来 群
- `Current Stage`: in_progress、blocked、直接依存だけ
- `Data Lineage`: dataset→transform→model→metric
- `Model Comparison`: common 問題例→三手法→評価指標
- `Future Analysis`: planned / hypothesis / external models
- `Evidence Gaps`: 不明、根拠不足、not 受入済み、known 矛盾

表示定義は登録簿のnode/relation参照から生成し、画面コードへ研究識別子を固定値として埋め込むしない。

## 6. ノード詳細Drawer

### 6.1 Header

- 表示名
- stable 識別子（コピー可能）
- node kind
- status badge
- readiness badge
- nature badge
- `Last reviewed` と確認者

<a id="62-summary--current-state"></a>

### 6.2 まとめ / 現行状態

- 目的・役割
- 現在できること
- 現在できないこと / `not_claimed`
- current state
- 研究 範囲、地理範囲、期間
- limitations / uncertainty

計画済み、blocked、不明の場合は理由を先頭近くに表示する。

<a id="63-dependencies-and-relations"></a>

### 6.3 Dependencies ・ 関係

- inputs / outputs
- upstream / downstream
- depends on / blocked by
- compared with
- 較正 / 検証関係
- 計画済み / hypothesis関係

各関係から相手ノードへ焦点できる。

<a id="64-variables-and-parameters"></a>

### 6.4 変数 ・ パラメーター

tableまたは定義 listで次を表示する。

- 名称、symbol、役割
- 値または `unknown`
- unit、range
- observed / derived / estimated / model_assumed / sensitivity / output
- 対象期間・地理範囲
- 根拠

値のない項目を画面都合で `0`、`N/A`、空文字へ変換しない。登録簿の `unknown` を表示する。

### 6.5 Hypotheses

- statement
- independent / dependent variables
- mechanism status
- planned test
- rejection condition
- 根拠と根拠 隔たり

hypothesisを研究結果と同じcard styleにしない。

### 6.6 進捗 / gates

- entry conditions
- exit conditions
- completed scope
- remaining scope
- 阻害要因と解除条件
- next actions

進捗率は登録簿に明示された定義と分母がある場合だけ表示する。状況から擬似的なpercentageを計算しない。

<a id="67-evidence--provenance"></a>

### 6.7 根拠 / 出典・来歴

根拠 cardごとに次を表示する。

- label、role、strength
- リポジトリ相対保存先
- heading / JSON pointer / symbol / artifact ID
- 版、変更記録、SHA-256（登録されている場合）
- supports / does not support
- 限界
- current / superseded / conflict
- `Open repository file` action

リンク先がdeploymentから開けない場合は保存先 コピーを提供し、404を成功扱いしない。Git外成果物には再生成方法またはavailability 注意事項を表示する。

### 6.8 Drawer 状態

- 幅: desktopでviewportの35–45%、最小360px、最大720px程度
- mobileでは全体-height bottom sheetまたは全体-screen panel
- 内容はsection単位で折りたためるが、状況、準備状況、限界、根拠 隔たりを初期非表示にしない
- deep リンクで直接開ける
- loading、not found、不正 登録簿、欠落 根拠を別状態で表示する

<a id="7-relation詳細drawer"></a>

## 7. 関係要素詳細Drawer

関係 click時は次を表示する。

- source → target
- 関係 種類と自然言語説明
- status、nature、uncertainty
- 何を意味し、何を意味しないか
- transformation / comparison conditions
- 根拠
- 計画済みの場合の入口 / exit 条件
- known conflict

特に `hypothesizes_influence_on` は「因果は未検証」、`projects_to` は「外部モデルまたは想定条件変換」、`supports` は「根拠 役割を超える主張をしない」と明記する。

<a id="8-evidence-link要件"></a>

## 8. 根拠 リンク要件

- リポジトリ内保存先を安全にencodeする。
- absolute 保存先をブラウザへ露出しない。
- allowlistされたリポジトリの最上位相対保存先だけを開く。
- 出典 viewerを設ける場合も読取り専用とし、編集・実行機能を持たせない。
- third-party 未加工 dataが非再配布の場合、ローカル未加工 保存先への公開リンクを出さず、台帳記録と出典 termsを表示する。
- 根拠 ファイルの内容をクライアントが読み、登録簿にない状況やまとめを抽出しない。

## 9. 状態・エラー表示

<a id="91-registry-validation-failure"></a>

### 9.1 登録簿 検証 不具合

本番構築時のデータ構造または参照整合誤りはdeploymentを停止する。既知の前回成功版を提供する場合は、画面上部に「stale 登録簿の版」を明示し、失敗版と混在させない。

<a id="92-partial-data"></a>

### 9.2 部分的データ

- 根拠 保存先 欠落: ノードは残し、根拠 cardに誤りを表示する。ただしCIでは原則構築 誤り。
- 不明 項目: `Unknown` と理由を表示する。
- いいえ 根拠: 計画済み hypothesisで許容された場合だけ `Evidence gap` と表示する。
- 後続版に置換済み 根拠: 既定値で折りたたみ、存在は明示する。
- 矛盾: 注意事項 bannerとconflicting 根拠両方を表示する。

### 9.3 空の状態

検索0件、絞り込みで0件、表示空、ノード 関係なしを区別し、reset 処理を出す。

## 10. Accessibility

- WCAG 2.2 AA相当を目標とする。
- 状況、kind、計画済み、hypothesisを色だけで区別しない。
- keyboardだけでHeader→絞り込み→グラフ ノード→Drawer→根拠 リンクへ移動できる。
- グラフにはDOM上のaccessible ノード listと関係 descriptionを用意する。
- 焦点 ringを明示し、Drawer close後に焦点を選択ノードへ戻す。
- screen reader向けに「出典、関係 種類、対象、状況」を読み上げる。
- text contrast 4.5:1を基本とする。
- prefers-縮約した-motionでは配置 移行、道路区間 animationを無効化する。
- zoom 200%でも主要操作とDrawer内容を失わない。

## 11. Responsive要件

- Desktop（1280px以上）: 絞り込み side panel + グラフ + right Drawer。
- Tablet: collapsible filter、graph、overlay Drawer。
- Mobile: グラフ簡略表示とaccessible list 表示を切替可能にし、Drawerは全体-screen。
- mobileでも状況 legend、現行 stage、blocked数、根拠へ3操作以内で到達できる。
- hoverだけに依存する情報を作らない。

## 12. 非機能要件

### 12.1 性能

- 初期目標は500 ノード / 1,500 関係まで通常操作を維持する。
- 初期表示は概観表示だけを描画し、Drawer詳細と大規模subgraphは遅延読込できる。
- 静的 登録簿 成果物はcontent ハッシュ値付きで一時保存する。
- 目標: broadband desktopで主要shellと概観が2.5秒以内、filter/search反応が100ms程度。ただし最終SLOは実装前に計測環境を確定する。

### 12.2 Reliability

- 同一登録簿の版から同一研究内容を決定論的に描画する。
- 配置座標差が研究内容差として扱われないよう、contentとpresentation ハッシュ値を分ける。
- 登録簿の版を全画面と出力に含める。
- 不正 登録簿をsilent 代替値で部分表示しない。

### 12.3 Security / privacy

- 読取り専用を初期範囲とする。
- 保存先 traversal、任意ファイル読取、外部URL injectionを防ぐ。
- 軽量マークアップ文書を表示する場合はsanitizeし、script/HTMLを実行しない。
- secret、個人情報、ローカル環境変数を登録簿へ入れない。
- third-party dataの利用・再配布条件に従う。

### 12.4 Maintainability

- 研究 ノード 識別子、状況 表示名、表示集合を画面コードへ固定値として埋め込むしない。
- 条件を統制した vocabularyだけをcomponent 対応付けへ持ち、未知列挙値は明示誤りにする。
- 登録簿 データ構造 版 migrationを用意できる構造にする。
- グラフ、Drawer、根拠 card、絞り込みのcomponent責務を分離する。

### 12.5 ブラウザー

組織内でサポートする現行Chrome/Edge/Firefox/Safariの最新版と1世代前を目標とする。確定ブラウザー 行列は実装開始時に利用環境を確認する。

<a id="13-ui-validation--test要件"></a>

## 13. 画面 検証 / 試験要件

- 各5 状況がbadge、shape/border、legend、screen reader textで区別できる。
- `implemented + not_accepted` を同時表示できる。
- planned/hypothesis/external モデルが現行根拠と視覚的に混同されない。
- ノード click、keyboard Enter、deep リンクのいずれでも同じDrawerを開く。
- 関係 clickで関係固有根拠を開く。
- 絞り込み適用・reset・URL共有・ブラウザー backが一貫する。
- 不明を0/空欄へ変換しない。
- missing/superseded/conflicting 根拠を正しく表示する。
- long Japanese labels、英数字識別子、長いリポジトリ 保存先で配置が破綻しない。
- mobile list 表示から全ノードと根拠へ到達できる。
- 500/1,500規模の性能試験を行う。
- axe等の自動検査に加え、keyboardとscreen readerの手動試験を行う。

## 14. 初期画面の受入シナリオ

1. 利用者が画面を開くと、Open データからFuture Analysesまでの中心線を確認できる。
2. 基準 Modelが `in_progress` であることと、正式研究利用の準備状況を同時に確認できる。
3. 共通配送問題、古典計算、Aer 量子近似最適化アルゴリズムが正式比較前であることを見分けられる。
4. 配送需要の充足を選択すると、指標定義と「なぜ正式値をまだ出せないか」を確認できる。
5. Aer 量子近似最適化アルゴリズムを選択すると、Aerが古典計算機上のシミュレーターであり量子優位性根拠ではないことを確認できる。
6. Future Analysesを展開すると、量子ビット 規模、電池 外部 モデル、demand statistical モデル、最終 fulfillment、Urban Society / Economyがplanned/hypothesisとして表示される。
7. 任意ノードから根拠 cardを経てリポジトリ 保存先へ追跡できる。
8. `Evidence Gaps` 表示で不明、blocked、not 受入済み、矛盾を一覧できる。

## 15. 実装しないこと

- 今回はWeb 画面を実装しない。
- 登録簿編集画面、認証・権限管理、コメント、通知、タスク割当を作らない。
- リポジトリ全文検索による研究内容の自動追加をしない。
- 実験実行、パラメーター変更、SUMO/QAOA job投入をしない。
- グラフから根拠ファイルを編集・削除しない。
- 実配送の運行監視、リアルタイム交通 dashboard、地理情報システム地物閲覧を目的にしない。
- 見栄えのために不明、blocked、計画済みを非表示または実装済みへ置換しない。
- 量子実機、量子優位性、社会・経済効果を示す未登録の装飾やコピーを追加しない。

## 16. 実装前の要確認事項

- deployment先からリポジトリ ファイルを開く方式（Git hosting URL、内部出典 viewer、保存先 コピーのみ）
- 日本語のみか日英切替か
- 登録簿 確認者と更新承認者
- ノード数の初期見積りと群展開粒度
- latest successful 登録簿を保持するdeploy方針
- Git外根拠となる成果物の公開・再生成・アクセス制御
- 評価指標の主名称（配送需要の充足 / 配送需要充足率 / 配送需要充足人口相当）
- brand、配色、組織のaccessibility基準
