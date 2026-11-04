from pathlib import Path
import json,hashlib,collections,re,subprocess,time,platform,sys
import pandas as pd
from docx import Document
from lxml import etree
O=Path(__file__).resolve().parents[1];R=O.parents[1];t0=time.perf_counter();checks=[]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ck(n,v,d=''):checks.append(dict(check=n,status='PASS' if v else 'FAIL',detail=str(d)));assert v,(n,d)
def md(n,t):(O/n).write_text(t.strip()+'\n')
required='SOURCE_THESIS_AUTHORITY.md ORIGINAL_THESIS_STRUCTURE.csv CHAPTER_SECTION_MAPPING.csv CONTENT_PRESERVATION_PLAN.md SOURCE_BASELINE_SHA256.csv CLAIM_ADOPTION_REVIEW.csv STEP3_TO_THESIS_EVIDENCE_MATRIX.csv REJECTED_OR_DEFERRED_CLAIMS.md CHEN_REFERENCE_USAGE_AUDIT.md LITERATURE_REVIEW_REVISED.md LITERATURE_EVIDENCE_MATRIX.csv RESEARCH_GAP_REVISED.md BACKGROUND_ARGUMENT_MAP.md BIBLIOGRAPHY_VERIFICATION.csv THESIS_REVISED_OUTLINE.md RQ_CHAPTER_ALIGNMENT.csv ORIGINAL_TO_REVISED_SECTION_MAP.csv THESIS_STEP4_INTEGRATED_TRIAL.docx THESIS_STEP4_INTEGRATED_TRIAL.pdf THESIS_FULL_TEXT.md THESIS_INTEGRATION_CHANGELOG.md THESIS_PRESERVED_CONTENT_AUDIT.csv FIGURE_TABLE_REGISTER.csv SECTION_CLAIM_EVIDENCE_MAP.csv NUMERICAL_INTEGRITY_AUDIT.csv STATISTICAL_INTERPRETATION_AUDIT.md FIGURE_TABLE_AUDIT.csv CITATION_AUDIT.csv WORD_COMPATIBILITY_HOLD.md STEP4_ACADEMIC_REVIEW.md THESIS_CHANGE_ADOPTION_MATRIX.csv RESEARCH_CONTRIBUTION_REVIEW.md ORIGINAL_VS_TRIAL_COMPARISON.md STEP5_HANDOFF.md README.md EXECUTIVE_SUMMARY.md STEP4_COMPLETION_MATRIX.csv UNRESOLVED_ITEMS.md'.split()
for n in required:ck('required '+n,(O/n).is_file() and (O/n).stat().st_size>0)
old=Document(O/'sources/BASELINE_THESIS.docx');new=Document(O/'THESIS_STEP4_INTEGRATED_TRIAL.docx');s=pd.read_csv(O/'ORIGINAL_THESIS_STRUCTURE.csv',keep_default_na=False);l=pd.read_csv(O/'THESIS_PRESERVED_CONTENT_AUDIT.csv')
ck('935 source blocks mapped once',len(s)==935 and len(l)==935 and l.block_id.is_unique and set(s.block_id)==set(l.block_id))
# All meaningful original paragraphs and tables must remain as exact text runs plus original mathematics.
get=lambda el:''.join(el.xpath('.//w:t/text() | .//m:t/text()'))
a=collections.Counter(get(el) for el in old._element.body if get(el));b=collections.Counter(get(el) for el in new._element.body if get(el));missing=a-b
ck('all meaningful source body texts retained',not missing,dict(missing))
def mathhash(el):
 def node(x):return (etree.QName(x).localname,tuple(sorted((etree.QName(k).localname,v) for k,v in x.attrib.items() if not etree.QName(k).localname.startswith('rsid'))),x.text or '',tuple(node(c) for c in x))
 return hashlib.sha256(repr(node(el)).encode()).hexdigest()
