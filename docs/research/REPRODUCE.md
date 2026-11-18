# 現行二目的分析の再現

2026-11-17の最新研究判断に基づく。正本は[二目的研究方針](DW_RESEARCH_POLICY.md)と[現行設定](../../configs/toc_delivery/dw_policy_20261117_v1.json)。旧本文は[変更前の保存版](../audits/dw_policy_20261117_v1/before/docs/research/REPRODUCE.md)に保全する。

リポジトリrootで、既存の予備計画だけを読む。新規需要・OD・実規模試行を生成しない。

```bash
/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B scripts/analyze_dw.py --output output/toc_delivery/dw_policy_20261117_v1
```

同名出力が存在するときは別の新しい出力先を指定する。元結果・旧集計は書き換えない。`DW_ANALYSIS.json`にD/W・取得状態・二次元非支配、`SOURCE_HASHES.json`に照合した入力・登録・結果、`POLICY.json`に現行方針を保存する。Tや旧Jの分析は出力しない。

小規模検証のみの入口：

```bash
PYTHONPATH=src /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B -m pytest tests/test_toc_contracts.py tests/test_dw_policy.py -q -p no:cacheprovider
```

旧研究の再現手順は[変更前の本文](../audits/dw_policy_20261117_v1/before/docs/research/REPRODUCE.md)と各日付付き保存snapshotに保持する。旧三目的CLIには`--historical-reproduction`を明示する。新しい研究のために旧時間予算を使わない。旧登録のsource hashと現在の変更後コードは一致しない場合があり、そのとき検査を迂回せず当該登録の保存snapshotを別環境で利用する。

本実験は未許可・HOLD。総合評価の定義や精度を補完して自動実行する入口は設けない。
