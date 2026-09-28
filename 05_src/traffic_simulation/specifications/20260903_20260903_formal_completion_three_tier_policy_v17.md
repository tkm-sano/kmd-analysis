<a id="formal道路網完成の三層方針-v17"></a>

# 正式道路網完成の三層方針 v17

文書識別子: `SPEC-P13-FORMAL-COMPLETION-THREE-TIER-V17`
役割: `CURRENT_NORMATIVE`
ライフサイクル: `CURRENT`
作成日: `2026-09-03`
最終更新日: `2026-09-03`
現行正本: `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`

Decision: `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001`
Registry: `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml`

以前のhierarchical-混合型 決定記録は履歴方針として保持し、本決定記録がsupersedeする。厳密方式 v17基準、阻害要因一覧、モデル選択ベンチマーク、欠落-領域成果物は読取り専用証拠として維持する。

## 意味論

構造上のは出典 truthであり、未加工 出典表現、接続構造、lineage、正規化した出典状態を表す。正式は研究・simulationで使用する完全なモデル-準備完了道路網である。正式値は出典観測値である必要はないが、各値は解決 階層、手法、確信度、仮定、元の欠落／阻害要因状態、出典・来歴を保持しなければならない。

解決 階層は`DIRECT`、`INFERRED`、`FALLBACK`だけとする。`DIRECT`は出典証拠または一意に採択した規則、`INFERRED`は再現可能な完成機構（外部data、局所伝播、経験的群化、統計／ML）、`FALLBACK`は決定論的既定値または保守的規則である。`INFERRED`と`FALLBACK`を`OBSERVED`または`DIRECT`として表現してはならない。

確信度は`HIGH`、`MEDIUM`、`LOW`、`FALLBACK`のいずれかとする。`DIRECT`の既定値は`HIGH`である。`INFERRED`の確信度はモデル確率、属性提供元一致、ベンチマーク性能、feature適用可能性を組み合わせる。欠落-領域 表示名がなければ確信度を下げるが、完成処理は停止しない。`FALLBACK`の確信度は常に`FALLBACK`である。

## 解決規則

統制対象となる車線、速度、通行許可／接続、関係、条件付き 記録はすべて`DIRECT → INFERRED → FALLBACK`に従う。推論に失敗した場合は代替値選択前にabstention理由を記録する。三層すべてで実行可能な最終値を生成できなかった技術的失敗だけを阻害要因とする。

車線は、正確にリンクできる場合は外部証拠を優先する。それ以外は連続性、距離、遷移実行制御を満たす局所伝播、経験的群または決定論的ML機構、道路種別／スーモ／MATSim形式／保守的代替値の順に選ぶ。既存ベンチマークの網羅率、bias、MAE、決定性、利用可能feature、確信度、費用を選択付随情報として記録する。明示値領域での性能を欠落-領域の証拠として提示しない。

速度について、具現化する道路網属性は`operational_speed_kph`とする。法定・標識上の`maxspeed`は分離し、運用速度予測で上書きしない。外部・経験・モデル機構を決定論的道路種別代替値より先に適用する。

通行許可／接続は、車種別の明示証拠と決定論的オープンストリートマップ意味論を優先する。利用できない場合は、決定論的方針 代替値により統制対象の配送車両をallowまたはdenyへ解決する。MLまたは経験的予測は確認候補を抽出できるが、法的接続を付与してはならない。

未対応関係または条件付き構文は、可能な場合は設定時刻で評価し、それ以外は決定論的制限 代替値または出典・来歴付き明示ignore規則を使う。出典構文と元阻害要因を保持する。

## 記録契約

各正式 記録は、`final_value`、`resolution_tier`、`method_id`、`method_version`、`confidence`、`source_evidence`、`source_identity`、`assumption_id`、`provenance`、`original_missing_or_blocker_state`を必ず含む。出典・来歴には出典 保存時点の記録 ハッシュ値、出典 道路地物／記録 同一性、決定識別子、手法／版、feature／入力 ハッシュ値、再生成コマンド、阻害要因 識別子、停止コードを含める。暗黙の代替値を禁止する。

## 品質と受入

主要な品質会計は、履歴阻害要因数ではなく、階層比率、確信度分布、手法分布、属性分布、未解決の技術的失敗である。`FORMAL_NETWORK_ACCEPTED=true`には、全統制属性の最終値、完全な出典・来歴、スーモ 構築・妥当性検査、connectivity、配送到達可能性、Request／配送地点の対応付け受入が必要である。

新規実行は過去の全実行から分離し、厳密方式成果物または登録簿を変更しない。
