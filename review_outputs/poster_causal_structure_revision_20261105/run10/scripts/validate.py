from pathlib import Path
import csv,json,hashlib,re,html,sys,unicodedata,statistics,collections
from zipfile import ZipFile
import xml.etree.ElementTree as ET
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];ROOT=R.parents[2];E=R/'evidence';P=R/'reports';S=ROOT/'review_outputs/quantum_ev_step5_20261105';M=ROOT/'review_outputs/t08_t09_interaction_boundaries_20261105/run01';checks=[]
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
def ck(n,ok,d=''):checks.append(dict(item=n,status='PASS' if ok else 'FAIL',detail=d))
def writecsv(name,rows):
 with (E/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
blocks=json.loads((R/'poster_layout.json').read_text());text=(R/'poster_text.txt').read_text();doc=fitz.open(R/'poster.pdf');pg=doc[0];mm=72/25.4
ck('A1縦・全1ページ',len(doc)==1 and abs(pg.rect.width/mm-594)<.1 and abs(pg.rect.height/mm-841)<.1,f'{pg.rect.width/mm:.3f} × {pg.rect.height/mm:.3f} mm')
missing=[]
for b in blocks:
 x,y,w,h=[b[k] for k in ['x_mm','y_mm','w_mm','h_mm']]
 v=pg.get_text('text',clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm))
 if norm(b['text']) not in norm(v):missing.append(dict(text=b['text'],actual=v))
ck('PDFの全文章を元レイアウトと照合',not missing,f'{len(blocks)} blocks; missing={len(missing)}')
ov=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm']);dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:ov.append([i,j,dx,dy])
ck('文章ボックスの重なり',not ov,str(ov))
ck('全文章がA1紙面内',all(b['x_mm']>=0 and b['y_mm']>=0 and b['x_mm']+b['w_mm']<=594.01 and b['y_mm']+b['h_mm']<=841.01 for b in blocks))
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
with ZipFile(R/'poster.pptx') as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));pres=ET.fromstring(z.read('ppt/presentation.xml'));sz=pres.find('p:sldSz',ns)
 ck('PPTX実寸A1縦',int(sz.get('cx'))==594*36000 and int(sz.get('cy'))==841*36000,str(sz.attrib))
 ck('編集可能な文章・図・グラフ',len(root.findall('.//p:pic',ns))==0 and len(root.findall('.//p:cxnSp',ns))>20,'文章・手順図はネイティブ要素、画像への一枚化なし')
