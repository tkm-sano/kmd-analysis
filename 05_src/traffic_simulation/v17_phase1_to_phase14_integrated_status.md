# v17 属性解決工程 1〜14 統合定義・現在地・証拠

> **文書状態**: 現状確認用の統合資料
>
> **基準日**: 2026-08-14（日本標準時）
>
> **対象**: 東京・大田区 スーモ 道路網の v17 属性解決ライフサイクル
>
> **構成識別子**: `ota_ward_sumo_network_v17`
>
> **方針識別子**: `ota_ward_attribute_resolution_policy_v17`
>
> **母集団版**: `ota_ward_relation_closure_v16`
>
> **現在地**: Phase 1〜12は正式記録上合格。Phase 12公開物をPhase 13入力としてハッシュ値固定し、108,189 阻害要因を10群へ集計済み。Phase 13は車両 概念体系の最初の根本原因規則を検証して進行中、Phase 14はゲート待ち。

## 1. この文書の目的

この文書は、これまで複数の仕様書、ヤムル形式記録、ロードマップ、学習資料に分散していた
v17 属性解決 Phase 1〜14について、次を一か所で確認できるようにする。

1. 各Phaseの定義と完了条件
2. 2026-08-14時点の状態
3. 状態判断の根拠となる実装、試験、記録、成果物
4. 未完了事項と次に進むための条件
5. `v17`、`v16`、`V&V`、Phase番号の区別

この文書は既存の規範仕様や機械可読契約を置き換えない。定義が競合する場合は、
承認済み規範仕様、機械可読設定・データ構造、各Phase完了記録、実行ロードマップ、
この統合資料、学習資料の順に参照する。

## 2. 用語と番号の区別

<a id="21-v-は-version-を表す"></a>

### 2.1 `v` は 版 を表す

- `v17`は**属性解決方針・設定・データ構造・実装契約のバージョン17**を表す。
- `v16`は**直前のバージョン16**を表す。
- 本作業は、受理済みの `ota_ward_relation_closure_v16` 母集団を変更せず、v17の規則で
  属性を再解決する。
- `v17 Phase 12`は「バージョン17のPhase 12」であり、「バージョン12」ではない。

<a id="22-vv-は-version-ではない"></a>

### 2.2 `V&V` は 版 ではない

`V&V`は **実装検証と妥当性確認** の略である。

- 実装検証は、仕様、規則、データ構造、実装、変換、道路構造が意図どおりであるかの確認である。
- 検証は、モデルが定めた利用目的に対して現実を十分に表すかの確認である。
- v17 Phase 1〜14は、主に道路属性解決の実装検証と受入に属する。
- Phase 14合格だけでは、スーモ道路網統合、交通較正、独立検証は完了しない。

### 2.3 工程番号と旧「工程」番号を混同しない

現行の番号は、本書で使用する **v17 Phase 1〜14** である。
`attribute_resolution_execution_procedure.md`には別体系の「工程0〜17」が残っており、
番号は一対一に一致しない。例えば、同文書の「工程11 版17全件実行」は現行の
**Phase 12 Full-母集団 Run**に相当する。状態判断にはPhase番号を優先する。

## 3. ライフサイクル全体

```text
v16履歴・母集団を固定
  ↓
v17規範仕様を承認
  ↓
Phase 1  Authority Synchronization
  ↓
Phase 2  Independent Fixtures and Oracles
  ↓
Phase 3  State Contract Migration
  ↓
Phase 4  Directed Segment Integration
  ↓
Phase 5  Directional Lane Resolution
  ↓
Phase 6  Static Access Resolution
  ↓
Phase 7  Conditional Access Resolution
  ↓
Phase 8  Final Permission Resolution
  ↓
Phase 9  Speed Resolution
  ↓
Phase 10 Formal Evidence Method
  ↓
Phase 11 Resolver Integration Test
  ↓
Phase 12 Full-population Run and Accounting
  ↓
Phase 13 Stop Record Resolution and Rerun
  ↓
Phase 14 Attribute Resolution Acceptance
  ↓
SUMO Network Integration Acceptance
  ↓
交通モデルのCalibration
  ↓
独立データによるValidation
  ↓
配送・古典最適化・Qiskit Aer QAOAの正式比較
```

