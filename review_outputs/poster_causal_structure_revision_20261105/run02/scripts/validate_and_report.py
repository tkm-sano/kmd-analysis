from pathlib import Path
import json,csv,hashlib,html,re,unicodedata,sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];E=R/'evidence';P=R/'reports';checks=[]
def ck(item,ok,detail):checks.append(dict(item=item,status='PASS' if ok else 'FAIL',detail=detail))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
d=fitz.open(R/'poster.pdf');pg=d[0];mm=72/25.4;blocks=json.loads((R/'poster_layout.json').read_text())
ck('A1 landscape single page',len(d)==1 and abs(pg.rect.width/mm-841)<.1 and abs(pg.rect.height/mm-594)<.1,'841×594mm')
missing=[]
for i,b in enumerate(blocks):
 x,y,w,h=[b[k] for k in ['x_mm','y_mm','w_mm','h_mm']]
 clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm)
 if norm(b['text']) not in norm(pg.get_text('text',clip=clip)):missing.append(dict(i=i,text=b['text'],actual=pg.get_text('text',clip=clip)))
ck('All text rendered',not missing,str(len(blocks))+' blocks')
overlaps=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm']);dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:overlaps.append((i,j,round(dx,2),round(dy,2)))
ck('No text overlaps',not overlaps,str(overlaps));ck('All text inside slide',all(b['x_mm']>=0 and b['x_mm']+b['w_mm']<=841.01 and b['y_mm']>=0 and b['y_mm']+b['h_mm']<=594.01 for b in blocks),'coordinate guards')
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(R/'poster.pptx') as z:root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
ck('Editable diagram',not root.findall('.//p:pic',ns) and len(root.findall('.//p:cxnSp',ns))>40,'native text/shapes/connectors')
for f in ['poster.svg','sociotechnical_structure.svg']:ET.parse(R/f)
ck('SVG well formed',True,'text and vectors remain editable')
for v in csv.DictReader((E/'ORIGINAL_SHA256.csv').open()):ck('Preservation '+Path(v['path']).name,hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'],'original SHA256')
ck('Primary claim values retained','0/36,800' in (R/'poster_text.txt').read_text() and '920' in (R/'poster_text.txt').read_text(),'same saved comparison and material-free DC cases; no new experiments')
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=overlaps),ensure_ascii=False,indent=2))
with (E/'VALIDATION.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=checks[0]);w.writeheader();w.writerows(checks)
pg.get_pixmap(matrix=fitz.Matrix(.88,.88),clip=fitz.Rect(0,108*mm,841*mm,338*mm)).save(R/'sociotechnical_structure_preview.png')
pg.get_pixmap(matrix=fitz.Matrix(1.25,1.25),clip=fitz.Rect(200*mm,130*mm,831*mm,328*mm)).save(R/'render/system_check.png')
style='body{font-family:sans-serif;max-width:1250px;margin:32px auto;padding:0 24px;color:#17232d;line-height:1.8}h1,h2{color:#143653}table{width:100%;border-collapse:collapse;font-size:14px}td,th{border:1px solid #bac6cf;padding:9px;vertical-align:top;text-align:left}th{background:#edf3f7}a{color:#286a96}'
def page(name,title,body):
 (P/(name+'.html')).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>'+style+'</style><body><p><a href="../index.html">成果物一覧</a></p><h1>'+html.escape(title)+'</h1>'+body+'</body></html>')
logic=[('社会的機能','物資を届ける機能を、複数の技術・主体・規則の関係が担う。研究の主語をEV配送の社会技術システムとする。'),('量子技術の位置','候補探索の能力と物性評価情報は、既存の構成へ組み込まれる候補である。技術供給から成果へ直結する配置を採らない。'),('利用主体と規則','主体は技術を選択・利用し、規則や慣行はその判断を方向付ける。技術構成も可能な行為を制約する。相互関係は理論枠組みであり現場調査の結果ではない。'),('二つの定量分析の役割','配送は探索範囲・取得・古典比較、材料は設計仮定・部材収支・固定走行応答を検討する。これらを社会技術システム全体の作用の実証と同一視しない。'),('研究で選んだ基準と現場判断','JCとの比較は研究上の品質基準であり、事業者が実際に採用する基準ではない。容量一定も研究で置いた設計仮定であり、設計者が現実にその目的を選ぶことは未確認である。'),('結論の範囲','技術的に得られる出力と、運用・設計に利用できる条件を分けて評価する。定量結果は構成の一部の接続に関する証拠である。組織・制度・市場・普及・社会的便益を実証した結論ではない。')]
page('01_RESEARCH_LOGIC','社会技術システムを主語とした研究の論理', ''.join('<h2>'+html.escape(a)+'</h2><p>'+html.escape(b)+'</p>' for a,b in logic)+'<h2>一次文献との対応</h2><p>Geels (2004), Sec.2/Fig.4, pp.900–903の、システム・主体・規則の相互に関連する分析次元を参照した独自図である。制度を組織そのものと同一視せず、役割を担う主体と、判断を方向付ける規則を区別した。<a href="https://doi.org/10.1016/j.respol.2004.01.015">原著書誌</a>。保存原著はposter_policy_revision_20261104/run06/sources/R4_STS.pdfで確認した。出版社のオンライン取得は403であり、保存済み一次資料と区別して記録する。</p><p>この枠組みを採ることは、面接・RIQ・M1を研究方法へ戻すことを意味しない。主体の実際の優先順位・採用基準・規則変更の接続は未検証として保持する。</p>')
rows=[dict(観点='研究全体の主語',前版='量子の二つの技術経路が中心であった',今回='EV配送の社会的機能を担う構成と、その中への技術の組込みを中心に置く'),dict(観点='因果関係の捉え方',前版='候補・情報が成果へ伝わる直列接続が中心であった',今回='主体・規則・技術構成の相互関係を上位に置く。定量的な接続はその部分分析とする'),dict(観点='評価の意味',前版='JとDCが分析の終点として前面に出ていた',今回='JとDCは研究で限定した評価量であり、社会的機能や採用の包括的実証と区別する'),dict(観点='方法の範囲',前版='技術的な因果経路が研究全体に見えた',今回='既存定量結果と文献を使用する方針は維持する。組織制度を測定したようには扱わない')]
with (P/'02_CHANGES.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
table='<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in rows[0])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in r.values())+'</tr>' for r in rows)+'</table>'
page('02_CHANGES','前版からの論理構造の修正',table+'<p>既存の数値・原稿・前版を保全した。Chen由来の旧具体値を主分析へ戻さず、定時配達率・量子優位性・面接/RIQ/M1も研究目的や方法へ戻していない。</p>')
validation_table='<table><tr><th>項目</th><th>状態</th><th>確認内容</th></tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r.values())+'</tr>' for r in checks)+'</table>'
page('03_VALIDATION','表示・編集可能性・保全の確認',validation_table+'<p>独立した人間による理解度テストや実寸の試し刷りは未実施である。図の理論的な相互関係は、実世界の因果効果を識別したことを意味しない。</p>')
links=[('poster.pptx','編集可能なポスターPPTX'),('poster.pdf','表示確認PDF'),('poster_preview.png','全体プレビュー'),('sociotechnical_structure.svg','社会技術システムの関係図SVG'),('sociotechnical_structure_preview.png','関係図の表示用PNG'),('reports/01_RESEARCH_LOGIC.html','研究全体の論理と文献の対応'),('reports/02_CHANGES.html','前版との構造の違い'),('reports/03_VALIDATION.html','表示・保全の確認'),('../../../poster_policy_revision_20261104/run06/index.html','既存の数値・出典・詳細方法・HOLD')]
# run02/index.html is two directories below review_outputs.
links[-1]=('../../poster_policy_revision_20261104/run06/index.html',links[-1][1])
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>社会技術システムを主語とする修正</title><style>'+style+'</style><body><h1>社会技術システムを研究全体の論理構造とする修正</h1><p>配送という社会的機能を、技術・主体・規則の相互関係が担う。量子計算の寄与は、その構成へどう組み込めるかとして検討する。二つの定量分析は、構成の一部の接続に対する証拠として位置付ける。</p><ul>'+''.join('<li><a href="'+a+'">'+html.escape(b)+'</a></li>' for a,b in links)+'</ul><p>現場の主体・規則・組織・制度の作用の実証、社会的便益の包括的評価、実運用改善の実証へ結果を拡張しない。</p></body></html>')
print(json.dumps(checks,ensure_ascii=False,indent=2))
if any(r['status']=='FAIL' for r in checks):sys.exit(1)
