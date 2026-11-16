from pathlib import Path
import json,csv,hashlib,re,sys,unicodedata,html
from zipfile import ZipFile
import xml.etree.ElementTree as ET
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];ROOT=Path('/home/takuma/kmd-analysis');PRE=ROOT/'review_outputs/poster_policy_revision_20261104/run06';E=R/'evidence';reports=R/'reports'
def write_table(name,rows):
 with (reports/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 body='<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in rows[0])+'</tr>'
 for r in rows:body+='<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r.values())+'</tr>'
 return body+'</table>'
style='body{font-family:sans-serif;max-width:1350px;margin:32px auto;padding:0 24px;color:#17232d;line-height:1.8}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #bac6cf;padding:9px;vertical-align:top;text-align:left}th{background:#edf3f7}h1,h2{color:#143653}a{color:#286a96}'
def page(name,title,body):
 (reports/(name+'.html')).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>'+style+'</style><body><p><a href="../index.html">成果物一覧</a></p><h1>'+html.escape(title)+'</h1>'+body+'</body></html>')
changes=[dict(問題='因果経路が文章内の矢印だけであった',今回の修正='10個の主要段階と条件入力・フィードバックを持つ2本の経路図を紙面中央へ配置した。',構造上の意味='計算能力、利用判断、下流の評価量までの接続を、媒介変数と修飾条件を含めて追える。'),dict(問題='方法・数値の充実を、研究構造の理解と取り違えた',今回の修正='主要結果を対応する接続の直下に配置した。数値の全来歴は既存92行の台帳へ接続する。',構造上の意味='結果は経路を検証する根拠となる。数値表を独立した分析として並べない。'),dict(問題='古典と量子の役割が本文説明にとどまった',今回の修正='古典側の角度更新と、CPU上の理想量子モデルの状態・測定との往復を図示した。',構造上の意味='候補を得た後も古典側が品質・制約を検証する。実QPUとのハイブリッドを実施したとはしない。'),dict(問題='配送の探索範囲と取得過程の違いが弱かった',今回の修正='探索範囲S→候補存在、初期化・混合等→取得、制約・締切→採用を別の矢印で描いた。',構造上の意味='この支持内に改善候補がなければ、同じ支持で取得能力だけを上げてもJCを改善できない。'),dict(問題='材料の上流量子接続とモデル内の換算が連続して見えた',今回の修正='量子材料評価→設計利用を点線で描き、今回の記号入力がその後の質量モデルへ入る分岐を描いた。',構造上の意味='量子材料情報の実用設計利用は未検証でも、設計入力以降のモデル条件を解析できる。量子由来の改善として帰属しない。'),dict(問題='部材相殺・走行条件が脚注になっていた',今回の修正='面積・塗工方針と会計外追加差を質量収支への入力とし、同一速度・係数を走行応答への修飾条件として配置した。',構造上の意味='b−δの境界と、同じ速度・物理条件での質量/DC符号対応を区別する。'),dict(問題='将来構成と実施済み結果の位置が曖昧であった',今回の修正='実線A、破線B、点線Cと段階内ラベルを併用した。動的更新・部分問題選択・実運行をCに置いた。',構造上の意味='実世界の因果効果を識別した図ではなく、検証範囲を明示した影響経路モデルである。')]
page('01_CHANGES','前回の問題と今回の構造修正',write_table('01_CHANGES',changes)+'<p>前回の84点という自己評価は、説明項目の有無に偏り、図で研究構造を追えるかという評価を過大に見積もっていた。今回は点数の再掲ではなく、経路・条件・根拠が図上で対応するかを確認した。新しい初見読者テストを実施したものではない。</p>')
# Each link gets a scientific interpretation and an evidence scope, rather than a generic "causal" label.
graph=json.loads((E/'DIAGRAM_STRUCTURE.json').read_text());allowed={v['id'] for k in ['nodes','modifiers','internal_nodes'] for v in graph[k]}
assert all(e['source'] in allowed and e['target'] in allowed for e in graph['edges'])
specific={
'P1_S_influence':('探索範囲Sと主対照JCが、改善候補の存在を定める','Step4 P1-08; Step2 PATH1_SUPPORT_AUDIT.csv','支持内最小とJCの数学的比較。量子手法一般の不可能性ではない'),
'P1_resources_influence':('初期状態・混合・有限学習/測定予算が取得過程を条件付ける','Step4 P1-09; QAOA_CONTROLLED_CELL_SUMMARY.csv','初期状態等は3診断入力の対照、予算自体の一要因効果を一般化しない'),
'P1_H_influence':('可行性と品質に加え、計算締切の充足が運用採用の判断へ入る','Step4 P1-12; PATH1_RUNTIME_RESULTS.csv','H未設定、全工程の公平計時は未確定。品質と時間を直列の因果としない'),
'P1_angles':('古典最適化が角度を理想量子モデルへ渡す','保存FITとStep2統制実装・Step4 P1-09','CPU上の役割分担。QPU実行や実機速度の実証ではない'),
'P1_evaluation':('状態/測定の評価が古典側の角度調整へ戻る','保存学習・評価記録、Step4 P1-09','学習評価と最終候補のbest取得を区別する'),
'P1_main_0':('支持に改善候補が存在することが、その支持からの取得の前提となる','Step4 P1-08; PATH1_CONTRIBUTION_CONDITIONS.md','JCを上回る解品質への寄与を扱う。等品質の計時寄与一般の必要条件とはしない'),
'P1_main_1':('保存候補を古典側が目的・順序・制約と照合する','Step4 P1-01; B_PLAN_REFERENCES_36800.csv','全保存bestを確認。運用で実採用した結果ではない'),
'P1_main_2':('採用された候補を運用中の全体計画へ反映する','Step4 P1-13/I-02; UNRESOLVED_ISSUES.md','動的更新・顧客部分問題の選択/統合は未実施。保存の限定支持は全顧客を保持する'),
'P1_main_3':('採用計画を実道路で実行して実移動時間へつなぐ','Step4 I-02','固定OD目的の解品質と実道路効果は別の評価段階である'),
'P1_dynamic_influence':('需要・道路の更新が計画への統合条件を変える','Step4 I-02; P1未解決事項','想定する動的運用の接続。更新実験は実施していない'),
'P1_road_influence':('道路・荷重・運行条件が実配送成果に関係する','Step4 I-02','モデル外の実世界接続。実測因果効果を主張しない'),
'P2_quantum_resource_influence':('精度・計算資源・費用が量子材料評価の利用可能性に関係する','Delgado2022; Shokrian Zini2023; Step4 P2-09','文献は計算法・資源推計の根拠。対象材料の量子改善や実用性の実証ではない'),
'P2_use':('量子材料評価の情報を設計者が実用条件の判断に利用する','Step4 P2-09; I-01','対象材料の物性改善・設計採用は未検証'),
'P2_adoption_unverified':('評価情報が設計条件へ採用される場合の接続','Step4 P2-09; P2-07','物性情報とq/u/V等の実用設計入力を同一視しない'),
'P2_symbolic_entry':('今回の解析では記号入力・設計仮定をモデルへ直接与える','Step4 P2-01〜03; PATH2_ANALYTICAL_SENSITIVITY.csv','Chen逆算qを主材料値として採用しない。量子生成物性を使っていない'),
'P2_mass_from_input':('入力容量・利用率・電圧・部材設計を質量へ換算する','Step4 P2-01/06; T08/T09','T08記号感度とT09構造補完は異なるモデル。未知部材を0で補わない'),
'P2_component_modifier':('設計方針は既知部材差bを変え、会計外差δが正味差を相殺する','Step4 P2-02/06; PATH2_BOUNDARY_ANALYSIS.csv','ΔM=b−δ、δ=bで0。同一非重複会計の恒等式であり完成pack成立の保証ではない'),
'P2_mass_dc':('他の質量を固定した電池差を走行総質量へ移し、転がり・並進加速の仕事を介するDCモデルの応答を評価する','Step4 P2-04/05; DC_MASS_KERNEL_INDEPENDENT.csv','両比較質量が1000〜1250kg内、同じ速度・係数・物理条件で符号対応する'),
'P2_driving_influence':('速度・物理係数が質量から電力量への写像を修飾する','凍結Controlled-DCモデル、Step4 P2-04','平坦・回生なし・補機/旋回除外・荷重一定。対象外物理の効果を新規に実測していない'),
'P2_real_link':('完成パックと実運行でモデルの効果が成立するかを検証する','Step4 P2-07/P2-09','完成pack、出力・寿命・安全性、実車、量子帰属は未検証'),
'P2_real_conditions_influence':('実用性能と運行条件が実車への適用を制約する','Step4 P2-07/09','必要条件を満たす製品・実用可能性を証明したものではない')}
rows=[]
for e in graph['edges']:
 meaning,source,scope=specific[e['id']]
 rows.append(dict(矢印ID=e['id'],入力=e['source'],接続先=e['target'],表示区分=e['status'],作用の意味=meaning,根拠=source,成立範囲と未検証事項=scope))
page('02_LINK_EVIDENCE','図の各接続が意味することと根拠',write_table('02_LINK_EVIDENCE',rows)+'<p>Aは固定モデル/保存計算内の確認、Bは数式・文献に基づく条件付き接続、Cは未検証である。各実線を実世界の因果効果の識別結果と読まない。一次資料と全数値は前版の数値台帳へ接続する。</p>')
# PDF content and editable source verification.
checks=[]
def ck(name,ok,detail):checks.append(dict(項目=name,状態='PASS' if ok else 'FAIL',確認内容=detail))
blocks=json.loads((R/'poster_layout.json').read_text());doc=fitz.open(R/'poster.pdf');pg=doc[0];mm=72/25.4
ck('A1横・全1ページ',len(doc)==1 and abs(pg.rect.width/mm-841)<.1 and abs(pg.rect.height/mm-594)<.1,'841×594mm')
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
missing=[]
for i,b in enumerate(blocks):
 x,y,w,h=[b[k] for k in ['x_mm','y_mm','w_mm','h_mm']];clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm)
 if norm(b['text']) not in norm(pg.get_text('text',clip=clip)):missing.append(dict(index=i,text=b['text'],actual=pg.get_text('text',clip=clip)))
