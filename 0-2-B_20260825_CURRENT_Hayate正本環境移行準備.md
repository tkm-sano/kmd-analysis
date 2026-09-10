# 0-2-B Hayate正本環境移行準備と移行後更新

```text
0-1 社会科学としての問い                    [PARTIAL]
0-2 研究設計                                [CURRENT]
0-3 方法論                                  [CURRENT]
  ├─ 0-2-B 正本実行環境のHayate移行         [CURRENT]  ← 今回
  ├─ 1. 道路・交通条件                      [PARTIAL]
  ├─ 2. 交通状態                            [CURRENT]
  │   ├─ 2-1 公式観測の取得・道路対応       [COMPLETE]
  │   ├─ 2-2 測定断面・検出位置固定         [COMPLETE]
  │   ├─ 2-3 交通量較正                     [CURRENT]
  │   │   ├─ 2-3-A 初期需要の空間不足診断   [COMPLETE]
  │   │   ├─ 2-3-B 初期OD・経路配分再設計   [COMPLETE]
  │   │   ├─ 2-3-C 区外通過OD範囲診断       [COMPLETE]
  │   │   └─ 2-3-D 本人運転OD統合           [PARTIAL]  ← 復帰先
  │   └─ 2-4 未使用観測による独立確認       [BLOCKED]
  ├─ 3. 配送条件                            [PARTIAL]
  ├─ 4. 配送simulation                      [PARTIAL]
  ├─ 5. 配送最適化問題                      [NOT STARTED]
  └─ 6. 計算手法比較                        [NOT STARTED]
```

- Current location: `0-2-B 正本実行環境のHayate移行`
- Parent research stage: `0-2 研究設計 / 0-3 方法論`
- Research question addressed: 研究に用いる交通・配送simulationを、同一データ・同一依存関係・同一乱数条件から再生成できる正本環境をどう固定するか。
- Why this task is necessary: Mac上の容量・CPU・Apple Silicon上のx86コンテナ実行が長時間simulationの主要制約になっているため。
- Main route / Branch route: 研究全体の実行基盤を整える派生ルート。
- Entry condition: Mac側の研究treeとHayateアカウントが存在する。
- Exit condition: 全資産の転送・hash一致、SUMO 1.24.0とPython環境の固定、主要pipelineのsmoke/full validationがHayateで成功する。
- Next destination: `2-3-D`の経路生成検証をHayateで再開し、その後`2-3`数値較正へ戻る。

## 2026-08-25移行後更新

正本repositoryは`/home/takuma/kmd-analysis`へ配置された。現在の標準実行環境は、同repository直下のConda prefixとユーザー領域SUMOである。

| 対象 | 現在の正本 |
|---|---|
| repository | `/home/takuma/kmd-analysis` |
| Python | `/home/takuma/kmd-analysis/.conda/bin/python`、3.11.15 |
| Python依存 | `reproducibility/environment/requirements-analysis.txt` |
| SUMO | `/home/takuma/kmd-analysis/.local/sumo-1.24.0`、1.24.0 |
| 全回帰 | Hayate nativeで`python -m pytest -q 05_src/traffic_simulation/validation` |
| Docker | 任意の副次クロスチェック。正本実行の必須条件ではない |

`.conda/`、`.local/`、`.bashrc`はGit管理しない。依存定義、再構築手順、検証scriptだけをGit管理する。詳細は`reproducibility/environment/README.md`を正本とする。

以下の移行前監査は、当時の判断と未確定事項を残す履歴である。現在の環境状態として読み替えない。

## 移行前監査時点の結論（履歴）

HayateへのRSA公開鍵認証は成功した。Hayateは384 CPU、1.5 TiBメモリを持つx86_64 Ubuntu 24.04サーバーであり、`/home`は14 TB NFS（確認時11 TB空き）である。研究正本の永続保存先として十分な候補だが、ユーザーquotaは確認できていない。

一方、共有SUMO、module、ジョブスケジューラは見つからず、ホストPythonは3.12.3で、研究の基準Python 3.11とは異なる。Dockerは導入済みだが`takuma`はDocker socketを利用できない。したがって、転送前のローカル準備は進められるが、正本実行環境の確定と主要pipeline実行は管理者確認待ちである。

## 事実・解釈・未確定事項

| 層 | 状態 | 内容 |
|---|---|---|
| 接続 | 確認済み | `takuma@hayate.q-est.wide.ad.jp`へRSA公開鍵で接続成功 |
| CPU・メモリ | 確認済み | x86_64、384 CPU、1.5 TiB RAM |
| 永続領域 | 候補確認済み | `/home/takuma`は14 TB NFS上。全体空き11 TB |
| 個人quota | 未確認 | `quota`コマンドがなく、管理者確認が必要 |
| 作業用領域 | 利用範囲確定 | 利用可能なのは`/home/takuma`配下だけ。`/tmp`は使用しない |
| SUMO | 未導入または非公開 | `sumo`コマンドとmodule環境は見つからない |
| Python | 不一致 | ホストは3.12.3。既存分析コンテナはPython 3.11 |
| コンテナ | 権限待ち | Docker 29.6.1 clientは存在するがsocket利用権限がない |
| scheduler | なし | Slurm、PBS、PJm、LSFのコマンド・processは見つからない |

