# 研究マップPortal

文書ID: `DOC-RESEARCH-PORTAL-README`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`

repository rootで`./research portal start`を実行し、`http://127.0.0.1:8876/`を開く。全研究commandは`./research commands`から確認する。

各pipelineのinput/output、command、authority、validation、acceptance、handoffは[`RESEARCH_PIPELINE_REFERENCE.md`](../RESEARCH_PIPELINE_REFERENCE.md)を参照する。

Portalは「概念研究マップ」と「実装／分析マップ」を主画面とし、研究の問いから現行Stage、成果物traceability、Stage 1～11までを有向graphで示す。Stage構成の人間向け入口は[`RESEARCH_OVERVIEW.md`](../RESEARCH_OVERVIEW.md)であり、graph taxonomyは`reproducibility/config/research_portal/research_map_v1.yml`で同じ構成を表す。

Conceptual Map近傍のEvidence-Supported Interpretationは、`reproducibility/evidence/fleet_capacity_interpretation_v1.yml`を正本とし、Delivery Fulfillmentを直接分析境界として、その下流を条件付き解釈として表示する。このEvidence chainはnetwork acceptance authorityでも企業投資予測でもなく、stage status（DONE / NEXT / FUTURE等）とは別の`evidence_status` / `claim_status`を使う。

現行道路網状態は`reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`を唯一の正本入口とし、受入済みrunの受入成果物とprovenance accountingから生成する。研究値をbrowserへhard-codeしない。strict v17は`HISTORICAL`、Hierarchical Hybridは`SUPERSEDED`として詳細領域から参照する。
