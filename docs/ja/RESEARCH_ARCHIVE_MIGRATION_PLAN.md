# 旧方針・履歴レコードのアーカイブ移行方針

作成日：2026-09-28<br>
状態：方針策定済み・移行未実施（PLAN_ONLY）

現行の研究方針と、過去の方針・実行履歴を分離する。旧方針は履歴として保存し、日常の参照先と将来の実行前検査を、現在必要な正本と依存ファイルへ絞る。古いという理由だけで実験証拠を削除しない。

この文書は移行計画であり、凍結済みの科学authority、保護対象一覧、実行条件を変更しない。科学実行、ファイル移動、削除、予算消費、予約は行っていない。

## 1. 判定基準

作成日ではなく、現在の役割と依存関係で分類する。同じディレクトリ内でもファイルごとに役割が異なる場合がある。

| 分類 | 判断基準 | 扱い |
| --- | --- | --- |
| 現行正本 | 当該範囲の最新方針・条件・予算・実行入口 | 現行領域に保持 |
| 現行依存物 | 現行コードが読み込むコード、設定、回路情報、検証器、証拠 | 古くても保持。依存解消後に移行を再判定 |
| 歴史的証拠 | 完了した実験結果、台帳、当時の予算・判断・生データ | 内容を変えずアーカイブ。現行参照があれば先に解決 |
| 失効・継承済み方針 | 後継の正本があり、現在の実行を直接規定しない指示・checkpoint | 後継との関係を記録し、アーカイブ候補にする |
| 再生成可能物 | キャッシュや一時ファイルで、必要な証拠・依存物ではない | アーカイブとは別に削除候補として審査 |
| 未判定 | 後継、参照元、保存理由が不明 | 移動・削除せず保留 |

研究タイトル、研究の問い・仮説、現在の研究計画は、実行authorityとは別の範囲の現行文書として扱う。「最新」をリポジトリ全体で一つの日付に揃えない。

## 2. 最初の分類対象

以下は候補の整理であり、各ディレクトリ全体の移動決定ではない。

| 対象 | 方針 |
| --- | --- |
| Runtime Policy V1と旧時間不足判断 | 歴史的authorityとして保存。V2で過去の残時間やBLOCKED判断を書き換えない |
| OFFLINE_ACCEPTANCE_ASSERTIONや開始時計欠落によるNOT_EXECUTED | 当時の記録として保存。PASSに変更しない |
| 後続の統合で解消済みのPARTIALLY_FROZEN、修正・準備記録 | 後継正本を明示し、現行依存がないものからアーカイブ |
| 完了済みstate実行の旧入口 | 現行入口から外す。歴史的スクリプトは削除しない |
| state実行統合ディレクトリの共通コード | 一括移動しない。samplingが利用するコードは現行依存物 |
| N002/M2のstate-level PASS成果物 | samplingの前提・回路identityの参照元を保持。単なる古い結果とは扱わない |
| N003/N004、Phase1/Phase2、N5、forensicの結果 | 歴史的証拠として保持。現在の判断根拠への参照を維持 |
| Battery、fleet、TW、formulation、Protocol v2 | 現在も有効なものは保持。後継が確認できた版だけ履歴化 |
| 旧状況説明を含む主要概要文書 | 必要なら旧版を保存したうえで、現行説明と履歴リンクを分離 |
| テストfixture、キャッシュ、一時ファイル | テスト証拠と再生成可能物を区別。凍結manifestへの包含理由を確認 |

現行sampling実装では、旧state統合の `audit_bridge.py` を読み込み、state成果物の `CANONICAL_CIRCUIT_METADATA.json` と `STATE_DECISION.json` を参照する。また、広い範囲の `SOURCE_PINS.json` / `PROTECTED_SOURCE_PINS.json` を検証する。このため、旧ディレクトリを先に移すと現行入口の受入検査が壊れる。

確認先：

- [現在の実行状況](../../CURRENT_EXECUTION.md)
- [sampling共通処理](../../reproducibility/outputs/traffic_simulation/r24_finite_shot_supervised_execution_integration/20260928_v1/sampling_common.py)
- [sampling pipeline](../../reproducibility/outputs/traffic_simulation/r24_finite_shot_supervised_execution_integration/20260928_v1/sampling_pipeline.py)
- [sampling監督入口](../../reproducibility/outputs/traffic_simulation/r24_finite_shot_supervised_execution_integration/20260928_v1/run_sampling_supervised.py)
- [既存の歴史的入口一覧](HISTORICAL_EXECUTION_ENTRYPOINTS.md)

## 3. 保護方法の整理

将来の保護を次の二つに分ける方針とする。

