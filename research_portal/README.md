<a id="研究マップportal"></a>

# 研究マップポータル

文書識別子: `DOC-RESEARCH-PORTAL-README`
役割: `CURRENT_REFERENCE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-04`
現行正本: `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`

リポジトリの最上位で`./research portal start`を実行し、`http://127.0.0.1:8876/`を開く。ポータルの主要な役割は、第三者が研究の問い、重要性、方法、現在地、検証済み事項、限界、次工程、条件付き解釈を理解するための`Research communication layer`である。

初期表示の`Public / Research View`は研究コミュニケーションを優先する。ハッシュ値、成果物 保存先、実行 識別子、検証器、コマンド、登録簿 / データ構造、詳細出典・来歴、過去の記録 / 後続版に置換済み情報は削除せず、閉じた`Technical Details`へ分離する。技術的な詳細は認証境界ではなく、情報階層上の詳細表示である。

各処理工程のinput/output、コマンド、正本、検証、受入、引継ぎは[`RESEARCH_PIPELINE_REFERENCE.md`](../RESEARCH_PIPELINE_REFERENCE.md)を参照する。

役割分担は次のとおりである。

- [`RESEARCH_OVERVIEW.md`](../RESEARCH_OVERVIEW.md): research overview / roadmap / conceptual framing
- [`RESEARCH_PIPELINE_REFERENCE.md`](../RESEARCH_PIPELINE_REFERENCE.md): commands / inputs / outputs / authority / validation / detailed execution
- Research Portal: third-party-facing research map / progress / explanation

研究の概要は概念研究マップと8段階の研究工程を表示する。詳細な実装／分析マップ、data 流れ、成果物追跡可能性、検証の判定基準は技術的な詳細で維持する。グラフの分類と公開説明モデルは`reproducibility/config/research_portal/research_map_v1.yml`で管理する。

受入済み道路網・配送問題の表示の道路網の規模は、現行の正本が指す受入済み `network_acceptance.json`の`validation.counts`を出典とする。`network_node_count`と有向`network_edge_count`が経路計算 グラフ 規模、`network_lane_count`がスーモ固有の補助指標である。経路計算の対象規模と配送問題 規模は別モデルで、正式運用 成果物が無い間は`NOT YET AVAILABLE`を返す。

概念マップ近傍の根拠に基づく解釈は、`reproducibility/evidence/fleet_capacity_interpretation_v1.yml`を正本とし、配送需要の充足を直接分析境界として、その下流を条件付き解釈として表示する。この根拠のつながりは道路網 受入 正本でも企業投資予測でもなく、stage 状況（完了 / 次の工程 / 将来の工程等）とは別の`evidence_status` / `claim_status`を使う。

現行道路網状態は`reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`を唯一の正本入口とし、受入済み実行の受入成果物と出典・来歴 会計から生成する。研究値をブラウザーへ固定値として埋め込むしない。厳密方式 v17は`HISTORICAL`、階層型混合方式は`SUPERSEDED`として詳細領域から参照する。
