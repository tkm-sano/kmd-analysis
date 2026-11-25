# 検証・再現と保全

開始HEADは `ab79b9ddf52b604d5a162fc66c37b0fc967690d4`。`GIT_STATUS_BEFORE.txt` / `GIT_DIFF_BEFORE.patch` に作業前の未コミット状態を保存し、既存103件のhashを `PRESERVATION_BEFORE.json` に記録した。コードを含む旧ファイルを変更せず、別package・設定・schemaを追加している。作業後の比較は `PRESERVATION_AFTER.json`、最終追加sourceのpatchとhashは `ADDED_SOURCES_FINAL.patch` / `IMPLEMENTATION_MANIFEST.json`。中間patchも保全する。

## 正本と版

- 元研究仕様1〜7：SHA-256 `297be6f6be2be000e627480af189bad1533a385bf269b25fc22dc4922b3de9be`。
- FCFS_v1：`51ab348d893c2044ec0d48e77b74a7d669e012c470e969cf6f971e6863578cd3`。
- 共通条件v1.1：`bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2`。
- 新勤務版：`configs/toc_delivery/duty_break_20261121_v1.json`、`4e6384dff71158184bb9661038c4bd4371c25905b22c97a61411c8ea1a2fe122`。

新設定のhash固定は同じ実装版の条件改変を拒否するためのもの。本実験全体のFreezeではない。既存p・shots・I_dual最終採択の設定とsealはそのまま保存した。

## 実行した検証

新規初回テストは `TEST_INITIAL.xml`、40 passed。追加の回帰・診断・新版再生CLI検証を含む最終実行は `TEST_FINAL.xml`。旧共通テストは `TEST_COMMON.xml` に分離した。中間の `TEST_RELEASE_GROUP.xml` / `TEST_VERIFIED.xml` も保全し、重複を検証数や統計標本へ加算しない。

`TEST_RELEASE.xml` は収集段階で失敗した。旧 `tests/toc_common/test_common.py` が `from conftest import ...` とimportするため `--import-mode=importlib` と互換にならなかった。旧テストやキャッシュを削除・改変せず、共通テストだけ既定のimport方式で別実行した。失敗証跡も保全する。

対象は、08時以前開始・19時境界／超過・バース20時維持・追加オフセットなし、12/13/14時境界、60分連続1回、欠測・重複・作業重複、最終帰着12時境界、未使用除外、場所モード、FCFS待機列の逆転・第2便接続、W定義、複数バース、CP内の一致と不整合の致命停止、B/C実生成、Q割当・順序保持／古典差替え拒否、新旧schema・hashの分離である。

| 最終証跡 | 件数／結果 |
|---|---|
| TEST_FINAL.xml | 144 PASS（うち新勤務版50件） |
| TEST_COMMON.xml | 72 PASS、上記と対象ファイルの重複なし |
| 合計 | 216 PASS、失敗・エラー・skip=0 |
| 旧source/config/Freeze | 103/103 hash一致、HEADと追跡済み差分も不変 |
| 最終再生の旧入力・計画 | 24/24 source hash不変、9/9モデル可行 |
| 最終source登録 | V3の17ファイルと実行後source一致 |

最終144件には既存Swig型の非推奨警告3件とHiGHSへのthreadsオプション転送警告3件がある。72件は警告なし。中間実行の件数を216へ加算しない。

既存共通/FCFS/cargo_wait/I_dualテストも実行した。過去実験全体の再計算やビット再現試行ではない。統計上の独立標本数へテスト・再生・内部CP解を加算しない。

## 再現コマンド

依存環境は既存 `/tmp/kmd-library-validation-20261114-v2/bin/python`。新規依存のインストールなし。以下の `NEW_*` は必ず未使用パスへ置き換える。

```
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
 /tmp/kmd-library-validation-20261114-v2/bin/python -B -m pytest -q -p no:cacheprovider \
 --import-mode=importlib tests/duty_break_v1 tests/fcfs_v1 tests/cargo_wait_v2 tests/d_final_selection_v1 \
 --junitxml=NEW_GROUP.xml

PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
 /tmp/kmd-library-validation-20261114-v2/bin/python -B -m pytest -q -p no:cacheprovider tests/toc_common \
 --junitxml=NEW_COMMON.xml

PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
 /tmp/kmd-library-validation-20261114-v2/bin/python -B -u scripts/duty_break_20261121_v1/replay_scales.py \
 --allow-unverified-rest-locations --output NEW_SCALE_REPLAY

PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
 /tmp/kmd-library-validation-20261114-v2/bin/python -B -m kmd_toc.duty_break_v1 replay \
 --duty-version duty-break-20261121-v1 --base-input BASE_INPUT --plan OLD_PLAN.json \
 --allow-unverified-rest-locations --output NEW_SINGLE_REPLAY
```

新プランの再評価には最後のCLIの `replay` を `evaluate` にし、`--plan` に新版plan.jsonを指定する。根拠を与える場合は `--confirmed-locations LOCATIONS.json`（地点ID→確認根拠のJSON object）。未確認仮定を許可しない既定モードでは、休憩可能地点の根拠なしに可行判定しない。

```
python -B scripts/verify_research_freeze_20261120.py
python -B scripts/verify_fcfs_policy_v1.py
PYTHONPATH=src python -B scripts/verify_d_final_selection_v1.py
```

最終のテスト・再生前の計算source登録は `REGISTERED_SOURCE_HASHES_V3.json`（17ファイル）。これは外側試行の統計的事前登録ではない。`replay_verified_v2/MANIFEST.json` と各ケースの `REPORT.json` にsource・入力・OD・元計画hashと環境を保存する。段階版は上書きせず別ディレクトリとした。

最終化では、真偽値が整数便番号として扱われないこと、および休憩不能な量子候補を古典修復せず棄却して有効な現計画を保持することを追加検証した。両者は旧ファイルを変更せず新版内に実装した。

## 再生の証拠と限界

`RESULTS.csv` は9保存計画、`VEHICLES.csv` は各車両、`TRIPS.csv` は全活動便。各ケースREPORTには、19時に分離した車両レコード、変更しないバース、全訪問・活動区間・休憩、元計画との経路／割当／順序の一致、D不変、総W変化、壁時計・CPU・RSSを保存する。RSSは逐次再生プロセスの生涯高水位で、独立な1計画ごとのピークとしない。再生秒を初期生成込みTへ転用しない。

旧入力は各load_problemの内部でも元manifest/file hashに照合し、終了時には全監査入力・元計画を再hashする。旧C等の時刻が現行FCFSと不一致でも黙って修正せず、明示した固定経路の**新条件再生**として別出力へ保存する。旧結果を新仕様の本実験結果にしない。

場所データ監査は、各規模のStop.sourceとOD metadataの項目を `MANIFEST.json/location_audit` に保存した。建物位置・道路snap・デポ入口確認は、休憩中の停車可能性の証明ではない。モデル可行と現地可行を区別する。今回は地点追加・迂回・道路生成をしていない。

CP解は共通スケジューラとready/start/return/Wの完全一致を検査し、不一致を可行incumbentで隠さない。独立validatorはスケジューラを呼ばず、別のイベントキューと共通ODから時間を再構築する。失敗時は固定割当・有限route pool・共通配置規則の限界とし、全問題の不可行性を証明したとは記さない。
