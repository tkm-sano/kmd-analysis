# Formal道路網完成の三層方針 v17

文書ID: `SPEC-P13-FORMAL-COMPLETION-THREE-TIER-V17`
役割: `CURRENT_NORMATIVE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`

Decision: `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`
Registry: `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml`

以前のhierarchical-hybrid Decisionは履歴policyとして保持し、本Decisionがsupersedeする。strict v17基準、blocker inventory、model選択benchmark、missing-domain成果物はread-only証拠として維持する。

## 意味論

Structuralはsource truthであり、raw source表現、topology、lineage、正規化したsource状態を表す。Formalは研究・simulationで使用する完全なmodel-ready道路網である。Formal値はsource観測値である必要はないが、各値はresolution tier、method、confidence、仮定、元のmissing／blocker状態、provenanceを保持しなければならない。

resolution tierは`DIRECT`、`INFERRED`、`FALLBACK`だけとする。`DIRECT`はsource証拠または一意に採択した規則、`INFERRED`は再現可能な完成機構（外部data、局所伝播、経験的group化、統計／ML）、`FALLBACK`は決定論的既定値または保守的規則である。`INFERRED`と`FALLBACK`を`OBSERVED`または`DIRECT`として表現してはならない。

confidenceは`HIGH`、`MEDIUM`、`LOW`、`FALLBACK`のいずれかとする。`DIRECT`の既定値は`HIGH`である。`INFERRED`のconfidenceはmodel確率、donor一致、benchmark性能、feature適用可能性を組み合わせる。missing-domain labelがなければconfidenceを下げるが、完成処理は停止しない。`FALLBACK`のconfidenceは常に`FALLBACK`である。

## 解決規則

統制対象となる車線、速度、permission／access、relation、conditional recordはすべて`DIRECT → INFERRED → FALLBACK`に従う。推論に失敗した場合はfallback選択前にabstention理由を記録する。三層すべてで実行可能な最終値を生成できなかった技術的失敗だけをblockerとする。

車線は、正確にlinkできる場合は外部証拠を優先する。それ以外は連続性、距離、遷移guardを満たす局所伝播、経験的groupまたは決定論的ML機構、道路種別／SUMO／MATSim形式／保守的fallbackの順に選ぶ。既存benchmarkのcoverage、bias、MAE、決定性、利用可能feature、confidence、costを選択metadataとして記録する。明示値domainでの性能をmissing-domainの証拠として提示しない。

速度について、具現化する道路網属性は`operational_speed_kph`とする。法定・標識上の`maxspeed`は分離し、運用速度予測で上書きしない。外部・経験・model機構を決定論的道路種別fallbackより先に適用する。

permission／accessは、車種別の明示証拠と決定論的OSM意味論を優先する。利用できない場合は、決定論的policy fallbackにより統制対象の配送車両をallowまたはdenyへ解決する。MLまたは経験的予測はreview候補を抽出できるが、法的accessを付与してはならない。

未対応relationまたはconditional構文は、可能な場合は設定時刻で評価し、それ以外は決定論的restriction fallbackまたはprovenance付き明示ignore規則を使う。source構文と元blockerを保持する。

## 記録契約

各Formal recordは、`final_value`、`resolution_tier`、`method_id`、`method_version`、`confidence`、`source_evidence`、`source_identity`、`assumption_id`、`provenance`、`original_missing_or_blocker_state`を必ず含む。provenanceにはsource snapshot hash、source Way／record identity、Decision ID、method／version、feature／input hash、再生成command、blocker ID、stop codeを含める。暗黙のfallbackを禁止する。

## 品質と受入

主要な品質accountingは、履歴blocker数ではなく、tier比率、confidence分布、method分布、属性分布、未解決の技術的失敗である。`FORMAL_NETWORK_ACCEPTED=true`には、全統制属性の最終値、完全なprovenance、SUMO build・妥当性検査、connectivity、配送routeability、Request／Stop mapping受入が必要である。

新規runは過去の全runから分離し、strict成果物またはregistryを変更しない。
