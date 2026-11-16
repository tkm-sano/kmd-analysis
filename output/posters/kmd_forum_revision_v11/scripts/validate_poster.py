from pathlib import Path
import csv,json,re,unicodedata,hashlib,math
from collections import Counter
import pymupdf as fitz
from pptx import Presentation
from pptx.enum.dml import MSO_LINE_DASH_STYLE
O=Path(__file__).resolve().parents[1];R=O.parents[2];mm=72/25.4
stem='v11_KMD_Forum_量子技術と物流配送計画_A1縦_言語改訂'
P=Presentation(O/f'{stem}.pptx');D=fitz.open(O/f'{stem}.pdf');page=D[0];checks=[]
def ck(name,ok,detail=''):checks.append(dict(check=name,passed=bool(ok),detail=detail))
def norm(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t))
ck('one editable slide and one PDF page',len(P.slides)==len(D)==1)
ck('exact PPTX A1 portrait',P.slide_width==594*36000 and P.slide_height==841*36000)
ck('PDF A1 portrait',abs(page.rect.width/mm-594)<.02 and abs(page.rect.height/mm-841)<.02,[page.rect.width/mm,page.rect.height/mm])
layout=json.loads((O/'evidence/LAYOUT.json').read_text());tables={x['tag']:x for x in json.loads((O/'evidence/TABLES.json').read_text())}
text=(O/'evidence/POSTER_TEXT.txt').read_text();ntext=norm(text)
ck('four editable native tables',set(tables)=={'conditions','execution','results','future'} and sum(x.has_table for x in P.slides[0].shapes)==4)
ck('execution table has two columns',all(len(r)==2 for r in tables['execution']['rows']) and len(tables['execution']['rows'])==9)
ck('result table has five columns',all(len(r)==5 for r in tables['results']['rows']) and len(tables['results']['rows'])==5)
ck('future table has five purposes',all(len(r)==2 for r in tables['future']['rows']) and len(tables['future']['rows'])==6)
ck('no chart or rasterized text',not page.get_images() and not any(sh.has_chart for sh in P.slides[0].shapes))
missing=[];outside=[];overlap=[]
for b in layout:
 rect=fitz.Rect(b['x']*mm,b['y']*mm,(b['x']+b['w'])*mm,(b['y']+b['h'])*mm)
 read=page.get_text(clip=rect+(-2,-2,2,3))
 if norm(b['text']) not in norm(read):missing.append(dict(tag=b['tag'],expected=b['text'],rendered=read))
 if not page.rect.contains(rect):outside.append(b['tag'])
for i,a in enumerate(layout):
 ar=fitz.Rect(a['x'],a['y'],a['x']+a['w'],a['y']+a['h'])
 for b in layout[i+1:]:
  br=fitz.Rect(b['x'],b['y'],b['x']+b['w'],b['y']+b['h']);intersection=ar&br
  if not intersection.is_empty and intersection.width>.5 and intersection.height>.5:overlap.append([a['tag'],b['tag']])