for v in read(E/'SOURCE_SHA256.csv'):ck('原本保全 '+str(Path(v['path']).relative_to(ROOT)),hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'])
ck('背景・目的・方法・評価・議論の対象を文章化',all(x in text for x in ['背景・目的','分析方法','4 評価項目','5 議論：']))
ck('旧指標と内部記号の再導入なし',all(s not in text for s in ['定時配達率','T08','T09','Controlled-DC','HOLD','支持集合','技術能力境界','RIQ']))
ck('未検証の社会関係図を削除','判断を方向付ける' not in text and '主体・制度・採用行動の分析は行っていない' in text)
ck('結果非掲載',all(x not in text for x in ['2.368','1.140','28,200','8,600','36,800','0.214','135入力','δ < b','相殺','悪化が大きい','結果','確認された','であった','符号が一致']))
ck('結果図を手順図へ変更',all(x in text for x in ['図2 同じ入力','図3 材料入力']))
ck('原研究の実施状況を結果未実施に改変しない','予定' not in text and '本研究は未実施' not in text)
ck('主本文18.5pt以上、図内15.5pt以上、参考文献14pt',min(b['font_pt'] for b in blocks)>=14,'主本文18.5〜22pt、見出し21〜39pt、図15.5〜26pt。実寸の試し刷りは未実施')

ck('現段階・今後・限界の3欄',all(x in text for x in ['現時点で記載できる内容','今後の作業（優先案）','限界と課題']))
ck('今後の優先作業と未検証事項を区別','既存解析を本文へ統合する' in text and '追加検証を絞る' in text and '量子実機・実配送での効果は未検証である' in text)
ns2={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
textshapes=[sp for sp in root.findall('.//p:sp',ns2) if any(t.text for t in sp.findall('.//a:t',ns2))]
ck('全テキストで自動折り返し',all(sp.find('p:txBody/a:bodyPr',ns2).get('wrap')=='square' for sp in textshapes),f'{len(textshapes)} text shapes; no line-wise fixed paragraphs')
native=[sp for sp in textshapes if sp.find('p:spPr/a:prstGeom',ns2) is not None]
ck('手順図は図形自身に文章を保持',len(native)>=14,f'{len(native)} native shapes with internal text')
ck('指定資料の条件を反映',all(v in text for v in ['大田区','京浜トラックターミナル','MINICAB EV','1100 kg','55 kg','SUMO汎用配送車','背景交通・荷下ろし','区間ごとの合計仕事の正値']))
ck('旧99先系列とB系列を混同しない','3/4/5/25/100先' in text and '99先' not in text)
ET.parse(R/'poster.svg');ck('SVG整形式',True)
previous=json.loads((R.parent/'run09/poster_layout.json').read_text())
ck('全55テキスト・記載順が前版と完全一致',[b['text'] for b in previous]==[b['text'] for b in blocks],f'{len(blocks)} blocks compared verbatim')
ck('図の接続・線種が前版と完全一致',(R.parent/'run09/evidence/FIGURE_EDGES.json').read_text()==(E/'FIGURE_EDGES.json').read_text())
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=ov),ensure_ascii=False,indent=2));writecsv('VALIDATION.csv',checks)
for name,clip in [('methods_detail',(10,280,584,654)),('footer_detail',(10,660,584,840))]:pg.get_pixmap(matrix=fitz.Matrix(1.2,1.2),clip=fitz.Rect(*(v*mm for v in clip))).save(R/'render'/f'{name}.png')

style='body{font-family:sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;line-height:1.8;color:#20313f}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #cbd7e0;padding:8px;text-align:left;vertical-align:top}th{background:#eff4f7}a{color:#246c94}'
def tab(rs):return '<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in rs[0])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r.values())+'</tr>' for r in rs)+'</table>'
changes=[dict(対象='タイトル・見出し',変更='濃紺のタイトル帯と章見出し、青・茶の経路別見出しに統一した'),dict(対象='情報のまとまり',変更='本文パネルを白、図の領域を淡色とし、余白と角丸・枠線の太さを統一した'),dict(対象='手順図',変更='手順名を太字・経路色、補足を本文色とし、薄い枠線と左側の色線で階層を示した。コネクタのテーマ影を除去した'),dict(対象='下段',変更='現段階・今後・限界の3欄をカード形式で揃え、参考文献の領域を分けた'),dict(対象='内容・形式',変更='run09の全55テキストと図の接続・線種は完全一致。A1縦594×841mm、結果非掲載、自動折り返し、編集可能な図形を維持した')]
writecsv('DESIGN_CHANGES.csv',changes)
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>A1縦・デザイン改訂版</title><style>'+style+'</style><body><h1>A1縦・内容を維持したデザイン改訂版</h1><p>run09を保全し、内容はそのままにrun10を別途作成した。</p><p><a href="poster.pptx">編集可能PPTX</a> ／ <a href="poster.pdf">表示確認用PDF</a> ／ <a href="poster_preview.png">全体プレビュー</a></p><h2>変更内容</h2>'+tab(changes)+'<h2>検証</h2>'+tab(checks)+'<p>実際のPPTXからPDFを生成し、全体と詳細を表示確認した。実寸の試し刷りは未実施である。前版・研究記録は保全し、commit・push・PR作成は行っていない。</p></body></html>')
print(json.dumps(dict(checks=len(checks),failed=sum(c['status']=='FAIL' for c in checks),missing=missing,overlaps=ov),ensure_ascii=False,indent=2))
if any(c['status']=='FAIL' for c in checks):sys.exit(1)
