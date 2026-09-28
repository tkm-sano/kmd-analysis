# 道路網完成パイプライン v17

文書識別子: `NETWORK-COMPLETION-PIPELINE-V17`
役割: `CURRENT_NORMATIVE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `reproducibility/config/traffic_simulation/current_network_completion_authority_v17.yml`

本書は、受入済み三層正式道路網に対する唯一の現行処理工程仕様である。

```text
Source → Structural → 三層Formal → SUMO → Mapping → Routeability → Acceptance
```

各段階は規範的かつ逐次的である。`SOURCE`は出典 truth、`STRUCTURAL`は接続構造と未加工正規化表現、`THREE_TIER_FORMAL`は`DIRECT`、`INFERRED`、`FALLBACK`によりモデル-準備完了値を生成する。`SUMO`は`net.xml`を具現化・検証し、`MAPPING`は配送要求数／配送地点数を対応付けし、`ROUTEABILITY`は配送経路を検証し、`ACCEPTANCE`は道路網の利用を許可する。

各段階は前段階のimmutable出力を消費し、入力 ハッシュ値、手法／版、決定識別子、決定論的再生成付随情報を公開する。判定基準不合格時は次段階の公開を停止する。受入には、全上流判定基準、完全な出典・来歴、スーモ 構築・属性妥当性、許容可能なconnectivity、決定論的な主要100組配送到達可能性 判定基準（`100/100`）、Request／配送地点の対応付け受入が必要である。主要標本は判定基準であり、全組合せの証明ではない。追加sanity結果は既知の限界として保持する。

以前のhierarchical-混合型 処理工程と三層化以前の阻害要因 処理工程は履歴であり`SUPERSEDED`である。追跡可能性のため閲覧可能なまま保持するが、現行実行正本ではない。

機械可読正本: `reproducibility/config/traffic_simulation/network_completion_pipeline_v17.yml`
