# 保存済み道路OD・S1配送計画の可視化

## 2026-11-13：単一ベースラインAを必須比較として追加

全4タブの上部に最新版DWT-v1.3.1のA対B/C/D比較を表示する。AのD551.1398km・W416.4分を固定参照とし、W上限/予算4条件を切替できる。旧保存系列のルート/バース・D/Wグラフにも同系列A2（W422.45分）を追加した。二系列を混合しない。Aの人手Tは未校正と表示し、プログラム時間へ置換しない。

追加データ・検証・変更前バックアップ・再現手順は[baseline_comparison_20261113_v1/README.md](baseline_comparison_20261113_v1/README.md)参照。保存結果の最適化・道路OD再生成・凍結需要の変更は行っていない。以下の元の検証件数・図は追加前のB/C/D表示の記録であり、追加Aの検証は別JSONに保存している。


2026-11-13。研究シミュレーションの保存結果を表示する。配送計画の生成、道路ODの再生成、外部経路APIへの通信は行わない。

## 開く

作業ツリー内で、次を実行してブラウザから **http://127.0.0.1:8765/index.html** を開く。

```bash
cd /home/takuma/kmd-analysis
PYTHONDONTWRITEBYTECODE=1 /home/takuma/.cache/kmd-analysis/venvs/toc-visualization-v1/bin/python -B output/toc_delivery/visualization_20261113_v1/serve.py --port 8765
```

サーバが起動済みの場合はURLを開くだけでよい。終了は起動した端末でCtrl+C。localhostにのみ接続し、保存済みRoute応答と座標索引を読み取る。OSRMサーバ、外部地図タイル、CDN、有料サービスは不要。

`index.html`を直接開く方法でも4画面と事前収録経路を表示できる。ただし、任意のOD地点対を指定する操作には上記サーバと元リポジトリのRouteキャッシュが必要。専用ディレクトリだけを別PCへコピーすると、この任意経路機能は使えない。

## 操作

1. **ODマップ**：S1〜S3を切り替え、配送先・道路対応点・道路を表示する。点をクリックするとID、入力座標、snap座標、保存ノードIDが表示される。ドラッグで移動、ホイールまたは±で拡大縮小。「全体」で復帰。出発・到着の地点番号は0がデポ、1以降がその規模の保存ID順。方向を入れ替えると別の有向経路になる。
2. **OD診断**：距離・時間・方向差の分布は全非対角要素。散布図だけは決定論的に等間隔抽出した2,500組／規模。欠損、非有限値、負値、到達不能、Route照合も表示する。
3. **S1配送計画比較**：B/C/D、車両v0〜v9、便1/2、全車両／選択車両を選ぶ。未使用車両は経路なし。訪問順番号は選択・拡大して確認する。第2便は破線。Dは保存された古典seedと最終計画を切り替えられる。B/Cの未保存の完成前計画は「記録なし」。B/Dの車両対応色と比較表も確認できる。
4. **バース運用**：B/C/Dを切り替え、バース2本の積込占有、車両・便別の準備完了、待機、積込、出発、帰着を確認する。下部の表に丸め前の保存時刻と待機値を示す。

## 保存物

- `figures/`：需要・道路、配送経路、バース、D/W/T、OD品質の5組。PNG（300dpi）・SVG・PDF。キャプションは`CAPTIONS.md`/`CAPTIONS.json`。
- `screenshots/`：実際のChromeで操作した7画面。
- `OD_VALIDATION.csv`：全ODの品質検査。`ARC_VALIDATION.csv`：3,051区間の道路距離・時間・形状照合。`ROUTE_VALIDATION.csv`：51便の計画・制約検査。
- `OD_GEOMETRY_SAMPLE_VALIDATION.csv`：任意経路APIの15組の実操作検査。
- `DATA_MANIFEST.json`：入力一覧・版・SHA256。`B_D_COMPARISON.json`：車両対応と経路・時刻比較。
- `INDEPENDENT_VALIDATION.json`：生成コードを呼ばない11,444項目の再計算。`BROWSER_VALIDATION.json`：46操作検査。
- `VISUALIZATION_REPORT.md`：結果・限界。`ENVIRONMENT.json`：依存版。`FINAL_VALIDATION.json`：終了時の保全。`ARTIFACT_INDEX.json`：新規成果物のSHA256。

## 再生成

既存成果を上書きせず、必ず別の新規ディレクトリを作る。以下の`NEW`には未使用のディレクトリ名を指定する。元リポジトリ内の`output/toc_delivery/`直下という深さを維持する。

```bash
set -e
cd /home/takuma/kmd-analysis
OLD=output/toc_delivery/visualization_20261113_v1
NEW=output/toc_delivery/visualization_fresh_run
test ! -e "$NEW" && mkdir -p "$NEW/data" "$NEW/figures" "$NEW/screenshots"
cp "$OLD"/*.py "$OLD/index.html" "$OLD/app.js" "$OLD/style.css" "$NEW/"
cp "$OLD/PRESERVATION_BEFORE.json" "$NEW/"
VIZ_PY=/home/takuma/.cache/kmd-analysis/venvs/toc-visualization-v1/bin/python
PYTHONDONTWRITEBYTECODE=1 "$VIZ_PY" -B "$NEW/extract_roads.py"
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "$VIZ_PY" -B "$NEW/build_data.py"
PYTHONDONTWRITEBYTECODE=1 "$VIZ_PY" -B "$NEW/make_figures.py"
PYTHONDONTWRITEBYTECODE=1 "$VIZ_PY" -B "$NEW/validate_visualization.py"
PYTHONDONTWRITEBYTECODE=1 "$VIZ_PY" -B "$NEW/serve.py" --port 8765
```

最後のサーバを起動したまま、別端末で同じ`NEW`と`VIZ_PY`を設定し、`"$VIZ_PY" -B "$NEW/browser_check.py"`を実行する。ブラウザ検査はポート8765を使用するため、旧サーバを先に停止する。検査はChrome `/usr/bin/google-chrome`を使用する。`finalize.py`は文書作成後の終了時hash検査用で、元の実行記録を再現実験の時間として転記しない。

依存関係は専用venvに分離した。再作成時はPython 3.12でvenvを作り、`numpy==2.3.1 scipy==1.16.0 matplotlib==3.10.3 osmium==4.1.1 pyproj==3.7.2 playwright==1.56.0`をインストールする。日本語静止図はローカルの`~/.local/share/fonts/NotoSansJP-Regular.ttf`を使用する。詳細は`ENVIRONMENT.json`。元アルゴリズム環境への追加インストールは不要。

## 容量と制限

表示データは約12.76MiB。PBF全ノードの座標索引約912.47MiBはサーバ側でmmapし、ブラウザへ送信しない。道路背景は範囲と車道種別を限定し、低ズームで生活道路等を省略する。配送便の道路形状は省略していない。

保存snapのノードID=0は未提供として表示する。snap座標は保持されており、架空のノード座標を補わない。道路線は同じPBFと保存Route node列から復元したOSRMプロファイル上の経路であり、距離最短性を別に証明したものではない。S2/S3の配送計画は存在せず表示しない。

© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) / ODbL。行政境界は国土交通省・国土数値情報N03。公開・配布時も出典を維持する。