## 4. 状態の読み方

| 状態 | 意味 |
|---|---|
| 合格 | Git管理された完了記録があり、当該Phaseで要求された実装・検証ゲートを通過している |
| 実行済み・正式完了未認定 | 成果物は存在するが、正式な完了記録または完了ゲートの充足確認が不足している |
| 未着手 | 前提Phaseまたは開始条件を満たしておらず、正式作業を開始していない |
| ゲート待ち | 受入処理自体は未実行で、前提条件の充足を待っている |

Phase単体の「合格」は、属性解決全体、正式スーモ道路網、または研究全体のV&V完了を意味しない。

## 5. 工程 1〜14 統合一覧

| Phase | 定義・目的 | 主な完了条件 | 2026-08-13現在 | 主要証拠 | 残作業・次の条件 |
|---:|---|---|---|---|---|
| 1 | **Authority Synchronization**。v17規範仕様、設定、データ構造、登録簿、意味上の不変条件、トレーサビリティを同期する | 権威資料間の不整合がなく、検証器と試験が合格する | **合格**（2026-08-03） | `v17_phase1_completion.yml`、承認済みv17方針、`sumo_network_v17.yml`、同期レビュー | なし。当該Phaseの合格は実行時間全件実行を意味しない |
| 2 | **Independent Fixtures and Oracles**。正式運用実装から独立した小型入力、期待結果、成果物一覧を固定する | 検証用データ・正解判定器・成果物一覧がデータ構造に適合し、相互ハッシュ値が一致する | **合格**（2026-08-03） | `v17_phase2_completion.yml`、`validation/fixtures/v17_attribute_resolution/` | なし。正式運用統合は後続Phaseで実施 |
| 3 | **State Contract Migration**。`resolution_status`と`value_origin`を分離したv17状態契約へ移行する | 旧版 reader、v17 writer、cross-項目 検証器、移行規則が実装・検証済み | **合格**（2026-08-03） | `v17_phase3_completion.yml`、`attribute_resolution_state_v17.py`、移行登録簿 | なし |
| 4 | **方向付き区間 Integration**。オープンストリートマップ 道路地物を方向付き区間へ正規化し、方向・区間・関係来歴を保持する | `oneway`を含む方向正規化、正本 interval、関係 対応付け、独立検証用データが合格する | **合格**（2026-08-04） | `v17_phase4_completion.yml`、`directed_segments_v17.py` | 正式停止は後続Phase 12〜13で扱う |
| 5 | **Directional 車線 Resolution**。方向別車線数、`lanes:both_ways`、スーモ 車線 索引との対応を解決する | 正式と構造上のの境界を守り、正式で根拠のない算術補完を行わない | **合格**（2026-08-04） | `v17_phase5_completion.yml`、`directional_lanes_v17.py` | 正式の未解決車線はPhase 13対象 |
| 6 | **Static Access Resolution**。静的な通行規則を車種・方向・車線軸で解決する | 最大適用規則選択と競合・未対応時の不確実な場合は拒否が実装・検証済み | **合格**（2026-08-04） | `v17_phase6_completion.yml`、`static_access_v17.py` | 条件付き 接続と最終 通行許可はPhase 7〜8で実施済み |
| 7 | **Conditional Access Resolution**。日時・曜日・祝日等の条件付き通行規則を固定想定条件 Contextで評価する | grammar、登録簿、期間内変化の不確実な場合は拒否、想定条件 Contextが検証済み | **合格**（2026-08-04） | `v17_phase7_completion.yml`、`conditional_access_v17.py`、runtime context | 未解決条件はPhase 13対象 |
| 8 | **Final 通行許可 Resolution**。静的・条件付き・範囲・axis dominanceから最終通行権限期待値を作る | 全通行許可 組を記録し、道路種別の対応表を正式権威として使用しない | **合格**（2026-08-04） | `v17_phase8_completion.yml`、`final_permission_v17.py` | 正式 通行許可未解決はPhase 13対象 |
| 9 | **速度 Resolution**。方向別・条件付き速度、法定速度、助言速度、simulation速度を分離して解決する | 日本速度規則が承認・ハッシュ値固定され、未根拠値を正式へ混入しない | **合格**（2026-08-04） | `v17_phase9_completion.yml`、`speed_resolution_v17.py`、`japan_speed_rules_v17.yml` | 正式速度未解決はPhase 13対象 |
| 10 | **正式 根拠 手法**。外部・派生証拠を正式値へ使用する方法と境界を統制する | 未承認手法、モデル-assumed 属性提供元、直接編集を不確実な場合は拒否にし、出発地 監査が合格する | **合格**（2026-08-04） | `v17_phase10_completion.yml`、`evidence_resolution_v17.py`、origin audit | 承認済み正式 根拠 手法は現在0件。証拠なしの停止を解消済みとはしない |
| 11 | **属性解決器 Integration 試験**。Phase 3〜10を統合し、データ構造、意味、独立正解判定器、metamorphic 関係を検査する | 4ゲートすべて合格し、cross-stage lineageが保たれる | **合格**（2026-08-04） | `v17_phase11_completion.yml`、`resolver_integration_v17.py`、統合fixture/oracle | Phase 11合格は母集団全体 受入を意味しない |
| 12 | **Full-母集団 Run and Accounting**。固定v16母集団をv17 structural/formal両設定プロファイルで2回独立実行し、全停止・除外・母集団差を保存する | 必須8成果物、全データ構造・意味検証、ハッシュ値、母集団式、識別子一意性、環境一致、2回決定論的一致、原子的公開がすべて合格する | **合格**（2026-08-14） | `v17_phase12_completion.yml`、`determinism_report.json`、各実行 成果物一覧、`v17_phase12_independent_rerun_20260813.yml` | Phase 13で阻害要因を属性・停止コード・根本原因別に解消する |
| 13 | **Stop 記録 Resolution and Rerun**。Phase 12の停止を根本原因別に解消し、全件成果物を再生成する | 判断→登録簿/表→データ構造→不変条件→検証用データ→独立正解判定器→コード→試験→全件実行の順を守り、未証明記録を残さない | **進行中**（2026-08-14開始） | Phase 13 入力 固定、阻害要因 aggregation、車両 概念体系 判断、全回帰597件合格 | `psv`・`motorcar`等を別判断で解消し、全件実行を新規出力へ再実行する |
| 14 | **属性解決の受入**。正式属性成果物の最終受入判定を行う | 阻害要因、確認-必須、配送地点-未解決、モデル-assumedが各0件。全記録解決、母集団式・通行許可被覆・データ構造・意味・正解判定器・projection不変・2回一致が合格する | **ゲート待ち** | 実行ロードマップ、正式 阻害要因 方針 | Phase 13再実行後に受入を実行する。合格しても正式スーモ道路網の承認とは別 |