## 正本配置

### 永続保存領域

```text
/home/takuma/research_canonical/
├── repo/research/                 # repo、raw、processed、reproducibility outputsを含む正本snapshot
├── environment/                   # image digest、pip freeze、version出力、環境manifest
├── transfer_manifests/            # Mac→Hayate転送単位のmanifestと検証結果
└── run_registry/                  # run ID、seed、入力hash、出力hash、終了状態
```

現在のコードはrepo-relative pathを前提としているため、最初の移行では9.4 GBの研究tree全体をbyte-for-byteで配置する。データを別領域へ分離するsymlink構成は、既存pipelineの動作確認後に必要性が生じた場合だけ検討する。

### 作業用領域

```text
/home/takuma/research_work/<RUN_ID>/
```

Hayateには、この研究で利用可能な独立scratch領域はない。`research_work`は永続領域と物理的に同じNFS上に置く、論理上の一時作業領域である。高速なローカルscratchとしては扱わない。実行途中の展開物、再生成可能な一時routingファイル、cacheだけを置き、次は作業用領域だけに残してはならない。

- 外部から再取得不能または版固定されたraw data
- 採否判断に使った中間生成物
- comparator、failed probe、warning、stderr/stdout
- 完了・失敗を問わず研究判断に利用したsimulation結果
- seed、入力hash、command、環境versionを含むmanifest

ジョブ終了時は、保存対象を`research_canonical`へコピーし、SHA-256一致を確認してから作業用領域を再利用可能とする。自動削除は導入しない。

## 移行対象

移行manifestは`reproducibility/outputs/environment_migration/20260825_hayate_migration_preparation/`へ生成する。対象はGit metadataを含む研究tree全体であり、未コミット・未追跡の既存研究成果も含む。

移行準備時点の対象は3,000超のfiles/symlinks、約10.1 GBである。正確な件数・bytesは自己参照を避けた`migration_inventory.json`を正とする。Git HEADは`722986952e7242f7389db748124d37ed4006340e`で、working treeは100件を超えるstatus linesを持つdirty snapshotであり、clean checkoutと誤認しない。

| manifest区分 | 概数 |
|---|---:|
| Git repository metadata | 96 MB |
| raw source data | 669 MB |
| processed research data | 1.20 GB |
| reproducibility・simulation outputs | 7.99 GB |
| research outputs | 2.7 MB |
| repository source・metadata | 150 MB |
| temporary review required | 21 MB |

| 区分 | 方針 |
|---|---|
| repo source・設定・文書 | 永続保存、Macから編集同期 |
| `.git`とdirty working tree | 現状態をそのまま移送。HEAD、status、binary diff hashを固定 |
| `03_data/raw` | 永続保存。原本hashを維持 |
| `03_data/processed` | 再利用価値があるため永続保存 |
| `reproducibility/outputs` | failed evidenceを含め全量永続保存 |
| simulation/calibration outputs | 再較正・比較に使うため全量永続保存 |
| `tmp`・`output` | 初回は保全して移送し、移行後に用途を人手review |

## Mac固有pathの監査

実行コード・設定に`/Users/tstakuma/...`を必要とする依存は確認されなかった。検出されたものは次の三種類である。

1. 過去の取得時の実行場所を記録したprovenance。
2. 絶対pathを拒否するvalidation test内の文字列。
3. visualization READMEの説明例。

1と2は意味を変えず保持する。新しい移行scriptは`git rev-parse --show-toplevel`と環境変数からpathを解決し、Macの絶対pathを保存しない。

## Python・SUMO・外部command

既存の正式条件は以下である。

- SUMO 1.24.0。
- SUMO imageは`ghcr.io/eclipse-sumo/sumo@sha256:a49874e6e5e355de055e6a10eefd819d48fab8f0047c3130f782a7dfdf1cc189`。
- analysis imageは`python:3.11-slim-bookworm`を基礎とし、`docker/analysis/requirements.txt`で直接依存をpinしている。
- 外部commandは主に`osmium`、`netconvert`、`marouter`、SUMO、Docker、Git、rsync、SHA-256である。

HayateのホストPython 3.12へ勝手に切り替えない。優先順位は次のとおりとする。

1. 管理者が共有SUMO 1.24.0を提供しているなら、そのbinaryとhash/versionを固定。
2. なければ、管理者承認済みcontainer runtimeで既存のdigest固定SUMO imageを使用。
3. どちらも不可なら、SUMO 1.24.0のユーザー領域buildを別途設計し、実装前に承認する。

