<a id="current-reproducibility-boundary"></a>

# 現行研究の再現性資料

このディレクトリには、現行のスーモ交通シミュレーション研究の管理済み設定と、版管理対象外の実行出力を保存する。

```text
reproducibility/
├── config/traffic_simulation/       # machine-readable current specifications
└── outputs/traffic_simulation/      # regenerable local run products
```

従来のスーモを使わない合成電気自動車配送問題の経路代理分析は、[旧分析の保管先](../legacy/non_sumo_route_proxy_analysis/)に分離している。その入力、出力、環境、ノートブック、試験は現行のスーモ実行経路に含まれない。

<a id="reduced-quantum-stage-evidence"></a>

## 縮約した量子計算段階の根拠

各段階の生成成果物は引き続き版管理対象外とする。正本は、実行識別子、ハッシュ値、ソースと根拠の変更履歴、および[実行計画](../EVRP_EXECUTION_PLAN.md)の状態記録によって特定する。

- R21の正本実行: `outputs/traffic_simulation/r21_qubo_validation/20260910_formal_reduced_v4/`
  (`validation_results.json` SHA-256 `c4baeead366ea2f750cd4ecdd18acc507746dfecd744d0803ed74b5bbb46049f`,
  `manifest.json` SHA-256 `9a6fc459ef1f5cbf1824b9b0197a2f56f9d67cc88de18bd6bcd8ff7f575691a2`).
- R22の正本実行: `outputs/traffic_simulation/r22_ising_conversion/20260910_formal_reduced_v1/`
  (`conversion_results.json` SHA-256 `1b6015bcaf38d58fb98a743f47346be9e68601c0b0f7c09567ca77186ea26cea`,
  `manifest.json` SHA-256 `2bd1bed556b265cc4b6f555497f78e1e432c8d22dabfcccb722fe0faf0da46d9`).

これらの成果物が検証するのは、初期の縮約した訪問順序問題の範囲のみである。R23の実装動作確認の出力は正本ではなく、管理された予備試験や正式な基準の代わりに使ってはならない。