## 6. 現在地の詳細

### 6.1 正式に確定している状態

- Git管理された累積完了記録は、Phase 1〜12を `passed` としている。
- Phase 11時点で、データ構造、意味上の不変条件、正式運用-independent 正解判定器、
  metamorphic 検証が合格している。
- `formal_build_ready` は `false` である。
- `attribute_resolution_acceptance` は `not_run` である。
- 正式スーモ道路網は未承認であり、較正、独立検証、配送・量子近似最適化アルゴリズム正式評価へ進めない。

### 6.2 工程 12の実行成果物

Phase 12の出力先は `.gitignore` 対象だが、ローカルには2026-08-13に新しい独立出力先で
生成した次の成果物が存在する。

- `runs/run_1/`
- `runs/run_2/`

記録された2回の実行は同一変更記録
`c86c7548bcd39b2f6fcdccd0b1e6c813fe10636c`、固定コンテナー ハッシュ値
`sha256:fbc7489e297359ccbd70a0030613d95d2f3dade061b6501b281d834e24bd3002`、
同一固定入力を使用した。両実行は終了コード0で、8個の実行単体検証器と実行後の独立コマンド操作再検査に
合格し、主要5成果物の意味上の SHA-256がすべて一致した。各実行 成果物一覧には、実際のコマンド操作引数、
各検証器のコマンド、終了コード、stdout/stderrログ、そのSHA-256、検査件数、検査結果が記録される。
Phase 12全体の`finalize()`は2026-08-14に合格し、`published/`と`determinism_report.json`を
生成した。実コマンド操作引数は保持し、比較時だけ各実行自身と一致する`--run-id`値を`<run_id>`へ正規化した。
それ以外の引数と実行条件は完全一致した。

