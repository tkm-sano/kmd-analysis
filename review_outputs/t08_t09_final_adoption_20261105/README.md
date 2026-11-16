# T08/T09最終評価

入口: FINAL_REPORT_JA.md。論文用: THESIS_INSERT_JA.md。data/に採用台帳、境界、感度、効果伝達、evidence/に入力hash・検算、figures/にPNG/PDF。

再実行（既存保存入力と.conda環境が必要）:

```bash
.conda/bin/python review_outputs/t08_t09_final_adoption_20261105/scripts/analyze.py
.conda/bin/python review_outputs/t08_t09_final_adoption_20261105/scripts/finalize.py
.conda/bin/python review_outputs/t08_t09_final_adoption_20261105/scripts/supplement.py
```

新規出力先だけを書き換える。元成果物は読取りのみ。T09完成質量/DCはHOLD。source manifestの外部保全パス依存があり、このディレクトリ単独では完全再現しない。
