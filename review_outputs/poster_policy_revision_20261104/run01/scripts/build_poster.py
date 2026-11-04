"""Native editable A1; all numeric values traceable to audit_inputs.py."""
import json
from pathlib import Path
from poster_primitives import Poster, BLUE, ORANGE, NAVY, INK, MUTED, PALE
from content import TITLE, PURPOSE, RQ, REFS
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'evidence/AUDIT_RESULTS.json').read_text())
p=Poster()
def tx(x,y,w,s,pt=24,b=False,c=INK,h=None,tag=''):
    return p.text(x,y,w,s,pt,b,c,max_h=h,tag=tag)
def sec(x,y,s,c): p.section(x,y,275,s,c)
# Title deliberately split at semantic boundaries.
tx(15,10,564,'量子計算がEV配送システムに寄与し得る条件：',48,True,NAVY,h=25)
tx(15,36,564,'配送計画と電池材料評価を介した影響経路の検討',40,True,NAVY,h=23)
tx(15,63,564,'佐野巧馬　｜　Q/est',27,c=MUTED,h=14)
p.line(15,82,579,82,NAVY,1.5)
tx(15,88,564,'研究上の問い　量子計算は、配送計画と電池材料評価を通じて、\nどのような条件下でEV配送システムに寄与し得るのか。',26,True,NAVY,h=27)
tx(15,117,564,'目的：保存された定量結果と一次文献から、技術的能力が運用・設計上の成果へ結び付く条件候補と制約を特定・整理する。',24,h=25)
tx(15,144,564,'分析視点：技術・関与主体・適用判断の区別 [4]。将来構成の予見と、評価尺度・設計前提の省察 [3]。',19,c=MUTED,h=18)
sec(15,170,'1　配送計画：探索範囲と解の採用',BLUE)
sec(304,170,'2　電池材料：設計と電力量への伝達',ORANGE)
tx(15,192,275,'方法｜保存されたCPU数値評価の照合',25,True,BLUE,h=14)
tx(15,209,275,'3・4・5・25・100・125配送先、計460問題例。1問題例は1組の配送先・移動時間行列である。時間窓は設けない。',23,h=33)
tx(15,244,275,'限定位置交換5条件、隣接交換1条件、Grover-mixer QAOA [1] 2条件（層数2・3、全順列の理想状態）。各10反復、各8192ショット後の保存最良解を照合した。',23,h=43)
tx(15,286,275,'比較：同一入力の古典初期解・同じ探索範囲の最小値・厳密参照値（407例、53例は未保存）。実機実行ではない。',21,h=30)
tx(304,192,275,'方法｜文献入力と条件付きモデルの照合',25,True,ORANGE,h=14)
tx(304,209,275,'Chenらの古典DFT・電極実験 [5] を参照した。100サイクル後の比容量÷容量保持率から、LP 171.9、S-200 196.0 Ah/kgを逆算した。',23,h=43)
tx(304,253,275,'容量20 kWh・平均電圧3.5 Vを固定。電極塗工層＋固定34 kgの質量推計を用いた。完成パックの実測ではない。',23,h=33)
tx(304,289,275,'同一の旧460保存速度軌跡でDC差を比較した。現行の配送計画460問題例とは別系列である。',21,h=28)
sec(15,324,'結果｜GM-QAOAと古典初期解',BLUE)
sec(304,324,'結果｜LPを分母とする削減率',ORANGE)
# table at readable 23pt; range expresses layers without treating depth contrast as contribution
xs=[15,78,133]; ws=[63,55,157]
for x,w,s in zip(xs,ws,['配送先数','例数','平均総移動時間差［秒］']): p.cell(x,345,w,15,s,20,True,PALE)
for i,row in enumerate(a['planning']['scale_results']):
    lo,hi=row['delta_min_s'],row['delta_max_s']
    def fmt(v):return ('−' if v<0 else '+' if v>0 else '')+f'{abs(v):,.2f}'
    val=fmt(lo) if abs(lo-hi)<.005 else fmt(lo)+'〜'+fmt(hi)
    for x,w,s in zip(xs,ws,[str(row['delivery_stops']),str(row['physical_inputs']),val]):p.cell(x,360+i*14,w,14,s,22,fill='#F6F9FB' if i%2==0 else None)
tx(15,447,275,'差＝保存解−古典初期解。負が改善である。入力内10反復を平均し、入力間を等重みで平均した。範囲は層数2・3の値である。',19,c=MUTED,h=28)
tx(15,477,275,'改善は4・5配送先の計7問題例で観測された。限定位置交換の2300学習記録では、同じ探索範囲の最小値が初期解と一致した。隣接交換の3点角度探索は全入力で初期解を選択した。',22,h=41)
tx(15,521,275,'CPU工程時間の例：25配送先・層数3の平均は学習0.888秒、最終検証168.745秒である。全工程時間・実機資源は未確認である。',19,c=MUTED,h=28)
# bars same scale, exact denominators and raw endpoints
rates=[5.666712059409347,.47790634461422765,.412579010060621]
labels=['電池質量','走行時総質量','DC消費電力量']
subs=['96.15 → 90.70 kg','1140.03 → 1134.59 kg','下側転がり係数・合計比']
for i,(rate,label,sub) in enumerate(zip(rates,labels,subs)):
    y=347+i*30
    tx(304,y,135,label,24,True,ORANGE,h=13)
    tx(304,y+13,136,sub,17,c=MUTED,h=11)
    p.rect(448,y+2,88*rate/6,9,ORANGE)
    tx(539,y-1,40,["5.67%","0.478%","0.413%"][i],24,True,ORANGE,h=13)