Phase 12成果物が示す主な数値は次のとおりである。異なる母集団単位の件数を単純合算して
モデル全体の欠損率などと解釈してはならない。

| 項目 | 件数・状態 |
|---|---:|
| 阻害要因一覧総件数 | 108,189 |
| directional lane governed | 26,220 |
| directional lane resolved | 2,082 |
| directional lane unresolved | 24,114 |
| directional lane conflict | 24 |
| static access governed | 2,082 |
| static access resolved | 1,563 |
| final permission governed | 6,984 |
| final permission resolved | 2,120 |
| final permission unresolved | 4,864 |
| speed governed | 94,745 |
| speed resolved | 16,129 |
| speed unresolved | 78,601 |
| production exclusion | 0 |
| structural permission record | 16,330 |
| formal permission record | 6,984 |
| structural/formal差 | 9,346（登録済み仮定 `BIDIRECTIONAL_EVEN_LANE_EQUAL_SPLIT_V1`） |
| run_1 単体完了判定 | 合格（8 検証器、失敗0） |
| run_2 単体完了判定 | 合格（8 検証器、失敗0） |
| 主要5成果物の2run 意味上の ハッシュ値一致 | 合格 |
| Phase 12全体`finalize()` | 合格 |

### 6.3 工程 12の正式判定と解釈

Phase 12全体は`passed`である。両実行の8単体検証器、実行 成果物一覧再検証、主要5成果物の
意味上の ハッシュ値一致、実行条件一致、決定性 報告 データ構造、原子的公開がすべて合格した。

108,189件の管理対象の 阻害要因が残るため、`formal_build_ready`は`false`である。ただしPhase 12は
阻害要因を漏れなく棚卸しし、母集団と因果関係を保存する工程であるため、阻害要因残存はPhase 12の
不合格条件ではない。阻害要因解消はPhase 13、0件確認と属性解決受入はPhase 14の責務である。

## 7. 工程 12から工程 14までの次の実行順序

詳細な実行履歴は
`reproducibility/config/traffic_simulation/v17_phase13_execution_log_20260814.yml`、
Phase 13再実行後から配送比較までの入口条件・成果物・検査・不合格時の戻り先は
`reproducibility/config/traffic_simulation/v17_post_phase13_to_experiment_execution_plan.yml`
を正本とする。
日々の実行チェックは`05_src/traffic_simulation/phase13_to_sumo_network_todo.md`で管理する。

1. **実装済み:** Phase 12 実行器が実際に受け取ったコマンド操作引数列を成果物一覧生成へ渡し、
   正式実行では`sha256:<64桁>`のコンテナー ハッシュ値を必須として未固定値を開始前に拒否する。
2. **実装・検証済み:** 各実行単体で存在、データ構造、意味上の ハッシュ値、意味整合、識別子一意性、
   母集団保存則、登録値、blocker/exclusion整合を検査する。各検証器の実コマンド、終了コード、
   stdout/stderrログ、ログSHA-256は新規実行 成果物一覧へ記録する。項目別・実行全体の合否は
   各検証器の検査件数と結果から集約し、固定の`passed`を使用しない。`finalize()`は実行 成果物一覧、
   環境 成果物一覧、全バイト ハッシュ値を再検査する。
3. 実行器、失敗時、2回実行、finalize、公開処理の試験を追加する。
   正常系、成果物欠落、値改変、識別子重複、母集団不整合、成果物上書き拒否、失敗実行の公開禁止、
   既存`published`上書き拒否は実装済みである。残るのは小型検証用データによる2回実行全経路である。
