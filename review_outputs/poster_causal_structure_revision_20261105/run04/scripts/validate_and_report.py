from pathlib import Path
from zipfile import ZipFile
import csv,json,re,hashlib,html,sys,unicodedata
import xml.etree.ElementTree as ET
from sections import SECTIONS
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];E=R/'evidence';P=R/'reports';checks=[]
def ck(item,ok,detail):checks.append(dict(item=item,status='PASS' if ok else 'FAIL',detail=detail))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
blocks=json.loads((R/'poster_layout.json').read_text());d=fitz.open(R/'poster.pdf');pg=d[0];mm=72/25.4
ck('A1 portrait, one page',len(d)==1 and abs(pg.rect.width/mm-594)<.1 and abs(pg.rect.height/mm-841)<.1,'594×841mm')
heads=[b['text'] for b in blocks if re.match(r'^[1-5] (目的|方法|結果|評価|議論)',b['text'])]
ck('Five explicit section headings',len(heads)==5 and all(h.startswith(str(i)+' '+name) for i,(h,name) in enumerate(zip(heads,SECTIONS),1)),str(heads))
prose=[s for ss in SECTIONS.values() for s in ss]
ck('Every section has prose',all(any(norm(s)==norm(b['text']) for b in blocks) for s in prose),f'{len(prose)} explanatory paragraphs; all five categories')
missing=[]
for i,b in enumerate(blocks):
 x,y,w,h=[b[k] for k in ['x_mm','y_mm','w_mm','h_mm']];clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm)
 actual=pg.get_text('text',clip=clip)
 if norm(b['text']) not in norm(actual):missing.append(dict(i=i,text=b['text'],actual=actual))
ck('All text present in rendered PDF',not missing,f'{len(blocks)} blocks; missing {len(missing)}')
overlaps=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm']);dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:overlaps.append((i,j,round(dx,2),round(dy,2)))
ck('No text overlaps',not overlaps,str(overlaps))
ck('All blocks inside page',all(b['x_mm']>=0 and b['x_mm']+b['w_mm']<=594.01 and b['y_mm']>=0 and b['y_mm']+b['h_mm']<=841.01 for b in blocks),'coordinate and overflow guards')
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(R/'poster.pptx') as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));pr=ET.fromstring(z.read('ppt/presentation.xml'));sz=pr.find('p:sldSz',ns)
 ck('Native editable shapes/text',not root.findall('.//p:pic',ns) and len(root.findall('.//p:cxnSp',ns))>30,'no flattened poster images')
 ck('PPTX portrait size',int(sz.get('cx'))==594*36000 and int(sz.get('cy'))==841*36000,str(sz.attrib))
for v in csv.DictReader((E/'ORIGINAL_SHA256.csv').open()):ck('Preserved '+Path(v['path']).name,hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'],'original SHA256')
old=json.loads(((R.parent/'run03')/'evidence/SYSTEM_STRUCTURE.json').read_text());new=json.loads((E/'SYSTEM_STRUCTURE.json').read_text())
for eid in ['rules_actors','actors_rules','actors_config','config_actors','rules_config','config_rules','quantum_config']:
 a=next(x for x in old['edges'] if x['id']==eid);b=next(x for x in new['edges'] if x['id']==eid)
 ck('Retained framework '+eid,all(a[k]==b[k] for k in ['source','target','status']),'same relation, repositioned')
base=Path('/home/takuma/kmd-analysis/review_outputs/poster_policy_revision_20261104/run06/evidence/CURRENT_AUDIT_CHECKS.csv')
audit=list(csv.DictReader(base.open(encoding='utf-8-sig')))
for name,val in [('primary_baselines','460'),('saved_candidates','36800'),('positive_vs_primary_greedy','0'),('DC_mass_cases','920')]:
 row=next(v for v in audit if v['item']==name);ck('Saved evidence '+name,row['actual']==val and row['status']=='PASS',str(base))
text=(R/'poster_text.txt').read_text()
ck('No rejected primary material rates',all(s not in text for s in ['5.67%','0.478%','0.413%','171.9','196.0']),'Chen-derived reference cases not reintroduced as primary effects')
ck('No on-time indicator or rejected interview method',all(s not in text for s in ['定時配達率','RIQ','M1','インタビュー']),'current quantitative/literature policy retained')
for f in ['poster.svg','sociotechnical_structure.svg']:ET.parse(R/f)
ck('Vector SVG valid',True,'editable diagram and poster')
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=overlaps),ensure_ascii=False,indent=2))
with (E/'VALIDATION.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=checks[0]);w.writeheader();w.writerows(checks)
pg.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(0,128*mm,594*mm,359*mm)).save(R/'sociotechnical_structure_preview.png')
pg.get_pixmap(matrix=fitz.Matrix(1.2,1.2),clip=fitz.Rect(10*mm,365*mm,584*mm,796*mm)).save(R/'render/prose_check.png')
style='body{font-family:sans-serif;max-width:1100px;margin:32px auto;padding:0 24px;line-height:1.85;color:#17232d}h1,h2{color:#143653}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:8px;border:1px solid #bac6cf;text-align:left;vertical-align:top}th{background:#edf3f7}a{color:#286a96}'
def page(name,title,body):
 (P/(name+'.html')).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>'+style+'</style><body><p><a href="../index.html">成果物一覧</a></p><h1>'+html.escape(title)+'</h1>'+body+'</body></html>')
