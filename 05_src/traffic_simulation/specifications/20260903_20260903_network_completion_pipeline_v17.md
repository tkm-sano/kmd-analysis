# 道路網完成パイプライン v17

文書ID: `NETWORK-COMPLETION-PIPELINE-V17`
役割: `CURRENT_NORMATIVE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`

本書は、受入済み三層Formal道路網に対する唯一の現行pipeline仕様である。

```text
Source → Structural → 三層Formal → SUMO → Mapping → Routeability → Acceptance
```

各Stageは規範的かつ逐次的である。`SOURCE`はsource truth、`STRUCTURAL`はtopologyとraw正規化表現、`THREE_TIER_FORMAL`は`DIRECT`、`INFERRED`、`FALLBACK`によりmodel-ready値を生成する。`SUMO`は`net.xml`を具現化・検証し、`MAPPING`はRequests／Stopsをmappingし、`ROUTEABILITY`は配送経路を検証し、`ACCEPTANCE`は道路網の利用を許可する。

各Stageは前Stageのimmutable出力を消費し、input hash、method／version、Decision ID、決定論的再生成metadataを公開する。gate不合格時は次Stageの公開を停止する。受入には、全上流gate、完全なprovenance、SUMO build・属性妥当性、許容可能なconnectivity、決定論的な主要100組配送routeability gate（`100/100`）、Request／Stop mapping受入が必要である。主要sampleはgateであり、全組合せの証明ではない。追加sanity結果は既知の限界として保持する。

以前のhierarchical-hybrid pipelineと三層化以前のblocker pipelineは履歴であり`SUPERSEDED`である。traceabilityのため閲覧可能なまま保持するが、現行実行正本ではない。

機械可読正本: `reproducibility/config/traffic_simulation/network_completion_pipeline_v17.yml`