4. 既存成果物を直接編集せず、新しい出力先または新しい実行識別子で2回再実行する。
   新しい固定出力先は
   `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun`
   とする。**2026-08-13実行済み:** 固定コンテナー ハッシュ値、同一出典 変更記録、同一入力から
   `run_1`と`run_2`を独立実行し、双方が8個の実行単体判定基準および実行後の独立コマンド操作再検査に合格した。
   主要5成果物の意味上の SHA-256も2runで一致した。実行証拠は
   `v17_phase12_independent_rerun_20260813.yml`に記録した。
5. **2026-08-14実行済み:** `run_id`だけを検証付きで正規化し、全体`finalize()`を実行した。
6. **2026-08-14実行済み:** Phase 12完了記録とロードマップを更新した。
7. **2026-08-14実行済み:** Phase 12公開7成果物をPhase 13入力としてバイト ハッシュ値と意味上の ハッシュ値で固定し、
   阻害要因 108,189件を `attribute_name`、`stop_code`、`root_cause_category` の10群へ集計した。
8. **進行中:** Phase 13の順序に従って根本原因を解消する。最初の車両 概念体系 判断では、
   `bicycle`、`foot`、`mofa`、`moped`を管理対象の車種との明示的な空交差として登録簿へ登録し、
   検証用データ、独立正解判定器、全母集団stage 試験、固定コンテナー全回帰597件で検証した。
9. 残る`psv`、`motorcar`、`horse`等を独立判断で処理し、証拠不足・真正競合は推測で解消しない。
10. Phase 13修正を反映し、新しい版付き出力先で全道路を2回独立再実行する。
11. Phase 12からの阻害要因 識別子遷移を比較し、減少・解消・新規発生の各理由を登録判断へ結び付ける。
12. 全入力記録を「管理対象の / 除外済み」、管理対象の内を「解決済み / 未解決 / 矛盾 /
    invalid / valid-but-unsupported」へ再集計し、母集団保存則を確認する。
13. 除外記録は道路識別子、規則、理由、根拠、承認者、日付、道路網影響を追跡し、残存未解決記録は
    理由別件数、影響道路・延長・接続性・配送到達性を評価する。
14. 管理対象の 阻害要因、確認-必須、配送地点-未解決、モデル-assumedがすべて0件になった後、
    Phase 14 Attribute Resolution Acceptanceを実行する。
15. Phase 14合格成果物だけをハッシュ値固定して正式 スーモ 構築 入力とする。

## 8. 工程 14後に残る工程

Phase 14は属性解決の受入であり、道路網全体や交通モデル全体のV&V完了ではない。
少なくとも次が後続する。

1. 受入済み オープンストリートマップ属性からスーモのノード、道路区間、車線、接続を生成し、方向、車線、速度、
   配送車両を含む車種別通行権限を正式反映する。
2. オープンストリートマップ道路識別子とスーモ edge/laneの対応を保持し、生成・非生成とその理由を記録単位で追跡する。
3. 交差点統合、車線 接続、右左折規制、信号リンク・段階・programを検査し、承認した修正から再生成する。
4. 正式候補道路網を生成し、ノード数、道路区間数、車線数、道路延長、信号交差点数、警告を集計する。
5. 配送車両が通行できる道路区間数、道路延長、到達範囲、孤立道路、到達不能領域、不正接続を検査する。
6. スーモ上で方向、通行許可、右左折、接続、信号の実行時間走行試験を行う。
7. 構築再現性、負荷、lineage、通行許可、網羅率、connectivity、実行時間試験をまとめて
   **スーモ道路網統合受入判定**を行い、合格道路網を固定する。
8. 正式道路網へ一般交通需要を投入し、較正用観測の交通量、速度、旅行時間で交通モデルを較正する。
9. 較正に使用していない日時または地点の観測で独立検証を行う。
10. 検証済み道路網・交通条件・配送需要・車両条件・乱数の種を共通実験入力として固定する。
11. 同一条件で非最適化、古典最適化、量子近似最適化アルゴリズムを実行し、距離、時間、遅延、電力消費、
    配送需要充足率を比較する。

