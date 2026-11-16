from pptx.enum.dml import MSO_LINE_DASH_STYLE
S.background.fill.solid();S.background.fill.fore_color.rgb=rgb(WHITE)
future_items=[]

def node1(key,x,y,w,h,label,pt=21,planned=False):
    assert '\n' not in label and len(wrap(label,w-8,pt,True))==1,(key,label)
    sh=rect(x,y,w,h,WHITE,I);sh.name='node:'+key
    if planned:sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    th=pt*1.18*25.4/72+1
    tsh=txt(x+3,y+(h-th)/2,w-6,th,label,pt,I,True,'center','label:'+key)
    diagram_nodes.append(dict(key=key,text=label,text_shape_id=tsh.shape_id,shape_id=sh.shape_id,planned=planned))

def edge(source,target,x1,y1,x2,y2,kind):
    arrow(x1,y1,x2,y2,I)
    diagrams.setdefault(kind,[]).append(dict(source=source,target=target))

def bullet(y,s):
    sh=txt(18,y,558,7.7,s,17,I,tag='future:'+str(len(future_items)+1))
    p=sh.text_frame.paragraphs[0];pr=p._p.get_or_add_pPr()
    pr.set('marL','180000');pr.set('indent','-180000')
    bf=OxmlElement('a:buFont');bf.set('typeface',FONT);pr.append(bf)
    bu=OxmlElement('a:buChar');bu.set('char','•');pr.append(bu)
    blocks[-1]['kind']='bullet';future_items.append(s)

txt(18,8,558,22,TITLE,42,I,True)
txt(18,33,558,14,'大田区の単一拠点を想定した、量子計算による訪問順探索のケース分析',25,I)
txt(18,51,558,11,'佐野巧馬｜慶應義塾大学大学院メディアデザイン研究科 修士2年｜永山研究室・Q/est',18.5)
line(18,66,576,66,I,1)
txt(18,73,558,11,'研究の問い',22,I,True)
txt(18,87,558,13,'量子計算は、どのような過程を経て、配送計画と配送成果に影響するか。',23,I,True)
txt(18,104,558,10,'出発前に使える時間の中で、通常の計算機だけで解く古典手法を基準に、計画の質と配達完了時刻を比較する。',20)
txt(18,117,558,9,'ラストマイル配送は、拠点から届け先までの最終区間の配送である。本研究は車両への割当てと訪問順を対象とする。',18.5)

section(135,'01  配送モデルの構造と仮定｜検証済みは1台・1巡回である')
txt(18,156,277,11,'単一拠点から配送先を回って帰る',22,I,True)
node1('depot',30,205,58,20,'拠点',23)
node1('customer_a',139,170,68,20,'配送先A',22)
node1('customer_b',219,214,68,20,'配送先B',22)
node1('customer_c',139,258,68,20,'配送先C',22)
edge('depot','customer_a',88,211,139,185,'model')
edge('customer_a','customer_b',207,185,244,214,'model')
edge('customer_b','customer_c',244,234,207,263,'model')
edge('customer_c','depot',139,263,88,219,'model')
txt(18,283,277,9,'A～Cは配送先の模式例であり、実位置ではない。',17.5)
txt(18,294,277,10,'各配送先を1回訪問し、同じ拠点へ戻る。',20)
txt(18,307,277,10,'往復の総旅行時間 J が短い計画を探す。',20,I,True)
table(310,156,[82,184],[
    ['項目','1台の保存実験の設定 [1,2]'],
    ['対象地域・拠点','大田区・京浜トラックターミナルの\n位置を想定した単一拠点 [3]'],
    ['配送全体の先数','3／4／5／25／100／125先'],
    ['量子側が扱う先数','全体と同じ3～125先の訪問順全体\n小さな顧客群への分割ではない＊'],
    ['車両・巡回数','1台・1巡回・拠点発着'],
    ['車両容量','216荷物相当／台（重量kgではない）'],
    ['配達作業の時間','102秒／先（拠点は0秒）'],
    ['拠点へ戻る期限','モデル開始から9時間（32,400秒）'],
    ['顧客ごとの時間枠','設定なし（拠点へ戻る期限とは別）'],
    ['道路の移動時間','方向別の固定値。時間帯では変えない。'],
    ['古典対照の手法','訪問順の交換を繰り返し、\n行き詰まると順序を崩して再探索']
],[11,18,12,18,12,12,12,12,12,12,18],pt=17.5,tag='conditions')