p.line(448,438,536,438,MUTED)
for z in [0,2,4,6]:
    x=448+88*z/6;p.line(x,438,x,441,MUTED);tx(x-4,442,14,str(z),17,c=MUTED,h=9)
tx(477,454,59,'削減率［%］',17,c=MUTED,h=10)
tx(304,469,275,'分母は各LP値である。固定条件：運転者55 kg、積載0、平坦・同一速度。回生・補機・荷重変化を除外した。DCは保存区間のみで、終端未保存分を補完していない。',20,h=36)
tx(304,508,275,'部材別183設計は完成パック質量が全て未確定（182保留、1設計は対向面積不適合）である。既知部材の軽量化 b は固定面積5.98／固定塗工量9.72 kgであるが、未確定部材の S−LP差 δ を加えた軽量化量は b−δ である。',20,h=42)
sec(15,561,'考察｜改善解の存在と全体への統合',BLUE)
sec(304,561,'考察｜材料情報の有用性と設計採用',ORANGE)
tx(15,582,275,'確認した制約：限定位置交換の範囲には改善解が存在しない。この範囲の厳密改善は、探索器の性能向上だけでは生じない。',23,h=34)
tx(15,619,275,'条件候補：改善解を含む探索範囲・部分問題を選び、古典側で実行可能性を検証して全体計画へ統合し、許容計算時間内に取得する構成である [6]。',23,h=43)
tx(304,582,275,'確認した制約：今回の計算では材料入力の変化は車両全体・DCで小さくなる。未知部材差 δ＝b は、この質量収支モデル内で軽量化が消失する境界である。',23,h=34)
tx(304,619,275,'条件候補：量子材料評価 [2,7] が選択に有用な情報を与え、試験とセル・パック設計に採用されることである。評価精度と、出力・寿命・安全性の成立は別の検証を要する。',23,h=43)
# shared framework: explicitly epistemic, not completed causal experiment
tx(15,675,564,'共通の検討枠組み｜技術的能力・適用判断・成果の接続',27,True,NAVY,h=15)
for x,w,title,body in [(15,169,'技術的能力','探索・材料評価'),(212,169,'運用・設計への適用判断','古典側の検証・電池試験'),(410,169,'システム上の成果','解品質・取得時刻／質量・DC')]:
    p.rect(x,695,w,28,PALE)
    tx(x+3,697,w-6,title,23,True,NAVY,h=13)
    tx(x+3,711,w-6,body,19,c=MUTED,h=11)
p.arrow(187,709,208,709);p.arrow(385,709,406,709)
tx(15,730,564,'許容計算時間は入力更新から採用判断までの時間枠であり、本研究では未測定である。問題分割・動的再計画・全体統合は未検証である。',20,h=19)
tx(15,750,564,'確認範囲：量子優位性、量子計算による材料改善、実車性能の改善を実証した結果ではない。二経路を通じた全接続の実証は今後の課題である。',20,h=19)
p.line(15,776,579,776)
refs=[
 '[1] Bärtschi & Eidenbenz (2020). IEEE QCE, 72–82. Grover mixers.',
 '[2] Delgado et al. (2022). Phys. Rev. A 106, 032428. 量子電池材料評価.',
 '[3] Stilgoe et al. (2013). Res. Policy 42, 1568–1580. 予見・省察.',
 '[4] Geels (2004). Res. Policy 33, 897–920. 社会技術システム.',
 '[5] Chen et al. (2020). Nat. Commun. 11, 3411. 材料参照値.',
 '[6] Holliday et al. (2026). Quantum Mach. Intell. 8, 37. 別方式のハイブリッド例.',
 '[7] Shokrian Zini et al. (2023). Quantum 7, 1049. 材料計算資源.'
]
for i,s in enumerate(refs):
    x=15 if i<4 else 304;y=782+(i if i<4 else i-4)*12
    tx(x,y,275,s,16,c=MUTED,h=12)
tx(304,819,275,'詳細な根拠・モデル条件・未検証事項は別添レビュー報告に示す。',16,c=MUTED,h=12)
p.save(TITLE+'\n'+PURPOSE+'\n'+RQ+'\n\n'+'\n'.join(f"[{v['n']}] {v['author']} ({v['year']}). {v['title']}. {v['journal']}. DOI: {v['doi']}\n利用範囲：{v['use']}" for v in REFS))
print('Built editable poster:',R/'poster.pptx')
