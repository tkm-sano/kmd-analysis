from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import csv,json,re,hashlib,html,sys,unicodedata
import xml.etree.ElementTree as ET
from sections import SECTIONS
sys.path.insert(0,'/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools/python')
import fitz
R=Path(__file__).resolve().parents[1];E=R/'evidence';P=R/'reports';checks=[]
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def ck(item,ok,detail):checks.append(dict(item=item,status='PASS' if ok else 'FAIL',detail=detail))
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).replace('−','-').replace('–','-')
binding=json.loads((E/'DATA_BINDING.json').read_text());ck('Saved-data checks',all(c['status']=='PASS' for c in binding['checks']),str(len(binding['checks']))+' data binding checks; no experiment/bootstrap rerun')
blocks=json.loads((R/'poster_layout.json').read_text());d=fitz.open(R/'poster.pdf');pg=d[0];mm=72/25.4
ck('A1 PORTRAIT one page',len(d)==1 and abs(pg.rect.width/mm-594)<.1 and abs(pg.rect.height/mm-841)<.1,f'{pg.rect.width/mm:.3f} × {pg.rect.height/mm:.3f} mm')
heads=[b['text'] for b in blocks if re.match(r'^[1-5] (目的|方法|結果|評価|議論)',b['text'])]
ck('Five explicit sections',len(heads)==5 and all(h.startswith(str(i)+' '+s) for i,(h,s) in enumerate(zip(heads,SECTIONS),1)),str(heads))
ck('All five sections have prose',all(any(norm(s)==norm(b['text']) for b in blocks) for ss in SECTIONS.values() for s in ss),'prose fields embedded as native text')
missing=[]
for i,b in enumerate(blocks):
 x,y,w,h=[b[k] for k in ['x_mm','y_mm','w_mm','h_mm']];clip=fitz.Rect((x-.6)*mm,(y-.6)*mm,(x+w+.6)*mm,(y+h+1)*mm)
 actual=pg.get_text('text',clip=clip)
 if norm(b['text']) not in norm(actual):missing.append(dict(i=i,text=b['text'],actual=actual))
ck('All PDF text present',not missing,f'{len(blocks)} blocks; missing {len(missing)}')
overlaps=[]
for i,a in enumerate(blocks):
 for j,b in enumerate(blocks[i+1:],i+1):
  dx=min(a['x_mm']+a['w_mm'],b['x_mm']+b['w_mm'])-max(a['x_mm'],b['x_mm']);dy=min(a['y_mm']+a['h_mm'],b['y_mm']+b['h_mm'])-max(a['y_mm'],b['y_mm'])
  if dx>.5 and dy>.8:overlaps.append((i,j,round(dx,2),round(dy,2)))
ck('No text overlaps',not overlaps,str(overlaps))
ck('All text within page',all(b['x_mm']>=0 and b['x_mm']+b['w_mm']<=594.01 and b['y_mm']>=0 and b['y_mm']+b['h_mm']<=841.01 for b in blocks),'portrait bounds')
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(R/'poster.pptx') as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));pres=ET.fromstring(z.read('ppt/presentation.xml'));sz=pres.find('p:sldSz',ns)
 ck('PPTX actual size',int(sz.get('cx'))==594*36000 and int(sz.get('cy'))==841*36000,str(sz.attrib))
 ck('Editable native poster',not root.findall('.//p:pic',ns) and len(root.findall('.//p:cxnSp',ns))>30,'text, shapes, table cells and connectors; no flattening')
