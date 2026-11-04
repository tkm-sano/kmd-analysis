from pathlib import Path
from html import escape
R=Path(__file__).resolve().parents[1]
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="780" viewBox="0 0 1400 780"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#455765"/></marker></defs><rect width="1400" height="780" fill="white"/><g font-family="sans-serif" fill="#17232d">']
def text(x,y,t,size=20):s.append(f'<text x="{x}" y="{y}" font-size="{size}">{escape(t)}</text>')
def box(x,y,w,h,lines,c):
 s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#f5f7f9" stroke="{c}" stroke-width="2"/>')
 for i,t in enumerate(lines):text(x+12,y+29+i*28,t,19)
def arrow(x,y,xx,yy,dash=False):s.append(f'<path d="M{x},{y} L{xx},{yy}" stroke="#455765" stroke-width="2" fill="none" marker-end="url(#a)"'+(' stroke-dasharray="8 6"' if dash else '')+'/>')
text(30,38,'量子計算の技術的能力から、適用判断と成果への接続',29)
text(30,72,'実線：保存結果・モデル内の関係　破線：未検証の接続／条件候補',20)
text(30,119,'配送計画：CPUによる理想化モデルの数値評価、時間窓なし',22)
box(30,140,260,120,['量子探索の技術能力','GM-QAOA等のモデル評価','実機資源は未保存'],'#286a96')
box(350,140,290,120,['探索範囲・候補の取得','改善解の存在と解品質','限定交換では改善解なし'],'#286a96')
box(700,140,285,120,['古典側での採用判断','実行可能性・全体への統合','許容計算時間との照合'],'#286a96')
box(1045,140,325,120,['計画上の成果','総移動時間・取得時刻','動的運用・DCへの接続は未検証'],'#286a96')
arrow(290,200,348,200);arrow(640,200,698,200,True);arrow(985,200,1043,200,True)
box(690,290,540,85,['許容計算時間＝入力更新から採用判断までの時間枠','未測定。顧客時間窓・出発余裕の改名ではない。'],'#455765');arrow(840,290,840,263,True)
text(30,422,'電池材料：量子評価の先行研究と、文献入力による条件付き計算を区別する',22)
box(30,447,260,120,['量子材料評価の技術能力','精度・資源の先行研究','対象材料への利用は未実施'],'#a6522c')
box(350,447,290,120,['評価情報→試験・材料選択','量子情報の有用性は未検証','Chen入力は古典研究由来'],'#a6522c')
box(700,447,285,120,['セル・パック設計の採用','容量固定の質量推計','未知部材・出力・寿命・安全性'],'#a6522c')
box(1045,447,325,120,['質量→走行DC','同一保存速度の条件付き計算','5.67%→0.478%→0.413%'],'#a6522c')
arrow(290,507,348,507,True);arrow(640,507,698,507,True);arrow(985,507,1043,507)
box(320,610,510,95,['文献入力（比容量逆算）＋容量20 kWh固定','電極・集電体・セパレータ・電解液の別途評価','完成パック183値は全て未確定'],'#a6522c');arrow(830,635,855,570)
box(905,610,465,95,['走行条件による修飾','速度・転がり係数・平坦・効率0.90','回生・補機・荷重変化除外、保存区間のみ'],'#455765');arrow(1180,610,1180,570)
text(30,754,'共通性は「適用判断」の分析構造にある。二経路の全接続や量子優位性を実証した図ではない。',21)
s.append('</g></svg>');(R/'reports/causal_model.svg').write_text(''.join(s))
