# 交通シミュレーション仕様の日本語版

このフォルダには、英語の規範仕様を理解・確認するための日本語版を保存する。
機械可読なYAML・XML・JSON Schemaと英語規範仕様が正本であり、日本語版は
同じ要件を説明する対応文書である。差異が見つかった場合は、正本を変更せずに
日本語版を修正する。規則変更時は英語版、日本語版、設定、traceability、
fixtureの整合を同じ変更で確認する。

`Source revision`は英語正本と日本語版の同期基準を示す。同一コミットで同期した
場合は「同一基準点」と記録し、具体的なコミットSHAはGit履歴から確認する。

| 内容 | 英語正本 | 日本語版 | Source revision | 同期状態 |
|---|---|---|---|---|
| Resolverの対象、入出力、failure、relation closure | [`../02_resolver_specification.md`](../02_resolver_specification.md) | [`02_resolver_specification_ja.md`](02_resolver_specification_ja.md) | 同一基準点 | 同期済み |
| 属性別criticality、証拠順位、placeholder gate | [`../attribute_criticality_and_evidence_specification.md`](../attribute_criticality_and_evidence_specification.md) | [`学習用日本語版`](../../learning/attribute_criticality_and_evidence_specification_ja.md) | 同一基準点 | 英語正本の固定内容を学習用に翻訳 |

## 関連する正本と統制表

- 共通状態語彙、外部証拠登録、出典管理：
  [`../../network_attribute_governance.md`](../../network_attribute_governance.md)
- failure code registry：
  [`../08_failure_taxonomy.md`](../08_failure_taxonomy.md)
- requirement・設定・test・fixture traceability：
  [`../09_requirements_traceability.md`](../09_requirements_traceability.md)
- profile別入力必須表：
  [`../attribute_criticality_and_evidence_specification.md#profile-specific-required-inputs`](../attribute_criticality_and_evidence_specification.md#profile-specific-required-inputs)
- 現在のreadiness gate：
  [`../../../../RESEARCH_STATUS.md`](../../../../RESEARCH_STATUS.md)
- 機械可読schema一覧：
  [`../../../../reproducibility/config/traffic_simulation/schemas`](../../../../reproducibility/config/traffic_simulation/schemas)

全工程における操作、定義、数値設定の関係は、日本語の
[`network_workflow_decisions_and_parameters.md`](../../network_workflow_decisions_and_parameters.md)
を参照する。現在工程はリポジトリ直下の`RESEARCH_STATUS.md`で確認する。
