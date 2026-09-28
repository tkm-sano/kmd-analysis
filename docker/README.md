<a id="optional-docker-environments-for-the-tokyo-traffic-extension"></a>

# 東京交通シミュレーション用の補助コンテナー環境

Hayateのnative Conda環境が現在の正本実行環境である。ここにあるDocker構成は、Docker daemonを利用できる環境で追加クロスチェックを行うための副次環境であり、Hayate実行の必須条件ではない。

Python依存の正本は`reproducibility/environment/requirements-analysis.txt`である。Dockerfileもこのファイルを参照し、Docker配下に同じ依存一覧を重複保持しない。正本の構築・検証手順は`reproducibility/environment/README.md`を参照する。

これらのサービスは、`legacy/non_sumo_route_proxy_analysis/reproducibility/requirements-lock.txt`に記録された旧研究の凍結環境を置き換えない。

<a id="services"></a>

## サービス

- `analysis`：道路網処理、時間依存の経路計算、較正、古典計算による電気自動車配送経路問題の基準を扱う実行環境。言語処理系はPython 3.11。
- `sumo`：道路網変換と微視的交通シミュレーションを行う、版を固定したスーモ1.24.0の環境。

両サービスは、補助的なコンテナー確認用の環境として`linux/amd64`を使う。アップル製半導体を搭載した機器ではコンテナー管理ソフトの命令体系変換を介し、対応するリナックスサーバーでは直接実行する。提供元の`v1_25_0`タグが実行時には1.24.0を報告するため、スーモのイメージはハッシュ値で固定している。

リポジトリは`/workspace`に接続する。第三者の未加工データと生成出力はホスト側に保持し、コンテナーイメージには複製しない。

<a id="sumo-network-build-execution-boundary"></a>

## 道路網構築の実行範囲

道路網構築では、分析処理と交通シミュレーターの実行を別サービスに分ける。

- `analysis`：管理済み設定、出典登録簿、対象地域の版、ハッシュ値を検証する。`.netccfg`と構築成果物一覧を生成し、生成後の`.net.xml`を検証する。
- `sumo`：補助コンテナー内で`netconvert`、`sumo`、`duarouter`を実行する。ハッシュ値で固定したイメージは追加確認用であり、正本の実行環境は研究サーバーに直接導入したスーモ1.24.0である。

両サービスは共有した`/workspace`を介して生成ファイルを交換する。`analysis`イメージにスーモを重複導入したり、その内部からコンテナー管理サービスを呼び出したり、記録のない`netconvert`引数を直接入力したりしてはならない。`.netccfg`は、版管理済みの`reproducibility/config/traffic_simulation/sumo_network.yml`から生成する。

計画中の利用者向け入口は次のとおり。

```bash
docker/run_sumo_network_build.sh structural ota_ward osm_geofabrik_kanto_20260716
docker/run_sumo_network_build.sh formal ota_ward osm_geofabrik_kanto_20260716
```

この入口では、`analysis`で準備、`sumo`で変換、`analysis`で検証を行い、いずれかの段階が失敗したら直ちに停止する。この入口と道路網設定は計画段階であり、まだ実装されていない。

<a id="optional-docker-checks"></a>

## 任意のコンテナー確認

実行前に互換性のあるコンテナー管理サービスを起動する。`docker compose config`による構成確認には常駐サービスは不要だが、構築と実行には必要となる。以下の確認は、正本の研究サーバー上の回帰検証を置き換えない。

```bash
docker compose build analysis
docker compose run --rm analysis python --version
docker compose run --rm analysis python -m pytest -q legacy/non_sumo_route_proxy_analysis/reproducibility/tests/test_audit.py
docker compose run --rm sumo sumo --version
docker compose run --rm sumo netconvert --version
```

新しい交通シミュレーション結果を既存の合成電気自動車配送問題のディレクトリへ書き込まない。`05_src/traffic_simulation/README.md`に記載した専用の保存先を使う。
