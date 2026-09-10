# 研究可視化ポータル UI仕様書

文書状態: Draft  
調査基準日: 2026-08-28  
関連研究仕様: [research_portal_research_spec.md](research_portal_research_spec.md)

## 1. UIの目的

利用者が最初の画面で研究の中心線、現在地、planned領域、blocked要因を識別し、ノードをクリックして詳細Drawerから変数、仮説、Evidenceまで追跡できるUIを提供する。

UIは研究内容を解釈・補完しない。表示内容、表示名、status、relation、Evidence、初期viewはResearch Portal Registryを唯一の入力とする。

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

ルートをページ分割する場合も、`/` を一枚地図、`/node/:id` と `/relation/:id` をdeep linkとし、詳細ページへ遷移して地図の文脈を失わせない。初期版では比較表やデータ台帳の独立ページを必須としない。

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

Future Analysesは次を折りたたみgroupとして持つ。

- quantum bit scale
- quantum computationからbattery performanceへのexternal model
- population / household等からdelivery demand変化を推論するstatistical model
- final delivery demand fulfillment
- Urban Society / Economy

研究仕様で定義したsubgraphは、group nodeの展開、breadcrumb、または「focus」操作で表示する。初期表示で全変数を展開して可読性を失わせない。

### 3.2 layout

- 主系列は固定rankをRegistry viewで指定し、毎回大きく並び替わらない。
- 同一rankの比較手法はBaseline、Classical、Qiskit Aer QAOAの順に縦配置する。
- current/in_progressの中心経路をviewport中央に置く。
- future subgraphは現行経路の右側または下段に隔離し、境界背景を変える。
- graph layoutが失敗した場合も、Registry順のaccessible list viewを提供する。
- node位置を利用者が一時移動できても、Registryまたは共有layoutへ自動保存しない。

### 3.3 node表現

nodeは色だけに依存せず、shape/icon、border、status badge、labelで区別する。

| status | 推奨表現 |
|---|---|
| `implemented` | solid border、check badge |
| `in_progress` | accent solid border、progress badge |
| `planned` | dashed border、薄いfill、`Planned` badge |
| `blocked` | 太い警告border、block icon、`Blocked` badge |
| `unknown` | dotted border、question icon、`Unknown` badge |

`readiness: not_accepted` はstatus色とは別に、node下部へ `Not accepted for research use` の小badgeを表示する。implementedでもnot acceptedになり得るため、上書きしない。

node kindは小iconまたはshapeで区別する。例: dataset=database、model=hexagon、method=rounded rectangle、metric=circle、external model=double border、hypothesis=diamond、issue=octagon。iconには常にaccessible nameを付ける。

### 3.4 planned / hypothesis / external model

- planned node・relationは破線を基本とする。
- hypothesis relationは破線に `Hypothesis` labelを付け、矢印だけで因果確定に見せない。
- external modelは二重枠または外部接続iconを使い、内部実装modelと区別する。
- repositoryに定量モデルがない場合、Drawer先頭に「モデル未構築」「定量結果なし」を表示する。
- Future Analyses領域全体に `Planned / not current evidence` の見出しを置く。

### 3.5 relation表現

- 実装済み・現行の確定relation: solid line
- in progress: solid line + progress marker
- planned: dashed line
- blocked: warning-colored interrupted line
- hypothesis: dashed line + diamond marker + text label
- `compares_with`: 双方向または共通比較brace
- `blocked_by`: issueから対象へ向かう警告線
- edge hover/focus時にrelation type、status、短い説明を表示する。
- relationのEvidenceはedge clickでrelation Drawerを開いて確認する。

### 3.6 graph操作

- single click / Enter: node選択とDrawer表示
- double clickまたは専用button: group展開・focus
- Escape: Drawerを閉じ、直前のnodeへfocusを戻す
- zoom in/out/reset、fit to view
- pan、minimap
- upstream / downstream highlight
- 「Evidenceまでのpath」「現在地までのpath」「blocked原因」をhighlight
- URL queryまたはpathでselected node、view、filtersを共有可能にする
- browser back/forwardで選択状態を復元する