ck('全テキストのPDF内存在',not missing,f'{len(blocks)}ブロック。欠落{len(missing)}')
(E/'TEXT_MISMATCHES.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2))
overlaps=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm']);dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:overlaps.append((i,j,round(dx,2),round(dy,2)))
ck('文字矩形の重なりなし',not overlaps,str(overlaps))
ck('全ブロックが用紙内',all(0<=b['x_mm'] and b['x_mm']+b['w_mm']<=841.01 and 0<=b['y_mm'] and b['y_mm']+b['h_mm']<=594.01 for b in blocks),'座標・高さガード')
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(R/'poster.pptx') as z:root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
ck('編集可能な図・本文',len(root.findall('.//p:pic',ns))==0 and len(root.findall('.//p:cxnSp',ns))>40,'画像化せず、ネイティブ図形・コネクタ・テキストを使用')
ck('破線・点線のネイティブ線種',len(root.findall('.//a:prstDash',ns))>=15,'PPTXとPDFの線種を対応させた')
ck('2経路・段階・接続の登録',len(graph['nodes'])==10 and len(graph['edges'])==21 and len(rows)==21,'主要10段階、21接続。外生条件と内部往復も別登録')
ck('図の全端点が登録済み',all(e['source'] in allowed and e['target'] in allowed for e in graph['edges']),'内部計算・外生条件・入力合流点を含む')
preserved=[]
for v in csv.DictReader((E/'ORIGINAL_SHA256.csv').open()):
 p=Path(v['path']);h=hashlib.sha256(p.read_bytes()).hexdigest();preserved.append(dict(path=str(p),sha256=h,unchanged=h==v['sha256']))
ck('前版と研究根拠の保全',all(v['unchanged'] for v in preserved),f'{len(preserved)}対象を開始時hashと照合')
assert len(list(csv.DictReader((PRE/'reports/03_NUMERIC_PROVENANCE.csv').open(encoding='utf-8-sig'))))==92
ck('数値来歴の維持',True,'前版92行をそのまま参照。新規計算結果は追加していない')
page('03_VALIDATION','表示・構造・保全の確認',write_table('03_VALIDATION',checks)+'<p>全ページをPPTXからPDFへレンダリングして確認した。実寸試し刷りと、独立した初見読者の理解度テストは未実施である。研究結果の再集計や新しい量子・材料・走行実験は実行していない。</p>')
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=overlaps,preserved=preserved),ensure_ascii=False,indent=2))
# New index links the current poster and the unchanged full numerical dossier.
prior_rel='../../poster_policy_revision_20261104/run06/'
body='<h1>因果経路を中心にした研究ポスター修正</h1><p>前版の問題は、説明項目と数値を増やしても、接続条件を図で追える構成になっていなかったことである。今回は二つの影響経路、条件入力、古典/理想量子モデルの往復、設計仮定の入力位置、未検証の下流を図示した。</p><ul>'
links=[('poster.pptx','編集可能なポスターPPTX'),('poster.pdf','PPTXから出力したPDF'),('poster_preview.png','全体プレビュー'),('causal_paths.svg','因果経路図の編集可能SVG'),('poster.svg','ポスター全体SVG'),('reports/01_CHANGES.html','何が意図とずれていたか・今回の構造修正'),('reports/02_LINK_EVIDENCE.html','21接続の意味・根拠・限界'),('reports/03_VALIDATION.html','表示・構造・保全の確認'),(prior_rel+'reports/03_NUMERIC_PROVENANCE.html','既存92行の数値・出典・計算条件'),(prior_rel+'reports/06_HOLD.html','既存HOLDと未検証事項'),(prior_rel+'reports/07_RESEARCH_EXPLANATION.html','詳しい方法・結果の説明')]
body+=''.join('<li><a href="'+a+'">'+html.escape(b)+'</a></li>' for a,b in links)+'</ul><p>Aは保存計算・モデル内の確認、Bは数式/文献に基づく条件付き接続、Cは未検証である。材料上流、実機、実車、動的更新、完成パック等のHOLDは解除していない。独立した人間のレビューや因果効果の実世界推定を実施したという意味ではない。</p>'
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>因果経路による構造改訂</title><style>'+style+'</style><body>'+body+'</body></html>')
# Actual rendered crops for visually checking direction, joins, annotations and line style.
pg.get_pixmap(matrix=fitz.Matrix(.92,.92),clip=fitz.Rect(0,101*mm,841*mm,524*mm)).save(R/'causal_paths_preview.png')
for n,box in [('path1',(10,150,831,299)),('path2',(10,358,831,524)),('hybrid',(185,180,335,245))]:pg.get_pixmap(matrix=fitz.Matrix(1.4,1.4),clip=fitz.Rect(*[v*mm for v in box])).save(R/'render'/f'{n}_check.png')
print(json.dumps(checks,ensure_ascii=False,indent=2))
if any(v['状態']=='FAIL' for v in checks):sys.exit(1)