ck('all text recovered within its box',not missing,dict(blocks=len(layout),missing=len(missing)))
ck('no intended boxes outside page',not outside,outside)
ck('no text or cell box overlap',not overlap,overlap)
oob=[b[:5] for b in page.get_text('blocks') if b[0]<-.5 or b[1]<-.5 or b[2]>page.rect.width+.5 or b[3]>page.rect.height+.5]
ck('all rendered glyphs within page',not oob,oob)
spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
ck('original blue and black text only',set(s['color'] for s in spans)=={0,int('225F83',16)})
ck('Noto Sans JP fonts embedded',all('NotoSansJP' in f[3] for f in page.get_fonts()))
accent=tuple(int(x,16)/255 for x in ['DC','EE','F8'])
colors=[v for d in page.get_drawings() for k in ['fill','color'] if (v:=d.get(k)) is not None]
chromatic=[c for c in colors if max(c)-min(c)>.001]
ck('original pale blue fill only',bool(chromatic) and all(max(abs(a-b) for a,b in zip(c,accent))<.006 for c in chromatic))
nodeinfo=json.loads((O/'evidence/DIAGRAM_NODES.json').read_text());edges=json.loads((O/'evidence/DIAGRAM_EDGES.json').read_text());byid={s.shape_id:s for s in P.slides[0].shapes}
ck('same nineteen editable diagram nodes',len(nodeinfo)==19)
ck('diagram structures retained',len(edges['model'])==4 and len(edges['pipeline'])==6 and len(edges['qaoa'])==9)
ck('single-line diagram labels',all('\n' not in n['text'] and '\n' not in byid[n['text_shape_id']].text for n in nodeinfo))
ck('all diagram shapes white with black outline',all(str(byid[n['shape_id']].fill.fore_color.rgb)=='FFFFFF' and str(byid[n['shape_id']].line.color.rgb)=='000000' for n in nodeinfo))
ck('all diagram labels black',all(str(run.font.color.rgb)=='000000' for n in nodeinfo for para in byid[n['text_shape_id']].text_frame.paragraphs for run in para.runs))
planned=[n for n in nodeinfo if n['planned']]
ck('future diagram nodes explicitly labelled and dashed',len(planned)==2 and all(n['text'].startswith('今後：') and byid[n['shape_id']].line.dash_style==MSO_LINE_DASH_STYLE.DASH for n in planned))
ck('QAOA parameter loop and extraction retained',any(e['source']=='q_update' and e['target']=='q_init' for e in edges['qaoa']) and any(e['source']=='q_fixed' and e['target']=='q_restate' for e in edges['qaoa']))
ck('best candidate selection precedes save',next(n['text'] for n in nodeinfo if n['key']=='q_best')=='最短候補を選び、条件確認して保存')
ck('no wave metaphor', '波のずれ' not in text)
ck('requested title and this-poster question',all(t in text for t in ['量子計算を用いた配送計画の比較評価','今回検証した問い','QAOAで生成した候補と古典手法の基準計画では、総移動時間にどの程度の差があるか。']))
ck('current scope is one vehicle visit order',all(t in text for t in ['今回の対象は、車両1台','採用後の配送結果は今後評価する']))
ck('no claim of current multi-vehicle assignment','今回の対象は配送先への車両の割当て' not in text and '複数台の配送へ拡張する' in text)
ck('no unconfirmed capacity quantity or on-time metric',all(t not in text for t in ['216','荷物相当','期限内配達率','parcel equivalent']))
ck('no intermediate placeholders or unresolved markers',all(t not in text for t in ['要確認','未確認','未定義','不明','定義の追記が必要','仮に','TBD','TODO','＊']))
ck('six customer sizes discrete without continuous range',norm('3・4・5・25・100・125か所') in ntext and '3～125' not in text)
ck('J excludes service and computation time','配達作業時間と計画の計算時間を含めない' in text)
ck('difference is objective minus objective','ΔJ＝J（QAOA候補）−J（基準計画）' in text)
ck('no equality of computation conditions claim',all(t not in text for t in ['公平な比較','同一条件での性能比較','量子計算は役に立たない','実際の配送が遅れた']))
ck('return origin is model origin',norm('モデル上の開始時刻から9時間（32,400秒）') in ntext)
ck('defined final delivery completion only','最後の配送先での配達完了時刻' in text)
ck('all references 1 through 6 retained',all(f'[{i}]' in text for i in range(1,7)))
ck('authors retained',all(t in text for t in ['佐野巧馬','慶應義塾大学大学院メディアデザイン研究科 修士2年','永山研究室・Q/est']))
ck('execution count composition explicit',all(norm(t) in ntext for t in ['460組 × 8設定 ＝ 3,680件','3,680件 × 10回 ＝ 36,800件','8,192回の候補抽出','同じパラメータを用い','同じ訪問順の重複']))
ck('comparison limitations directly below result table',next(b['y'] for b in layout if b['tag']=='comparison_limits')==tables['results']['y']+sum(tables['results']['heights'])+3)
ck('baseline initial retention and old budget preserved',all(t in text for t in ['古典手法は初期計画を最良候補に含む','QAOAは抽出候補を保存した','古典手法の計算時間上限は旧実験に基づき','今回の8設定とはそろっていない']))
expected=[['27,600','1,551.7','1,552.7','+1.0'],['4,600','1,551.7','3,317.7','+1,766.0'],['4,600','1,551.7','3,313.7','+1,762.0'],['36,800','1,551.7','1,993.5','+441.8']]
ck('all result display values match requested one-decimal table',[r[1:] for r in tables['results']['rows'][1:]]==expected)
orig=json.loads((O/'evidence/ORIGINAL_NUMERIC_VALUES.json').read_text());d=orig['overall'];gs=orig['groups']
newinput=(O/'evidence/POSTER_DATA.json').read_bytes();oldinput=(R/'output/posters/kmd_forum_language_audit_v10/evidence/POSTER_DATA.json').read_bytes()
ck('original unrounded source values kept byte for byte',newinput==oldinput and (O/'evidence/POSTER_RESULT_TABLE.csv').read_bytes()==(R/'output/posters/kmd_forum_language_audit_v10/evidence/POSTER_RESULT_TABLE.csv').read_bytes())
ck('display differences rounded from original group differences',all(expected[i][3]==f"+{float(g['delta_mean_s']):,.1f}" for i,g in enumerate(gs)))
ck('maximum difference rounded from original saved statistic',f"+{d['max_delta_s']:,.1f}秒" in text)
ck('exact equality definition with original counts',all(t in text for t in ['同等（保存値の差＝0）','28,200件','8,600件','0件']))
ck('absolute difference column removed',not any('絶対' in c for c in tables['results']['rows'][0]))
ck('mean and rounding note present',all(t in text for t in ['平均総移動時間','8設定を同じ重みで平均した','差は丸め前の値から算出','小数第1位']))
ck('main table and diagram typography legible',min(x['pt'] for x in layout if x['kind']=='cell' and not x['tag'].split(':')[1]=='0')>=17.5 and min(x['pt'] for x in layout if x['tag'].startswith('label:'))>=18.5)
emptycells=[(tag,i,j) for tag,t in tables.items() for i,r in enumerate(t['rows']) for j,c in enumerate(r) if not c.strip()]
ck('no empty table cells after omission',not emptycells,emptycells)
# Source v10 text is checked against the requested input PDF, allowing whitespace and width variants.
sourcepdf=fitz.open(R/'v10_KMD_Forum_量子技術と物流配送計画_A1縦_言語監査.pdf');sp=sourcepdf[0]
oldlayout=json.loads((R/'output/posters/kmd_forum_language_audit_v10/evidence/LAYOUT.json').read_text());oldmissing=[]
for b in oldlayout:
 rect=fitz.Rect([v*mm for v in [b['x'],b['y'],b['x']+b['w'],b['y']+b['h']]])
 if norm(b['text']) not in norm(sp.get_text(clip=rect+(-2,-2,2,3))):oldmissing.append(b['tag'])