## 4. HeaderとContext bar

Headerには次を表示する。

- 研究名
- Registry `updated_at`
- `reviewed_by` / `reviewed_at`。unknownの場合はunknownと表示する
- Registry validation状態
- global search
- legend / help

Context barには次を表示する。

- current stage名と短い要約
- implemented / in_progress / planned / blocked / unknown件数
- not accepted件数
- active filter chips
- filter reset

更新日を「研究データの観測日」と誤読させないため、`Registry updated` と表記する。

## 5. 検索・filter・view

### 5.1 検索対象

- node ID、日英label、summary
- variable / parameter名とsymbol
- hypothesis、issue、blocker
- Evidence labelとrepository path
- tag

検索結果は地図上でhighlightし、kind、status、該当fieldを表示する。検索indexもRegistryから生成し、Evidence本文を全文検索して未登録内容を表示しない。

### 5.2 filter

- status
- readiness
- node kind
- nature: repository grounded / design / hypothesis / external model
- research stage
- Evidence availability / Evidence role
- current / future
- blocker有無
- tag

filterでnodeが消える場合、選択nodeの親子関係が理解できるようghost connectorまたは「N nodes hidden」を表示する。blocked/unknownをdefaultで隠してはならない。

### 5.3 preset view

- `Research Overview`: 中心線とfuture group
- `Current Stage`: in_progress、blocked、直接依存だけ
- `Data Lineage`: dataset→transform→model→metric
- `Model Comparison`: common instance→三手法→metrics
- `Future Analysis`: planned / hypothesis / external models
- `Evidence Gaps`: unknown、Evidence不足、not accepted、known conflict

view定義はRegistryのnode/relation参照から生成し、UIコードへ研究IDをhard-codeしない。

## 6. ノード詳細Drawer

### 6.1 Header

- label
- stable ID（copy可能）
- node kind
- status badge
- readiness badge
- nature badge
- `Last reviewed` とreviewer

### 6.2 Summary / current state

- 目的・役割
- 現在できること
- 現在できないこと / `not_claimed`
- current state
- research scope、地理範囲、期間
- limitations / uncertainty

planned、blocked、unknownの場合は理由を先頭近くに表示する。

### 6.3 Dependencies and relations

- inputs / outputs
- upstream / downstream
- depends on / blocked by
- compared with
- calibration / validation関係
- planned / hypothesis関係

各relationから相手nodeへfocusできる。

### 6.4 Variables and parameters

tableまたはdefinition listで次を表示する。

- 名称、symbol、role
- valueまたは `unknown`
- unit、range
- observed / derived / estimated / model_assumed / sensitivity / output
- 対象期間・地理範囲
- Evidence

値のないfieldをUI都合で `0`、`N/A`、空文字へ変換しない。Registryの `unknown` を表示する。

### 6.5 Hypotheses

- statement
- independent / dependent variables
- mechanism status
- planned test
- rejection condition
- EvidenceとEvidence gap

hypothesisを研究結果と同じcard styleにしない。

### 6.6 Progress / gates

- entry conditions
- exit conditions
- completed scope
- remaining scope
- blockersと解除条件
- next actions

progress率はRegistryに明示された定義と分母がある場合だけ表示する。statusから擬似的なpercentageを計算しない。

### 6.7 Evidence / provenance

Evidence cardごとに次を表示する。

- label、role、strength
- repository相対path
- heading / JSON pointer / symbol / artifact ID
- version、commit、SHA-256（登録されている場合）
- supports / does not support
- limitations
- current / superseded / conflict
- `Open repository file` action

link先がdeploymentから開けない場合はpath copyを提供し、404を成功扱いしない。Git外artifactには再生成方法またはavailability warningを表示する。