body='<p>以下はポスター本文と同一の説明文である。図のラベルだけに依存せず、研究目的・方法・結果・評価・議論を順に読むことができる。</p>'
for i,(name,ss) in enumerate(SECTIONS.items(),1):
 body+='<h2>'+str(i)+' '+html.escape(name)+'</h2>'+''.join('<p>'+html.escape(s)+'</p>' for s in ss)
page('01_POSTER_PROSE','ポスター本文：目的・方法・結果・評価・議論',body)
(R/'poster_prose.txt').write_text('\n\n'.join(str(i)+' '+name+'\n'+'\n\n'.join(ss) for i,(name,ss) in enumerate(SECTIONS.items(),1)))
page('02_CHANGE_REPORT','文章による説明を加えた改稿の内容','<p>A1縦、二経路、青・茶の配色、社会技術システムの関係図を維持した。目的・方法・結果・評価・議論を独立した見出しと文章で記述した。</p><p>方法には入力の定義、配送先数、8設定、測定反復、古典主対照、材料の記号式・部材会計、材料値を使わないDC応答検算を記載した。結果には保存値と解析結果を置き、評価には比較基準と解釈範囲、議論には利用主体・判断基準・技術構成との関係を置いた。</p><p>新規の量子学習、solver、材料実験、実車実験、社会調査を実施していない。元の原稿・前版・保存結果は保全した。実際の主体・規則・運用採用、完成パック・実用性能・量子帰属のHOLDは解除していない。</p>')
table='<table><tr><th>項目</th><th>状態</th><th>確認内容</th></tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row.values())+'</tr>' for row in checks)+'</table>'
page('03_VALIDATION','内容・表示・元資料保全の確認',table+'<p>PDF全1ページをレンダリングして確認した。独立した人間による読解テストと実寸試し刷りは未実施である。commit・push・PR作成は行っていない。</p>')
links=[('poster.pptx','編集可能なA1縦ポスター'),('poster.pdf','表示確認用PDF'),('poster_preview.png','全体プレビュー'),('reports/01_POSTER_PROSE.html','目的・方法・結果・評価・議論の説明文'),('poster_prose.txt','説明文TXT'),('sociotechnical_structure.svg','社会技術システム図SVG'),('reports/02_CHANGE_REPORT.html','修正内容と残存HOLD'),('reports/03_VALIDATION.html','確認結果'),('../../poster_policy_revision_20261104/run06/index.html','既存の詳細方法・数値来歴・参考文献')]
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>5項目と文章説明を備えたA1縦版</title><style>'+style+'</style><body><h1>目的・方法・結果・評価・議論を明記したA1縦版</h1><p>594×841mm。社会技術システムの関係図を保持し、五つの項目を本文で説明した。</p><ul>'+''.join('<li><a href="'+a+'">'+html.escape(b)+'</a></li>' for a,b in links)+'</ul></body></html>')
print(json.dumps(checks,ensure_ascii=False,indent=2))
if any(v['status']=='FAIL' for v in checks):sys.exit(1)