a=collections.Counter(map(mathhash,old._element.xpath('.//m:oMath')));b=collections.Counter(map(mathhash,new._element.xpath('.//m:oMath')));ck('all 86 original OMML semantically retained',sum(a.values())==86 and not a-b)
import zipfile
with zipfile.ZipFile(O/'sources/BASELINE_THESIS.docx') as z:a=collections.Counter(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
with zipfile.ZipFile(O/'THESIS_STEP4_INTEGRATED_TRIAL.docx') as z:b=collections.Counter(hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
ck('all original media bytes retained',not a-b,{'source_media':sum(a.values()),'output_media':sum(b.values())})
ck('all 27 source tables plus seven new',len(old.tables)==27 and len(new.tables)==34)
ck('19 source images plus seven new',len(old.inline_shapes)==19 and len(new.inline_shapes)==26)
ck('empty-layout deletion only',s[s.block_id.isin(l[l.category=='D'].block_id)].text.eq('').all() and len(l[l.category=='D'])==88)
starts=new._element.xpath('.//w:bookmarkStart/@w:name');ck('unique bookmark names',len(starts)==len(set(starts)))
ids=new._element.xpath('.//wp:docPr/@id');ck('unique drawing IDs',len(ids)==len(set(ids)))
# Current text is scoped before the historical appendix; no silent scan of legacy text as current claims.
main=[]
for p in new.paragraphs:
 if p.text=='付録B　元原稿の保全記録':break
 main.append(p.text)
text='\n'.join(main)
for term in ['量子技術がEV配送システムに寄与する条件','36,800','正改善は0','414','46','41','58/97','78/97','H_plan','条件付き参考','未採用','1000','1250','完成pack']:
 ck('retained current policy/numeric '+term,term in text)
ck('RQI retained; no independent RQ3', 'RQIは' in text and 'RQ3を新設した' not in text)
c=pd.read_csv(O/'CLAIM_ADOPTION_REVIEW.csv');ck('31 scientific/adoption separated',len(c)==31 and c.claim_id.is_unique and c.adoption_recommendation.value_counts().to_dict()=={'B':23,'C':6,'A':2} and c.formal_adoption.eq('NOT_DECIDED').all())
loc=pd.read_csv(O/'SECTION_CLAIM_EVIDENCE_MAP.csv');ck('all31 have actual current paragraph locator',set(loc.claim_id)==set(c.claim_id) and loc.locator_status.eq('PASS').all())
for col in ['source','analysis_code','execution_log']:ck('trace actual files '+col,all(Path(x).is_file() for x in loc[col]))
n=pd.read_csv(O/'NUMERICAL_INTEGRITY_AUDIT.csv');ck('27 numerical rechecks pass',len(n)==27 and n.status.eq('PASS').all())
reg=pd.read_csv(O/'FIGURE_TABLE_REGISTER.csv');ck('all 60 figure/table elements catalogued',len(reg)==60 and reg[reg.type=='figure'].shape[0]==26 and reg[reg.type=='table'].shape[0]==34)
ck('current figure/table IDs unique',reg[reg.scope=='current'].id.is_unique)
pa=json.loads((O/'render/PAGE_AUDIT.json').read_text());run=json.loads((O/'render/RENDER_RUN.json').read_text());ck('all114 pages exported',len(pa)==run['pages']==114 and all((O/p['image']).is_file() for p in pa));ck('no replacement characters',all(p['replacement_characters']==0 for p in pa));ck('outside page blocks zero',run['outside_page_blocks']==0);ck('PDF matches final DOCX build',(O/'THESIS_STEP4_INTEGRATED_TRIAL.pdf').stat().st_mtime>(O/'THESIS_STEP4_INTEGRATED_TRIAL.docx').stat().st_mtime)
mp=pd.read_csv(O/'render/TOC_PAGE_MAP.csv');ck('all chapter/appendix entries mapped',len(mp)==10 and mp.page.tolist()==sorted(mp.page.tolist()) and mp[mp.bookmark=='s4_refs'].page.iloc[0]==25)
# Reopen final PDF, compare rendered body figure/table captions, not the Word source alone.
txt=(O/'render/TEXT.txt').read_text();ck('PDF key numerics and captions present',all(k in txt for k in ['36,800','414','58/97','78/97','図4-1','図5-3','表5-2']))
ci=pd.read_csv(O/'CITATION_AUDIT.csv');ck('all47 source/citation review entries retained',len(ci)==47 and ci.reference_id.is_unique);co=pd.read_csv(O/'CITATION_OCCURRENCES.csv');ck('all detected citation identities match or explicitly held',not co.status.eq('HOLD_NO_UNIQUE_MATCH').any())
# End-to-end original preservation, including external primary input files.
base=pd.read_csv(O/'SOURCE_BASELINE_SHA256.csv');tracked=pd.read_csv(O/'evidence/TRACKED_BASELINE.csv');pres=[]
for label,df in [('source',base),('tracked',tracked)]:
 for x in df.to_dict('records'):
  p=Path(x['path']);h=sha(p) if p.is_file() else '';pres.append(dict(scope=label,path=str(p),baseline_sha256=x['sha256'],final_sha256=h,status='PASS' if h==x['sha256'] else 'FAIL'))
pd.DataFrame(pres).to_csv(O/'evidence/SOURCE_PRESERVATION_RESULTS.csv',index=False);ck('all source and tracked bytes unchanged',all(x['status']=='PASS' for x in pres),len(pres))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();ck('HEAD unchanged',head==json.loads((O/'evidence/START.json').read_text())['head']);ck('tracked diff unchanged',subprocess.check_output(['git','diff','--binary'],cwd=R)==(O/'evidence/GIT_DIFF_START.patch').read_bytes())
pd.DataFrame(checks).to_csv(O/'evidence/FINAL_CHECKS.csv',index=False)
# Honest visual review scope and retained layout limitations.
visual=[]
for p in pa:visual.append(dict(page=p['page'],contact_sheet='contact_'+str((p['page']-1)//12+1).zfill(2)+'.png',review='CONTACT_SHEET_ALL_PAGES',enlarged=p['page'] in [13,18,109],finding='no detected overlap/cropping; some intentional short pages',status='PASS_WITH_WORD_HOLD'))
pd.DataFrame(visual).to_csv(O/'render/VISUAL_PAGE_REVIEW.csv',index=False)
md('DOCX_PDF_VISUAL_AUDIT.md','''# DOCX/PDF表示監査
最終PDF114ページ全体を10枚のcontact sheetで確認し、方法・T09数式の13頁、主分析と参考例を分けた18頁、長表の109頁を拡大確認した。初回はコピー元のexact行間により文字の重なりを検出し、trial内の段落間隔へ自動行間を設定した。原文字列・OMML・画像は保持した。
目次の「参考文献」を目次ページ自身と誤認する初回処理を修正し、実際の章開始ページを使った。固定目次10項目のページは再レンダリング後も一致する。図の内部番号を現行章番号に揃え、保存図の旧番号とは範囲を分けた。
最終版のページ領域外テキストblockは0、置換文字0。元19画像と86数式が構造上残り、新7図の画像とcaptionも表示される。長表は幅を縮小し行分割を許可した。接触シートの目視で切断・文字重なり・欠落は検出しなかった。5頁の序論末尾、21頁の参考表等、章開始を固定したことによる余白の多いページは残る。提出版の組版最適化はStep5の対象である。
Microsoft Word実機は利用していない。代替フォント、Wordでの数式/改頁、自動目次・相互参照の最終確認はHOLDである。数式や書誌の内容が正しいという判断を、レンダリング成功だけで代替しない。
''')
md('REPRODUCIBILITY_REPORT.md','''# 再現性と環境
Pythonは既存.conda/bin/python3.11を-B付きで使用した。研究コード・既存環境を変更せず、全スクリプトをtrial/scriptsに保存した。新たな大規模実験は行っていない。
再実行は別の一意な新規trialへscriptsをコピーし、開始時にSTART/Git状態/追跡SHA台帳を作ってから、inventory.py → literature_audit.py → finalize_literature.py → review_claims.py → write_content.py → figures_step4.py → build_thesis.py → render_thesis.py → write_audits.py → add_verifications.py → final_audit.pyの順で行う。現行の元原稿・旧trialを上書きしない。
write_content後には3.6の古典主対照に、run_cpu_matched_classical_swaps.pyで確認した隣接降下・乱数摂動・soft CPU cap・incumbent保持の説明を加えた。最終drafts/が実際の文章版であり、生成スクリプトの初期草稿だけを再現最終版としない。DOCXの生成はこの最終drafts/を入力にする。源文章版のhashは出力台帳に記録する。
図の再生成はdata/PATH2_SENSITIVITY_SUMMARY.csvとCROSS_PATH_CONDITION_MATRIX.csvをStep3からコピーし、三つのFIGURES出力ディレクトリを作った上でfigures_step4.pyを実行する。編集済みの章番号を画像内へ反映した。図データは元CSVを変更していない。
表示は既存LibreOffice24.2.7.2バイナリを読み取り専用で使用し、profile/cacheはtrial内に作った。DOCXからPDFへ二回変換し、章ページを照合して固定目次を更新する。全ページPNG/contact sheetはrenderに保存する。Word実機の表示は未確認である。
源の一部は外部保全領域にあり、このtrialだけで原地理データから実験全体を再生成できるとはしない。書誌照合のHTTP失敗・確認範囲は原ログを参照する。Step5では採否、文献の全文確認範囲、保存付録の提出形態を別途判断する。
''')
summary=dict(status='TRIAL COMPLETE',scientific_status='CONDITIONAL; HOLD and inherited FAIL retained',pages=114,figures=26,tables=34,original_OMML_retained=86,new_figures=7,new_tables=7,source_blocks=935,preserved_main=53,preserved_appendix=794,layout_only_omitted=88,claims=31,adoption={'A':2,'B':23,'C':6},numerical_checks=27,final_checks=len(checks),failures=0,source_files=len(base),tracked_files=len(tracked),preservation_records=len(pres),wall_s=time.perf_counter()-t0)
(O/'evidence/FINAL_RUN.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
report=f'''# Step4最終監査報告
総合実行判定はTRIAL COMPLETEである。研究者の正式採用や修士論文の承認を意味しない。科学的な主張はCONDITIONALを含み、HOLD・既存FAILを維持する。
基準版は11月3日統合のtmp_RsrchMstrDc_1026_results_integrated.docx、SHA256 53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99fである。7候補を来歴・内容・保全性で比較し、正式版の権威を独断認定せず内容基準に限定した。
Task4-1〜4-7を実施した。元935blockは53を本文、794を保存付録、88の無内容空段落だけ省略した。元86OMML、27表、19画像は全て構造・テキスト/画像byteで確認した。新7図7表を追加し、最終114ページ、26画像・34表となった。現行本文と参考文献/付録Aは1〜27頁、保存付録Bは28頁からである。旧内容の保全と現在の科学的採用を区別した。
31主張はA2/B23/C6の採用推奨であり、科学的判定と別軸である。主greedyへの正改善0/36,800、mirror支持460、3診断の9,312fit/93,120測定、58/97対78/97、R5/p2の平均−5,983.7秒/入力間SD1,314.4秒（70入力）、414/46/41、限定CPUscopeを反映した。予算・出力規則の差を残し、一般の量子不可能性やQPU性能へ拡張しない。
経路2は連続入力の解析感度、一般b−δ境界と材料非依存DC応答（460対応軌跡×2Crr、1000〜1250kg）を主とした。Chen逆算入力と5.448297kg/.877094/3.193156V/約0.413%、T09具体差は参考例である。完成pack、量子材料、実EVの改善を結果に含めない。
文献は47審査項目を記録し、現行の20項目の比較台帳は15の限定的原著確認と5の書誌/確認範囲告知を区別する。元本文・付録と現行草稿の著者年引用を照合した。書誌実在確認を全文精読とせず、未確認の旧引用はHOLD。PapachristosのFutures候補は実在を確認したが元引用意図を確定せず自動置換しない。調査文献に存在するEVの統合研究を認め、先例不存在を研究ギャップにしない。
独立の軽量数値再検算27件と最終整合検査{len(checks)}件は全PASSである。同一エージェントの分離工程であり第三者査読ではない。PDF全114頁の接触シート確認と代表頁拡大を実施し、初回行重なり/目次誤認を修正した。最終領域外block0、置換文字0。Word実機、大学提出様式、自動目次/引用・相互参照の最終整形はHOLDである。
残る事項は46厳密証明、41外部証明、H_plan/総時間/QPU、旧方式の予算統制、材料full-cell適格性、未知BOM、実車・実道路・量子→実材料、需要/地理の完全再生成、未確認書誌/原意図である。旧道路受入FAILとT09_ROW183対向FAILを消去しない。未限定の改善/量子優位/完成pack等の7候補解釈はDとして棄却した。最終主論証に未修正の同種FAILを採用しない。
保全対象{len(base)}源ファイルと追跡{len(tracked)}ファイルのSHA256は開始終了で一致した。HEADとtracked diffも不変である。元データ・既存コード・正式側原稿・Step1〜3を変更していない。commit/push/公開/正式原稿反映は行っていない。
Step5では正式採否、文献精読と引用原意図、保存付録を含む提出形態、Word実機・大学体裁を優先する。今回の成果物は独立したStep4 trialであり、正式採用は未決定である。
'''
md('FINAL_AUDIT_REPORT.md',report)
(O/'evidence/ENVIRONMENT.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform()),indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
