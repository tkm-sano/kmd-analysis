# Main poster layout; combined with the existing editable native primitives.
rect(0,0,594,80,N);rect(0,78,594,2,B)
txt(18,7,558,10,'KMD FORUM  |  研究ポスター',17,'#D1E1EA',True)
txt(18,21,558,24,TITLE,46,WHITE,True)
txt(18,47,558,15,'大田区の単一拠点を想定したケース分析',29,WHITE)
txt(18,65,558,12,'佐野巧馬  ｜  Q/est',22,'#D1E1EA')

section(90,'01  出発前に、使える配送計画を得る')
txt(18,109,558,20,'限られた出発前の時間で、容量と帰庫期限を満たす配送計画を用意する必要がある。\n対象は配送先の車両割当てと訪問順である。量子計算の寄与を、探索・取得・採用・実行の接続から検討する。',21.5)
rect(18,132,558,39,PALE);rect(18,132,2,39,B)
txt(23,135,548,9,'研究の問い',17,B,True)
txt(23,146,548,23,'出発までに使える時間の中で、量子計算から得た候補を取り入れると、\n既存の古典手法と比べて配送計画の質や配送成果はどの程度変わるか。',24,N,True)

section(183,'02  寄与の構造：候補の質・取得時間・採用判断を経て、配送成果につながる')
flow=[(18,100,'共通需要・道路旅行時間','入力：拠点・先・需要'),
      (128,100,'古典基準計画を作成','出力：割当て・訪問順'),
      (238,130,'同一入力の古典・量子比較','目的・制約／次は時間も統一'),
      (378,100,'出発前に採用判断','質・取得時間・制約'),
      (488,88,'配送成果を評価','完了時刻・道路距離')]
for j,(x,w,title,desc) in enumerate(flow):
    rect(x,203,w,24,PALE,RULE)
    txt(x+2,205,w-4,9,title,17.5,N,True)
    txt(x+2,216,w-4,8,desc,15.5,M)
    if j<4:
        arrow(x+w+1,215,flow[j+1][0]-1,215)
        edges.append(dict(source=j+1,target=j+2))

def node(x,y,w,h,title,body,color,body_y=None):
    rect(x,y,w,h,WHITE,color);rect(x,y,1.5,h,color)
    txt(x+4,y+3,w-8,12,title,21,color,True)
    if body:
        bh=len(wrap(body,w-8-.8,18.5))*18.5*1.18*25.4/72+1
        txt(x+4,body_y or y+18,w-8,bh,body,18.5)

node(18,244,139,96,'量子探索の設計','探索する訪問順の範囲\n初期解・調整方法・抽出回数',B)
line(22,293,153,293,RULE,.7)
txt(22,300,131,34,'改善解の存在と得やすさ、\n計算に要する時間の\n両方に関係する。',18.5,B)
node(183,244,110,41,'得られた候補の質','総旅行時間 J\n容量・帰庫条件の充足',B,body_y=261)
node(183,300,110,41,'使えるまでの時間','前処理・探索・検証の合計\n全工程の比較は未検証',A,body_y=317)
arrow(157,264,183,264,B)
arrow(157,320,183,320,A)
structural_edges.extend([dict(source='quantum_design',target='candidate_quality',status='saved_plan_comparison'),dict(source='quantum_design',target='acquisition_time',status='conditional_not_total_runtime_validation')])

rect(322,244,111,79,PLAN,A)
txt(326,247,103,10,'計画担当者・配車システム',17.5,A,True)
txt(326,259,103,12,'出発前の採用判断',22,A,True)
txt(326,275,103,27,'①古典基準より短い\n②締切内に検証が完了\n③容量・帰庫期限を満たす',18.5)
txt(326,308,103,10,'3条件を全て満たす（案）',17,A,True)
arrow(293,264,322,264,B)
line(293,320,307,320,A,1.5);line(307,320,307,296,A,1.5);arrow(307,296,322,296,A)
structural_edges.extend([dict(source='candidate_quality',target='adoption_gate',condition='strict_improvement_and_feasibility'),dict(source='acquisition_time',target='adoption_gate',condition='completed_before_common_departure_deadline')])

