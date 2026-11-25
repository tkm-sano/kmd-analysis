# 大田区ToC配送の公開検証と再現の範囲

正式RQは「量子計算を活用することで、配送車両の走行距離を短縮しながら、荷物の積み込みを待つ時間も削減できるか。」です。

[研究仕様1〜7](../frozen/配送計画最適化_評価指標と実験条件_1-7.md)、[FCFS_v1](FCFS_OPERATING_POLICY_V1.md)、[記述統計v1](statistical_scope_20261121_v1/FREEZE_SPEC.md)はそれぞれの適用範囲で凍結されています。FCFS_v1の積込1800秒・文字列ID順と、[グループ受付v2](iterative_d3/GROUPED_LOADING_V2_IMPLEMENTATION.md)の積込900秒・数値ID順は別条件です。[勤務・休憩](duty_break_20261121_v1/REPORT.md)の履歴とも分けます。旧平均荷待ちおよび旧RQを含む `configs/toc_delivery/study.json` と `dw_policy_20261117_v1.json` は対応する履歴入口の設定として保全します。

## 結果と実行状態

Bは有向Clarke–Wright、CはOR-Toolsを使う古典最適化、D古典とD量子はグループ受付v2の外側探索を共有する内部対照です。D量子の局所順序候補はCPU上のQAOAシミュレーションで得ます。探索内のB基準候補採択と、報告上のC基準I_dualは分けます。主要値は総走行距離D、全活動便の総積込待機W、C基準I_dualです。Aは出典・単位が異なる行政外部参照で、分布と試行を持ちません。

[予備の集計](../../results/toc_grouped_v2_20261124/pilot_summary.csv)は各規模1件です。S1・S2・S3のD量子はCより総Wが小さく、Dも小さいのはS2でした。内部枝・学習評価・shotsは独立試行に数えず、各規模1件の標本SDは未定義です。予備は有限作業量による比較で、同一wall時間での比較は未検証です。図3の分母は稼働車両日で、総Wと配置車両日で割った値とは区別します。

グループ受付v2は正式ケース90件、各規模30件を登録済みで、正式worker投入・観測は0件です。この版の登録件数は、別系統の記述統計v1で保留中の一般的な独立Jの精度設計を置き換えません。正式実験はHOLDです。サイズ予備は264ジョブ中244完了・4中断・16未実行で、n=10/12/14の最終採択は未確定。登録の基準はn=12です。p=2、学習各1000・最終10000 shotsは既定で、最大24評価と初期角Aは当該予備の設定です。正式適用をこの公開作業で採択しません。

## 実装と入口

| 対象 | 入口・実装 |
|---|---|
| 固定需要の読込・生成の検証 | [固定需要v1の読込契約](../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/READING_CONTRACT.md)、`kmd_toc.frozen_demand`、`kmd_toc.freeze_demand --verify-only` |
| 道路・有向OD | [OSRM準備](../../scripts/bootstrap_local_osrm.py)、[共通道路入力](../../scripts/build_common_road_od.py)、[Route pair OD](../../scripts/build_route_pair_od.py) |
| 予備・初期B・方式比較 | [グループ受付v2入口](../../scripts/run_grouped_loading_v2.py)、[完成器](../../src/kmd_toc/grouped_loading_v2/)、[条件](../../configs/grouped_loading_20261124_v2/conditions.json) |
| QAOAサイズ診断・チェックポイント | [サイズ比較入口](../../scripts/run_grouped_qaoa_size_pilot.py)、[有限探索](../../src/kmd_toc/grouped_loading_v2/search.py)、[局所QAOA](../../src/kmd_toc/iterative_v3/quantum.py) |
| 正式登録・実行・再開 | [登録](../../scripts/prepare_grouped_formal_v2.py)、[実行・継続・集計](../../scripts/run_grouped_formal_v2.py) |
| 評価・統計・可視化 | [独立再評価](../../scripts/audit_grouped_loading_v2.py)、[記述統計](../../scripts/analyze_descriptive_v1.py)、[予備作図](../../scripts/plot_grouped_pilot_v2.py)、[刊行図の生成](../../scripts/report_grouped_pilot_publication.py) |

正式入口の運用リース、原登録と入力のハッシュ、実行環境の検査は維持しています。公開ツリーのソース249件が正式登録の固定ハッシュと一致することを確認しました。公開の登録索引は下記の照合用データです。原MANIFEST・固定B・承認記録・正式実行ミラーを要求する入口に投入できる登録ファイルではありません。古い操作記録の絶対パスは当時の環境を示します。公開からの軽量検証には以下のコマンドを使います。

