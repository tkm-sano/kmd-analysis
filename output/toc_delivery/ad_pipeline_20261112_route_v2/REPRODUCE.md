# A〜D共通パイプライン再実行

2026-11-12。repo rootで実行。既存出力を上書きしない。現在の確定結果は `output/toc_delivery/ad_pipeline_20261112_route_v2`。新しい比較では出力rootも新規版へ変更し、設定/コードhashを先に保存する。

環境：Linux x86_64、AMD EPYC9684X、Python3.12、numpy2.3.1、scipy1.16.0、qiskit2.1.1、ortools9.14.6206、osmium4.1.1、pytest8.4.2。ENVIRONMENT_FREEZE.txt/CPU.txt/PLATFORM.txtを参照。専用venvは `/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python`。既存vehicle-day-v1を改変せず新venvへ追加。VeRyPy外部cloneのcommit/ライセンスはVERY_PY_PROVENANCE.json、import pathはvenv .pthに保存。

別環境の最小依存は上記版とmatplotlib3.10.3。VeRyPyは https://github.com/yorak/VeRyPy のcommit8698f910ffcfb4bc8743aedbf203d6de72fbe006、MIT。既存外部cloneを変更せず、別の新規cloneを同commitへ固定し、そのpathをPYTHONPATHまたはvenv .pthへ追加する。Gurobiや有料TSPサービスは呼ばない。全freezeは環境台帳で、無関係なGPUパッケージ全ての再導入を必須としない。

```bash
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export KMD_AD_OUTPUT_ROOT=output/toc_delivery/ad_pipeline_20261112_route_v2
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -m pytest tests/toc_pipeline tests/toc_baseline_a tests/toc_common tests/toc_cg tests/toc_vehicle_day tests/toc_search_improvement tests/test_toc_contracts.py -q -p no:cacheprovider

# 例：確定共通S1を新しい一時結果へ。入力読込は実行器内で計時。
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python scripts/run_ad_method.py --input output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1 --method A3 --output /tmp/ad-new-A3
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python scripts/run_ad_method.py --input output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1 --method B --primary D --other-limit 422.45 --output /tmp/ad-new-B
```

C/Dは--method C/D、同じε、同じ新規出力。A感度は `--offset 0`、`--offset 120`、`--offset 240`。C Routing60秒、共通schedule30秒、D外側stage300秒。Dは既存PricingAOAの実Qiskit simulationを使用。T内訳はresult.json timing_events、RSSはprocess KiB。未可行時T_programは空欄、失敗経過時間はelapsed_wall_s。

全固定条件の逐次実行は `scripts/run_ad_experiments.py`。完了resultは読み取り再利用して二重実行せず、A45試行→EPSILON_REFERENCES.json固定→B/C/Dの小中S1→S1両方向εの順。失敗は自動成功化しない。Table親版のFAILED_ATTEMPTS_REGISTER.jsonは初回D保存失敗2件の保全で、v2へ数値を流用しない。experiments/S1/*repeat*を別の同seed反復として読む。固定Aレンジへ反復を重複加算しない。

ODを再生成する場合は無料ローカルOSRM5.27.1。`scripts/bootstrap_local_osrm.py --rootfs /tmp/osrm-new-rootfs` は保存manifestの公式imageのlayer SHA256を検証しDocker不要で取り出す。LD_LIBRARY_PATHはそのusr/local/lib:usr/lib/x86_64-linux-gnu。PBFは保全した関東rawファイルを別作業ディレクトリへコピーし、下記を実行（binaryはrootfs/usr/local/bin）。

```bash
osrm-extract -p /tmp/osrm-new-rootfs/opt/car.lua -t 4 kanto.osm.pbf
osrm-partition -t 4 kanto.osrm
osrm-customize -t 4 kanto.osrm
osrm-routed --algorithm mld --port 5000 --threads 4 --max-table-size 1000 kanto.osrm
```

**採用OD生成口**は `scripts/build_route_pair_od.py --parent output/toc_delivery/ad_pipeline_20261112 --output NEW_ROOT --process-workers 8 --port 5002`。5002には同じOSRM5.27.1/graphを8threadで起動し、必要なら--verbosity ERRORとする。親版から使うのは凍結ID・座標・採択snap・道路来歴だけで、親のTable距離はコピーしない。全pairをRoute objectから取得し、注釈付きnode経路を保存する。S1完成後、同じRoute pairをS2/S3へhash付き参照で再利用。Linux fork workerの動作とthread/fork双方のcache再開/改竄拒否は回帰試験済み。OD_RESOURCE_REVISION_1.jsonに実行資源の変更を記録。

同じ採択snapを再現するには親版の保存済みnearest（expanded含む）/SNAP_ROAD_WAYS/CONNECTIVITY_REVIEW/SNAP_EXCEPTION_REVIEWと出入口decisionを維持する。旧build_common_road_odはTable診断の再現用で、最終採用ODの生成口ではない。メタデータの生成時刻もhashに含むので完全な同一入力hash比較には確定bundleを使う。新規graph版は新しいODとして区別。途中再開は同じroot/context、改竄cacheは拒否。通常の再実行で一度限りのforensic回復scriptsを実行しない。

集計・監査は `scripts/audit_ad_results.py` → `scripts/audit_d_macro_scope.py --include-s1` → `scripts/audit_ad_full_routes.py --all-feasible` → `scripts/audit_route_data.py` → `scripts/audit_ad_preservation.py` → `scripts/write_ad_reports.py`。解析対象rootは上記環境変数で指定する。旧Table結果を混ぜない。raw result/planを先に保存し、CSV/文書は派生物。Source snapshotとhash manifestが実装の版。

Dの最終整数同点規則はD_LEX_POLICY_REVISION.json、OD資源変更はOD_RESOURCE_REVISION_1.json、両者を反映した値はEFFECTIVE_SETTINGS.json。初期登録JSONを後から書き換えず、A/B/C・共通条件・ε/seedを維持した修正履歴を分離する。D_PRE_LEXICOGRAPHICは修正前で、最終比較へ混ぜない。再現性/帰属を再計算する場合はsummarize_ad_reproducibility.pyとaudit_d_attribution.pyも実行する。

上流原資料：OSRM/OSM/JMT/OR-Tools/VeRyPy/日本郵便事例のURL・取得hashはsources内manifest。非公開データ・有料API・会社連絡は使用しない。
