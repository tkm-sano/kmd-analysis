# T08・T09追加計算

入口はFINAL_REPORT_JA.md。条件・探索範囲はEXPERIMENT_DESIGN.md、モデル比較はT08_T09_COMPARABILITY.md。

再実行はリポジトリrootで以下を実施する。出力環境変数を新しいパスにして旧成果物を保全する。

```bash
export T08_T09_OUTPUT="$PWD/review_outputs/t08_t09_interaction_boundaries_20261105/replay01"
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/t08_t09_interaction_boundaries_20261105/run01/scripts/analyze.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/t08_t09_interaction_boundaries_20261105/run01/scripts/audit_and_report.py
```

指定6値だけを先に確認するにはanalyze.pyに--reproduce-onlyを渡す。RUN_CONFIG.jsonは実行条件の記録で、数値仕様の正本はscripts/analyze.py。Python/numpy/pandas/matplotlibバージョンも記録。保存アーカイブへの絶対パス依存があり、この出力ディレクトリ単独では完全再現しない。SOURCE_MANIFEST.csvが必要入力とhashを列挙する。

INTERACTION_RESULTS.csvはユニーク比較条件の質量・部材、CASE_MEMBERSHIP.csvは複数の実験設計への所属、BOUNDARY_SURFACES.csvは連続境界の標本、DC_INTERACTION_RESULTS.csvは全対応軌跡の絶対Wh/差分/成分、FACTOR_IMPORTANCE.csvは局所/探索範囲効果。DC表のtrajectory_sha256でTRAJECTORY_METRICS.csvを結合すればparent/group・減速度・停止指標を取得できる。新旧区別はoriginとexisting_case_ids。data/に要約・層別・交互作用・境界代表点、figures/にPNG/PDF、evidence/に数値監査と保全hashを保存した。

削減差はLP−S、追加/未知部材差はS−LP。正の削減差がS優位。W1=転がり、W2=空力、W3=並進、W4=回転。空欄は未定義または未確定であり0ではない。