section(330,'02  評価の流れ｜計画の比較と、採用後の配送成果を区別する')
txt(18,348,558,9,'古典基準と量子近似最適化アルゴリズム（QAOA）の候補を同じ入力で比較する。破線枠の採用・実行は今後の検証対象である。',18.5)
node1('input',18,372,86,17,'共通の入力',20)
node1('classical',132,359,121,17,'古典基準計画',21)
node1('quantum',132,389,121,17,'QAOA候補',21)
node1('compare',284,372,102,17,'同じ入力で比較',20)
node1('decision',414,372,162,17,'出発前に採用判断',21,True)
line(104,380.5,117,380.5,I,1.5);line(117,367.5,117,397.5,I,1.5)
edge('input','classical',117,367.5,132,367.5,'pipeline')
edge('input','quantum',117,397.5,132,397.5,'pipeline')
line(253,367.5,269,367.5,I,1.5);line(269,367.5,269,397.5,I,1.5);line(253,397.5,269,397.5,I,1.5)
edge('classical','compare',269,380.5,284,380.5,'pipeline')
diagrams['pipeline'].append(dict(source='quantum',target='compare'))
edge('compare','decision',386,380.5,414,380.5,'pipeline')
edge('decision','outcomes',495,389,495,401,'pipeline')
node1('outcomes',414,401,162,17,'配送成果を評価',21,True)
txt(18,409,382,9,'採用案：出発前に検証を終え、容量・帰庫条件を満たす、基準より短い候補を使う。',17.5)
txt(18,420,558,8.5,'候補が得られない、または旅行時間が基準以上の場合は古典基準を使う。成果は帰着・完了時刻・道路距離で評価する。',18)

section(435,'03  QAOAのアルゴリズム｜量子操作と古典計算による調整を組み合わせる')
txt(18,453,558,9,'量子近似最適化アルゴリズム（QAOA）は、旅行時間を反映する位相操作と混合操作を交互に行い、候補の確率分布を変える。[4–6]',18.5)
txt(133,465,210,8,'この2操作の組をp回繰り返す',16.5,I,True,align='center',tag='qaoa:layers')
line(128,475,350,475,I,.8);line(128,475,128,479,I,.8);line(350,475,350,479,I,.8)
qnodes=[('q_init',18,88,'初期状態を用意'),('q_cost',128,100,'費用位相操作'),('q_mix',250,100,'混合操作'),('q_eval',372,98,'評価値を計算'),('q_update',492,84,'調整係数を更新')]
for k,x,w,label in qnodes:node1(k,x,480,w,17,label,19.5)
for a,b in zip(qnodes,qnodes[1:]):edge(a[0],b[0],a[1]+a[2],488.5,b[1],488.5,'qaoa')
line(520,497,520,510,I,1.3);line(520,510,62,510,I,1.3);edge('q_update','q_init',62,510,62,497,'qaoa')
txt(210,500,160,8,'通常計算機で調整を継続',16.5,I,align='center',tag='qaoa:feedback')
line(550,497,550,520,I,1.3);line(550,520,79,520,I,1.3);edge('q_update','q_fixed',79,520,79,529,'qaoa')
txt(430,511,100,8,'調整完了',16.5,I,align='center',tag='qaoa:finish')
xs=[18,163.33,308.67,454]
for j,(x,label) in enumerate(zip(xs,['調整結果を固定','状態を再計算','候補を繰り返し抽出','制約確認と最良候補保存'])):
    node1(['q_fixed','q_restate','q_sample','q_best'][j],x,529,122,16,label,18.5)
    if j<3:edge(['q_fixed','q_restate','q_sample'][j],['q_restate','q_sample','q_best'][j],x+122,537,xs[j+1],537,'qaoa')
txt(18,548,558,9,'pは操作の組の回数（層数）である。本実験は通常計算機で模擬し、全訪問順型にはGrover型の混合操作を用いる。[1,2,6]',18)

