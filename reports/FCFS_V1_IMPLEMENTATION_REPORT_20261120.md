# FCFS_v1正式採用・実装・整合性検証（2026-11-20）

**積込規則の判定：PASS。本実験全体：HOLD。** 追加のFCFS採用判断は不要。正式全体Q、計算時間上限、n/K/R_local、目的・統計等の未決定事項を今回自動承認しない。

## 1. 凍結

運用仕様 `docs/research/FCFS_OPERATING_POLICY_V1.md`、SHA-256 `51ab348d893c2044ec0d48e77b74a7d669e012c470e969cf6f971e6863578cd3`。全文manifestは `docs/frozen/FCFS_V1_MANIFEST.json`。元研究仕様1〜7は `297be6f6be2be000e627480af189bad1533a385bf269b25fc22dc4922b3de9be` のまま。双方の固定hash検証PASS。
FCFS_v1は追加運用仕様であり原本の数式・数値・H1・I_dualを変更しない。将来は明示承認と新規FCFS_v2が必要。検証scriptと新規CIを追加し、生成・検査時にも固定hashを確認する。commit/push・リモート設定変更・README変更は行っていない。

## 2. 共通化した処理と変更位置

|対象|実装・位置|適用内容|
|---|---|---|
|共通スケジューラ|[src/kmd_toc/fcfs_v1/scheduler.py:10](../src/kmd_toc/fcfs_v1/scheduler.py#L10)、[src/kmd_toc/fcfs_v1/scheduler.py:56](../src/kmd_toc/fcfs_v1/scheduler.py#L56)|全便共通待機列、ready/ID優先、全空きバース中ID最小、全時刻・訪問・帰着再計算|
|独立検証|[src/kmd_toc/fcfs_v1/validation.py:6](../src/kmd_toc/fcfs_v1/validation.py#L6)|別方式のイベント再生＋共通物理検査。不適合を拒否|
|CPモデル|[src/kmd_toc/fcfs_v1/cp.py:24](../src/kmd_toc/fcfs_v1/cp.py#L24)|モデル内部でFCFS開始再帰とready順位を制約化。CPとスケジューラの時刻・Wを完全照合|
|候補比較前の完成|[src/kmd_toc/fcfs_v1/cp.py:157](../src/kmd_toc/fcfs_v1/cp.py#L157)|初期候補・CP候補ともFCFS後のD/Wを比較。最終評価だけの修復ではない|
|B/C完成器の接続|[src/kmd_toc/termination_v1/solvers.py:7](../src/kmd_toc/termination_v1/solvers.py#L7)、[src/kmd_toc/termination_v1/solvers.py:86](../src/kmd_toc/termination_v1/solvers.py#L86)|FCFS_v1フラグ時のみ新完成器。旧設定の再現分岐を保持|
|既存名Dの整数処理|[src/kmd_toc/fcfs_v1/master.py:5](../src/kmd_toc/fcfs_v1/master.py#L5)、[src/kmd_toc/termination_v1/master.py:90](../src/kmd_toc/termination_v1/master.py#L90)|固定カレンダーWのIPを使用せず、同じ経路プールのFCFS CP完成へ接続|
|D候補の採択接続|[src/kmd_toc/termination_v1/methods.py:39](../src/kmd_toc/termination_v1/methods.py#L39)|FCFS整数候補から全時刻を構築してから既存のD/W比較へ渡す|
|新局所Q|[src/kmd_toc/fcfs_v1/local.py:7](../src/kmd_toc/fcfs_v1/local.py#L7)、[src/kmd_toc/fcfs_v1/local.py:17](../src/kmd_toc/fcfs_v1/local.py#L17)|既存の2便再配分を保持し共通スケジューラ使用。採択規則を新規決定しない|
|現行人工入口|[src/kmd_toc/cargo_wait_v2/methods.py:10](../src/kmd_toc/cargo_wait_v2/methods.py#L10)|通常はFCFS_v1を強制。Qを内部Dへ明示対応。旧生成はhistorical_reproduction=True|
|履歴adapter検証|[tests/cargo_wait_v2/test_waiting.py:206](../tests/cargo_wait_v2/test_waiting.py#L206)|旧pass-through検証にhistorical_reproduction=Trueを明示。現行FCFSは独立testで検証|
|凍結検証|[src/kmd_toc/fcfs_v1/policy.py:22](../src/kmd_toc/fcfs_v1/policy.py#L22)、[scripts/verify_fcfs_policy_v1.py:11](../scripts/verify_fcfs_policy_v1.py#L11)|固定期待hashを参照し、通常実行・CIで改変検出|
|現行評価・適格性|[src/kmd_toc/fcfs_v1/evaluation.py:5](../src/kmd_toc/fcfs_v1/evaluation.py#L5)、[scripts/analyze_dw.py:13](../scripts/analyze_dw.py#L13)、[scripts/evaluate_fcfs_v1.py:13](../scripts/evaluate_fcfs_v1.py#L13)|FCFSを独立検証し総積込Wを明示。不適合・旧新混在を拒否。入力を黙って修復しない|

経路生成（CW、Routing、量子候補の復号・マクロ構成）を変更しない。CPでは補助の時刻/rankを先に分岐して有限仕事量を費やすことを避けるため、既存FIXED_SEARCH内で経路選択変数を先に分岐する順序を明示した。距離優先・同距離時に総積込W、0.1m分解能、最大256 conflicts・最大8改善解等の既存有限仕事量設定は変更しない。これらを正式な本実験停止規則として新採択したわけではない。
旧Dの共有FCFS待機は車両日列の加算費用では表せないため、旧待機IPを呼ばない接続が必要となった。LPは距離pricingの補助だけに使い、旧Wを最適化・採択指標とせず、FCFS全体問題の証明付き下界とも称さない。実装versionをFCFS_v1として区別する。
旧DのIP node上限はFCFS制約付きCPの仕事量へ直接換算できない。新経路では既存の共通完成器のconflict/callback上限を利用し、正式な本実験の時間・停止契約として採択していない。旧IPと新CPの計算費用を同条件として混ぜない。
旧hash固定の局所予備・P1・量子kernel・過去成果は変更していない。新局所Qはfcfs_v1.localの別接続を用いる。正式全体Qランナーは以前から未完成でHOLD、今回それを完成済みにはしていない。低水準旧実装を直接呼んだだけでは現行FCFS有効計画とならず、厳格な評価ゲートの独立検証が必要。旧登録のsource hashを書き換えて再開せず、必要な履歴再現には保存snapshotと別出力を用いる。

## 3. CP内FCFSの数学的整合

同じ30分積込・同じ利用可能時間帯のmバースについて、readyとIDで並べた活動便jの開始はmax(ready[j],start[j−m]+1800)。先頭m便は開場時刻とのmaxをとる。第2便ready=第1便開始+積込+走行+作業であり、順位は経路・開始に依存するのでCPで同時に解く。inactive sentinelは全活動便の後ろに置く。
最終スケジューラはCPの自由時刻を修正するのではなく、同じ数理モデルの時刻を再構築して一致を検査する。一致しない場合はFCFSModelConsistencyErrorで停止し、可行incumbentへの退避で隠さない。独立検証器はこの再帰式も製品スケジューラも呼ばず、到着・バース解放のイベントを再生する。

## 4. 自動検証

最終releaseは **88 passed、failures/errors/skipped=0**。証拠：[TEST_RELEASE.xml](fcfs_v1_20261120/TEST_RELEASE.xml)。別途CLI有効/不適合拒否の2件も確認。[CLI_ELIGIBILITY.json](fcfs_v1_20261120/CLI_ELIGIBILITY.json)。
CP失敗ガードの最終変更後にもFCFS関連30件を再実行し全通過（TEST_FCFS_AFTER_GUARDS.xml）。releaseと重複する回帰であり、独立試行数に加算しない。
- 1/複数バース、異なる/同一ready、全バース使用中、同時解放、IDの昇順、意図的アイドル拒否。
- 第2便の帰着release、全車共通待機列、作業非中断、全便30分、容量・最大2便・勤務終了の再検証。
- 「最も早く空いたバース」と「現在空いているID最小」の差を検証。
- 小規模CP解の目的Wと再構築Wの一致、独立全割当列挙の最小D/Wとの一致、30個の決定的人工ケースで別イベントoracleとの照合。これらのseedを需要の独立試行数へ加えない。
- 同じ経路・readyをB/C/Q/Dへ与えて全積込時刻・バース・Wが一致。
- B/Cの実経路生成、D/Q aliasの量子エンジン代役による候補伝播、旧待機IP非呼出し、新局所Qの再配分保持を確認。実量子回路・実shotsは0であり、量子品質の実測とはしない。
- CP不整合の致命停止、旧新結果混在拒否、FCFS/元研究仕様のhash改変・欠落・manifest同時改変のFAIL。改変テストはコピーのみ。
初回は.condaにVeRyPy/Qiskitがなく、一部は環境不足で失敗した。人工長距離fixtureのOD hashも修正した。完全な既存環境へ切替後、CP分岐順と旧adapterテストの明示的履歴指定を検証した。途中の失敗XMLも保全している（TEST_HISTORY.json）。新規依存のインストールは行っていない。
Swigの非推奨警告と、既存HiGHSへのthreadsオプション転送警告が残るがテスト失敗ではない。テストwall timeはNFS読込待ちを含み、計画作成時間Tや性能比較に使わない。

## 5. 保存計画の分類と指定事例

監査範囲は旧登録75試行と、列挙時点で保存済みだったp2予備の最終plan.json 30件、計105件。入力を各規模ごとに一度に1組だけ読み、768MiBの安全ゲートを設けた。最適化・量子処理は起動していない。
|分類|件数|扱い|
|---|---:|---|
|FCFS適合|64|積込規則だけの適合。他の本実験条件はHOLD|
|FCFS不適合|26|本実験主要比較に使用不可|
|未確認（監査範囲内）|0|列挙後の更新や他研究・中間候補まで0件と主張しない|
|対象外|15|旧A計画。現行の行政参照Aではない|

|旧予備の対象|S1 適合/不適合|S2 適合/不適合|S3 適合/不適合|
|---|---|---|---|
|B|5/0|5/0|5/0|
|C|0/5|0/5|0/5|
|D|5/0|0/5|4/1|
|D古典代役（診断）|5/0|0/5|5/0|
p2局所予備の最終保存計画30件はこのスナップショットでは全て適合（S1 18、S2 10、S3 2）。これはFCFS_v1で新しく生成した性能結果ではなく、旧計画の時刻の適合分類である。その他の未監査・途中・更新後の計画は未確認として扱う。
全ファイル・source hash・違反フィールドは[CLASSIFICATION.json](fcfs_v1_20261120/past_plan_audit/CLASSIFICATION.json)とCSVに保存。旧新の生成版を評価出力にも保持し、混在を拒否する。

|指定S1 C 第2便|ready|旧積込開始|FCFS開始|FCFS帰着|
|---|---|---|---|---|
|v3|12:13:56|12:29:38|12:27:55|15:57:59|
|v2|12:22:23|12:27:55|12:29:38|15:59:44|
同じ経路の実再構築で全物理制約・FCFS適合を確認。Dは不変、旧/新の総積込Wはともに354.983333333333分。この例でW改善を主張しない。他計画の結果をここから推測しない。元ファイルを保全し、新計画は[S1_C_r01_CONVERTED_PLAN.json](fcfs_v1_20261120/past_plan_audit/S1_C_r01_CONVERTED_PLAN.json)へ分離した。

## 6. D/W・凍結値・既存変更への影響

Dの全デポ発着を含む道路距離、W=Σ(start−ready)/60、I_dual、H1、S1〜S3、p2、学習1000/最終10000、容量・作業時間は変更していない。平均Wは旧評価器の診断欄として残るが、FCFS入口の研究W_minは総積込Wを明示する。I_dualの本体実装・統計支持・最適化目的の正式選定を今回追加しない。
固定経路の再構築ではDは不変だがW・帰着・可行性は変わり得る。FCFS制約付き探索で採択経路が変わればDも変わり得る。S1〜S3を最適化し直していないので、その性能差は未測定。
PRESERVATION.jsonで元研究仕様全文・manifest、p/shots凍結、既存研究設定、README、AGENTS、旧局所Qコード、開始時の他の未コミット変更の内容hash一致を確認した。HEAD不変。旧登録75計画のsource hashも一致。既存出力・需要・OD・ログを書き換えず、独立して動いていた予備プロセスを停止・起動していない。

## 7. 残存事項と次工程

積込規則の追加意思決定は不要。FCFS_v1の部品とB/C/内部D、新局所Qの共通経路は利用可能。正式全体Q・同一時間契約・n/K/R_local・最適化目的・量子W改善方法・試行数・統計的支持等は本依頼の範囲外で未確定。本実験全体のHOLDを維持する。
新規計画・本実験を開始する場合は新しい登録/source hash/出力を使い、FCFS厳格評価を必須にする。過去source sealを新しい値に差し替えたり、旧非FCFS結果を再ラベルして比較へ入れない。
新規CIはローカルファイルだけ追加。リモート保護・必須check・レビュー設定は変更せず、CIのリモート実行は未確認。FCFS仕様を正当な改訂なしに書き換えないことをローカルhashだけで完全強制できるとは主張しない。

## 8. 再現と成果物

```bash
python -B scripts/verify_fcfs_policy_v1.py
python -B scripts/verify_research_freeze_20261120.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /tmp/kmd-library-validation-20261114-v2/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/fcfs_v1 tests/cargo_wait_v2/test_waiting.py tests/cargo_wait_v2/test_quantum_connection.py \
  tests/test_research_freeze_20261120.py tests/test_research_freeze_contracts_20261120.py
# 保存計画の再監査は必ず別の未使用出力先へ（最適化は起動しない）
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .conda/bin/python -B scripts/audit_fcfs_v1.py --output <new-directory>
```

環境versionはENVIRONMENT.json、修正前コードとhashはbefore/とBEFORE.json、差分はCODE_DIFF_FROM_TASK_START.patch、コード位置はCODE_POSITIONS.json、全成果物の一覧はFILES.jsonへ保存。元の未コミット差分を含むgit diffと、今回の変更差分は区別する。
