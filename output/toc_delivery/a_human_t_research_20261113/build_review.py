"""Render the cross-sector human planning-time evidence review; no model edits."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOC = Path('docs/research/toc_delivery_a')
manifest = {r['id']: r for r in json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())}
rows = []

def add(key, source_id, name, task, before, low, high, relation, workload, staff,
        boundary, limitations, role, scores, locator):
    source = manifest[source_id]
    row = dict(id=key, source_id=source_id, name=name, task=task, before_original=before,
        before_s_low=low, before_s_high=high, numeric_relation=relation,
        workload=workload, staffing=staff, measurement_boundary=boundary,
        limitations=limitations, evidence_role=role,
        source_score=scores[0], time_score=scores[1], scale_score=scores[2],
        staff_score=scores[3], boundary_score=scores[4], total_score=sum(scores),
        score_max=10, S1_direct_adoption='HOLD', source_url=source['url'], locator=locator,
        local_source=source.get('path',''), source_sha256=source.get('sha256',''),
        verification='retained_primary' if source.get('status')==200 else 'web_primary_only',
        value_nature='published report/interview; not independently observed by researcher')
    rows.append(row)

add('SUWA', 'suwa', '諏訪梱包運輸／ライナロジクス', '複数車両の潤滑油配送計画',
    '2時間30分〜3時間（詳細工程記述）。別箇所に概括2〜3時間', 9000,10800,'reported_approx_range',
    '100〜150配送件/日、6〜7台。全社140両と混同しない',
    '主担当者の実名インタビュー。補助者を含む全参加人数は未確定',
    '翌日オーダー確定後の重量/配送先チェック→配車→ドライバーへ指示できる状態',
    '件数と時間の個票対応なし。繁忙時は3時間超。全地点ゼロから設計かは不明。共通バース制約/検査時間の包含不明',
    'PRIMARY_CALIBRATION_CANDIDATE', [2,2,2,1,2], '導入前の課題／配車業務の工数、2025-01-28')
add('OKUMURA','okumura','奥村商事／配車頭','産業廃棄物の収集配車',
    '毎日2時間ほど',7200,7200,'approx_point','対象件数/車両数未取得',
    '配車主担当本人が作成。別の営業事務が電話受付',
    '受付して予定表へ記入した後、帰社後に配車計画を作成',
    '受付/転記は別工程。N/V不明のため1件係数へ換算できない。全体最終検査範囲不明',
    'EXTERNAL_DAILY_PLAN_ANCHOR',[2,2,0,2,1],'課題と背景。導入前2021-03以前')
add('TOMAS','tomas','TOMAS／ジェイ・ビー・クラフト','手動配車の供給者スタッフ検証',
    '約4時間',14400,14400,'approx_point','大阪の企業間集配50案件、10台、約30%時間指定',
    '供給者スタッフ。人数と並列性は不明',
    '受注データとMAPから配車スケジュール作成',
    '実事業者の日常観測ではなくデモ検証。50集配案件は50地点とは限らない。経験不明',
    'EXTERNAL_MANUAL_BENCHMARK',[2,2,2,0,1],'テストデータ／ケース1')
add('STOPSTART','stopstart','Stop Start／Descartes','大型・取扱注意品の全体配車',
    '本文では3人で毎日4時間超。要約は4時間',14400,None,'greater_than_reported_threshold',
    '本文約1200配送/70台、要約約1000配送/50台で不一致。対象時点は特定不能',
    '3人の計画チーム。4時間を12時間の経過時間として扱わない',
    '手動の紙ベース計画。plan and executeの工程混在に注意',
    'N/Vの時点不一致、原測定境界・個票なし。12人時超への換算にも全員の連続稼働仮定が必要',
    'EXTERNAL_TEAM_ELAPSED_ANCHOR',[2,2,1,2,1],'The Challenge／Case Study Key Takeaways')
add('SPRINGHOPE','routific','Spring Hope Food Drive／Routific','フードバンク活動の複数車両ルート作成',
    '4時間',14400,14400,'reported_point','改善前30台。配送地点数未取得',
    '主催者Landon Gooldの作業。補助者の有無は不明',
    '手作業でイベントの経路を作成',
    '年次イベントで日常の熟練配車とは異なる。SVGの15.5時間は走行時間でTではない',
    'EXTERNAL_MANUAL_BENCHMARK',[2,2,1,1,1],'Case study: Spring Hope Food／原SVGを描画し目視、本文照合')
add('MSJ','msj','メジャーサービスジャパン／ダイセーHD','紙地図とExcelによる配車',
    '1日平均約4時間',14400,14400,'approx_average','全6拠点合計150台/200ドライバー。拠点別車両/配送件数不明',
    '配車人数未取得',
    'Excelで計画作成、紙地図で配送順を検討',
    '各拠点での改善を記述。全社150台を4時間の対象台数へ直結しない。150/6台の代表値も作らない',
    'EXTERNAL_DAILY_PLAN_ANCHOR',[2,2,1,0,1],'導入前の課題、2026-03-25発表')
add('JP_EXPERT','nihonyubin','日本郵便／Loogia','各ドライバーの紙地図ルート作成',
    '熟練者5〜10分',300,600,'reported_approx_range','配送先数/便数不明',
    '各ドライバーによる作成。全車両を共同計画する人数ではない',
    'ルート作成。全体割当/バース/最終検査の包含不明',
    '1便か1日か未確定。100先/台や最大2便へ直接換算不可',
    'ROUTE_SUBTASK_REFERENCE',[2,2,0,1,1],'導入前の課題。2021年時点の事例、Web原文確認、直接取得403')
add('JP_NOVICE','nihonyubin','日本郵便／Loogia','各ドライバーの紙地図ルート作成',
    '新人30分〜1時間',1800,3600,'reported_approx_range','配送先数/便数不明',
    '各ドライバーによる作成',
    'ルート作成のみと識別。配達時間との差分67分は使わない',
    'N不明のため1先比例係数を同定できない',
    'ROUTE_SUBTASK_REFERENCE',[2,2,0,1,1],'導入前の課題、Web原文確認')
add('ZENRIN_EXPERT','zenrin','関東燃料卸売業者／ゼンリン','各ドライバーの1日配送ルート作成',
    '熟練者約10分',600,600,'approx_point','繁忙期20〜30配送件/日、部門全体20台',
    '各ドライバーが記憶/経験に基づき作成',
    '前日に配送リストで配送先を把握してからルートを検討',
    'NとTの同じ個票対応なし。地点確認を前処理で済ませる可能性。20台全体Tではない',
    'ROUTE_SUBTASK_REFERENCE',[2,2,1,1,1],'課題・背景')
add('ZENRIN_NOVICE','zenrin','関東燃料卸売業者／ゼンリン','新人/代行者の1日配送ルート作成',
    '30分〜1時間',1800,3600,'reported_approx_range','新人等10〜15配送件/日、部門全体20台',
    '各ドライバーによる作成',
    'ルート作成。配達中の住所確認ロス5〜10分/件は加えない',
    '熟練者と割当件数自体が異なる。両者の差を純粋な熟練効果とみなさない',
    'ROUTE_SUBTASK_REFERENCE',[2,2,1,1,1],'課題・背景')
add('MLIT_NAGOYA','mlit172','国交省研究172号／SWAT Mobility聴取','粗大ごみ収集の人手配車',
    '半日',None,None,'qualitative_day_fraction','対象件数/車両数不明。2t/4t混在の記述',
    '人数不明','紙による収集ルート作成・配車計画',
    '半日の実働時間は未定義。勝手に4時間/14400秒へ変換しない',
    'QUALITATIVE_EXTERNAL_REFERENCE',[2,0,0,0,1],'本文p.13、PDF19ページ、2022-11インタビュー')
add('MLIT_TAMANO','mlit_tamano','国交省手引き／岡山県玉野市','乗合タクシーの配車計画',
    '20分',1200,1200,'reported_point','1回の計画対象人数/案件数/車両数不明',
    '人数不明','予約受付5分と配車計画20分を区別',
    '一日全体か予約バッチか不明。別事例の久米南町5両を混ぜない',
    'EXTERNAL_DISPATCH_REFERENCE',[2,2,0,0,1],'印刷p.31、PDF31ページ、玉野市の効果欄')
add('FAREYE','fareye','インドネシア食料品チェーン／FarEye','手動ルート生成',
    '1ルート120分',7200,7200,'reported_point_per_route','チェーン180超店舗/40都市。1ルートの配送先数は不明',
    '人数不明','原文はeach routeのgeneration',
    '顧客匿名、ルート単位が不明。チェーン店舗数を1回の計画規模にしない',
    'LOW_PRIORITY_SUBTASK_REFERENCE',[1,2,0,0,1],'1ページPDF Challenges欄。100000routesは累積指標')
add('HANDUP','routific_handup_summary','Hand Up Toronto／Routific','食料支援の配送ルート作成',
    '300世帯分の計画にteamで10時間',36000,36000,'reported_ambiguous_team_time','300世帯。車両数未取得',
    'teamとの記述のみ。総人時か経過時間か未確定',
    '配送計画。全体の開始終了定義不明',
    '10時間をそのままwall-clock Tにしない。8→35人は組織の成長で計画担当人数ではない',
    'HOLD_TIME_UNIT',[2,1,1,0,1],'Manual route management: the old way')
add('DEGRAAF','degraaf','De Graaf Logistics／PTV','旧ソフトを用いた半自動計画',
    '少なくとも3時間、21時開始で翌1時終了も多い',10800,14400,'minimum_and_example_not_range','75台。件数不明',
    '旧チームの人数不明。担当/補助の記述あり',
    'Route Optimiser STを使い手修正する半自動作業',
    '純粋な人手Aの時間係数に混ぜない。3〜4時間の実測分布とも呼ばない',
    'EXCLUDE_PURE_MANUAL_CALIBRATION',[2,2,1,1,1],'Since2012／Planning time cut to1.5 hours')
add('SMRJ_BILLING','smrj_billing','中小機構・省力化事例','配車入力から請求確定までの事務',
    '4時間',14400,14400,'reported_point_wrong_scope','件数/車両数不明','人数不明',
    '配車入力→請求金額確定',
    '請求/経理を含むので本研究Tへ代入不可。配車という名称だけで採用しない',
    'EXCLUDE_WRONG_BOUNDARY',[2,0,0,0,0],'成果欄、1ページPDF')
add('HITACHI_MONTH','hitachi','三井物産・日立','複数拠点の月次配送計画',
    '複数熟練者で1〜2日',None,None,'reported_work_days_undefined','検証は物流3社/4センター半年分。個別計画のN/V不明',
    '複数熟練者、人数/並列稼働は不明',
    '月次計画、配送日・車両・横付けスペース利用順の調整',
    '1日=8hに勝手に換算しない。月次を30で割って日次Tにしない',
    'STRATEGIC_PLANNING_REFERENCE',[2,0,0,1,1],'2019-02-28発表、注記3')
add('COOP_REDESIGN','coop','コープさっぽろ／調和技研','センター全体の大改廃',
    '夕方以降の作業で3か月',None,None,'calendar_duration_not_working_time','約2万配送先、車両数不明',
    '30〜40人','紙地図への地点記入→コース設計→システム再入力',
    '日々の計画ではなく全面再設計。作業日数/時間不明、日次Tへ換算不可',
    'STRATEGIC_PLANNING_REFERENCE',[2,0,1,2,2],'46万世帯への配達コースを人手で作成していた、2024-01-31')
add('VISSER1989','visser','Visser & Scheltes (1989)','手動/ソフト配送計画の比較研究',
    '表2のTotal timeは運行31/78時間等',None,None,'operating_hours_not_planning_time','40/80集配案件、最良人手解6/7台、参加計画者7人',
    '7人は比較対象の計画者数。共同作業人数ではない',
    '表2の時間は配送運行の合計と残業時間',
    '論文本文と表2原画像を確認。計画作成時間の数値は未取得',
    'EXCLUDE_WRONG_METRIC',[2,0,2,0,0],'Journal of Transportation Research Forum30(1),47–52、表2p.51（PDF6ページ）')
add('METI_LEAD','meti_hayashi','経産省事例集／林ホールディングズ候補','生コン配車の候補資料',
    '検索紹介では1〜2時間、原資料の当該ページ未確認',None,None,'unverified_search_lead','未確認','未確認','未確認',
    '原資料取得403。検索紹介のみで時間値を採用しない。PDF全体の公開URLを記録',
    'UNVERIFIED_NO_ADOPTION',[0,0,0,0,0],'2025事例集。再取得が必要')

def table(headers, body):
    return '|'+ '|'.join(headers)+'|\n|'+'|'.join('---' for _ in headers)+'|\n'+''.join('|'+ '|'.join(str(v).replace('|','/') for v in row)+'|\n' for row in body)

def main():
    outcsv=ROOT/'EVIDENCE.csv'
    with outcsv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (ROOT/'EVIDENCE.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    selected=[r for r in rows if r['id'] in ['SUWA','OKUMURA','TOMAS','STOPSTART','SPRINGHOPE','MSJ','MLIT_TAMANO','MLIT_NAGOYA']]
    summary=table(['候補','改善前の人手T','確認できた規模/人員','評価点/10','利用判定'],[
        [f"[{r['name']}]({r['source_url']})",r['before_original'],r['workload']+'。'+r['staffing'],r['total_score'],r['evidence_role']] for r in selected])
    model_checks=[]
    for N in [100,150]:
        for V in [6,7]:
            seconds=600+4*N+60*V+120*V+24*N
            model_checks.append(dict(N=N,V=V,P_assumed=1,old_central_model_s=seconds,old_central_model_min=seconds/60,
                published_source='SUWA',published_s_low=9000,published_s_high=10800,
                interpretation='unpaired workload corners; one-planner assumption; compatibility diagnostic, not validation data'))
    assert min(r['old_central_model_s'] for r in model_checks)==4480
    assert max(r['old_central_model_s'] for r in model_checks)==6060
    with (ROOT/'OLD_MODEL_COMPATIBILITY.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(model_checks[0]));w.writeheader();w.writerows(model_checks)
    sources_verified=sum(r.get('status')==200 for r in manifest.values())
    report=f'''# Aの人手T：業種横断による再調査

2026-11-13。ToC一致を必須条件にせず、人手による計画作成の作業範囲・規模・人数・経過時間を評価した。配送そのものの所要時間を調べた報告ではない。

**結論：複数車両を人が計画する作業について、約2〜4時間の公開事例を新たに確認した。これは異なる事例の外部参照集合であり、S1の推計レンジ・信頼区間・佐川実績ではない。** 最優先候補は諏訪梱包運輸の100〜150件/6〜7台、確認開始から指示可能になるまで約150〜180分のインタビュー。数値を合わせるために既存の係数を調整しない。

## 監査範囲と保存

国内B2B配送、廃棄物収集、食料支援、海外大型品配送、公共交通配車、月次配送計画、学術的な人手VRP比較まで拡大した。一次の実名事例・企業発表・行政原PDFを優先し、匿名のAI紹介記事や二次要約から数値を確定しなかった。{len(rows)}候補/条件を登録、直接取得できた原資料{sources_verified}ファイルをURL・取得日時・SHA256と保存。直接HTTP取得に失敗してもWeb原文を確認できた資料と、検索結果のみの候補を区別した。

成果根：`{ROOT.relative_to(Path.cwd())}/`。`SOURCE_MANIFEST.json`、`EVIDENCE.csv/json`、原HTML/PDF・テキスト、図表画像を保存。本文は原文の要約であり、原資料の公開利用条件はそれぞれに従う。公開ページとオープンライセンスのデータセットは同一ではなく、本調査で人手作業の個票データセットを取得したとはしない。

既存A1〜A3、凍結需要、A〜D実験結果、採用設定、`A_HUMAN_TIME_CALIBRATION.md`を変更しない。既存の統合判定を上書きしない追加調査で、commit/push・事業者連絡・有料サービスは行わない。

## 評価方法

業種一致は採点条件にしない。各項目0〜2点、合計10点：①原資料の信頼性（実名の当事者報告/行政/原著2、匿名事例1、原文未確認0）、②時間単位と人手Tの識別（秒分時間と対象明瞭2、労働量/経過が曖昧1、運行時間/日月の実働換算不能0）、③規模（同じ作業のN/Vが両方判明2、一方だけ/時点不整合1、両方不明0）、④作成人員（人数明記2、各担当者/主担当の記述のみ1、未取得0）、⑤工程（始終点と作業内容明記2、工程の概略のみ1、別業務/未確認0）。

点数は文献利用時の情報充足度で、測定精度・統計的信頼度・S1換算可能性を表さない。高得点でも半自動処理や対象工程が違えば人手モデルの係数には採用しない。数字は供給者記事・企業インタビュー等の公表値であり、研究者が独立実測した値ではない。開始終了の生ログ、人数ごとの稼働、日ごとのN/V/Tが得られた事例は確認できなかった。

## 有力な参照値

{summary}

## 優先資料と解釈

1. **諏訪梱包運輸を第一の校正候補とする。** 潤滑油の配送を地域別に割り当て、重量/件数の偏りを調整する作業は、Aの地域割当と負荷調整に近い。詳細工程はオーダー確定→重量と配送先の確認→配車→ドライバーへ指示できる状態、150〜180分。概括の120〜180分を優先して下限を下げない。主担当者は分かるが全参加人数は未確定。繁忙時は3時間超もあるので180分を上限保証にしない。業種差は説明項目であり除外理由ではない。
2. **奥村商事の約120分は国内の単独主担当による日次計画参照。** 受注受付は別の営業事務で、その工程を含めた全Tではない。N/Vは未取得なので1件あたり秒数にはしない。
3. **TOMASの約240分は手動作成の検証例。** 50件の集配案件/10台という規模が分かるが、供給者スタッフのデモで実事業者の実務観測と同じには扱わない。50案件=50配送地点としない。
4. **Stop Startは複数人の経過時間の参考。** 3人/4時間超と記載されるが、要約の1000件/50台と本文1200件/70台の時点が整合しない。片方を都合よく選んで比例係数を作らない。4時間を3倍して12時間の経過時間としない。総人時への換算にも全員がその間稼働したという仮定が必要。
5. **Spring Hopeは主催者の約240分/改善前30台の手動ルート作成例。** 本文と原SVGで一致。図の15.5時間は合計走行時間でTではない。3分の自動計算時間や改善率をAに採用しない。地点数と補助者は未取得。
6. **メジャーサービスジャパンは日次約240分の実名企業発表。** 全社150台/6拠点を、時間測定と同じ単位の150台として使わない。配車担当人数・拠点別案件数未取得。

## 行政資料と不採用例

- 国交省研究172号の名古屋粗大ごみ収集は、印刷p.13/PDF19ページに人手の配車計画に半日と記載。半日の実働時間未定義のため4時間へ数値化しない。
- 国交省手引きの玉野市は印刷/PDFともp.31に配車計画20分と予約受付5分を別記。人数・案件単位未取得なのでS1へ直接換算しない。同ページの別自治体の5両と混ぜない。
- 日立2019-02-28発表の月次計画1〜2日は、複数熟練者の作業。1日8時間や日次への30分割は裏付けがない。
- PTV/De Graafの旧計画3時間以上/21時〜翌1時は、旧Route Optimiser STを使う半自動運用。人手のみのAへ混ぜない。システム間比較の参考に留める。
- FarEyeの120分は原文で1ルートの生成時間。1ルートの地点数不明、匿名顧客。全車両の計画Tに代入しない。
- Hand Upの300世帯/10時間はteamという記載で経過時間か総人時か未確定。主比較へ採用しない。
- 中小機構の4時間は配車入力から請求金額確定までを含むため、計画作成Tに使わない。
- Visser & Scheltes (1989)の原著PDFを取得し表2原画像と本文を確認。31/78時間等は運行時間で計画作成Tではない。学術資料という理由で混同しない。
- 経産省の林HD候補は当該原ページを取得できず、検索紹介の1〜2時間を数値登録しない。資料未取得はデータ不存在を意味しない。

## 既存中央モデルの数値照合

先の171分はS1の均等100地点/台、5人並列という研究仮定から得た10240秒。文献による校正値ではない。約2〜4時間という他事例の時間帯に入ることだけでは妥当性を確認できない。

旧中央係数を保ち、仮に主担当1人、全車使用とすると、同モデルは `T=600+4N+60V+120V+24N=600+28N+180V` 秒となる。諏訪の記事のN=100〜150、V=6〜7を代入した端点組合せは4480〜6060秒（74.67〜101分）で、記事の詳細150〜180分と一致しない。

これは作成人数・工程差・地理・重量判断等を未観測のまま行う**整合性診断**であり、同一個票に対する予測誤差検証ではない。各端点が同じ運行日に対応するとは分からない。旧係数を文献校正済みとする根拠にはならず、時間帯だけを合わせた新係数も作らない。

## AのTへの採用方針

### 確認済みとして採用できるもの

- 複数車両の計画作成について、国内外に約120分、150〜180分、約240分、240分超の公開例がある。各行の工程と単位付きの**外部参照値**として採用する。
- 1担当者の訪問順検討に関する日本郵便/ゼンリンの5〜10分/30〜60分等は、下位工程の参考として残す。全車両の割当・バース計画Tをその値だけで構成しない。
- 上記は異なる母集団・規模・工程の選択事例。120〜240分を人手一般の統計的レンジやS1の確定Tとしない。資料選択には長時間例もあり、全てを包含する範囲でもない。

### 今後の感度条件として提案するもの（未採用）

必要なら `7200 / 10800 / 14400秒` を「公開事例を参考に設定した全体計画時間の感度条件」として事前登録できる。7200と14400は各別事例の参考、10800は諏訪の詳細記述に対応する時間水準で、同じS1計画の分布や中央値ではない。**A1〜A3・S1〜S3の測定Tとして代入せず、プログラムTとの実証速度比を主張しない。** 今回は設定・既存結果を変更していない。

### S1のTモデルを更新する条件

全体の始終点を共通定義へ揃え、`T_A=T準備・割当+並列経路作成の完了まで+Tバース調整・検査`という逐次工程仮定を明示する。工程が重複する場合は依存関係に従う完了時刻を用い、単純加算しない。Pは車両数から推定せず独立した感度条件。日別のN/V/P/工程時刻がない資料から1地点秒数、固定準備、調整時間を同時に同定できない。

問い合わせをしない方針でも、研究者自身が同じROAD_N20/ROAD_N120の計画作成を行い、工程開始終了と修正・検査を測ることは可能。その場合も佐川の熟練者実測とはしない。人手実測を行わず完結させる場合は、文献参照型の仮定モデルと感度分析として論文へ記載し、外部参照とS1推計を分ける。人手TとD/Wは同じ実行計画から同時観測された3指標ではないことも明示する。

## 判定

|判定対象|結果|
|---|---|
|業種横断での人手計画Tの外部参照値|GO：工程・単位付きで取得|
|Aの仮定モデル/感度条件への文献利用|CONDITIONAL GO：実務工程と人数の仮定を明記|
|既存24秒/地点・5人・171分の文献校正|HOLD：直接の裏付けなし|
|S1の全工程人手Tの確定・実測速度比|HOLD：同条件の工程時刻/作成人数が未確認|

再現：原資料はsources/とSOURCE_MANIFEST.json、数値はEVIDENCE.csv/json。`python {ROOT.relative_to(Path.cwd())}/build_review.py`で表/旧モデルの算術を再生成。既存コードの試験を再実行する変更はしていない。単位換算・資料との対応・保存hash・既存ファイルの保全はVALIDATION.jsonを参照。
'''
    doc=DOC/'A_HUMAN_T_CROSS_SECTOR_REVIEW_20261113.md'
    doc.write_text(report)
    (ROOT/doc.name).write_text(report)
    (DOC/'A_HUMAN_T_CROSS_SECTOR_EVIDENCE_20261113.csv').write_bytes(outcsv.read_bytes())
    print('rendered',len(rows),'evidence rows',doc)

if __name__=='__main__': main()