for v in read(E/'SOURCE_SHA256.csv'):ck('Source preserved '+Path(v['path']).name,hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'],'pinned SHA256')
old=json.loads((R.parent/'run04/evidence/SYSTEM_STRUCTURE.json').read_text());new=json.loads((E/'SYSTEM_STRUCTURE.json').read_text())
for eid in ['rules_actors','actors_rules','actors_config','config_actors','rules_config','config_rules','quantum_config']:
 a=next(e for e in old['edges'] if e['id']==eid);b=next(e for e in new['edges'] if e['id']==eid);ck('Framework relation '+eid,all(a[k]==b[k] for k in ['source','target','status']),'same theoretical relation, rerouted')
# Main table values are mechanically formatted from the bound source CSV, not hand inferred.
table=read(E/'SCALE_METHOD_STATISTICS.csv')
text=(R/'poster_text.txt').read_text()
for a in table:
 digits=3 if a['config']=='MEAN_P2' else 1
 val=f"{float(a['mean_relative_percent']):.{digits}f}±{float(a['SD_relative_points']):.{digits}f}"
 ck('Printed mean/SD '+a['scale']+'/'+a['config'],val in text,val)
full=read(E/'CONFIG_INPUT_DISTRIBUTIONS.csv')
for cfg,val in [('MEAN_P2',0),('GROVER_P2',3963),('GROVER_P3',3965)]:
 a=next(z for z in full if z['config_id']==cfg and z['metric']=='delta_s');ck('Printed IQR '+cfg,round(float(a['q3'])-float(a['q1']))==val,'seconds, all460 input means')
ck('Updated sign convention','ΔJ=JQ−JC' in text and '正は主古典解JCに対する悪化' in text,'positive is worse, matching Step5')
ck('Material progress/HOLD separated','計算・検算済み（保存記録）' in text and 'HOLD：実用入力・完成パック' in text and binding['materials']['scientific_practical_adoption']=='HOLD','numerical completion is not practical adoption')
ck('Rejected effects/indicators excluded',all(t not in text for t in ['5.67%','0.413%','定時配達率','RIQ','M1','インタビュー']),'no reintroduction of rejected primary claims or methods')
for n in ['poster.svg','sociotechnical_structure.svg']:ET.parse(R/n)
ck('SVG valid',True,'portrait SVGs with native text')
(E/'VALIDATION.json').write_text(json.dumps(dict(checks=checks,missing=missing,overlaps=overlaps),ensure_ascii=False,indent=2))
with (E/'VALIDATION.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=checks[0]);w.writeheader();w.writerows(checks)
pg.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(0,128*mm,594*mm,328*mm)).save(R/'sociotechnical_structure_preview.png')
pg.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=fitz.Rect(10*mm,459*mm,584*mm,657*mm)).save(R/'render/results_check.png')
# Companion report: full precision, explicit data units and source roles.
style='body{font-family:sans-serif;max-width:1500px;margin:32px auto;padding:0 24px;color:#17232d;line-height:1.8}h1,h2{color:#143653}table{border-collapse:collapse;width:100%;font-size:13px;margin:18px 0}td,th{border:1px solid #bac6cf;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#edf3f7}.scroll{overflow-x:auto}a{color:#286a96}'
def page(name,title,body):
 (P/(name+'.html')).write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>'+style+'</style><body><p><a href="../index.html">成果物一覧</a></p><h1>'+html.escape(title)+'</h1>'+body+'</body></html>')
def tab(rs):
 return '<div class="scroll"><table><tr>'+''.join('<th>'+html.escape(str(k))+'</th>' for k in rs[0])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r.values())+'</tr>' for r in rs)+'</table></div>'
