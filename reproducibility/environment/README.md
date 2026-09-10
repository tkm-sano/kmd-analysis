# HayateネイティブConda正本実行環境

文書ID: `DOC-HAYATE-NATIVE-CONDA-ENVIRONMENT`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-08-25`
最終更新日: `2026-09-03`
現行正本: `reproducibility/environment/requirements-analysis.txt`

```text
0-1 社会科学としての問い                    [PARTIAL]
0-2 研究設計                                [CURRENT]
0-3 方法論                                  [CURRENT]
  ├─ 0-2-B 正本実行環境のHayate移行         [CURRENT]
  │   ├─ 0-2-B-1 Mac側Git整理               [COMPLETE]
  │   └─ 0-2-B-2 Conda正本化                [COMPLETE] ← この文書
  ├─ 1. 道路・交通条件                      [PARTIAL]
  ├─ 2. 交通状態                            [CURRENT]
  │   └─ 2-3 交通量較正                     [CURRENT]  ← 環境確認後の復帰先
  ├─ 3. 配送条件                            [PARTIAL]
  ├─ 4. 配送simulation                      [PARTIAL]
  ├─ 5. 配送最適化問題                      [NOT STARTED]
  └─ 6. 計算手法比較                        [NOT STARTED]
```

- 現在位置: `0-2-B-2 Hayate実行環境のConda正本化`
- 上位研究段階: `0-2-B 正本実行環境のHayate移行`
- 対応する研究上の問い: Docker daemonを使わず、同じPython依存とSUMO版から研究処理を再実行できるか。
- 必要性: Hayateでは一般ユーザーがDocker daemonを利用できず、Dockerを必須条件にすると正本環境で実行できないため。
- 本線／派生ルート: 研究の正本実行基盤を固定する派生ルート。
- 開始条件: HayateにPython 3.11.15のConda prefixとSUMO 1.24.0が存在する。
- 完了条件: native環境検証、`pip check`、全交通simulation回帰が合格し、Dockerなしで再実行できる。
- 次の作業: Hayate上の主要pipeline確認後、`2-3-D`から交通量較正へ戻る。

## 正本と副次環境

| 対象 | 位置付け | 正本 |
|---|---|---|
| Hayate native Conda | 標準・正本実行環境 | Python 3.11.15、`requirements-analysis.txt` |
| Hayate native SUMO | 標準・正本SUMO実行環境 | SUMO 1.24.0 |
| Docker Compose | daemonを利用できる環境での任意クロスチェック | 正本ではない |

依存定義をDockerfileと別に手動複製しない。Python依存の唯一の現行正本は次である。

```text
reproducibility/environment/requirements-analysis.txt
```

`docker/analysis/Dockerfile`も同じファイルを参照する。旧研究の`legacy/non_sumo_route_proxy_analysis/reproducibility/requirements-lock.txt`は別の凍結監査環境であり、変更しない。

## 現在の標準起動

新しいVSCode terminalまたはSSHの対話bashでは、ユーザーの`.bashrc`により自動有効化される。非対話shellや明示的に再設定する場合は次を実行する。

```bash
cd /home/takuma/kmd-analysis
source /opt/miniconda/etc/profile.d/conda.sh
conda activate /home/takuma/kmd-analysis/.conda

export SUMO_HOME=/home/takuma/kmd-analysis/.local/sumo-1.24.0/share/sumo
export PATH=/home/takuma/kmd-analysis/.local/sumo-1.24.0/bin:$PATH
export PYTHONPATH=/home/takuma/kmd-analysis/.local/sumo-1.24.0/share/sumo/tools:${PYTHONPATH:-}
export LD_LIBRARY_PATH=/home/takuma/kmd-analysis/.conda/lib:${LD_LIBRARY_PATH:-}
```

`.bashrc`自体はユーザーローカル設定でありGit管理しない。Gitで管理するのはこの手順、環境変数例、依存正本、検証scriptだけである。

## Conda環境の新規再構築

次は`.conda`が存在しない新規構築時だけ実行する。既存環境を同名で上書きしない。

```bash
cd /home/takuma/kmd-analysis
test ! -e /home/takuma/kmd-analysis/.conda
source /opt/miniconda/etc/profile.d/conda.sh
conda create --prefix /home/takuma/kmd-analysis/.conda python=3.11.15 pip
conda activate /home/takuma/kmd-analysis/.conda
python -m pip install -r reproducibility/environment/requirements-analysis.txt
python -m pip check
```

`.conda/`と`.local/`はHayate固有の実行環境であり、Gitへ追加しない。依存版を変更する場合はrequirementsを版管理し、変更理由、検証結果、実行日時を別のrun記録へ残す。

## SUMO設定

正本SUMOは次へ固定する。

```text
/home/takuma/kmd-analysis/.local/sumo-1.24.0
```

`sumo`、`netconvert`、`marouter`等はこのprefixの`bin`から実行する。ユーザー領域にある実体をGitへ登録せず、版、実行path、入力hash、出力hashをrun manifestへ保存する。

## 標準検証

環境だけの厳格な検証は次で再実行できる。

```bash
bash reproducibility/scripts/hayate/verify_hayate_native_environment.sh
```

標準全回帰はDockerを介さず実行する。

```bash
python -m pytest -q 05_src/traffic_simulation/validation
```

特定moduleを直接起動する場合は、repository rootで`05_src`を一時的に先頭へ加える。

```bash
PYTHONPATH="05_src:${PYTHONPATH:-}" python -m traffic_simulation.<module>
```

## 任意のDocker交差確認

Docker daemonを利用できる別環境では、次を追加確認として実行できる。

```bash
docker compose config --quiet
docker compose build analysis
docker compose run --rm analysis python --version
docker compose run --rm sumo sumo --version
docker compose run --rm analysis python -m pytest -q 05_src/traffic_simulation/validation
```

Dockerの成功はHayate native回帰の代用ではない。過去のDocker command、log、hashは当時の実行証拠として保持し、native表記へ書き換えない。

## 不確実性と来歴

- `requirements-analysis.txt`: Git管理された固定直接依存。
- `.conda`: requirementsから構築したHayateローカル環境。Git管理外。
- `.local/sumo-1.24.0`: HayateローカルSUMO実体。Git管理外。
- `.bashrc`: 利便性のためのユーザーローカル設定。Git管理外。
- Docker: 任意の副次的再現環境。

Pythonの全推移依存、OS、CPU、実行command、seed、入力・出力hashは、正式runごとにmanifestへ固定する。requirementsに記載された直接依存だけを、OSを含む完全な実行状態と表現しない。
