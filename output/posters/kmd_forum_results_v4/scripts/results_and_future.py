section(562,'04  検証結果｜古典対照とQAOA候補の平均往復旅行時間を比べる')
txt(18,580,558,9,'Jは往復の総旅行時間［秒］（短いほど良い）。ΔJ＝QAOA候補−古典対照。負が改善、正が悪化である。[1,2]',18.5)

# Native PowerPoint shapes: paired bars, zero baseline, labels, counts and exact gaps.
rect(18,594,10,4.5,WHITE,I)
txt(32,591,81,10,'古典対照',19,I)
rect(119,594,10,4.5,'#BFBFBF',I)
txt(133,591,110,10,'QAOA候補',19,I)
txt(470,591,106,10,'平均差／平均絶対差［秒］',17.5,I,True)
x0,pw,maximum=151,278,3600
for tick in [0,1000,2000,3000,3600]:
    x=x0+pw*tick/maximum
    line(x,605,x,699,'#D8D8D8',.65)
    line(x,699,x,702,I,.7)
    txt(x-10,704,22,8,f'{tick:,}',16,I,align='center',tag='result:tick:'+str(tick))
line(x0,699,x0+pw,699,I,.9)
txt(444,704,26,8,'秒',16,I,align='right')
plot_rows=[]
for label,key in [('位置交換型・6設定','位置交換など6設定'),('全訪問順型・p=2','GROVER_P2'),('全訪問順型・p=3','GROVER_P3')]:
    g=GROUPS[key]
    plot_rows.append(dict(label=label,n=int(g['comparisons']),classical=float(g['classical_mean_s']),qaoa=float(g['candidate_mean_s']),delta=float(g['delta_mean_s']),absolute=float(g['absolute_mean_s'])))
plot_rows.append(dict(label='全8設定の混合',n=DATA['comparisons'],classical=DATA['classical_mean_s'],qaoa=DATA['candidate_mean_s'],delta=DATA['delta_mean_s'],absolute=DATA['absolute_mean_s']))
bar_records=[]
for j,r in enumerate(plot_rows):
    cy=614+24*j
    txt(18,cy-9,129,10,r['label'],19.5,I,True,tag='result:group:'+str(j))
    txt(18,cy+3,129,9,f"{r['n']:,}比較",18,I,tag='result:count:'+str(j))
    for k,dy,fill in [('classical',-7,WHITE),('qaoa',2,'#BFBFBF')]:
        length=pw*r[k]/maximum
        sh=rect(x0,cy+dy,length,4.5,fill,I);sh.name=f'result:bar:{j}:{k}'
        txt(x0+length+2,cy+dy-1.65,56.5,8.7,f"{r[k]:,.3f}",18,I,tag=f'result:value:{j}:{k}')
        bar_records.append(dict(shape_id=sh.shape_id,group=j,series=k,value_s=r[k],width_mm=length))
    txt(470,cy-4,106,10,f"+{r['delta']:,.3f} / {r['absolute']:,.3f}",17.5,I,tag='result:gap:'+str(j))

txt(18,717,558,9,'差の中央値0秒、最大+9,483.990秒。同等28,200・悪化8,600・改善0件。全ての差が0以上のため平均差と平均絶対差は等しい。',17)
txt(18,728,558,9,'460入力×8設定×10抽出反復＝36,800候補。全体行は8設定の混合である。計算予算・初期解保持規則は未統一であり、速度優位は未判定である。',16.5)
(O/'evidence/RESULT_FIGURE.json').write_text(json.dumps(dict(rows=plot_rows,bars=bar_records,axis_max_s=maximum,axis_width_mm=pw,axis_origin_mm=x0,unit='seconds',aggregation='fixed input cohort; paired classical and candidate means; equal setting weighting in overall row'),ensure_ascii=False,indent=2))

section(741,'05  今後実施すること｜運用条件の調査と、比較条件をそろえた再検証')
items=[
    '調査：実営業所の配備車両数と同一便の稼働台数、配送先数、出発前の計画作成時間を公開資料で調べる。',
    '調査：車両容量・配達作業時間・拠点へ戻る期限・顧客別の配達期限について、現行設定の根拠を確認する。',
    '再検証：両側で最良計画を保存し、同じ入力・時間枠で古典手法とQAOAを再比較して、全工程時間を測る。',
    '再検証：探索範囲・初期状態・層数・係数調整を一つずつ変え、改善候補の有無と取得頻度を確認する。',
    '再検証：複数台の割当てと訪問順を古典手法で作り、局所改善後も全配送先への訪問と容量・帰庫条件を確認する。',
    '再検証：顧客別期限と採用規則を明示し、完了時刻・未配達を含む期限内配達率・道路距離への影響を調べる。'
]
for j,s in enumerate(items):
    sh=txt(18,759+j*8.8,558,8.8,s,18.5,I,tag='future:'+str(j+1))
    p=sh.text_frame.paragraphs[0];pr=p._p.get_or_add_pPr()
    pr.set('marL','180000');pr.set('indent','-180000')
    bf=OxmlElement('a:buFont');bf.set('typeface',FONT);pr.append(bf)
    bu=OxmlElement('a:buChar');bu.set('char','•');pr.append(bu)
    blocks[-1]['kind']='bullet';future_items.append(s)
line(18,816,576,816,RULE,.8)
refs=[
    '[1] Step5（2026-11-05）：B_PLAN_GAPS_36800.csv／B_INPUT_CONDITIONS_460.csv、条件整理・運用影響の報告書。',
    '[2] no_sumo_full_analysis（2026-11-02）：B_PLAN_REFERENCES_36800.csv／B_RESOURCES_PER_FIT.csv。',
    '[3] 日本自動車ターミナル「京浜トラックターミナル」施設案内。[4] Farhi et al. (2014), arXiv:1411.4028.',
    '[5] Hadfield et al. (2019), Algorithms 12, 34. [6] Bärtschi & Eidenbenz (2020), QCE, 72–82.'
]
for j,s in enumerate(refs):txt(18,818+j*5.2,558,5.2,s,12,I,lh=1.0)
