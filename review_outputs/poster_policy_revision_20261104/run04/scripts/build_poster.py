"""A1 native text/shapes. Saved data only; extra percentage column is arithmetic."""
import json
from pathlib import Path
from poster_primitives import Poster,BLUE,ORANGE,NAVY,INK,MUTED,PALE,RULE
from content import TITLE,PURPOSE,RQ,REFS
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'evidence/EXTENDED_AUDIT.json').read_text());p=Poster()
def tx(x,y,w,s,pt=24,b=False,c=INK,h=None):return p.text(x,y,w,s,pt,b,c,max_h=h)
def sec(x,y,s,c):p.section(x,y,275,s,c)
def badge(x,y,w,s,fill):
 p.rect(x,y,w,13,fill);tx(x+3,y+1,w-6,s,21,True,NAVY,h=12)
def dashed(x1,y,x2):
 from pptx.enum.dml import MSO_LINE_DASH_STYLE
 p.pdf.setDash(4,3);p.arrow(x1,y,x2,y);p.pdf.setDash()
 for shape in list(p.slide.shapes)[-3:]:shape.line.dash_style=MSO_LINE_DASH_STYLE.DASH
# Research question and combined purpose/method avoid duplicate introductory paragraphs.
tx(15,10,564,'量子計算がEV配送システムに寄与し得る条件：',48,True,NAVY,h=25)
tx(15,36,564,'配送計画と電池材料評価を介した影響経路の検討',40,True,NAVY,h=23)
tx(15,63,564,'佐野巧馬　｜　Q/est',27,c=MUTED,h=14)
p.line(15,82,579,82,NAVY,1.5)
tx(15,89,564,'研究上の問い｜量子計算は、配送計画と電池材料評価を通じて、\nどのような条件下でEV配送システムに寄与し得るのか。',26,True,NAVY,h=25)
tx(15,116,564,'目的・方法｜保存定量結果の再集計・実装照合と文献検討により、寄与し得る条件候補と制約、未検証の接続を特定・整理する。',23,h=22)
badge(15,144,180,'A　保存結果で確認','#DFEBF4');badge(205,144,180,'B　条件付き推論','#F2E7DE');badge(395,144,184,'C　未検証','#F0F1F2')
sec(15,170,'配送計画｜探索範囲と解品質',BLUE);sec(304,170,'電池材料｜モデル内の伝達と相殺',ORANGE)
tx(15,192,275,'比較設計｜同一入力・同一目的関数',24,True,BLUE,h=13)
tx(15,208,275,'3・4・5・25・100・125配送先、460問題例（1例＝配送先・時間行列の1組）。全訪問・容量・帰庫制約、時間窓なしで評価した。',23,h=33)
for i,(left,right) in enumerate([
 ('限定位置交換：5設定','対称位置の交換で範囲を限定'),
 ('隣接交換：1設定','層数3・角度3点の限定探索'),
 ('GM-QAOA：2設定 [1]','層数2・3、理想一様の全順列状態')]):
 y=246+i*22
 p.rect(15,y,275,20,PALE if i%2==0 else '#F7F9FB')
 tx(18,y+2,105,left,20,True,BLUE,h=17);tx(126,y+2,161,right,20,h=17)
