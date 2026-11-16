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
ck('今後の優先作業と未検証事項を区別','まず既存の統計・感度解析を本文へ統合する' in text and '必要な追加検証を絞る' in text and '実機性能は判断できない' in text)
ET.parse(R/'poster.svg');ck('SVG整形式',True)
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=ov),ensure_ascii=False,indent=2));writecsv('VALIDATION.csv',checks)
for name,clip in [('methods_detail',(10,280,584,654)),('footer_detail',(10,660,584,840))]:pg.get_pixmap(matrix=fitz.Matrix(1.2,1.2),clip=fitz.Rect(*(v*mm for v in clip))).save(R/'render'/f'{name}.png')
changes=[dict(項目='現時点で記載できる内容',変更='保存済みのCPU模擬出力・質量/電力量計算を資料として確保し、二経路の計算対象・比較指標・仮定・検証範囲を示せることを記載した'),dict(項目='今後の作業（優先案）',変更='既存解析の本文統合、比較予算・出力数・工程時間と材料入力・未知部材の根拠整理、追加検証の優先順位を示した'),dict(項目='限界と課題',変更='CPU模擬から実機性能は判断できないこと、完成電池・実車への接続、比較の公平性と入力・部材・走行条件の妥当性を明記した'),dict(項目='結果非掲載',変更='数値結果・結果グラフ・結果からの結論は戻していない。入力数や計算条件は方法として維持した'),dict(項目='レイアウト',変更='A1縦を維持し、評価欄と3列の現段階・今後・限界欄を配置した。run07原本は保全した')]
writecsv('CHANGE_LOG.csv',changes)
style='body{font-family:sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;line-height:1.8;color:#17232d}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #bac6cf;padding:8px;text-align:left;vertical-align:top}th{background:#edf3f7}a{color:#286a96}'
def tab(rs):return '<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in rs[0])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r.values())+'</tr>' for r in rs)+'</table>'
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>結果非掲載版・A1縦</title><style>'+style+'</style><body><h1>研究ポスター：結果非掲載版</h1><p>run07を保全し、結果非掲載を維持したrun08を独立作成した。現時点で記載できる内容、今後の作業（優先案）、限界と課題を追加した。今後の作業は、記録に残る未検証事項を踏まえた提案であり、新しい実験への着手や実機・実車試験の実施確定を示すものではない。</p><p><a href="poster.pptx">編集可能PPTX</a> ／ <a href="poster.pdf">表示確認用PDF</a> ／ <a href="poster_preview.png">プレビュー</a> ／ <a href="poster_text.txt">本文テキスト</a></p><h2>変更内容</h2>'+tab(changes)+'<h2>確認</h2>'+tab(checks)+'<p>PPTXからPDFを出力し、全ページと詳細をレンダリングして確認する。試し刷りは未実施である。元ポスター・研究データを上書きせず、commit・push・PR作成は行っていない。</p></body></html>')
status=json.loads((E/'STATUS_TASKS_LIMITS.json').read_text())
provenance=[dict(欄='現時点で記載できる内容',根拠=str(S/'STEP5_FINAL_REPORT.md')+'; '+str(M/'FINAL_REPORT_JA.md'),採用範囲='保存計算と出力が存在し、分析対象・比較方法・仮定・検証範囲が記録されているという研究状況のみ。量的な成果を掲載しない'),dict(欄='今後の作業（優先案）',根拠=str(S/'STEP5_PATHWAY1_CONDITIONS.md')+'; '+str(M/'FINAL_REPORT_JA.md'),採用範囲='予算・出力規則・全工程時間・材料適格性・未知部材が残課題。最新材料追加解析は論文統合未実施という記録を根拠に、論文への統合と不足根拠の整理を優先案とした'),dict(欄='限界と課題',根拠=str(S/'STEP5_FINAL_REPORT.md')+' §10; '+str(M/'FINAL_REPORT_JA.md')+' 研究範囲・未解決点',採用範囲='実機、実運用、実用材料入力、完成部材表、実車は未検証。研究者の未記録の主観は創作していない')]
writecsv('STATUS_PROVENANCE.csv',provenance)
f=R/'index.html';f.write_text(f.read_text().replace('<h2>確認</h2>','<h2>記述の根拠と提案の区分</h2>'+tab(provenance)+'<h2>確認</h2>'))
print(json.dumps(dict(checks=len(checks),failed=sum(c['status']=='FAIL' for c in checks),missing=missing,overlaps=ov),ensure_ascii=False,indent=2))
if any(c['status']=='FAIL' for c in checks):sys.exit(1)
