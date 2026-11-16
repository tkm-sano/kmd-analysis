# White background, black text; every diagram node has one single-line label.
from pptx.enum.dml import MSO_LINE_DASH_STYLE
S.background.fill.solid();S.background.fill.fore_color.rgb=rgb(WHITE)

def node1(key,x,y,w,h,label,pt=22,planned=False):
    assert '\n' not in label and len(wrap(label,w-8,pt,True))==1,(key,label)
    sh=rect(x,y,w,h,WHITE,I)
    sh.name='node:'+key
    if planned:sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    th=pt*1.18*25.4/72+1
    textshape=txt(x+3,y+(h-th)/2,w-6,th,label,pt,I,True,'center','label:'+key)
    diagram_nodes.append(dict(key=key,text=label,text_shape_id=textshape.shape_id,shape_id=sh.shape_id,planned=planned))

def edge(source,target,x1,y1,x2,y2,kind):
    arrow(x1,y1,x2,y2,I)
    diagrams.setdefault(kind,[]).append(dict(source=source,target=target))

txt(18,7,558,10,'KMD FORUM  |  研究ポスター',17,I,True)
txt(18,22,558,24,TITLE,46,I,True)
txt(18,49,558,15,'大田区の単一拠点を想定したケース分析',29,I)
txt(18,67,558,11,'佐野巧馬  ｜  Q/est',22,I)
line(18,82,576,82,I,1)
txt(18,90,558,11,'研究の問い',23,I,True)
txt(18,105,558,24,'出発までに使える時間の中で、量子計算から得た候補を取り入れると、\n既存の古典手法と比べて配送計画の質や配送成果はどの程度変わるか。',24,I,True)
txt(18,135,558,11,'対象は配送先の車両割当てと訪問順である。出発前に、容量と帰庫期限を満たす計画を得る条件を検討する。',21)

section(154,'01  モデルの構造と仮定｜検証した1台の配送計画')
txt(18,176,277,11,'単一拠点・1台・1巡回の模式図',22,I,True)
node1('depot',30,225,58,20,'拠点',23)
node1('customer_a',139,190,68,20,'配送先A',22)
node1('customer_b',219,234,68,20,'配送先B',22)
node1('customer_c',139,278,68,20,'配送先C',22)
edge('depot','customer_a',88,231,139,205,'model')
edge('customer_a','customer_b',207,205,244,234,'model')
edge('customer_b','customer_c',244,254,207,283,'model')
edge('customer_c','depot',139,283,88,239,'model')
txt(18,303,277,9,'A～Cは配送先を模式的に示した例である。',17.5)
txt(18,315,277,11,'道路は方向ごとの旅行時間で表す。',21)
txt(18,328,277,11,'J：拠点往復の総旅行時間を最小化する。',21,I,True)
txt(18,341,277,10,'各配送先を1回訪問し、同じ拠点へ戻る。',20)

table(310,176,[82,184],[
    ['項目','時間枠なしB系列の仮定・設定 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]'],
    ['配送全体の先数','3／4／5／25／100／125先'],
    ['量子側へ渡す先数','全体と同じ3～125先の訪問順全体\n小ブロックへの切出しではない＊'],
    ['車両・巡回','1台・1巡回・拠点発着'],
    ['車両容量','216荷物相当／台（重量kgではない）'],
    ['配送先の作業時間','102秒／先（拠点は0秒）'],
    ['帰庫期限','モデル開始から9時間（32,400秒）'],
    ['顧客別時間枠','なし（共通の帰庫上限とは別である）'],
    ['道路旅行時間','時間帯によらない固定値である'],
    ['古典対照','訪問順の交換を繰り返し、\n行き詰まると順序を崩して再探索']
],[11,19,13,19,13,13,13,13,13,13,19],pt=18,tag='conditions')

section(359,'02  評価パイプライン｜共通入力から候補比較・採用判断・成果評価へ')
txt(18,378,558,9,'入力は拠点・配送先・需要・道路旅行時間、配送成果は帰庫・各先の完了時刻・道路距離である。',19.5)
node1('input',18,414,86,18,'共通の配送入力',20)
node1('classical',139,390,132,18,'古典基準計画',22)
node1('quantum',139,442,132,18,'量子候補の生成',22)
node1('compare',313,414,111,18,'同一条件で比較',21)
node1('decision',452,414,124,18,'出発前の採用判断',21,True)
line(104,423,120,423,I,1.5);line(120,399,120,451,I,1.5)
edge('input','classical',120,399,139,399,'pipeline')
edge('input','quantum',120,451,139,451,'pipeline')
line(271,399,292,399,I,1.5);line(292,399,292,451,I,1.5);line(271,451,292,451,I,1.5)
edge('classical','compare',292,423,313,423,'pipeline')
diagrams['pipeline'].append(dict(source='quantum',target='compare'))
edge('compare','decision',424,423,452,423,'pipeline')
node1('adopt_candidate',365,463,94,18,'候補を採用',20,True)
node1('fallback',482,463,94,18,'基準計画を採用',20,True)
edge('decision','adopt_candidate',487,432,412,463,'pipeline')
edge('decision','fallback',543,432,529,463,'pipeline')
txt(418,438,35,9,'成立',17,I,False,'center','branch:pass')
txt(546,446,30,9,'不成立',17,I,False,'center','branch:fail')
node1('outcome',401,496,175,18,'配送成果の評価',22,True)
edge('adopt_candidate','outcome',412,481,412,496,'pipeline')
edge('fallback','outcome',529,481,529,496,'pipeline')