1. **実行時の保護**：現行authority、科学入力、回路・設定、decoder・validator、必要なライブラリ、active budget・ledgerなど、実行の正当性に必要な依存物を検証する。
2. **履歴の保護**：アーカイブ全体のmanifestとハッシュで証拠の完全性を検証する。移行時、復元時、および別途定める保存点検で確認する。

現在の凍結済み保護一覧から項目を直接削除しない。実行時の対象を縮小する場合は、依存関係を確認した新しい版の検証authority・manifest・入口を作り、オフライン回帰試験後に将来向けに切り替える。元の一覧と判断は保存する。

削減するファイル数や割合を先に目標にしない。過去の一覧に載っていることだけを永続保護の理由とせず、現在必要な依存か、歴史保存だけでよいかを説明できる状態を目標にする。

## 4. 移行台帳と保存形式

移行前に、各候補について次の項目を台帳へ記録する。

- 元パス、移行先、分類、対象範囲、後継正本、移行理由。
- 現行参照・import・動的読込み・manifest参照の有無。
- SHA-256、サイズ、Git追跡／未追跡／ignoredの区分。
- バックアップの保存先と検証結果、移行batch、復元方法、未解決点。

保存先案は `reproducibility/archive/traffic_simulation/r24/<移行版>/payload/<元のリポジトリ内パス>` とする。研究概要などの履歴は既存の `archive/project_management/` の規約に合わせる。

各batchに外付けのREADME、移行manifest、SHA-256一覧、旧パス対応表を置く。歴史的payload内の記述、古いパス、当時のmanifestを直接修正しない。対応表と読取り専用resolverで解決し、必要な再現は隔離した作業先へ旧パス構造を復元して行う。

[既存R23アーカイブ](../../reproducibility/archive/traffic_simulation/r23/README.md)と[移行記録](../../reproducibility/archive/traffic_simulation/r23/ARCHIVE_MANIFEST.md)を先例とする。追跡済みファイルは原則 `git mv`、ignoredの成果物はGitだけをバックアップとみなさず別コピーを検証する。大容量成果物を一括でGit追跡へ追加しない。

同じディスク内の移動は容量削減にならない。今回の主目的は現行方針と履歴の分離であり、圧縮・外部保管・削除は別途判断する。

## 5. 段階的な実施順序

### 第1段階：候補台帳の作成

読取りだけで候補を分類する。現行入口を起点に依存関係を確認し、後継正本と移行先の対応を具体化する。未判定のものは保留する。これを次の作業とする。

### 第2段階：参照先の整理

主要文書からは現行正本を参照し、旧方針は履歴一覧から辿る形にする。旧版を保存し、科学的な結論や研究条件を変更しない。この段階では物理移動を急がない。

### 第3段階：現行依存と履歴検証の分離

旧コード・旧パスを現在も使う箇所を解決する。必要なら共通コードの配置・adapter・将来用manifestを版管理し、科学ロジックを変えずにオフライン試験する。新しい検証authorityへの切替が必要な箇所は明示し、旧authorityを上書きしない。

### 第4段階：バックアップと段階移行

先にコピーとハッシュ一致を確認する。依存が解消済みの旧方針文書から小さなbatchで移行し、旧入口、完了済み証拠は別batchにする。現行検証が旧パスを要求する間は移動しない。一括削除やディレクトリ単位の無条件移動は行わない。

### 第5段階：検証と移行確定

以下を満たすbatchだけを確定する。

- 移行前後でpayloadのハッシュ・サイズが一致する。
- 現行リンク、コード依存、manifest参照が解決できる。
- 履歴の旧パス対応と復元手順が検証できる。
- 必要な既存監督・統合テストがfake workerで通る。科学backendは呼ばない。
- 科学台帳・予算・既存結果が不変で、実行guardが閉じている。
- `git diff --check` が通り、無関係なユーザー変更を保持している。

依存不明、バックアップ不備、ハッシュ不一致、参照破損、科学task実行中の場合は該当batchを停止する。復元は移行台帳に従って元のバイト列とパスを戻す。科学実行のretryや予算リセットは行わない。

## 6. 完了条件と非対象

現行正本が範囲ごとに一意に辿れ、旧方針が現行指示と混同されず、必要な歴史的証拠を復元・検証できれば移行完了とする。全履歴を毎回の科学実行前に読み直す必要性と、証拠を保存する必要性を区別する。

本計画は研究内容、科学結果、Protocol v2、Runtime Policy V2、shot数、seed、数値閾値、取得方式、時間・資源上限を変更しない。state budgetの2/2消費、sampling budgetの0/2 calls・0/128 shots、予約0は正本の記録をそのまま保持する。過去のFAIL・BLOCKED・NOT_EXECUTEDを再解釈しない。

本方針策定での移動・削除・科学実行・backend呼出し・shots・optimizer・retry・reservationはすべて0。METHOD_COMPARISON_SCALEとMain S0の状態も変更しない。
