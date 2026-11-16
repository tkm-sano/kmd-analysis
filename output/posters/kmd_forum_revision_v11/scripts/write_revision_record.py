from pathlib import Path
import csv,json,hashlib,shutil,re,unicodedata
O=Path(__file__).resolve().parents[1];R=O.parents[2]
OLD=R/'output/posters/kmd_forum_language_audit_v10'
a=json.loads((OLD/'evidence/LAYOUT.json').read_text());b=json.loads((O/'evidence/LAYOUT.json').read_text())
oldtables={t['tag']:t for t in json.loads((OLD/'evidence/TABLES.json').read_text())};newtables={t['tag']:t for t in json.loads((O/'evidence/TABLES.json').read_text())}
newbytag={x['tag']:x for x in b};changes=[]
def oldfind(needle):
 matches=[x['text'] for x in a if needle in x['text']]
 assert matches,needle
 return matches[0]
def add(location,before,after,basis):changes.append(dict(location=location,before=before,after=after,basis=basis))
for needle,tag in [('量子技術が物流の配送計画に及ぼす影響','title'),('大田区の単一拠点を想定した','subtitle'),('研究の問い','question_heading'),('出発前に使える時間の中で','question')]:
 add(tag,oldfind(needle),newbytag[tag]['text'],'今回の掲載対象に合わせた指定文言。研究全体のRQは変更しない。')
add('scope',oldfind('通常の計算機だけで計画を作る方法')+'\n'+oldfind('対象は配送先への車両の割当て'),newbytag['scope']['text'],'今回のB系列は1台の訪問順比較。複数台割当て・採用判断・実配送成果を今後に位置づける。')
for sec,newtitle in [('01','01  対象と計算条件'),('02','02  評価の流れ'),('03','03  QAOAの計算手順'),('04','04  実験条件と比較結果'),('05','05  今後の検証')]:
 before=next(x['text'] for x in a if x['text'].startswith(sec+'  '));after=next(x['text'] for x in b if x['text'].startswith(newtitle))
 add('section:'+sec,before,after,'指定の見出しに変更。実施済みと今後を区別する。')
oldnodes={x['key']:x for x in json.loads((OLD/'evidence/DIAGRAM_NODES.json').read_text())};newnodes={x['key']:x for x in json.loads((O/'evidence/DIAGRAM_NODES.json').read_text())}
for key,n in newnodes.items():
 if oldnodes[key]['text']!=n['text']:add('node:'+key,oldnodes[key]['text'],n['text'],'図の接続構造を維持しラベルを改訂。q_bestの順序はDEFINITION_DECISIONS.json参照。')
for tag in ['pipeline_intro','adoption_rule','future_outcomes','qaoa_intro','qaoa_scope','result_metric','result_description','result_notes','comparison_limits','model_heading','model_schematic','model_objective']:
 if tag in newbytag:
  # Prior tags retained in v10 where available; otherwise the source block is identified semantically.
  oldbytag={x['tag']:x for x in a}
  fallback={'pipeline_intro':'配送先・荷物量・道路の移動時間を共通','adoption_rule':'採用条件案：','future_outcomes':'候補がない場合や移動時間が基準以上','qaoa_intro':'QAOAは、量子状態の波のずれ','qaoa_scope':'pは操作の組の回数','result_metric':'結果：Jは往復の総移動時間','result_description':'差の中央値0秒','result_notes':'差の中央値0秒','comparison_limits':'計算に使える時間と','model_heading':'単一拠点から配送先を回って帰る','model_schematic':'A～Cは説明用の配送先','model_objective':'往復の総移動時間 J'}
  if tag in oldbytag:before=oldbytag[tag]['text']
  else:before=oldfind(fallback[tag])
  add(tag,before,newbytag[tag]['text'],'保存実験資料に照合。作業中の注記や未確認の定義はポスターに記載しない。')
# Keep exact before/after rows, including original decimals and removed cells.
for tag in ['conditions','execution','results']:
 add('table:'+tag,'\n'.join(' | '.join(r) for r in oldtables[tag]['rows']),'\n'.join(' | '.join(r) for r in newtables[tag]['rows']),'全セルを原PDF・編集元PPTXと照合。元数値はORIGINAL_NUMERIC_VALUES.jsonに保持。')