body=''
for i,(k,ss) in enumerate(SECTIONS.items(),1):body+='<h2>'+str(i)+' '+k+'</h2>'+''.join('<p>'+html.escape(s)+'</p>' for s in ss)
page('01_POSTER_PROSE','ポスターの説明文：目的・方法・結果・評価・議論',body)
(R/'poster_prose.txt').write_text('\n\n'.join(str(i)+' '+k+'\n'+'\n\n'.join(ss) for i,(k,ss) in enumerate(SECTIONS.items(),1)))
body='<p>ΔJ=JQ−JC、相対差=100ΔJ/JCであり、負が改善、正が悪化である。入力ごと・設定ごとに保存測定10反復を平均し、同じ規模・設定の入力を等重みで集計した。10反復は同じ学習fitに対する測定反復であり、10独立学習ではない。保存B系列は460入力・8設定・3680fit・36800最良候補で、需要群25・親入力26の構造を持つ。36800を独立標本数として推論しない。</p>'
body+='<p>紙面は相対差の平均［%］±入力間標準偏差［ポイント］を表示する。SDは平均の標準誤差や信頼区間ではない。限定5設定と隣接1設定は平均・SD・中央値・四分位の数値が各々一致することを照合した。6設定を一つの母集団効果へプールした列ではない。</p><h2>方式・規模別の全記述量</h2>'+tab(table)
body+='<p>中央値、IQR、P5/P95は入力間分布の記述であり、母平均の信頼区間ではない。P5/P95は中央90%のデータ範囲の端点である。相対差の入力平均と平均移動時間同士の比は異なる指標である。全8設定を混ぜた平均をGM-QAOA一般の性能として提示しない。</p><h2>設定別の全460入力分布</h2>'+tab(full)
selected=[r for r in read(E/'IMPROVED_EQUAL_WORSENED.csv') if r['level'] in ['all_plans','by_config']]
body+='<h2>改善・目的値一致・悪化の記述内訳</h2>'+tab(selected)+'<p>一致は保存有理数目的値の一致であり、統計的同等性の検証ではない。改善0件を一般の改善確率0と解釈しない。</p>'
page('02_PATH1_STATISTICS','経路1：集計単位・差の分布・改善内訳',body)
interval=read(E/'SAVED_RESAMPLING_SENSITIVITY.csv')
body='<p>以下は既存Step2の保存区間を再表示したものである。新しいbootstrapは実行していない。旧ΔJ=JC−JQから最新Step5のJQ−JCへ、点推定の符号と上下端を反転した。全112行の点推定をStep5の入力平均と照合した。</p><p>GROUP_RESAMPLING_SENSITIVITY_NOT_REAL_FLEET_CIは需要群の構造を保つ補助感度区間、MEASUREMENT_RESAMPLING_FIXED_INPUT_FITは入力・学習状態を固定した測定の再標本化である。どちらも実配送母集団や未見入力の信頼区間として用いない。零改善の再標本化で得たゼロ区間も未知の改善確率0を証明しない。</p>'+tab(interval)
body+='<p>学習初期値による再現性は既存の3診断入力・97学習開始点などの別実験として扱う。全460入力に対する複数学習開始の効果、共通予算/出力数の公平比較、実機、全工程時間とHは未検証である。</p>'
page('03_RESAMPLING_SCOPE','保存再標本化区間と、その解釈範囲',body)
ex=binding['existence'];existrows=[dict(区分='改善解存在：強い参照証拠',入力数=ex['strong_better'],意味='再列挙・DP・独立有理数双対の証拠に基づく'),dict(区分='改善解存在：条件付き証拠',入力数=ex['conditional_better'],意味='保存MIP等値証拠、外部証明未了'),dict(区分='古典解＝参照',入力数=ex['greedy_equal'],意味='現在の比較で改善余地が確認されない'),dict(区分='全問題最適値未証明',入力数=ex['unproved'],意味='改善解不存在として数えない')]
page('04_CANDIDATE_EXISTENCE','候補の存在と取得を区別する',tab(existrows)+'<p>限定交換支持では全460入力で支持内最小＝初期解≥主greedyである。全順列支持では別の参照証拠で改善可能性を判定する。不存在と未証明、支持内最小と全問題最適値を混同しない。保存候補の主対照超えが0件であることだけから、取得失敗の単一原因を特定しない。</p>')
M=Path('/home/takuma/kmd-analysis/review_outputs/t08_t09_final_adoption_20261105')
progress=[dict(区分='計算・検算完了（保存記録）',内容='T09既存183設計行の既知小計を再現し、追加感度と相殺・逆転境界を評価した。基準側固定・変更側一要因と電圧/利用率条件を区別する。',出典=str(M/'FINAL_REPORT_JA.md')),dict(区分='数値出力の規模',内容=f"239質量条件、T08→DC105800計算行。設計格子・計算行数であり独立実験標本数ではない。460軌跡×2Crrも920独立走行実験ではない。",出典=str(M/'evidence/RUN_RESULT.json')),dict(区分='入力の科学的採用HOLD',内容='逆算容量の初回/full-cell適格性、他材料・製品からの移用、実担持/空隙等は未確定。計算モデルの条件付き実行許可と実用採用を分ける。',出典=str(M/'data/PARAMETER_ADOPTION.csv')),dict(区分='完成パック・実車HOLD',内容='未知外装・タブ・余白・構造・熱/BMS等をNULLに保持する。T09完成質量・絶対DC・実用出力/寿命/安全・量子帰属を確定しない。',出典=str(M/'FINAL_REPORT_JA.md'))]
body=tab(progress)+'<p>T08は簡略質量会計の主モデル、T09は面積・空隙・箔・膜・液を介する構造依存の補完である。T08固定部材をT09小計へ重ねず、活物質と塗工材を二重加算しない。bは同じ部材会計内の基準−変更後、δは会計外の変更後−基準［kg］、正味軽量化はb−δである。</p><p>追加の一要因比較は基準LP側を固定しS側を変える設計で、以前の両材料共通条件変更と同一ではない。fixed_area_LPの担持変更時はS側の設計基準面積も変わり得るため、全ケースで両材料面積が常に等しいとは書かない。数値再現PASSで既存T09対向条件FAILや道路受入FAILを解除しない。</p><p>密度±20%や追加q点などは仮想診断を含み、文献上の実現可能範囲ではない。入力間の物理的な独立変更可能性は未検証である。根拠のない確率分布・信頼区間を与えない。個別材料参照入力からの具体値は参考例に限定し、主たる量子材料効果率へ昇格させない。</p>'
body+='<h2>入力の採用台帳</h2>'+tab(read(E/'MATERIAL_PARAMETER_ADOPTION.csv'))+'<h2>感度範囲の来歴</h2>'+tab(read(E/'MATERIAL_SENSITIVITY_ORIGINS.csv'))+'<h2>科学的採用と検算の区別</h2>'+tab(read(E/'MATERIAL_FINAL_AUDIT.csv'))
page('05_PATH2_PROGRESS','経路2：追加解析の進捗と科学的HOLD',body)
page('06_REVIEW','表示・保全・データ整合性の確認',tab(checks)+'<p>全1ページを実際のPPTXからPDF化・レンダリングして確認した。新規の量子学習・solver・SUMO・材料実験・実車実験・社会調査・bootstrapは実行していない。実寸の試し刷りと独立した読者テストは未実施である。元データ・前版を保全し、commit/push/PR作成は行っていない。</p>')
links=[('poster.pptx','編集可能なA1縦ポスター'),('poster.pdf','実際のPPTXから出力したPDF'),('poster_preview.png','全体プレビュー'),('reports/01_POSTER_PROSE.html','目的・方法・結果・評価・議論の本文'),('reports/02_PATH1_STATISTICS.html','経路1：全精度の方式・規模別統計'),('reports/03_RESAMPLING_SCOPE.html','経路1：既存再標本化感度区間'),('reports/04_CANDIDATE_EXISTENCE.html','経路1：改善候補の存在と証拠強度'),('reports/05_PATH2_PROGRESS.html','経路2：追加解析・入力採用・HOLD'),('reports/06_REVIEW.html','表示・保全・整合性の確認'),('sociotechnical_structure.svg','社会技術システム図SVG'),('evidence/SCALE_METHOD_STATISTICS.csv','方式・規模別統計CSV'),('evidence/SAVED_RESAMPLING_SENSITIVITY.csv','保存感度区間CSV')]
(R/'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><title>A1縦：統計評価と材料解析進捗の改稿</title><style>'+style+'</style><body><h1>A1縦：経路1の統計評価・経路2の追加解析進捗</h1><p>594×841mm・全1ページ。目的、方法、結果、評価、議論と社会技術システムの関係図を維持した。経路1は入力単位の規模/方式別相対差・標準偏差・中央値/IQRと記述内訳を表示する。経路2は計算完了と実用入力/完成パックHOLDを分ける。</p><ul>'+''.join('<li><a href="'+a+'">'+html.escape(b)+'</a></li>' for a,b in links)+'</ul><p>再生成コードは元の作業環境・前版を参照する。PPTX内の図・表・文章はネイティブ要素として編集可能である。補足の区間・入力台帳を実配送・実材料への実証値と読まない。</p></body></html>')
print(json.dumps(dict(checks=len(checks),failed=sum(c['status']=='FAIL' for c in checks),text_blocks=len(blocks),missing=missing,overlaps=overlaps),ensure_ascii=False,indent=2))
if any(c['status']=='FAIL' for c in checks):sys.exit(1)