node(469,244,107,79,'配送の実行と成果','帰庫・各先の完了時刻\n走行距離\n実交通下の効果は未検証',A,body_y=268)
txt(437,250,28,9,'成立',16,A,True,align='center')
arrow(433,266,469,266,A)
txt(322,325,111,10,'一つでも不成立',16.5,A,align='center')
arrow(377.5,335,377.5,340,A)
rect(322,341,111,19,PALE,B)
txt(326,344,103,12,'古典基準計画を使う',19,B,True)
line(433,350,451,350,B,1.5);line(451,350,451,304,B,1.5);arrow(451,304,469,304,B)
structural_edges.extend([dict(source='adoption_gate',target='delivery_outcomes',condition='all_gates_pass'),dict(source='adoption_gate',target='classical_fallback',condition='any_gate_fails'),dict(source='classical_fallback',target='delivery_outcomes',condition='use_retained_baseline')])
rect(469,333,107,30,PLAN,RULE)
txt(473,335,99,8,'成果を左右する条件',16.5,A,True)
txt(473,345,99,16,'期限までの余裕・交通・\n配送先での作業時間',17.5)
arrow(522.5,333,522.5,323,A)
structural_edges.append(dict(source='deadline_slack_traffic_service',target='delivery_outcomes',status='conditions_not_empirical_effect_identification'))

for x,w,title,body in [
    (18,176,'A  探索範囲が寄与を制限する','指定した位置交換5設定の範囲には、\n古典対照より良い解が存在しない。\n他の範囲へは一般化しない。[1]'),
    (204,176,'B  取得と採用を分ける','旅行時間の短い候補でも、出発前に\n検証が完了しなければ採用できない。\nこれは次の実験の採用規則の案である。'),
    (390,186,'C  時間差と期限遵守を分ける','両側が帰庫期限を満たす場合は、\n旅行時間が異なっても\n帰庫期限の遵守は変わらない。[1]')]:
    rect(x,374,w,44,PALE,RULE)
    txt(x+3,377,w-6,10,title,19,B,True)
    txt(x+3,390,w-6,25,body,18)
txt(18,423,558,16,'青は保存計画での検証範囲、茶は採用・実行に向けた条件と次の検証を表す。矢印は検討する接続であり、実運用の因果効果を実証したものではない。量子近似最適化（QAOA）を通常計算機上で模擬した結果を用いる。',17.5,M)