Pythonも既存Dockerfileの3.11環境を優先し、Hayate固有の3.12 venvへ暗黙移行しない。環境確定時に`pip freeze`、OS、CPU architecture、image ID/digest、各外部commandのversionを保存する。

## seed・hash・manifest

- 既存コード・設定内でseed関連記録を持つファイルは26件確認した。
- seedを持たない処理でも、入力hash、command、tool version、開始・終了時刻、exit codeをrun manifestへ保存する。
- `RESEARCH_RUN_ID=YYYYMMDD_task_scenario_seed`を作業用領域と永続出力の共通IDにする。
- 転送時はファイルごとのSHA-256とsymlink target hashを検査する。
- expected件数に合わせて再実行結果を調整せず、実測値を正とする。

## 転送手順

管理者確認が完了するまでは実転送を行わない。承認後の手順は次のとおり。

```bash
# Hayate側で永続配置を作る
ssh takuma@hayate.q-est.wide.ad.jp \
  'mkdir -p /home/takuma/research_canonical/repo/research /home/takuma/research_canonical/environment /home/takuma/research_canonical/transfer_manifests /home/takuma/research_canonical/run_registry'

# Mac側で差分だけを確認する（削除なし）
bash reproducibility/scripts/hayate/transfer_research_snapshot.sh dry-run

# 人手でdry-runを確認した後だけ実転送
bash reproducibility/scripts/hayate/transfer_research_snapshot.sh execute

# Hayate側でbyte hashを検証
ssh takuma@hayate.q-est.wide.ad.jp \
  'python3 /home/takuma/research_canonical/repo/research/05_src/research_environment/verify_hayate_migration_inventory.py \
    --root /home/takuma/research_canonical/repo/research \
    --inventory /home/takuma/research_canonical/repo/research/reproducibility/outputs/environment_migration/20260825_hayate_migration_preparation/migration_inventory.json'
```

転送scriptは意図的に`--delete`を使用しない。過去成果やfailed evidenceを転送同期で削除しないためである。

## 主要pipelineの確認順序

1. 転送manifest全件のSHA-256一致。
2. Git HEAD・dirty status hash・working-tree patch hash一致。
3. Python 3.11、依存version、SUMO 1.24.0、image digest一致。
4. path・schema・小型fixture test。
5. SUMO `netconvert --version`と最小fixture network生成。
6. v17道路網の既存focused validation。
7. 191配送先の往復到達性とSUMO Network Integration Acceptance再確認。
8. 2-3-Dの公式PT外外本人運転ODによる経路生成。
9. 固定27測定群・160検出位置の不変確認。
10. full regression後にのみ2-3数値較正を再開。

## 管理者確認が必要な事項

1. `/home/takuma`の個人quotaとbackup方針。
2. 共有SUMO 1.24.0の有無。異なるversionしかない場合は使用しない。
3. Docker group付与が許可されるか、代わりにrootless Podman/Apptainerを使うべきか。
4. schedulerが本当にないか、長時間処理の正式な起動・監視方法。

Docker groupは実質的に管理者権限へつながるため、こちらから勝手に所属変更を依頼・実施せず、管理者の運用方針に従う。

## 移行Acceptance Criteria

- Mac側manifestの全file/symlinkがHayateで一致する。
- source raw data、historical output、failed evidenceに欠落・上書きがない。
- SUMOは正確に1.24.0で、version出力とimage/binary provenanceが保存される。
- Pythonの基準versionと全依存が固定される。
- Mac固有絶対pathなしで主要pipelineが動く。
- seed、入力hash、tool version、command、exit code、出力hashがrunごとに残る。
- 作業用領域の保存対象が正本領域へhash確認付きで回収される。
- 既存focused validationとfull regressionがHayateでpassする。
- 191配送先の往復到達性、27測定群、160検出位置が変化しない。
- Macで生成したsimulation結果を正本として扱わない運用へ切り替わる。

## 終了時記録

- What was learned: Docker daemon権限がなくても、repository直下のConda環境とユーザー領域SUMOで正本処理を構成できる。
- What was decided: Hayate native CondaとSUMO 1.24.0を正本とし、Dockerは任意の副次環境とする。
- What remains unresolved: native全回帰、主要pipeline、191配送先、27測定群・160検出位置の再確認。quota、backup、長時間処理運用も管理者確認が残る。
- Whether this branch is closed: いいえ。`CURRENT`。
- Where we return to in the main route: native検証合格後、`2-3-D`から`2-3 交通量較正`へ戻る。

要するに、正本実行方式はHayate native CondaとSUMO 1.24.0へ確定した。残るのは、この環境での全回帰と主要pipelineの実測確認である。