capacity=next(r for r in oldtables['conditions']['rows'] if '216' in ' '.join(r))
add('conditions:capacity',' | '.join(capacity),'積載上限の数値行を省略','DEFINITION_DECISIONS.json：積載上限の単位・換算基準')
add('future', '\n'.join(json.loads((OLD/'evidence/FUTURE_ITEMS.json').read_text())), '\n'.join(' | '.join(r) for r in newtables['future']['rows']), '6項目を目的別5行の表に統合。期限内配達率の名称と定義はB系列の根拠を確定できないため省略。')
with (O/'evidence/REVISION_LOG.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=['location','before','after','basis']);w.writeheader();w.writerows(changes)
num=json.loads((O/'evidence/ORIGINAL_NUMERIC_VALUES.json').read_text());numeric=[]
for i,g in enumerate(num['groups']):
 newrow=newtables['results']['rows'][i+1]
 for col,key in [(2,'classical_mean_s'),(3,'candidate_mean_s'),(4,'delta_mean_s')]:
  val=float(g[key]);numeric.append(dict(group=g['poster_group'],metric=key,original_unrounded=g[key],v10_display=(f'+{val:,.3f}' if col==4 else f'{val:,.3f}'),v11_display=newrow[col],rule='round original value to one decimal, never subtract rounded displayed means'))
g=num['overall'];newrow=newtables['results']['rows'][-1]
for col,key in [(2,'classical_mean_s'),(3,'candidate_mean_s'),(4,'delta_mean_s')]:
 val=g[key];numeric.append(dict(group='all8',metric=key,original_unrounded=repr(val),v10_display=(f'+{val:,.3f}' if col==4 else f'{val:,.3f}'),v11_display=newrow[col],rule='round original value to one decimal, never subtract rounded displayed means'))
with (O/'evidence/NUMERIC_DISPLAY_AUDIT.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
v=json.loads((O/'evidence/VALIDATION.json').read_text());sourcechecks=json.loads((O/'evidence/SOURCE_CHECKS.json').read_text());definitions=json.loads((O/'evidence/DEFINITION_DECISIONS.json').read_text())
review=dict(whole_page=str(O/'poster_preview.png'),sections=[dict(section=n,image=str(O/'render'/f'section_{n}.png'),reviewed=True) for n in ['top','01','02','03','04','05']],checks=['A1縦・1ページ','本文・表・数値の欠けと重なりなし','表の単位を見出し内で改行し対応を確認','図の矢印と1行ラベルを確認','破線枠と今後の表を未実施の評価として表示','36,800件の成り立ちを表示','元値を保持して表示のみ丸め','空行・注記記号・作業中のプレースホルダーなし'],method='PDFを全体および各セクションの画像にレンダリングし目視確認。文字回収・ページ寸法・重なりも検査。')
(O/'evidence/VISUAL_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
report=f'''v11 改訂・定義照合・表示確認の記録

完成ファイル
v11_KMD_Forum_量子技術と物流配送計画_A1縦_言語改訂.pptx
v11_KMD_Forum_量子技術と物流配送計画_A1縦_言語改訂.pdf

編集元と保全
対象のv10 PDFと対応するPPTX、生成スクリプトをrgで特定した。編集元はoutput/posters/kmd_forum_language_audit_v10/scripts/build_poster.pyである。同じNoto Sans JP、薄水色#DCEEF8、見出し文字#225F83、著者・所属情報を維持した。元のv10と実験資料を変更していない。原文はPDF抽出の空白・改行・全半角を正規化して照合した。対象確認前の一括置換は行わず、各セクションの本文と表を保存資料に照合して記述した。

主な変更
・題目、副題、冒頭を指示文に合わせ、研究全体のRQを変更せず「今回検証した問い」を総移動時間差に限定した。
・01で今回の1台の条件、離散的な6規模、QAOAが扱う配送先と探索範囲、Jの意味を記載した。
・02で総移動時間を比較した工程と、今後実施する採用・配送結果評価を明示した。採用規則は今後検証する規則として表示した。
・03の比喩を削除し、量子操作・古典計算によるパラメータ調整・候補抽出を示した。図の構造を維持し、最短候補の選択、条件確認、保存の順を保存実装に合わせた。最短は抽出候補内の最短である。
・04は実行内容の2列表と結果の5列表に変更した。入力→設定→調整→抽出→繰返し→保存の順で36,800件の成り立ちを示した。比較条件の説明は結果表の直下に移した。
・差の絶対値の平均列を除き、時間表示を小数第1位にした。元の集計値は保持し、表示値同士の引き算で差を作り直していない。
・05の6箇条書きを、目的別の5行の表に整理した。複数台の割当てと採用後の配送結果は今後の評価としている。

定義の採否
'''
for d in definitions:
 report+=f"・{d['topic']}：{d['decision']}\n"
report+='''
省略の扱い
積載上限の216PEは記録を確認できたが、この実験に対応した換算基準を確定できなかったため、条件表の数値行を省略した。積載上限の存在と保存計画への条件確認という独立に確認できる内容は残した。
今回のB系列は配送先固有期限を設けず、contractual_on_time_rateが全件空欄である。他系列の率や一般文献の分母を流用せず、期限内配達率の指標名・定義を今後の表も含めて省略した。最後の配送先の作業完了時刻と帰着時刻は、保存コードで定義を確認できたので残した。
完成ポスターには未確認・要確認等の注記、空行、空欄、参照先のない注記記号を残していない。

保存実験との対応
・review_outputs/quantum_ev_step5_20261105/data/B_PLAN_GAPS_36800.csv
・同B_INPUT_CONDITIONS_460.csv
・同STEP5_OBJECTIVE_GAP_ANALYSIS.md（B系列の解品質差の定量評価）
・同STEP5_OPERATIONAL_IMPACT.md（解品質差と配送運用成果）
・同scripts/analyze.py
・review_outputs/no_sumo_full_analysis_20261102/run01/B_PLAN_REFERENCES_36800.csv
・同B_RESOURCES_PER_FIT.csv、run_b.py、FROZEN_PROTOCOL.json、00_FROZEN_ANALYSIS_PROTOCOL.md
・外部保全ディレクトリ/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputsのstaged_qaoa_validation_20261102（mirror_family、grover_depth、active_adjacent_p3）のPROTOCOL.jsonとSOURCE_SNAPSHOT、cpu_matched_classical_swaps_r0_r5_20261101のPROTOCOL.jsonとSOURCE_SNAPSHOT。
Step5の掲載値に対応する比較基準はITERATED_GREEDY_ADJACENT_SWAPの保存結果である。no_sumoのclassical_initial列の比較値へ置き換えていない。460入力の保存NPZ、設定別・規模別の元測定記録、元CSVの対応キーとハッシュを照合した。新しい実験・道路計算・QAOA・シミュレーションを実行していない。

表示・成果物の検証
'''
report+=f'''・A1縦594×841mm、PPTX1枚・PDF1ページ。図・表・文字は編集可能である。
・表示の検査{len(v['checks'])}項目と、保存実験との照合{len(sourcechecks)}項目が合格した。
・全体と冒頭・01～05を画像化し、文字、単位、表の改行、矢印とラベル、読み順、今後の表示を目視確認した。
・文字欠落、ページ外へのはみ出し、文字・表セルの重なりを検出しなかった。図のラベルは全て1行である。
・本文を収めるために図を画像化したり、新しいグラフ・装飾を追加したりしていない。
・生成スクリプトはscripts/build_poster.py、書出しはscripts/render_poster.py、表示検査はscripts/validate_poster.pyである。

作業記録
・evidence/REVISION_LOG.csv：実際の元表現→修正後の表現（{len(changes)}記録）。
・evidence/DEFINITION_DECISIONS.json・csv：各定義の採否、根拠ファイルと該当行・列。
・evidence/ORIGINAL_NUMERIC_VALUES.json：元の精度を保持した数値。
・evidence/NUMERIC_DISPLAY_AUDIT.csv：元値・v10表示・v11表示の対応。
・evidence/SOURCE_MANIFEST.csv：保全対象と参照資料のSHA-256。
・evidence/VALIDATION.json・csv、VISUAL_REVIEW.json：表示と目視確認の記録。
'''
(O/'改訂記録と表示確認.txt').write_text(report)
stem='v11_KMD_Forum_量子技術と物流配送計画_A1縦_言語改訂';outputs=[]
for ext in ['pptx','pdf']:
 src=O/f'{stem}.{ext}';dst=R/src.name
 if dst.exists() and dst.read_bytes()!=src.read_bytes():raise RuntimeError(f'Conflicting file: {dst}')
 shutil.copyfile(src,dst);outputs.append(dict(path=str(dst),bytes=dst.stat().st_size,sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
for rel in ['改訂記録と表示確認.txt','scripts/build_poster.py','scripts/render_poster.py','scripts/validate_poster.py','evidence/REVISION_LOG.csv','evidence/DEFINITION_DECISIONS.json','evidence/NUMERIC_DISPLAY_AUDIT.csv','evidence/ORIGINAL_NUMERIC_VALUES.json','poster_preview.png']:
 p=O/rel;outputs.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'evidence/OUTPUT_MANIFEST.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2))
print(json.dumps(dict(revision_records=len(changes),outputs=outputs[:2],report=str(O/'改訂記録と表示確認.txt')),ensure_ascii=False,indent=2))
