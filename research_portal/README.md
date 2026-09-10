# 研究マップPortal

文書ID: `DOC-RESEARCH-PORTAL-README`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-04`
現行正本: `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`

repository rootで`./research portal start`を実行し、`http://127.0.0.1:8876/`を開く。Portalの主要な役割は、第三者が研究の問い、重要性、方法、現在地、検証済み事項、限界、次工程、条件付き解釈を理解するための`Research communication layer`である。

初期表示の`Public / Research View`は研究コミュニケーションを優先する。SHA、artifact path、run ID、validator、command、registry / schema、詳細provenance、historical / superseded情報は削除せず、閉じた`Technical Details`へ分離する。Technical Detailsは認証境界ではなく、情報階層上の詳細表示である。

各pipelineのinput/output、command、authority、validation、acceptance、handoffは[`RESEARCH_PIPELINE_REFERENCE.md`](../RESEARCH_PIPELINE_REFERENCE.md)を参照する。

役割分担は次のとおりである。

- [`RESEARCH_OVERVIEW.md`](../RESEARCH_OVERVIEW.md): research overview / roadmap / conceptual framing
- [`RESEARCH_PIPELINE_REFERENCE.md`](../RESEARCH_PIPELINE_REFERENCE.md): commands / inputs / outputs / authority / validation / detailed execution
- Research Portal: third-party-facing research map / progress / explanation

Public Viewは概念研究マップと8段階の研究工程を表示する。詳細な実装／分析map、data flow、成果物traceability、validation gateはTechnical Detailsで維持する。graph taxonomyと公開説明modelは`reproducibility/config/research_portal/research_map_v1.yml`で管理する。

Accepted Network / Instance ViewerのNetwork Scaleは、current authorityが指すaccepted `network_acceptance.json`の`validation.counts`をsourceとする。`network_node_count`と有向`network_edge_count`がrouting graph size、`network_lane_count`がSUMO固有の補助指標である。Routing workloadとDelivery Instance scaleは別modelで、production artifactが無い間は`NOT YET AVAILABLE`を返す。

Conceptual Map近傍のEvidence-Supported Interpretationは、`reproducibility/evidence/fleet_capacity_interpretation_v1.yml`を正本とし、Delivery Fulfillmentを直接分析境界として、その下流を条件付き解釈として表示する。このEvidence chainはnetwork acceptance authorityでも企業投資予測でもなく、stage status（DONE / NEXT / FUTURE等）とは別の`evidence_status` / `claim_status`を使う。

現行道路網状態は`reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`を唯一の正本入口とし、受入済みrunの受入成果物とprovenance accountingから生成する。研究値をbrowserへhard-codeしない。strict v17は`HISTORICAL`、Hierarchical Hybridは`SUPERSEDED`として詳細領域から参照する。