ck('v10 original expressions verified against target PDF',not oldmissing,dict(blocks=len(oldlayout),missing=oldmissing))
sourcechanges=[]
for r in csv.DictReader((O/'evidence/SOURCE_MANIFEST.csv').open()):
 if hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()!=r['sha256']:sourcechanges.append(r['path'])
ck('all original files preserved',not sourcechanges,sourcechanges)
sourcechecks=json.loads((O/'evidence/SOURCE_CHECKS.json').read_text())
ck('frozen experiment audit passed',all(r['passed'] for r in sourcechecks),len(sourcechecks))
# Whole page and all five sections are rendered for visual review.
sections={'top':(12,0,582,118),'01':(12,117,582,282),'02':(12,283,582,399),'03':(12,400,582,538),'04':(12,539,582,717),'05':(12,720,582,815)}
for name,rect in sections.items():
 page.get_pixmap(matrix=fitz.Matrix(1.8,1.8),clip=fitz.Rect([z*mm for z in rect]),alpha=False).save(O/'render'/f'section_{name}.png')
result=dict(checks=checks,missing_text=missing,overlaps=overlap,page_mm=[page.rect.width/mm,page.rect.height/mm],outside_page=outside,glyphs_outside=oob,original_text_missing=oldmissing)
(O/'evidence/VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
with (O/'evidence/VALIDATION.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=['check','passed','detail']);w.writeheader();w.writerows(checks)
print(json.dumps(dict(checks=len(checks),failed=[c for c in checks if not c['passed']],missing=missing),ensure_ascii=False,indent=2))
if not all(c['passed'] for c in checks):raise SystemExit(1)