tx(15,316,275,'全てCPU数値評価である。各設定・入力の10測定反復で、8192標本中の保存最良解を評価した。実機の状態準備・性能は未実証である。',20,h=30)
tx(15,345,275,'GM-QAOA＝Grover-mixer QAOA [1]。',18,c=MUTED,h=10)
tx(304,192,275,'分析設計｜二つの質量モデルを分離',24,True,ORANGE,h=13)
p.rect(304,210,275,62,'#F7F0EB')
tx(308,213,267,'① 簡略推計：電極塗工層＋固定34 kg',23,True,ORANGE,h=14)
tx(308,230,267,'容量20 kWh・平均セル電圧3.5 Vで必要電極量を換算し、同一の旧460保存速度軌跡で走行DCを計算した。',23,h=36)
p.rect(304,280,275,66,'#FAF6F3')
tx(308,283,267,'② 部材別推計：183設計条件',23,True,ORANGE,h=14)
tx(308,300,267,'電極・集電体・セパレータ・電解液を計上し、固定面積／固定担持量と未知部材差を検討した。①とは別の質量モデルである。',22,h=38)
tx(308,333,267,'B　量子評価情報の設計利用が条件候補である [2,7]。',18,c=ORANGE,h=11)
sec(15,356,'A　GM-QAOAと古典初期解',BLUE);sec(304,356,'A　①簡略推計の変化率',ORANGE)
# Each range = two separately averaged settings, NOT confidence intervals.
xs=[15,55,91,215];ws=[40,36,124,75]
for x,w,s in zip(xs,ws,['配送先','例数','平均ΔJ［秒］','平均相対差［%］']):p.cell(x,377,w,16,s,19,True,PALE)
for i,n in enumerate([3,4,5,25,100,125]):
 rows=[v for v in a['normalized_scale_results'] if v['n']==n and v['config_id'].startswith('GROVER_')]
 def fmt(v,places):return ('−' if v<0 else '+' if v>0 else '')+f'{abs(v):,.{places}f}'
 def span(key,d):
  lo,hi=sorted(v[key] for v in rows);return fmt(lo,d) if round(lo,d)==round(hi,d) else fmt(lo,d)+'〜'+fmt(hi,d)
 vals=[str(n),str(rows[0]['inputs']),span('mean_delta_s',2),span('mean_relative_delta_percent',2 if n<=5 else 1)]
 for x,w,s in zip(xs,ws,vals):p.cell(x,393+i*14,w,14,s,21,fill='#F4F8FB' if i%2==0 else None)
tx(15,480,275,'Jはデポ発着のOD旅行時間和である。ΔJ＝保存最良値−古典初期値J₀（負が改善）。相対差＝100ΔJ/J₀。入力内10反復→入力間で平均した。幅は層数2・3であり、信頼区間ではない。',19,h=35)
p.rect(15,520,275,37,'#EAF1F7')
tx(19,522,267,'改善7例：4配送先1例・5配送先6例である。25配送先以上では平均悪化した。限定位置交換5設定は同範囲の最小値＝初期値であった。',22,h=34)
# Common scale makes attenuation visible. These are T08 model rates only.
for i,(label,sub,val,out) in enumerate([
 ('推計電池質量','96.15 → 90.70 kg',5.666712059409347,'5.67%'),
 ('走行時総質量','1140.03 → 1134.59 kg',.47790634461422765,'0.478%'),
 ('走行DC電力量','460軌跡合計・下側転がり抵抗係数',.412579010060621,'0.413%')]):
 y=380+i*29;tx(304,y,138,label,24,True,ORANGE,h=13);tx(304,y+13,138,sub,18,c=MUTED,h=11)
 p.rect(448,y+2,88*val/6,9,ORANGE);tx(539,y-1,40,out,24,True,ORANGE,h=13)
p.line(448,465,536,465,MUTED)
for z in [0,2,4,6]:
 x=448+88*z/6;p.line(x,465,x,468,MUTED);tx(x-4,470,14,str(z),17,c=MUTED,h=9)