最重要ゲートは、Phase 13で阻害要因件数を減らした事実だけではない。Phase 14で
**「この道路属性成果物をスーモ変換へ渡してよい」**と正式判定し、その後に別の
**スーモ道路網統合受入判定**で生成道路網そのものを承認する。両判定を一つにまとめない。

```text
Phase 13: 問題を直す
  → Phase 14: 道路属性を承認する
  → accepted OSM属性をSUMOへ変換する
  → SUMO道路網を生成・検証する
  → SUMO道路網を承認する
  → 一般交通を較正し、未使用データで検証する
  → 共通入力を固定して配送手法を比較する
```

## 9. 正本・証拠索引

### 9.1 全体定義と現行ロードマップ

- `05_src/traffic_simulation/specifications/10_approved_attribute_resolution_policy_v17_complete.md`
- `05_src/traffic_simulation/learning/v17_phase1_beginner_guide_full_intent_hierarchy_ja.md`
- `reproducibility/config/traffic_simulation/v17_phase9_to_phase14_execution_roadmap.yml`
- `reproducibility/config/traffic_simulation/v17_phase13_execution_log_20260814.yml`
- `reproducibility/config/traffic_simulation/v17_post_phase13_to_experiment_execution_plan.yml`
- `05_src/traffic_simulation/specifications/11_formal_blocker_resolution_exclusion_policy_v17.md`
- `reproducibility/config/traffic_simulation/formal_blocker_policy_v17.yml`

### 9.2 工程 1〜11の完了記録

- `reproducibility/config/traffic_simulation/v17_phase1_to_phase11_record.yml`
- `reproducibility/config/traffic_simulation/v17_phase1_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase2_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase3_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase4_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase5_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase6_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase7_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase8_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase9_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase10_completion.yml`
- `reproducibility/config/traffic_simulation/v17_phase11_completion.yml`

### 9.3 工程 12の契約、実装、試験、成果物

- `05_src/traffic_simulation/specifications/12_phase12_full_population_output_contract_v17.md`
- `reproducibility/config/traffic_simulation/v17_phase12_output_contract.yml`
- `reproducibility/config/traffic_simulation/v17_phase12_output_contract_adoption.yml`
- `05_src/traffic_simulation/network/execute_v17_phase12_full_population.py`
- `05_src/traffic_simulation/network/validate_v17_phase12_run_completion.py`
- `05_src/traffic_simulation/network/validate_v17_phase12_output_contract.py`
- `05_src/traffic_simulation/validation/test_phase12_output_contract_v17.py`
- `05_src/traffic_simulation/validation/test_phase12_run_completion_v17.py`
- `reproducibility/config/traffic_simulation/v17_phase12_independent_rerun_20260813.yml`
- `reproducibility/config/traffic_simulation/v17_phase12_completion.yml`
- `reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase12_20260813_independent_rerun/`

### 9.4 V&V全体と後続工程

- `05_src/traffic_simulation/20260730_20260903_simulation_model_development_and_vv.md`
- `05_src/traffic_simulation/attribute_resolution_execution_procedure.md`
- `reproducibility/config/traffic_simulation/research_stage.yml`

## 10. 更新規則

この文書を最新状態として維持する場合、次のいずれかが起きた時点で同じ変更セット内で更新する。

- Phase完了記録を追加・変更したとき
- Phase 12以降の実行を新規生成したとき
- 阻害要因件数または根本原因分類が変わったとき
- `formal_build_ready`または`attribute_resolution_acceptance`が変わったとき
- v17から新しい版へ移行したとき
- Phaseの定義、順序、完了条件を変更したとき

新しい版へ移行する場合は、本文中の`v17`を機械的に置換しない。母集団版、方針識別子、
構成識別子、データ構造版、完了記録、成果物ハッシュ値を個別に確認し、旧版の履歴を保持する。
