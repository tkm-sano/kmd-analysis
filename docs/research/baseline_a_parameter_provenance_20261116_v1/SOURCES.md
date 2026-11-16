# 出典と確認範囲（2026-11-16）

本台帳の外部資料は業務構造・他条件の参考情報であり、現行数値の導入元と自動的に認定しない。公表日と本調査の確認日を区別する。本文のR番号は研究内の設定・履歴証拠、S番号は外部一次資料である。原文の長い転載は行わず、確認箇所と主張の範囲を記す。

## 外部一次資料

<a id="s01"></a>
### S01 佐川急便「集荷から配送までの流れ」

[公式URL](https://www.sagawa-exp.co.jp/customer/send/guide/beginners/)。公表日未確認。STEP4は営業所の担当エリア、STEP7はエリア別仕分けと担当ドライバーの積込を説明する。日本国内の集配ネットワークの定性的説明である。区域の存在を支持するが、車両別の角度区域、容量、便数、FCFSは示さない。今回Web本文と[保存HTML](sources/S01.html)を確認した。先行証拠は[証拠台帳v2のS01](../baseline_a_redesign_20261113_v2/BASELINE_A_EVIDENCE.md)である。

<a id="s02"></a>
### S02 佐川急便「『ラストワンマイル』を担うセールスドライバー®の業務負担低減」

[公式URL](https://www.sagawa-exp.co.jp/about-csr/column/article_02.html)。2024-04-01。本文冒頭、「スマート集配」「夜積みアプリ」。国内の担当配送について、朝の積込時にルートを考える業務と、AIによる順序提示、夜勤者による積込を説明する。特定拠点の計測研究ではない。朝積込が全事業者共通とはいえず、荷台6区画は容量60の出典ではない。今回Web本文と[保存HTML](sources/S02.html)を確認した。先行台帳v2 S02と照合した。

<a id="s03"></a>
### S03 日本郵便「AIによる配達ルート自動作成などを活用した配達業務支援システムの試行導入」

2020-06-15。[発表ページ](https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02.html)、[本文PDF p.1](https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_01.pdf)、[別紙 pp.1–2 §2–3](https://www.post.japanpost.jp/notification/pressrelease/2020/00_honsha/0615_02_02.pdf)。日本の郵便局の一部エリア、ゆうパック・ゆうパケット等を対象とする試行計画である。積込・配達・順序自動作成・配送状況管理の機能を確認した。約200局は予定規模であり、配送地点数でも導入完了数でもない。具体的な順序アルゴリズムや本研究の固定時間を示さない。今回Web PDFと[本文原本](sources/S03a.pdf)・[別紙原本](sources/S03b.pdf)、抽出テキストを確認した。先行台帳v2 S03と照合した。

<a id="s04"></a>
### S04 ヤマト運輸・ヤマトHD掲載「もっと知りたい！宅急便」

[公式PDF](https://www.yamato-hd.co.jp/facilities/kansai-gateway/pdf/childpamphlet_jp.pdf)。表紙に2026.2。PDF全8ページ中p.5＝冊子7–8ページ「宅急便のしくみ①」、PDF p.6＝冊子9–10ページ「しくみ②」。着営業所での配達エリア別仕分けと、届け先情報によるルート自動設定を確認した。日本の宅急便の教育資料であり、対象拠点の実績表ではない。今回Web PDFと[保存原本](sources/S04.pdf)、抽出テキストを確認した。先行台帳v2 S04と照合した。PDFページと冊子ページを混同しない。

<a id="s05"></a>
### S05 厚生労働省 job tag「宅配便配達員」

[公式URL](https://shigoto.mhlw.go.jp/Occupation/Detail?occupationId=483)。公表日未確認。「どんな仕事？」。国内一般の職業説明として、地域ごとの割当、順序を考えた積込、営業所へ戻り次の荷物があれば積み込む流れを確認した。固定の一日2便上限や対象拠点の実績を示さない。今回Web閲覧の本文を直接確認し、その取得表示を[web_primary_2.txt](sources/web_primary_2.txt)に保存した。一方、直接HTTP保存した[S05.html](sources/S05.html)は業務本文を確認できないアクセス対策応答である。HTTP 200を本文取得成功と扱わない。この区別は先行台帳v2 S05とも一致する。

<a id="s09"></a>
### S09 日本自動車ターミナル「施設案内」「京浜トラックターミナル」

[施設一覧](https://www.j-m-t.co.jp/terminal/)、[京浜施設案内](https://www.j-m-t.co.jp/terminal/keihin.html)。公表日未確認。施設一覧「各ターミナルの概要」、京浜ページ「概要」。大田区平和島2-1-1という所在地を確認した。施設一覧の382バースは施設全体の公表値であり、研究対象ToC業務が使用できる2/4/8バースとは別の集計範囲である。単一事業者への割当や専用利用の記録は取得していない。今回Web本文と[一覧HTML](sources/S09.html)・[京浜HTML](sources/S09b.html)を確認した。探索時の末尾`/keihin/`はWeb取得失敗であり、実在する`keihin.html`で確認した。施設内の別サービスの営業時間を配送車両の08:00〜20:00の根拠にしない。

<a id="s12"></a>
### S12 Google OR-Tools「Resource Constraints」

[公式ドキュメント](https://developers.google.com/optimization/routing/cvrptw_resources)。公表日未確認。冒頭および「Create the data」「Add resource constraints」。配送経路と拠点の同時積卸し台数制約を結合する教材例である。コード例のload/unload time=5、depot_capacity=2は教材内の設定であり、本研究の1800秒や2/4/8バースを実証しない。旧研究計画の文献[4]に引用されており、モデル構造の参考との接続は確認できるが、数値の転記経路は確認できない。今回Web本文と[保存HTML](sources/S12.html)を確認した。

<a id="s13"></a>
### S13 Amazon「配送サービスパートナー」日本語パンフレット V1.1

[公式配布PDF](https://m.media-amazon.com/images/G/01/DSP2/DSP_Brochure_Japanese_V1.1.pdf)。発行日未確認。PDF p.3「商品の配送」と脚注、p.10の留保。日本の独立した配送サービスパートナー事業モデルについて、一日20〜40台の目安に、一台一日2ルートの場合という条件が付く。台数・ルートの単位であり、大田区の観測日や同時出発数ではない。再積込の拠点、便接続、上限2便は当該脚注から確定できない。今回Web PDFと[保存原本](sources/S13.pdf)・[抽出テキスト](sources/S13.txt)を確認した。[2026-11-05の比較資料](../../../investigations/lastmile_single_depot_20261105/japan_carrier_comparison/COMPARISON.md)・[証拠台帳JA04–JA06](../../../investigations/lastmile_single_depot_20261105/japan_carrier_comparison/evidence_ledger.csv)は既にこの参考情報を記録していた。後から初めて発見した資料ではないが、現行の最大2便や10/20/40台をこの資料から決めたという直接の採択記録は未確認である。

<a id="s14"></a>
### S14 Project OSRM「OSRM HTTP server」v5.27.1

[版固定の公式リポジトリ原文](https://raw.githubusercontent.com/Project-OSRM/osrm-backend/v5.27.1/docs/http.md)。資料の公表日未確認。General options、Route service、Route object。profileを事前処理で決めること、Routeの距離m・時間sを確認した。今回[原文保存](sources/S14b.md)とWeb表示を確認した。`https://project-osrm.org/docs/v5.27.1/api/`の直接取得は404であり、失敗も[取得ログ](SOURCE_ACCESS_LOG.json)に残した。公式仕様は単位・計算上の意味を示すが、対象日の実走行時間や混雑再現の証拠ではない。現行ODの実使用版・道路日付はR09のmanifestで確認する。

## 研究内の設定・履歴証拠

以下の版日付は文書・設定内の記載である。Gitで追跡されていない資料について、ファイル名の日付やmtimeを導入commitの証明にしない。

<a id="r01"></a>
### R01 共通条件 v1.0 / v1.1

[v1.0 JSON](../../../configs/toc_delivery/common_conditions_v1.json)、[現行v1.1 JSON](../../../configs/toc_delivery/common_conditions_v1_1.json)、[説明文](../toc_delivery_common/COMMON_CONDITIONS_V1.md)。設定中のoperations、scenarios、scope、provenance、revisionを直接確認した。2026-11-11採択、運行値はresearch_assumption/measured=false、指示識別子を記録する。v1.0の準備900秒のみv1.1で0秒へ変わる。指示識別子は原指示全文や数値の科学的根拠そのものではない。旧road_policy/comparison/unresolvedの一部は後続R05/R09で扱いが更新されており、その文言だけで現行の道路・Aの名称を決めない。

<a id="r02"></a>
### R02 2026-11-08計画・スコープ監査

[TOC_DELIVERY_SPEC.md](../TOC_DELIVERY_SPEC.md)（冒頭の11/10追補と11/08本文を分けた）、[study.json](../../../configs/toc_delivery/study.json)、[計画原本](../../../docs/audits/toc_scope_20261108/source_plan_original.docx)、[改訂計画](../../../research_plan_toc_three_objectives_faceted_20261108.docx)、[変更記録](../../../docs/audits/toc_scope_20261108/DOCX_CHANGES.json)。DOCXをZIP/XMLから読取り、[原本段落](source_plan_original_TEXT.json)と[改訂段落](research_plan_toc_three_objectives_faceted_20261108_TEXT.json)を保存した。段落番号は0始まり。18–33に規模、37に2便・時間窓なし、39に旧作業時間、41に旧216PE、43に旧07:00、48–53に帰着とバースの接続、125–130に文献がある。原本段落39は102秒を既存研究設定、20分を仮定とする。改訂版とstudy.jsonは適用根拠未確認のHOLDとして保持しており、現行採択値ではない。

<a id="r03"></a>
### R03 旧研究の102秒・216PE

[QUANTITATIVE_GUIDE.md](../../QUANTITATIVE_GUIDE.md) §3/§8、[RESEARCH_BASELINE_20261009.md](../RESEARCH_BASELINE_20261009.md) §5、[11/05パラメータ判定](../../../investigations/lastmile_single_depot_20261105/parameter_decisions.csv)、[11/05入力監査](../../../investigations/lastmile_single_depot_20261105/probes/local_input_audit.json)のsummary/inputsの一部を確認した。保存監査には10/06を含む旧入力の102秒があるが、本調査で旧NPZ全件を再検査したものではない。Gitではガイドの102の記載が少なくとも`84bb50141240da5f53055c3008bdaa4a5b6e5977`（2026-10-09）に存在し、基準文書は`1376dc50265557abeb37abe396774177fc8f39b2`（同日）で記載された。このcommitは説明文の導入であり、102という値の最初の生成・選択理由を示すものではない。旧ガイドも102秒を研究仮定とし、全来歴未確定を明記する。

<a id="r04"></a>
### R04 A2・A-area-v3・証拠台帳

[11/12 A_RULE_BASELINE_SPEC.md](../toc_delivery_a/A_RULE_BASELINE_SPEC.md)、[実装計画](../toc_delivery_a/A_RULE_IMPLEMENTATION_PLAN.md)、[旧設定](../../../configs/toc_delivery/a_rule_baseline_v1.json)、[11/13証拠台帳v2](../baseline_a_redesign_20261113_v2/BASELINE_A_EVIDENCE.md)、[11/13仕様](../baseline_a_redesign_20261113_v2/BASELINE_A_SPEC.md)、[11/15 A-area-v3仕様](../baseline_a_area_v3_20261115/BASELINE_A_SPEC.md)を確認した。A2の地点proxy負荷調整と新Aの全体時刻O/Hは別である。旧A1〜A3の0/120/240度比較は現行Aの多開始角ではない。A-area-v3は外部訪問順校正でNNを選んだ記録であり、既に11/12にあるNN導入の起源でも対象実績適合の証明でもない。

<a id="r05"></a>
### R05 A_rule_v1の確定版

[仕様](../baseline_a_rule_v1_20261115/BASELINE_A_RULE_SPEC.md)、[仮定・変更台帳](../baseline_a_rule_v1_20261115/ASSUMPTION_AND_CHANGE_LOG.md)、[実験契約](../baseline_a_rule_v1_20261115/EXPERIMENT_CONTRACT.md)、[最終報告](../baseline_a_rule_v1_20261115/FINAL_REPORT_JA.md)、[採否JSON](../baseline_a_rule_v1_20261115/DECISION.json)、[現行設定](../../../configs/toc_delivery/a_rule_v1_20261115.json)、[生成器](../../../src/kmd_toc/baseline_a/rule_v1.py)、[入力アダプタ](../../../src/kmd_toc/baseline_a/rule_inputs.py)、[規則検証](../../../src/kmd_toc/baseline_a/rule_validation.py)、[CLI](../../../scripts/run_a_rule_v1.py)。角度、NN、分割、FCFS、O/H、停止の実装を読取り照合した。全体時刻に基づく調整、先着厳密改善、最大V回の設計目的が変更台帳に明記される。

<a id="r06"></a>
### R06 新比較契約と過去のDWT設定

[COMPARISON_CONTRACT.md](../comparison_integration_v1_20261115/COMPARISON_CONTRACT.md)、[A接続仕様](../comparison_integration_v1_20261115/A_INTEGRATION_SPEC.md)、[参照・集計仕様](../comparison_integration_v1_20261115/REFERENCE_AND_AGGREGATION_SPEC.md)、[完了記録](../comparison_integration_v1_20261115/COMPLETION_STATUS.json)、[旧4枝DWT設定](../../../configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json)、[比較CLI](../../../scripts/run_comparison_v1.py)。方式全体比較、A固有FCFS、B/C/D完成器、共通物理条件、計時範囲、4物理コア枠を確認した。DWT設定8版のA/参照/資源等を[BCD_CONFIG_HISTORY_READ.json](BCD_CONFIG_HISTORY_READ.json)へ抽出した。旧Tref60秒・旧Aの名称は現行基準に使わない。新契約のTには必要な子プロセス準備と受渡しを含める。

<a id="r07"></a>
### R07 凍結需要と生成履歴

[凍結設定](../../../configs/toc_delivery/frozen_demand_v1.json)、[凍結読取契約](../../../03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/READING_CONTRACT.md)、[TOC仕様11/10追補](../TOC_DELIVERY_SPEC.md)。元の39,956建物地点の町丁目別地点数比率を用い、候補34,912から最大剰余配分と共通SHA256順位で無復元抽出する。1,000/2,000/4,000は包含関係を持つ。住所・建物の実在性と、その日の配送需要の観測は別である。

<a id="r08"></a>
### R08 既存データ用途監査

[DATA_USAGE_LEDGER.md](../baseline_a_existing_data_audit_20261115_v1/DATA_USAGE_LEDGER.md)、[セル・行照合記録](../baseline_a_existing_data_audit_20261115_v1/run02/DATA_LINEAGE_CHECKS.json)。国勢調査2020、住宅・土地統計2023、東京都市圏物資流動調査2024、PLATEAU大田区2025等の利用接続と未回復工程を確認した。本調査は同記録を読んだもので、統計原表の全セル照合を再実行していない。母集団・単位・使用済みデータと独立検証の違いを引き継ぐ。これらは現行60/120/1800等の運行値を測定した資料ではない。

<a id="r09"></a>
### R09 現行Route版OD

[S2 manifest](../../../output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S2/od/manifest.json)のmetadata、filesを確認した。OSM関東2026-07-16、OSRM5.27.1、static car、同一Route objectの距離・時間、Route per ordered pair、table_distances_used=falseを記録する。S1/S3も現行設定でこの版を固定する。研究地域は大田区だが道路graphは関東全体である。道路が大田区境界で切断されるという意味ではない。道路の新規取得・OD再生成や全配列の科学的再検算は本調査では行っていない。

<a id="r10"></a>
### R10 保存済み実行・検証記録

[全試行](../baseline_a_rule_v1_20261115/ALL_ATTEMPTS.json)、[再現性記録](../baseline_a_rule_v1_20261115/REPRODUCIBILITY.json)、[再現コマンド](../baseline_a_rule_v1_20261115/REPRODUCE.md)、R05/R06の最終報告と完了記録。既存の限定検証と対象実績未取得の判定を読取り確認した。S2の保存原形式計画hashは本調査の読取監査でも照合する。既存テストのPASSを本調査で新たに実行したPASSと数えない。

## 保全・履歴の限界

[Git監査](GIT_HISTORY_AUDIT.json)と[開始時状態](GIT_STATUS_BEFORE.txt)が確認範囲の正本である。HEADは`8605d5412f6af62229a83095c35ab04c8c7dd9b1`である。現行共通設定・A設定・11月の設計資料の多くは未追跡であり、導入commitを確定できない。設定のauthorityは採択指示を記録した事実であり、その原指示を全て回収したという意味ではない。旧資料の数値と後続採択値を混同せず、説明上の差分として残す。

追加取得の時刻・HTTP状態・hashは[SOURCE_ACCESS_LOG.json](SOURCE_ACCESS_LOG.json)と[補足ログ](SOURCE_ACCESS_SUPPLEMENT.json)、Web本文の保存はsources/web_primary_*.txtにある。後から確認した資料は、当初の採択理由が欠けた部分を補う証明として用いない。