### 6.8 Drawer states

- width: desktopでviewportの35–45%、最小360px、最大720px程度
- mobileではfull-height bottom sheetまたはfull-screen panel
- 内容はsection単位で折りたためるが、status、readiness、limitations、Evidence gapを初期非表示にしない
- deep linkで直接開ける
- loading、not found、invalid Registry、missing Evidenceを別状態で表示する

## 7. relation詳細Drawer

relation click時は次を表示する。

- source → target
- relation typeと自然言語説明
- status、nature、uncertainty
- 何を意味し、何を意味しないか
- transformation / comparison conditions
- Evidence
- plannedの場合のentry / exit condition
- known conflict

特に `hypothesizes_influence_on` は「因果は未検証」、`projects_to` は「外部モデルまたはscenario変換」、`supports` は「Evidence roleを超える主張をしない」と明記する。

## 8. Evidence link要件

- repository内pathを安全にencodeする。
- absolute pathをブラウザへ露出しない。
- allowlistされたrepository root相対pathだけを開く。
- source viewerを設ける場合もread-onlyとし、編集・実行機能を持たせない。
- third-party raw dataが非再配布の場合、ローカルraw pathへの公開linkを出さず、台帳recordとsource termsを表示する。
- Evidence fileの内容をクライアントが読み、Registryにないstatusやsummaryを抽出しない。

## 9. 状態・エラー表示

### 9.1 Registry validation failure

本番build時のSchemaまたは参照整合errorはdeploymentを停止する。既知の前回成功版を提供する場合は、画面上部に「stale Registry version」を明示し、失敗版と混在させない。

### 9.2 partial data

- Evidence path missing: nodeは残し、Evidence cardにerrorを表示する。ただしCIでは原則build error。
- unknown field: `Unknown` と理由を表示する。
- no Evidence: planned hypothesisで許容された場合だけ `Evidence gap` と表示する。
- superseded Evidence: defaultで折りたたみ、存在は明示する。
- conflict: warning bannerとconflicting Evidence両方を表示する。

### 9.3 empty states

検索0件、filterで0件、view空、node relationsなしを区別し、reset actionを出す。

## 10. Accessibility

- WCAG 2.2 AA相当を目標とする。
- status、kind、planned、hypothesisを色だけで区別しない。
- keyboardだけでHeader→filter→graph node→Drawer→Evidence linkへ移動できる。
- graphにはDOM上のaccessible node listとrelation descriptionを用意する。
- focus ringを明示し、Drawer close後にfocusを選択nodeへ戻す。
- screen reader向けに「source、relation type、target、status」を読み上げる。
- text contrast 4.5:1を基本とする。
- prefers-reduced-motionではlayout transition、edge animationを無効化する。
- zoom 200%でも主要操作とDrawer内容を失わない。

## 11. Responsive要件

- Desktop（1280px以上）: filter side panel + graph + right Drawer。
- Tablet: collapsible filter、graph、overlay Drawer。
- Mobile: graph簡略表示とaccessible list viewを切替可能にし、Drawerはfull-screen。
- mobileでもstatus legend、current stage、blocked数、Evidenceへ3操作以内で到達できる。
- hoverだけに依存する情報を作らない。

## 12. 非機能要件

### 12.1 Performance

- 初期目標は500 nodes / 1,500 relationsまで通常操作を維持する。
- 初期表示は概観viewだけを描画し、Drawer詳細と大規模subgraphは遅延読込できる。
- static Registry artifactはcontent hash付きでcacheする。
- 目標: broadband desktopで主要shellと概観が2.5秒以内、filter/search反応が100ms程度。ただし最終SLOは実装前に計測環境を確定する。

### 12.2 Reliability

- 同一Registry versionから同一研究内容を決定論的に描画する。
- layout座標差が研究内容差として扱われないよう、contentとpresentation hashを分ける。
- Registry versionを全画面とexportに含める。
- invalid Registryをsilent fallbackで部分表示しない。

