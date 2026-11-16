"""Evidence-led adoption of a route-creation reference, not full human T."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DOC=Path('docs/research/toc_delivery_a')
CONFIG=Path('configs/toc_delivery/a_human_route_time_reference_v1.json')
sources={s['id']:s for s in json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())}

# Selected passages read through the web tool. These are selected excerpts,
# not complete downloaded HTML, and are labelled separately from HTTP archives.
web_passages={
 'JP':{'verification':'live primary page read via web tool; direct urllib HTTP403',
       'passage':'ベテランが5分～10分で終わるところを、新人は30分～1時間程度かかっていました。',
       'locator':'導入前の課題、2021年時点の事例'},
 'SAGAMI':{'verification':'indexed original case body read; live web open timed out, urllib HTTP403, ordinary public Chrome timed out',
       'passage':'各自1時間ほど／4人で合計約4時間',
       'locator':'導入してどんな効果がありましたか。掲載本文の索引確認で、完全HTML取得済みとはしない'},
 'SUPERPHARMACY':{'verification':'live primary customer page read via web tool; direct urllib HTTP403',
       'passage':'up to one hour every day manually planning routes',
       'locator':'The Challenge'},
 'WINWASTE':{'verification':'live primary customer page read via web tool; direct urllib HTTP403',
       'passage':'Daily Route Planning Time | 45–60 minutes',
       'locator':'Performance Metrics'},
}

records=[]
def add(key,client,category,low,high,original,unit,experience,workload,comment):
 s=sources[key]
 records.append(dict(id=key,client=client,category=category,before_s_low=low,before_s_high=high,
   original_before=original,unit=unit,experience=experience,workload=workload,comment=comment,
   source_url=s['url'],source_sha256=s.get('sha256',''),local_original=s.get('path',''),
   verification=web_passages[key]['verification'] if key in web_passages else 'retained primary original',
   counts_as_separate_case=category not in ['general_vendor_claim','duplicate'],
   independently_measured_by_us=False))

add('JP','日本郵便','anchor',None,None,'熟練者5〜10分、新人30〜60分',
 '各ドライバーのルート作成、1便/1日の区別は未取得','経験区分を明記',
 '配送先数・車両数・日別人数未取得。22郵便局は22独立時間測定ではない',
 '値の採用元。熟練と新人の2条件は1事例として数える')
add('ZENRIN','関東の燃料卸売業者（匿名A社）','paired_experience_match',None,None,
 '熟練者約10分、新人/代行者30〜60分','各配送員の1日分のルート作成',
 '経験区分を明記','部門20台、熟練者20〜30件/日、新人等10〜15件/日',
 '日本郵便とは別現場・別提供者。匿名顧客で独立測定ログなし。件数が異なり経験効果だけを識別できない')
add('TOSA','土佐ガス','individual_duration_support',1800,3600,'平均30分〜1時間/日',
 '配送員が行う訪問先選定と訪問順作成','熟練/新人別の時間は未公表',
 '全7名の配送員が導入後利用。1週間の指図リストから日次計画を選定',
 '30〜60分は概要記載。山崎氏の個別談は従来約30分。導入後の5〜10分は見直し時間で、人手熟練者の根拠にしない')
add('SAGAMI','相模石油','individual_duration_support',3600,3600,'各自約1時間、4人合計約4人時',
 '帰社後に各配送員が翌日の配送を検討','経験別の時間は未公表',
 '4人の計画時間の合計を公表。日次の全経過時間と区別',
 '60分程度という補助整合。ライブ本文取得不可のため索引掲載本文を補助として使用。4時間を経過Tにしない')
add('COMPACT','Compact Gaz（ポーランド）','aggregate_duration_support',1800,2400,'30〜40分',
 '複数車両のルート計画全体','専門担当に依存、熟練/新人別時間なし',
 '6台、最大60地点/日。従来は表計算とGoogle Mapsへ転記',
 '日本郵便の各担当者単位とは異なる。30分の計画可能窓と実績30〜40分を混同しない')
add('SUPERPHARMACY','SuperPharmacy（豪州）','aggregate_duration_support',None,3600,'毎日最大1時間',
 '配送チームの処方薬ルート作成','経験別時間なし','地点数・車両数・計画担当人数未取得',
 '上限表現であり平均60分/下限30分とはしない。導入後10分を熟練者の手作業時間にしない')
add('WINWASTE','Win Waste Solutions（米国）','aggregate_duration_support',2700,3600,'45〜60分/日',
 '管理者による5人分のルート構成','経験別時間なし',
 'Tracyが地域別グループ化/負荷調整、現場員5人。業務全体で200〜300地点/日との記述',
 '現場員5人は計画者5人ではない。地点数の改善前後個票なし。日本郵便の1担当者へ直接換算不可')
add('SAINTCARE','セントケアグループ','adjacent_task_duration_support',1800,3600,'従来30分〜1時間',
 '在宅介護の訪問ルート作成','職員熟練度はルート制約であり、計画者の経験別所要時間ではない',
 '訪問先/職員の相性・負担平準化を考慮。規模/計画者人数未取得',
 '2014-11-13の当事者公式発表p.1。業種が異なっても数十分の計画工程を補助する')
add('TRIVALUE','TriValue／CTC','scope_counterexample',10800,10800,'熟練担当者の手組み3時間',
 '複数車両の実配送計画策定','熟練者と明記',
 '2025-04-02〜05の実証、92宅配件数・10台、さいたまセンター',
 '熟練者なら計画全体が常に5〜10分という一般化への反例。日本郵便の個別観測自体への反証ではない')
add('MAPBOOKING','TetraSoft一般説明','general_vendor_claim',600,600,'経験ある計画者は40地点/4ルートを約10分で作れるとの説明',
 '一般的な宣伝上の例示','experienced plannerとの説明',
 '40地点/4ルートという例。実測対象・測定者・日時なし',
 '数値の桁は近いが観測事例として数えない')
for key,client,origin in [('JP_REPRINT','日本郵便事例の二次要約','JP'),
                          ('SUPERPHARMACY_REUSE','Locate2u別記事での同一事例再利用','SUPERPHARMACY'),
                          ('WINWASTE_REUSE','Upper別記事での同一事例再利用','WINWASTE')]:
 add(key,client,'duplicate',None,None,'同一事例の再掲','原事例と同じ','原事例と同じ','独立した新しい観測ではない',
     '重複元='+origin+'。原URL掲載本文の取得状態はSOURCE_MANIFESTに保存。検索ヒットを独立件数へ加算しない')

def mdtable(headers,body):
 return '|'+ '|'.join(headers)+'|\n|'+'|'.join('---' for _ in headers)+'|\n'+''.join('|'+ '|'.join(str(v).replace('|','/') for v in row)+'|\n' for row in body)

def main():
 with (ROOT/'EVIDENCE.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 (ROOT/'EVIDENCE.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'WEB_VERIFIED_PASSAGES.json').write_text(json.dumps(web_passages,ensure_ascii=False,indent=2)+'\n')
 counts={'anchor_cases':1,'additional_paired_experience_cases':1,
   'additional_individual_duration_cases':2,'additional_aggregate_duration_cases':3,
   'additional_adjacent_task_cases':1,'additional_supporting_case_reports':7,
   'scope_counterexample_cases':1,'non_observational_vendor_examples':1,'duplicate_pages_not_counted':3,
   'directly_read_additional_supporting_primary_pages':6,
   'indexed_original_body_only_additional_cases':1,
   'interpretation':'Distinct client reports, not independent instrumented datasets; same supplier may publish several cases.'}
 config={
  'schema_version':'1.0','reference_version':'A-human-route-time-reference-v1.0','adopted_date':'2026-11-13',
  'kind':'external_literature_reference_only',
  'adoption_status':'CONDITIONAL GO',
  'source_anchor':{'client':'Japan Post','publisher':'OPTIMIND/Loogia','case_as_of_year':2021,'url':sources['JP']['url']},
  'metric':'T_human_route_creation','unit':'seconds per human route-creation episode',
  'experience_conditions':{'experienced':{'min_s':300,'max_s':600},'novice':{'min_s':1800,'max_s':3600}},
  'distribution':None,'default_midpoint':None,
  'mapping':{'stops_per_episode':None,'trips_per_episode':None,'episodes_per_vehicle_day':None,
             'planning_workers':None,'full_A_T_s':None},
  'allowed_use':['source-labelled external reference','experience-dependent route-creation sensitivity after episode/workload mapping is explicitly fixed'],
  'not_established':['Sagawa measured time','S1 full-plan human wall time','time per delivery stop','human ability to reproduce A1-A3 output plans'],
  'automatically_used_in_existing_experiments':False,
  'replaces_a_rule_baseline_v1_coefficients':False,
  'scopes_not_included_or_unconfirmed':['shared input preparation','joint vehicle/trip allocation','berth coordination','global feasibility checking and correction'],
  'do_not_map_experience_to_A1_A2_A3':True,
  'corroboration_counts':counts,
  'evidence_csv':'docs/research/toc_delivery_a/A_JAPAN_POST_T_CORROBORATION_EVIDENCE.csv',
 }
 CONFIG.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'ADOPTED_REFERENCE.json').write_bytes(CONFIG.read_bytes())
 table=mdtable(['別現場の原資料','導入前の人手時間','日本郵便との対応','注意点'],[
  [f"[{r['client']}]({r['source_url']})",r['original_before'],r['unit'],r['comment']]
  for r in records if r['category'] in ['paired_experience_match','individual_duration_support','aggregate_duration_support','adjacent_task_duration_support']])
 report=f'''# 日本郵便の人手ルート作成時間：他事例との整合と採用判断

2026-11-13。日本郵便/Loogiaの改善前の熟練者5〜10分・新人30〜60分を軸に、業種を限定せず再調査した。取得結果に合わせて「多数」の件数閾値を作らず、何が繰り返し確認できたかと測定範囲を区別する。

**判断：日本郵便の値を、人手による訪問順・ルート作成工程の文献参照値として条件付き採用する。全車両・全便・バースを含むA全体のTを5〜10分/30〜60分に確定する採用ではない。**

## 主資料の確認

[日本郵便/Loogiaの原資料]({sources['JP']['url']})は2021年時点の日本郵便担当者インタビュー。紙地図でのルート作成について熟練者5〜10分、新人30〜60分を記載。各ドライバーによる作成という業務説明があるが、配送先数、1便か1日か、全計画の同時開始終了、事前割当や検査の範囲は未公表。22郵便局の試行導入という記述を22件の独立した時間測定に数えない。

使うのは導入前の時間。導入後の新人10〜15分、配達業務時間差67分→17分、配送個数の増加は人手Tの数値根拠に混ぜない。論文の出典は「日本郵便担当者へのインタビューを掲載したLoogia導入事例」とし、日本郵便公式の原計測ログを取得したとは記述しない。

## 別現場で確認できた情報

{table}

## 独立件数と証拠の強さ

- **同じ経験差まで近い別現場：1事例。** ゼンリンの燃料卸売顧客。熟練者約10分、新人等30〜60分。事業者は匿名であり、個票は未公開。
- **配送員個別の数十分〜1時間を補助する別現場：2事例。** 土佐ガス、相模石油。新人だけの時間とはしない。相模石油はライブ原HTMLを取得できず、一次ページの索引化された掲載本文による補助確認とする。
- **全体ルート構成など、単位は異なるが数十分〜1時間という時間帯を示す別現場：3事例。** Compact Gaz、SuperPharmacy、WinWaste。1担当車両あたりの時間へ割らない。
- **隣接する訪問計画：1事例。** セントケア。業種一致は必要条件にしないが、職員割当や時間制約など工程差を残す。

したがって、日本郵便以外の補助事例は**7件（うち原ページ/原PDFの直接閲覧6件、掲載本文の索引確認のみ1件）**。日本郵便を含む8現場の公表例であり、熟練者と新人の両範囲を同条件で検証した8実験ではない。Loogia掲載の日本郵便と相模石油は別顧客だが同じ掲載主体であり、情報発信の独立性も区別する。

日本郵便記事の転載・要約、SuperPharmacyの他記事/地域版、WinWasteの他記事は、各々同じ原事例へ束ねて追加観測として数えない。TetraSoftの40地点/4ルートを約10分で計画するという説明は、実測対象のない一般宣伝例であり件数に含めない。供給者の事例紹介が中心で、無作為抽出や独立計測データではない。件数が増えても統計的な信頼区間・分布・普遍的標準時間にはならない。

## 反対の情報と適用限界

[CTC/TriValueの一次発表]({sources['TRIVALUE']['url']})には、2025年4月2〜5日のさいたまセンター実証で、92宅配件数・10台の配送計画について熟練担当者が手組みで3時間との記述がある。このため、熟練者なら全計画が常に5〜10分で完成するという一般化は支持されない。日本郵便の各担当者の作業時間自体を否定する情報ではなく、作業範囲の差を示す。

土佐ガスの導入後5〜10分は自動計画の再検討であり、熟練者によるゼロからの人手5〜10分の追加観測にしてはならない。SuperPharmacy/WinWasteの自動化後10分も同様。相模石油の4人合計約4時間は人時であって4時間の経過時間ではない。WinWasteの現場員5人を計画者5人としない。Compact Gazの6台/60地点は日本郵便の未取得配送先数を補完する値ではない。

## 採用した参照仕様

|経験条件|文献参照時間|扱い|
|---|---|---|
|熟練者|300〜600秒|1回の人手ルート作成についての日本郵便の公表範囲|
|新人|1800〜3600秒|同上。別事例の数十分〜1時間が時間水準を補助|

版付き機械可読ファイル：`{CONFIG}`。分布・平均・中央値・標準偏差を新たに与えない。上下限を統計的保証範囲とも呼ばない。日本郵便の値を採用元として明示し、他社の時間を同じ日本郵便計画から得た数値に合成しない。Aは佐川の従来業務を参考にした規則推計モデルのままとし、Tの参照は日本郵便等の別出典であることを明示する。

設定の`kind=external_literature_reference_only`、`automatically_used_in_existing_experiments=false`、`full_A_T_s=null`により、既存のa_rule_baseline_v1係数とS1結果を置換しない。既存の未校正171分/人手感度の状態は変更しない。共通条件・凍結需要・アルゴリズム・A〜D実験CSVは変更しない。

## A全体のTへ接続する場合

元資料の作成単位を「便」「車両日」のどちらかへ無条件に対応付けない。まず研究仮定として配送先数、作成単位数、作成人数P、担当分担を固定する。各作業iの時間をtau_iとしたとき、ルート作成部分の経過時間は`max_p sum(tau_i assigned to p)`。総人時の単純和とは区別する。

共通準備・全体割当・バース調整・全体検査が逐次なら、上記の前後に各工程時間を加える。重複する工程なら依存関係に基づく完了時刻で計算する。未取得工程を0と仮定して全Tを完成扱いしない。A1/A2/A3と熟練/新人を勝手に対応付けず、全規則で共通の熟練度条件を用いる。プログラムが生成したA計画を人がこの時間で再現できることは別の検証事項。

## 最終判定

|判定対象|判断|
|---|---|
|日本郵便が人手ルート作成時間を公表していること|GO|
|別現場の数十分〜1時間という時間水準の補強|GO（公表事例の範囲。相模石油は索引本文による補助）|
|熟練者5〜10分/新人30〜60分の工程参照としての採用|CONDITIONAL GO：採用した参照仕様を保存|
|同じ経験差が多数の独立実測で再現されたとの主張|HOLD：追加の経験対比は1事例に留まる|
|S1全車両・全便を含むAの確定人手T|HOLD：作成単位・人数・残余工程が未確定|

原URL・取得日時・SHA256・HTTP失敗は`{ROOT.relative_to(Path.cwd())}/SOURCE_MANIFEST.json`。Webで閲覧した抜粋は`WEB_VERIFIED_PASSAGES.json`に別記し、完全HTMLを保存したと偽らない。数値/分類は同EVIDENCE.csv/json。採用JSON、原資料対応、重複件数、単位、既存ファイル保全の検査はVALIDATION.json。

研究者による人手実験、事業者問い合わせ、非公開データ取得、有料API、commit/pushは実施していない。今回は参照値の調査・限定採用であり、A〜Dの数値比較を再実行した報告ではない。
'''
 doc=DOC/'A_JAPAN_POST_T_CORROBORATION.md';doc.write_text(report);(ROOT/doc.name).write_text(report)
 (DOC/'A_JAPAN_POST_T_CORROBORATION_EVIDENCE.csv').write_bytes((ROOT/'EVIDENCE.csv').read_bytes())
 print('records',len(records),'additional case reports',counts['additional_supporting_case_reports'],'reference',CONFIG)

if __name__=='__main__':main()