txt(18,518,558,8.5,'取得時間は前処理・候補生成・検証・選択の合計である。破線の枠は採用・実行の検証計画を表す。',18)
txt(18,529,558,9,'量子近似最適化（QAOA）は候補の得やすさを調整する手法である。本結果は通常計算機上での模擬計算である。[1,2]',19)
txt(18,540,558,9,'採用規則（案）：古典基準より短く、出発前に検証が完了し、容量・帰庫期限を満たす候補を採用する。',19)

section(557,'03  検証済みの主結果｜同じ入力の古典対照と量子候補を比較する')
txt(18,575,558,9,'Jは往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝量子候補−古典対照。負が改善、正が悪化である。',19.5)
rows=[['設定','比較件数','古典 J 平均［秒］','候補 J 平均［秒］','平均 ΔJ［秒］','平均絶対差［秒］']]
for label,key in [('位置交換など6設定','位置交換など6設定'),('全訪問順型・2層','GROVER_P2'),('全訪問順型・3層','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,587,[126,62,93,93,92,92],rows,[13,12,12,12,12],pt=19.5,tag='results',aligns=['left','right','right','right','right','right'])
txt(18,651,558,16,'460入力（3・4・5・25・100先が各78、125先が70）×8設定＝3,680件の調整。全体行は8設定の混合平均である。\n各調整済み状態から8,192回抽出×10反復し、反復ごとの最良候補36,800件を保存した。10反復は状態を共用する。[1,2]',18)
txt(18,670,558,23,'全差の中央値0秒、最大+9,483.990秒。同等28,200件・悪化8,600件・改善0件。帰庫余裕は最小7,435.748秒である。\n＊交換範囲を制限する設定を含む。計算予算・初期解の保持規則が異なり、時間優位は未判定である。\n実採用効果・顧客別期限内配達率は未検証、道路距離は主比較で未集計である。実営業所の配置・運用の再現は未確認である。',17.5)

section(695,'04  複数台への拡張計画｜全体割当てと局所改善を分ける')
for j,(x,label) in enumerate(zip([18,162.33,306.67,451],['古典手法で全体割当て','局所の改善方法を比較','全体の制約を再検証','共通締切で採用判断'])):
    node1('multi_'+str(j),x,714,125,15,label,18.5,True)
    if j<3:edge('multi_'+str(j),'multi_'+str(j+1),x+126,721.5,[18,162.33,306.67,451][j+1]-1,721.5,'multi')
table(18,733,[105,104,271,78],[
    ['全体の車両数・先数','量子側の部分問題','検証すること','実施状況'],
    ['5台・500先','3～5先から（案）','車両割当て・各車両の訪問順・同一時間予算の比較手順','計画・未実施'],
    ['10台・1,000先','3～5先から（案）','割当てと訪問順の再現性、同一時間予算の比較手順','計画・未実施'],
    ['20台・2,000先','再現できた規模のみ','古典基準の品質・取得時間を評価し、量子比較の到達規模を記録','計画・未実施'],
    ['30台・3,000先','再現できた規模のみ','容量・帰庫期限への妥当性と古典基準を評価し、量子比較範囲を報告','計画・未実施']
],[12,12,12,12,12],pt=17.5,tag='extension')
txt(18,796,558,15,'最大30台・3,000先は妥当性を確認する計画値である。配備32台の国内例 [4] は規模の参考であり、同一便の稼働台数の根拠ではない。\n各台100先の作業は2時間50分、移動余裕6時間10分（待機なしの概算）。全工程を同じ時間枠で比較する。日間個数は配送先数に換算しない。',16.5)
line(18,814,576,814,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800／B_INPUT_CONDITIONS_460、PATHWAY1_CONDITIONS・OPERATIONAL_IMPACT',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv（再集計・照合）',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内：j-m-t.co.jp/terminal/keihin.html',
    '[4] ヤマト運輸（2023-10-02）八幡営業所公表資料：yamato-hd.co.jp/news/2023/newsrelease_20231002_3.html'
]
for j,s in enumerate(refs):txt(18,816+j*5.7,558,5.7,s,13,I,lh=1.05)