tx(470,481,69,'LP基準の削減率［%］',17,c=MUTED,h=11)
tx(304,496,275,'入力 [5]：LP 171.9／S-200 196.0 Ah/kg。比容量÷保持率の逆算参照値であり、初回全電池の実測値・量子由来の改善値ではない。',20,h=29)
tx(304,528,275,'固定条件：運転者55 kg・積載0・平坦・同一保存速度。回生・補機・荷重変化を除外した。DCは保存区間のみである。',19,h=28)
sec(15,568,'結果から言える条件と制約',BLUE);sec(304,568,'②の質量差が消失・逆転する条件',ORANGE)
tx(15,590,275,'B　同一目的関数での厳密改善には範囲内の改善解が必要である。Aの限定位置交換には改善余地がなく、全順列GMでも25先以上は平均悪化した。範囲の広さだけでは取得品質は保証されない。',23,h=42)
tx(15,636,275,'C　入力更新から採用判断までの許容計算時間は未測定であり、部分問題選択・全体統合は未検証である。候補の制約検証は運用採用を保証しない。',22,h=40)
tx(15,674,275,'参照：古典初期値J₀、範囲内最小値、全問題最適値407例。未証明53例（100先21・125先32）。',18,c=MUTED,h=21)
tx(304,590,275,'A　代表LP/S比較の既知部材軽量化 b は、固定面積5.98／固定担持量9.72 kgである。完成パックは183条件とも質量未確定で、1条件は対向面積不適合である。',22,h=36)
for i,(title,body) in enumerate([('δ＜b','軽量化'),('δ＝b','消失'),('δ＞b','逆転')]):
 x=304+i*91.66;p.rect(x,631,89.66,27,'#F5ECE5')
 tx(x+3,633,83.66,'B　'+title,22,True,ORANGE,h=12);tx(x+3,646,83.66,body,20,h=11)
tx(304,663,275,'正味軽量化量＝b−δ［kg］。δは未確定部材のS−LP差である。②の質量収支内の境界であり、実用電池の成立境界ではない。',19,h=27)
# This is the UNVALIDATED full-system chain; observed endpoints are explicitly stated below.
tx(15,699,564,'共通枠組み B｜技術と採用判断の区別 [4]、将来構成の予見・前提の省察 [3]',25,True,NAVY,h=14)
for x,title,body in [(15,'技術的能力（モデル・文献）','探索／材料物性評価'),(212,'C　運用・設計への適用','候補の採用・全体統合／電池設計'),(410,'C　実運用の成果','配送運用／実車走行電力量')]:
 p.rect(x,718,169,28,PALE);tx(x+3,720,163,title,21,True,NAVY,h=12);tx(x+3,733,163,body,18,c=MUTED,h=11)
dashed(187,731,208);dashed(385,731,406)
tx(15,752,564,'Aの到達点は、配送側が採用前の計画品質、材料側が固定速度下のモデル電力量である。実運用成果とは区別する。',20,h=19)
tx(15,766,564,'量子優位性・対象材料の量子計算による改善・完成パックの出力／寿命／安全性・実車性能は未実証である。',18,c=MUTED,h=10)
p.line(15,778,579,778)
short=[
 '[1] Bärtschi & Eidenbenz (2020). IEEE QCE, 72–82.',
 '[2] Delgado et al. (2022). Phys. Rev. A 106, 032428.',
 '[3] Stilgoe et al. (2013). Res. Policy 42, 1568–1580.',
 '[4] Geels (2004). Res. Policy 33, 897–920.',
 '[5] Chen et al. (2020). Nat. Commun. 11, 3411.',
 '[6] Holliday et al. (2026). Quantum Mach. Intell. 8, 37.',
 '[7] Shokrian Zini et al. (2023). Quantum 7, 1049.'
]
for i,s in enumerate(short):tx(15 if i<4 else 304,784+(i if i<4 else i-4)*12,275,s,18,c=MUTED,h=12)
tx(304,820,275,'全条件・参照値の定義・工程時間・未検証事項は別添監査報告に示す。',18,c=MUTED,h=12)
p.save(TITLE+'\n'+RQ+'\n'+PURPOSE+'\nA=固定条件の保存結果の確認、B=文献・モデルに基づく条件付き推論、C=未検証。\n研究方針：面接・RIQ・M1を含めない。\n\n'+'\n'.join(f"[{v['n']}] {v['author']} ({v['year']}). {v['title']}. {v['journal']}. DOI: {v['doi']}\n利用範囲：{v['use']}" for v in REFS))
print('Built run04 poster')
