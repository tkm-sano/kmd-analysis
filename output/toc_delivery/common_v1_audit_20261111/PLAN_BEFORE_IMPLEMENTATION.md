# A〜D共通基盤 実装前計画 v1.0

採用日：2026-11-11。ユーザーの「A〜D共通条件 v1.0」を今回の正本とする。本ファイルの初版を証拠ディレクトリへ保存した後に実装を開始する。

## 監査で確認した差分

- 作業開始時HEADは8605d54、mainはorigin/mainより7 commit先行。読み取り専用の`git ls-remote origin HEAD`は1b00bd7927fa1e7688e4772ac1da9db46d9bac11。pull/resetしない。
- README/.gitignoreに既存変更、大量の未追跡成果が存在する。AGENTS.mdはリポジトリ内・親階層で見つからない。
- 11/8計画DOCX・study.json・contracts.pyは旧HOLD契約。11/10需要追補を優先し、今回の容量60、作業120秒、積込1800秒、準備900秒、8〜20時、均等ready、最大2便・未使用可を新しい設定へ採択する。
- Aは代理計画から出典付き実績・参照水準へ、BはVeRyPy Clarke–Wright、CはOR-Tools、DはHuang CG＋AOA。既存文書は保全し差分を新文書へ記載する。
- DEP_006（35.586971,139.745306）は代理座標。車両用出入口の根拠は未確認。既存SUMO対応・固定担当内ODは新OSRM全有向ODへ転用しない。
- Dの日列・価格付け改善は小規模人工問題の成果。長い便、全列依存、整数化、秒精度と研究ODの接続はHOLDを維持する。

## 保全対象・変更境界

凍結需要8ファイル、既存src/tests/scripts/configs、A〜C・Dコード、研究計画DOCX、旧研究文書・保存結果、README/.gitignoreの既存変更を保全する。既存ファイルは編集しない。新規のcommon/、設定、テスト、実行スクリプト、共通文書・監査成果だけを追加する。アルゴリズム本体の変更予定はない。commit/push、本比較実験、需要生成、公開OSRMへの通信は行わない。

## 構成・依存関係・実装順序

|順|新規パス|役割・依存|
|---|---|---|
|1|configs/toc_delivery/common_conditions_v1.json|版付き採択値・由来・単位・未確認項目。標準ライブラリJSON|
|2|src/kmd_toc/common/config.py, models.py|設定値厳格検査、不変モデル、JSON入出力・fingerprint。凍結loaderだけを既存から利用|
|3|src/kmd_toc/common/od.py|有向distance/time同経路OD、欠損・到達不能・snap監査、mmap binary読込、ローカルOSRMブロック生成。NumPyはOD保存読込時のみ|
|4|src/kmd_toc/common/validation.py|解法をimportしない秒単位の独立全制約検査・D/W再計算。失敗は理由を保持しnull指標|
|5|src/kmd_toc/common/runtime.py, adapters.py|読込前から検証終了までのperf_counter計時、Dへの単位変換入口（求解なし）、B/C/D接続契約|
|6|tests/toc_common/|4〜6/20地点の人工有向OD、手計算/Decimal別実装、変異試験、入出力・時計境界、凍結hash・文書設定同期|
|7|scripts/audit_toc_common.py|凍結需要/既存道路hash、下界・資源見積り・小規模検証記録。最適化を呼ばない|
|8|docs/research/toc_delivery_common/COMMON_*.md|条件・監査・仕様・検証・適用判定。条件表はJSONから生成しテストで一致検査|

証拠はoutput/toc_delivery/common_v1_audit_20261111/。初期status、既存ファイルhash、計画snapshot/開始時刻、入力出力、テストlog、時間/RSS、hash再照合、diffを保存する。新規依存のインストールは予定しない。既存vehicle-day-v1環境のPython/NumPy/pytestを使用する。

## ODの設計判断

OSRM tableの`annotations=distance,duration`を同一要求で取得する。距離は採択した最速経路の道路距離であり、最短距離とは主張しない。fallback_speedを禁じ、nullを到達不能として保存する。全必要ペアの欠損・到達不能は本実験HOLD。道路源のURL/取得日時/OSM日時/版/生データ・profile・生成成果hash、OSRM版・実行引数をmanifestへ保存する。

固定需要の座標を変更せず、別表にnearestの座標・hint・node候補・snap距離・確認根拠を保存する。距離閾値は自動承認根拠ではない。高速道路、反対車線、私道、入口の誤対応は地図・アクセス確認を要し、未確認は拒否する。全ペアは同じhint・座標・profile・graphを使う。公共サーバは拒否しローカルloopbackのみ許可する。

S3の4001²ペアはブロック100×100、1681要求を上限見積りとし、2 float64＋1 boolで272,136,017 bytes＋metadata。全行列をPython objectへ展開せずmmap/逐次書込み。実時間はローカルgraph構築・小ブロック測定後のみ推定し、未測定を創作しない。今回は研究OD生成は入口確認不足のため実行しない。

## 独立テストと完了条件

1. Test 1：ID/欠損/単位/数/需要/凍結pin、設定改変・hash不一致の拒否。
2. Test 2：shape/対角/有向非対称/null/欠損/単位/同じODの経路再計算。OSRM応答stubとblock読込も検査。
3. Test 3〜5：0/1/2便・3便拒否、容量、準備前/帰着前2便、積込/バース競合/境界、作業時間、20時ちょうど/超過。
4. Test 6：同一計画を別実装でD/W再計算。Tを偽時計と実時計で検査、読込・変換・求解・復号・整数化・後処理・検証を含む。
5. Test 7：開始時の全保全対象hashを終了時再照合。新規テストと既存ToC/Dテスト、既存公開APIの回帰検査を実施し失敗も記録。

条件定義、共通モジュール、小規模検証、実OD、A参照値、B/C/D全体接続、S1〜S3は別判定とする。容量/時間下界は可行性証明ではない。未取得OD・入口・solver機能不足が残る限りS1〜S3はHOLD。ε水準は可行参照計画後までnullを維持する。