## 環境と検証コマンド

Linux上で新規の検証用環境を用意する場合、Python 3.12.11に NumPy 2.3.1、SciPy 1.16.0、OR-Tools 9.14.6206、Qiskit 2.1.1、Matplotlib 3.10.3、pytest 8.4.2を使います。道路生成では追加でosmium 4.1.1。QAOA枝の過去環境とC環境の版記録は[量子側](../../configs/p1_pricing/requirements-validation.txt)と[古典側](library_implementation_20261114_v2/evidence/requirements.lock.txt)にあります。VeRyPyを使う経路は[上流の指定コミット](https://github.com/yorak/VeRyPy/tree/8698f910ffcfb4bc8743aedbf203d6de72fbe006)を別に取得し、そのcloneをPYTHONPATHに含めます。

```bash
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export MPLBACKEND=Agg OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

python -B scripts/run_grouped_formal_v2.py --help
python -B scripts/run_grouped_qaoa_size_pilot.py --help
python -B scripts/evaluate_fcfs_v1.py --help
python -B -m pytest -q -p no:cacheprovider tests/grouped_loading_v2 tests/descriptive_v1 -k 'not prior_work_protected'
```

上記は人工入力による共通評価・計算の回帰検証です。登録済みの実配送規模の実行には正式入力と環境指紋が必要です。保存計画を用いる再評価と、最適化を伴う全体再実行は異なる検証です。

Linuxの新規検証環境の構成例です。

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install numpy==2.3.1 scipy==1.16.0 ortools==9.14.6206 qiskit==2.1.1 matplotlib==3.10.3 pytest==8.4.2
git clone https://github.com/yorak/VeRyPy.git vendor/VeRyPy
git -C vendor/VeRyPy checkout --detach 8698f910ffcfb4bc8743aedbf203d6de72fbe006
export PYTHONPATH="$PWD/src:$PWD/vendor/VeRyPy"
```

道路入力作成用のosmium、履歴のAer・Qulacs、C++のcompactルックアップは各経路が必要とするときだけ追加します。履歴のcompactルックアップは `scripts/large_n_20261119_v5/cost_table.cpp` から `g++ -O3 -std=c++17 -shared -fPIC cost_table.cpp -o cost_table.so` で構築します。公開検証で既存の実験環境やFreezeの環境指紋は更新しません。

## 正式seed台帳の再生成

次のコードは既存アルゴリズムを呼んでseed表をメモリ内に再生成します。90正式ケースに加え、元表に含まれる先行予備3ケースのコンテキスト順を保持しています。

```bash
PYTHONPATH=src python -B - <<'PY'
import hashlib
import json
from pathlib import Path
from kmd_toc.iterative_d3.rng_v2 import build

index = json.loads(Path("results/toc_grouped_v2_20261124/formal_registration_index.json").read_text())
registered = index["seed_table"]
text, _ = build(registered["ordered_contexts"], excluded=registered["excluded"])
assert len(text.splitlines()) - 1 == registered["rows"]
assert hashlib.sha256(text.encode("utf-8")).hexdigest() == registered["sha256"]
print(registered["rows"], registered["sha256"])
PY
```

## 入力、権利、再現の境界

- 公開済み固定需要v1の読込みには [固定需要のチェックサム](../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/SHA256SUMS)を使用します。元集合からの全量再生成には凍結時の建物・世帯由来の配送地点候補と監査入力も必要です。来歴と対象範囲は[既存のデータカタログ](../QUANTITATIVE_GUIDE.md#12-githubと研究用保存領域の役割)を参照します。
- 採用ODの[出典・OSMハッシュ・入力照合値](../../results/toc_grouped_v2_20261124/input_provenance.json)を掲載します。関東OSM PBF、OSRM 5.27.1の固定レイヤー、スナップ確認済みの親道路入力を用い、`build_common_road_od.py` から共通道路契約を構成し、`build_route_pair_od.py --parent PARENT --output NEW_OUTPUT` で注釈付きの有向Routeを取得します。道路生成と正式OD全量の再生成はこの公開監査では未実施です。版、時刻メタデータ、スナップ記録の差で生成物のハッシュが変わり得ます。
- 正式OD配列、訪問順と計画、全探索・shots、リソース監視ログ、個別の承認記録、元入力の再配布未確認資料は収録範囲外です。既存の[ライセンス・権利区分](../QUANTITATIVE_GUIDE.md#13-データの出典帰属利用条件)を維持します。保存済み予備の集計とダウンロード可能な図を利用できます。図の元計画からの全再作図には原計画・監査入力・日本語フォントが必要です。