### 12.3 Security / privacy

- read-onlyを初期scopeとする。
- path traversal、任意file読取、外部URL injectionを防ぐ。
- Markdownを表示する場合はsanitizeし、script/HTMLを実行しない。
- secret、個人情報、ローカル環境変数をRegistryへ入れない。
- third-party dataの利用・再配布条件に従う。

### 12.4 Maintainability

- research node ID、status label、view集合をUIコードへhard-codeしない。
- controlled vocabularyだけをcomponent mappingへ持ち、未知enumは明示errorにする。
- Registry Schema version migrationを用意できる構造にする。
- graph、Drawer、Evidence card、filterのcomponent責務を分離する。

### 12.5 Browser

組織内でサポートする現行Chrome/Edge/Firefox/Safariの最新版と1世代前を目標とする。確定browser matrixは実装開始時に利用環境を確認する。

## 13. UI validation / test要件

- 各5 statusがbadge、shape/border、legend、screen reader textで区別できる。
- `implemented + not_accepted` を同時表示できる。
- planned/hypothesis/external modelが現行Evidenceと視覚的に混同されない。
- node click、keyboard Enter、deep linkのいずれでも同じDrawerを開く。
- relation clickでrelation固有Evidenceを開く。
- filter適用・reset・URL共有・browser backが一貫する。
- unknownを0/空欄へ変換しない。
- missing/superseded/conflicting Evidenceを正しく表示する。
- long Japanese labels、英数字ID、長いrepository pathでlayoutが破綻しない。
- mobile list viewから全nodeとEvidenceへ到達できる。
- 500/1,500規模の性能testを行う。
- axe等の自動検査に加え、keyboardとscreen readerの手動testを行う。

## 14. 初期画面の受入シナリオ

1. 利用者が画面を開くと、Open DataからFuture Analysesまでの中心線を確認できる。
2. Baseline Modelが `in_progress` であることと、正式研究利用のreadinessを同時に確認できる。
3. Common Delivery Instance、Classical、Aer QAOAが正式比較前であることを見分けられる。
4. Delivery Fulfillmentを選択すると、指標定義と「なぜ正式値をまだ出せないか」を確認できる。
5. Aer QAOAを選択すると、Aerが古典計算機上のsimulatorであり量子優位性Evidenceではないことを確認できる。
6. Future Analysesを展開すると、qubit scale、battery external model、demand statistical model、final fulfillment、Urban Society / Economyがplanned/hypothesisとして表示される。
7. 任意nodeからEvidence cardを経てrepository pathへ追跡できる。
8. `Evidence Gaps` viewでunknown、blocked、not accepted、conflictを一覧できる。

## 15. 実装しないこと

- 今回はWeb UIを実装しない。
- Registry編集画面、認証・権限管理、コメント、通知、タスク割当を作らない。
- repository全文検索による研究内容の自動追加をしない。
- 実験実行、parameter変更、SUMO/QAOA job投入をしない。
- graphからEvidenceファイルを編集・削除しない。
- 実配送の運行監視、リアルタイムtraffic dashboard、GIS地物閲覧を目的にしない。
- 見栄えのためにunknown、blocked、plannedを非表示またはimplementedへ置換しない。
- 量子実機、量子優位性、社会・経済効果を示す未登録の装飾やcopyを追加しない。

## 16. 実装前の要確認事項

- deployment先からrepository fileを開く方式（Git hosting URL、内部source viewer、path copyのみ）
- 日本語のみか日英切替か
- Registry reviewerと更新承認者
- node数の初期見積りとgroup展開粒度
- latest successful Registryを保持するdeploy方針
- Git外Evidence artifactの公開・再生成・アクセス制御
- metricの主名称（Delivery Fulfillment / 配送需要充足率 / 配送需要充足人口相当）
- brand、配色、組織のaccessibility基準