section(562,'04  検証結果｜同じ配送入力に対する往復旅行時間の差を比べる')
txt(18,580,558,9,'Jは拠点往復の総旅行時間［秒］（作業・計算時間を除く）。ΔJ＝QAOA候補−古典対照。負が改善、正が悪化である。',18.5)
rows=[['設定','比較件数','古典 J 平均［秒］','QAOA J 平均［秒］','平均 ΔJ［秒］','平均絶対差［秒］']]
for label,key in [('位置交換型・6設定','位置交換など6設定'),('全訪問順型・p=2','GROVER_P2'),('全訪問順型・p=3','GROVER_P3')]:
    g=GROUPS[key]
    rows.append([label,f"{int(g['comparisons']):,}",f"{float(g['classical_mean_s']):,.3f}",f"{float(g['candidate_mean_s']):,.3f}",f"+{float(g['delta_mean_s']):,.3f}",f"{float(g['absolute_mean_s']):,.3f}"])
rows.append(['全8設定の混合',f"{DATA['comparisons']:,}",f"{DATA['classical_mean_s']:,.3f}",f"{DATA['candidate_mean_s']:,.3f}",f"+{DATA['delta_mean_s']:,.3f}",f"{DATA['absolute_mean_s']:,.3f}"])
table(18,592,[126,62,93,93,92,92],rows,[12,11,11,11,11],pt=18.5,tag='results',aligns=['left','right','right','right','right','right'])
txt(18,651,558,16,'比較入力は460件（3・4・5・25・100先は各78件、125先は70件）。8設定で計3,680件の係数調整を行った。\n同じ調整結果で8,192回の抽出から最良1件を保存する処理を10回反復した。保存候補は36,800件、全体行は8設定の混合平均である。[1,2]',17.5)
txt(18,670,558,8.5,'差の中央値0秒、最大+9,483.990秒。同等28,200・悪化8,600・改善0件。拠点へ戻る期限までの余裕は最小7,435.748秒である。',17.5)
txt(18,681,558,9,'＊交換範囲を制限する設定を含む。計算予算・初期解保持規則は未統一であり、速度優位・実配送の効果・顧客別期限内配達率は未検証である。',17.5)

section(695,'05  今後実施すること｜複数台への拡張と、出発までの同じ時間枠での検証')
table(18,714,[105,105,280,68],[
    ['全体規模（計画）','量子側の部分問題','主な確認事項','状況'],
    ['5台・500先','3～5先から（案）','車両割当て・訪問順・同じ時間枠での比較手順','未実施'],
    ['10台・1,000先','3～5先から（案）','割当てと訪問順の再現性・比較手順','未実施'],
    ['20台・2,000先','再現できた規模のみ','古典基準を評価し、量子比較の到達規模を記録する','未実施'],
    ['30台・3,000先','再現できた規模のみ','容量・帰庫期限への妥当性と比較可能な規模を確認する','未実施']
],[11,10,10,10,10],pt=16.5,tag='extension')
items=[
    'QAOAの探索範囲・初期状態・係数の調整方法を見直し、改善候補が得られる条件を調べる。',
    '前処理から採用判断までの時間枠と、最良計画を保持する規則を古典側とそろえる。',
    '5・10台で、配送先の車両への割当てと各車両の訪問順を確認し、改善方法を比較する。',
    '20・30台では古典基準を評価し、QAOAとの比較は再現できた部分問題の規模を報告する。',
    '30台・3,000先の妥当性を容量・帰庫条件で確認する。配備台数と同一便の稼働台数は区別する。[7]',
    '顧客ごとの配達期限を定め、未配達も含む期限内配達率と、各先の完了時刻を評価する。'
]
for j,s in enumerate(items):bullet(768+j*7.7,s)
line(18,816,576,816,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800.csv／B_INPUT_CONDITIONS_460.csv、条件整理・運用影響の報告書。',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv。',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内。[4] Farhi et al. (2014), arXiv:1411.4028.',
    '[5] Hadfield et al. (2019), Algorithms 12, 34. [6] Bärtschi & Eidenbenz (2020), QCE, 72–82. [7] ヤマト運輸（2023-10-02）八幡営業所公表資料。'
]
for j,s in enumerate(refs):txt(18,818+j*5.2,558,5.2,s,12,I,lh=1.0)