section(444,'03  検証済み｜1台の条件と主結果  —  改善候補の取得と、成果への伝達を分ける',B)
table(18,466,[80,199,80,199],[
    ['条件','時間枠なしB系列の設定 [1,2]','条件','時間枠なしB系列の設定 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]','車両容量','216荷物相当／台（重量kgではない）'],
    ['配送全体の先数','3／4／5／25／100／125先','QAOAに渡した\n配送先数','全体と同じ3～125先の訪問順全体\n小ブロックへの切出しではない＊'],
    ['車両・巡回','1台・1巡回・拠点発着','作業時間','102秒／先（拠点は0秒）'],
    ['帰庫期限','モデル開始から9時間（32,400秒）','顧客別時間枠','なし（共通の帰庫上限とは別である）'],
    ['古典対照','訪問順の交換を繰り返し、\n行き詰まると順序を崩して再探索','道路旅行時間','時間帯によらない固定値である']
],[11,18,18,11,11,18],pt=18,tag='conditions')
txt(18,556,558,9,'主結果：Jは拠点往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝量子候補−古典対照。負が改善、正が悪化である。',19.5,N,True)
rows=[['設定','比較件数','古典 J 平均［秒］','候補 J 平均［秒］','平均 ΔJ［秒］','平均絶対差［秒］']]
for label,key in [('位置交換など6設定','位置交換など6設定'),('全訪問順型・2層','GROVER_P2'),('全訪問順型・3層','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,569,[126,62,93,93,92,92],rows,[13,12,12,12,12],pt=19.5,tag='results',aligns=['left','right','right','right','right','right'],bodycolors={4:'#E1EDF4'})
txt(18,633,558,9,'全候補の差の中央値0秒、最大+9,483.990秒。同等28,200件・悪化8,600件・改善0件。帰庫余裕は最小7,435.748秒である。[1]',18.5)
txt(18,644,558,16,'460入力（3・4・5・25・100先が各78、125先が70）×8設定＝3,680件の調整。全体行は8設定の混合平均である。\n各調整済み状態から8,192回抽出×10反復し、反復ごとの最良候補36,800件を保存した。10反復は状態を共用する。[1,2]',18)
txt(18,663,558,16,'＊交換範囲を制限する設定を含む。計算予算・初期解保持規則が異なり、全工程の時間優位は未判定である。顧客別期限内配達率は未評価、道路距離は主比較で未集計である。実営業所の車両配置・運用の再現は未確認である。',17.5,M)

section(684,'04  計画｜全体の割当てと、局所の改善を分けて比較する',A)
px=[18,162.33,306.67,451]
for j,(x,title) in enumerate(zip(px,['全体の割当て・基準訪問順\n古典手法で作る','同じ局所を改善\n古典候補／量子候補を比較','全体計画に戻して検証\n容量・帰庫・全先訪問','共通締切で採用判断\n両側で最良計画を保持'])):
    rect(x,701,125,16,PLAN,RULE)
    txt(x+2,702,121,14,title,16,A,True,align='center')
    if j<3:arrow(x+126,709,px[j+1]-1,709,A)
table(18,721,[105,104,271,78],[
    ['全体の車両数・先数','量子側の部分問題','検証すること','実施状況'],
    ['5台・500先','3～5先から（案）','車両割当て・各車両の訪問順・同一時間予算の比較手順','計画・未実施'],
    ['10台・1,000先','3～5先から（案）','割当てと訪問順の再現性、同一時間予算の比較手順','計画・未実施'],
    ['20台・2,000先','再現できた規模のみ','古典基準の品質・取得時間を評価し、量子比較の到達規模を記録','計画・未実施'],
    ['30台・3,000先','再現できた規模のみ','容量・帰庫期限への妥当性と古典基準を評価し、量子比較範囲を報告','計画・未実施']
],[13,13,13,13,13],pt=18,tag='extension',color=A,bodycolors={1:'#FBF7F3',2:PLAN,3:'#FBF7F3',4:PLAN})
txt(18,789,558,14,'最大30台・3,000先は妥当性を確認する計画値である。配備32台の国内例 [4] は規模の参考であり、同一便の稼働台数の根拠ではない。日間個数は配送先数に換算しない。',17,M)
txt(18,804,558,8,'各台100先なら作業2時間50分、移動余裕6時間10分（待機なしの概算）。各台216荷物相当と9時間帰庫を個別に検算する。全工程を同じ時間枠で比較する。[1]',16,M)
line(18,814,576,814,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800／B_INPUT_CONDITIONS_460、PATHWAY1_CONDITIONS・OPERATIONAL_IMPACT',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv（再集計・照合）',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内：j-m-t.co.jp/terminal/keihin.html',
    '[4] ヤマト運輸（2023-10-02）八幡営業所公表資料：yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html'
]
for j,s in enumerate(refs):
    sh=txt(18,816+j*5.7,558,5.7,s,13,M,lh=1.05)
    if j>=2:
        url=['https://www.j-m-t.co.jp/terminal/keihin.html','https://www.yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html'][j-2]
        for p in sh.text_frame.paragraphs:
            for r in p.runs:r.hyperlink.address=url
