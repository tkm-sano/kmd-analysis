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
 ck('編集可能な文章・図・グラフ',len(root.findall('.//p:pic',ns))==0 and len(root.findall('.//p:cxnSp',ns))>20,'図と棒・マーカー・誤差棒はネイティブ要素、画像への一枚化なし')
for v in read(E/'SOURCE_SHA256.csv'):ck('原本保全 '+str(Path(v['path']).relative_to(ROOT)),hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'])
ck('背景・目的・方法・評価・議論の対象を文章化',all(x in text for x in ['背景・目的','分析方法','4 評価項目','5 議論の対象']))
ck('旧指標と内部記号の再導入なし',all(s not in text for s in ['定時配達率','T08','T09','Controlled-DC','HOLD','支持集合','技術能力境界','RIQ']))
ck('未検証の社会関係図を削除','判断を方向付ける' not in text and '主体・制度・採用行動の分析は行っていない' in text)
ck('結果非掲載',all(x not in text for x in ['2.368','1.140','28,200','8,600','36,800','0.214','135入力','δ < b','相殺','悪化が大きい','結果','確認された','であった','符号が一致']))
ck('結果図を手順図へ変更',all(x in text for x in ['図2 同じ入力','図3 材料入力']))
ck('原研究の実施状況を結果未実施に改変しない','予定' not in text and '本研究は未実施' not in text)
ck('主本文18.5pt以上、図内15.5pt以上、参考文献14pt',min(b['font_pt'] for b in blocks)>=14,'主本文18.5〜22pt、見出し21〜39pt、図15.5〜26pt。実寸の試し刷りは未実施')

ET.parse(R/'poster.svg');ck('SVG整形式',True)
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=ov),ensure_ascii=False,indent=2));writecsv('VALIDATION.csv',checks)
for name,clip in [('methods_detail',(10,280,584,674)),('footer_detail',(10,680,584,840))]:pg.get_pixmap(matrix=fitz.Matrix(1.2,1.2),clip=fitz.Rect(*(v*mm for v in clip))).save(R/'render'/f'{name}.png')
changes=[dict(項目='結果と結果図',変更='総移動時間差グラフ、保存候補内訳、候補存在の実績、質量感度分布・数値を削除した'),dict(項目='結果からの結論',変更='相殺・逆転条件や比容量×利用率の条件を主張する記述を外し、議論する対象を示した'),dict(項目='方法の可視化',変更='古典解とCPU模擬候補の比較手順、材料入力から電力量への計算手順を新たに描いた'),dict(項目='方法の数値',変更='460入力、配送先数、20kWh、8192試行など、結果でなく分析設定を表す数値は維持した'),dict(項目='研究状況',変更='未掲載を未実施・未完了へ読み替えず、既存研究の実施状況は変更していない'),dict(項目='形式・保全',変更='A1縦594×841mmの編集可能PPTXと実際のレンダリングPDFを作成し、run06原本を保全した')]
writecsv('CHANGE_LOG.csv',changes)
style='body{font-family:sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;line-height:1.8;color:#17232d}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #bac6cf;padding:8px;text-align:left;vertical-align:top}th{background:#edf3f7}a{color:#286a96}'
def tab(rs):return '<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in rs[0])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r.values())+'</tr>' for r in rs)+'</table>'
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>結果非掲載版・A1縦</title><style>'+style+'</style><body><h1>研究ポスター：結果非掲載版</h1><p>run06を保全し、結果を掲載しないrun07を独立作成した。入力数や分析条件は方法として残し、数値結果・結果図・結果から導く結論を除いた。分析方法、評価項目、議論の対象を説明する版である。</p><p><a href="poster.pptx">編集可能PPTX</a> ／ <a href="poster.pdf">表示確認用PDF</a> ／ <a href="poster_preview.png">プレビュー</a> ／ <a href="poster_text.txt">本文テキスト</a></p><h2>変更内容</h2>'+tab(changes)+'<h2>確認</h2>'+tab(checks)+'<p>PPTXからPDFを出力し、全ページと詳細をレンダリングして確認する。試し刷りは未実施である。元ポスター・研究データを上書きせず、commit・push・PR作成は行っていない。</p></body></html>')
print(json.dumps(dict(checks=len(checks),failed=sum(c['status']=='FAIL' for c in checks),missing=missing,overlaps=ov),ensure_ascii=False,indent=2))
if any(c['status']=='FAIL' for c in checks):sys.exit(1)
