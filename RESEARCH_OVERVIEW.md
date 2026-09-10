# 研究概要（stable entry）

文書ID: `ALIAS-RESEARCH-OVERVIEW`
役割: `PRIMARY_ENTRY`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-09`
現行正本: `20260903_20260903_RESEARCH_OVERVIEW.md`

現行の研究概要・roadmapは次の文書である。

- [研究概要・ロードマップ v17](20260903_20260903_RESEARCH_OVERVIEW.md)
- [現行Research Pipeline実行・正本・検証リファレンス](RESEARCH_PIPELINE_REFERENCE.md)

## 2026-09-09の設計更新

今後の研究パイプラインは[最新B2C配送パイプライン](RESEARCH_PIPELINE_REFERENCE.md#b2c-pipeline-20260909)を設計正本とする。住宅向け宅配を主対象に、39,956候補地点から層化・重み付き非復元抽出し、customer数nと複数seedを実験パラメータにする。主需要単位は配送件数、Baselineは単一depot、主指標はDFR_orders。OR-ToolsとQUBO→QAOA→Qiskit Aerは同一instance・共通Hard Constraintsを使用し、独立Validatorを通して比較する。技術Scenarioではcustomer・需要・Time Window・道路条件を原則固定する。

旧記述との不整合は上記の最新方針を優先する。既存成果物の生成・受入事実は保持し、今後の設計採択を実装完了とは扱わない。

本stable entryはGitHub、Portal、CLI、外部linkとの互換性のために維持する。日付入り文書が正本であり、本文はここに複製しない。

<a id="stage-1--routing-baseline-next"></a>

経路基準に関する判断は、上記の日付入り正本文書で維持する。
