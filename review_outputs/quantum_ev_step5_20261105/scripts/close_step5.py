from pathlib import Path
import json,hashlib,subprocess,datetime
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];E=O/'evidence';D=O/'data';s=json.loads((D/'SUMMARY.json').read_text());auto=json.loads((E/'FINAL_AUTOMATED_RESULT.json').read_text());science=json.loads((E/'SCIENCE_RESULT.json').read_text());nchecks=len(pd.read_csv(E/'NUMERICAL_CHECKS.csv'))
def write(n,t):(O/n).write_text(t.strip()+'\n')
def md(f):
 return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(str(x).replace('|','／').replace('\n',' ') for x in row)+' |' for row in f.itertuples(index=False,name=None)])
# Full rehash of start manifests; no existing research file is changed.
paths={}
for n in ['BASELINE_SHA256.csv','ANALYSIS_INPUT_SHA256.csv','SCIENCE_INPUT_SHA256.csv']:
 for x in pd.read_csv(E/n,keep_default_na=False).to_dict('records'):
  p=Path(x['path']);p=p if p.is_absolute() else R/p
  if str(p) in paths:assert paths[str(p)]['expected_sha256']==x['sha256']
  paths[str(p)]=dict(path=str(p),expected_sha256=x['sha256'],manifest=n)
results=[]
for x in paths.values():
 p=Path(x['path']);h=hashlib.sha256()
 if p.is_file():
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  digest=h.hexdigest()
 else:digest='MISSING'
 results.append(dict(**x,final_sha256=digest,status='PASS' if digest==x['expected_sha256'] else 'FAIL'))
pd.DataFrame(results).to_csv(E/'PRESERVATION_END_CHECK.csv',index=False);fails=[x for x in results if x['status']!='PASS'];assert all('/review_outputs/poster_causal_structure_revision_20261105/' in x['path'] and x['manifest']=='BASELINE_SHA256.csv' for x in fails),fails[:3]
# Detected updates are outside Step5 write scope. Preserve and disclose them, never revert them.
pd.DataFrame(fails).to_csv(E/'EXTERNAL_BASELINE_CHANGES.csv',index=False)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True);diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R);status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R,text=True)
(E/'GIT_STATUS_END.txt').write_text(status);(E/'GIT_HEAD_END.txt').write_text(head);(E/'GIT_DIFF_END.patch').write_bytes(diff)
start=(E/'GIT_STATUS_START.txt').read_text();prefix=str(O.relative_to(R))+'/'
filtered=lambda z:'\n'.join(l for l in z.splitlines() if prefix not in l)
assert head==(E/'GIT_HEAD_START.txt').read_text() and diff==(E/'GIT_DIFF_START.patch').read_bytes()
external_added=sorted(set(filtered(status).splitlines())-set(filtered(start).splitlines()));external_removed=sorted(set(filtered(start).splitlines())-set(filtered(status).splitlines()))
(E/'EXTERNAL_GIT_STATUS_CHANGES.json').write_text(json.dumps(dict(added=external_added,removed=external_removed),ensure_ascii=False,indent=2))
preservation=dict(files_verified=len(results),unchanged_files=len(results)-len(fails),external_baseline_changes=len(fails),research_input_failures=0,head_unchanged=True,tracked_diff_unchanged=True,non_step5_git_status_unchanged=filtered(start)==filtered(status),external_added_status_entries=len(external_added),external_removed_status_entries=len(external_removed),scope='baseline manifest plus every read analysis/science input; raw03_data inventory-only except used inputs; environment caches excluded');(E/'PRESERVATION_RESULT.json').write_text(json.dumps(preservation,ensure_ascii=False,indent=2))
issues=[
['F01','旧差の符号が依頼と逆','旧方法/図表/要旨/結論','候補−greedyへ統一し全36,800分数を旧差と逆符号照合','RESOLVED','NUMERICAL_CHECKS/FINAL_AUTOMATED_CHECKS'],
['F02','計画中央値と入力中央値の混同余地','4.2/全統計','0秒と7.473770秒、SD1459.379/622.305を別表示','RESOLVED','INPUT_UNIT_STATISTICS/GAP_DESCRIPTIVE_STATISTICS'],
['F03','平均相対率と平均J比の非同義性','3.8/4.2','22.243524%と28.471877%を分離','RESOLVED','RELATIVE_GAP_VS_RATIO_OF_MEANS'],
['F04','帰庫を配送完了と同一視する危険','4.5','最終帰路を除外してLを再構成。負差180件も保存','RESOLVED','OPERATIONAL_SUMMARY/B_PLAN_GAPS'],
['F05','共通上限遵守を契約定時率へ転用する危険','4.5/要旨/結論','モデル内100%両側と契約率NULLを分離','RESOLVED_SCOPE','S5-OP-02'],
['F06','存在と取得の混同','4.6/6.2','mirror不存在、全支持135+条件付41、238等値、46未証明を分離','RESOLVED_SCOPE','FULL_SUPPORT_EXISTENCE_BY_INPUT'],
['F07','Chen算術PASSを主材料採用に昇格する危険','5章/要旨/結論','主は記号感度と材料非依存DC。参考節はHOLD注記保持','RESOLVED_SCOPE','STEP4_EVIDENCE_DECISIONS'],
['F08','縮小後の新図の文字が小さい','図4-1〜4','実寸を想定したfigsize/文字サイズへ再生成、PDF代表頁を拡大確認','RESOLVED','scripts/refine_figures.py/render/page_017,019,020'],
['F09','同年Robinson Part I/IIの表記','2.4/参考文献','2008a=Part I、2008b=Part IIへ整形、内容HOLDは維持','RESOLVED_FORMAT','FINAL_AUTOMATED_CHECKS'],
['F10','PDF抽出でminus/arrowの順序がずれる','5.2/6.7','DOCXの字形を維持しPDF22/27頁を拡大目視。本文一致検査は当該字形を正規化','RESOLVED_RENDER_EXTRACTION','DOCX_PDF_PROSE_MATCH'],
['F11','Step5外の既存ポスターに開始後更新を検出','poster_causal_structure_revision_20261105','13ファイルのhash差と新規Gitエントリを記録。Step5は戻さず、研究入力と区別','EXTERNAL_CHANGE_RECORDED','EXTERNAL_BASELINE_CHANGES/EXTERNAL_GIT_STATUS_CHANGES'],
['H01','46最適値未証明/41外部証明未了','4.6/6.7','主greedy差は460全件使用可。最適gap等の断定を限定','HOLD_RESEARCH','Step4 P1-04/07'],
['H02','計画締切/全工程時間/QPU/実採用','3.11/4.6/6.7','不足数値を補作しない','HOLD_RESEARCH','Step4 P1-12/13'],
['H03','実材料/full-cell/未知BOM/実車','5/6.7','Chen入力適格性・完成pack・実車効果を断定しない','HOLD_RESEARCH','Step4 M-03/P2'],
['H04','旧引用原意図と原著未確認','2/参考文献/保存付録','Papachristos等を現行主結果の根拠から除外','HOLD_SUBMISSION_SCOPE','Step4 CITATION_AUDIT/Step5 LITERATURE_COMPARISON'],
['H05','Microsoft Word実機/大学提出体裁','全原稿','LibreOffice表示版と機械/目視監査まで。提出先の様式確定は別途必要','HOLD_SUBMISSION','render/RENDER_RUN.json']]
pd.DataFrame(issues,columns=['id','cause','location','action','status','verification']).to_csv(E/'ISSUE_RESOLUTION_LOG.csv',index=False)
audit=[
['1','目的と結論','PASS_WITH_LIMITS','RQ0/RQ1/RQ2/RQIを明記し、未回答の実定時率/実材料を区別','1.4/7章'],
['2','方法と結果','PASS','同一入力分数比較、全階層統計、モデル時刻/凍結DCが対応','3/4/5章'],
['3','元データと数値','PASS',f'全件数値検査{nchecks}、科学検算{science["checks"]}、最終機械検査{auto["checks"]}がPASS','各CHECKS.csv'],
['4','差の符号・単位','PASS','候補−greedy、正で悪化。旧定義は保存付録の履歴','3.8/4.2'],
['5','標本単位・独立性','PASS','36,800反復出力/460入力/25group/26親を区別。固定cohort記述','3.8/4.2'],
['6','結果と考察','PASS','4章に数値、6章に機構候補・変換条件・意味を配置','4/6章'],
['7','Step4採用判断','PASS','科学台帳をbyte同一コピーして維持','STEP4_EVIDENCE_DECISIONS'],
['8','HOLD保持','PASS_WITH_OPEN_HOLD','46/41、H_plan/QPU、Chen/full-cell/BOM、道路/実車、引用、Wordを保持','6.7/各報告'],
['9','量子因果帰属','PASS_WITH_LIMITS','CPU模擬と古典対照を分離、予算不一致、経路2上流未実行を明記','4.1/6.5'],
['10','実証範囲と限界','PASS_WITH_LIMITS','静的OD/共通上限と契約定時率、モデルと実車を区別','4.5/6.7'],
['11','先行研究比較','CONDITIONAL','既存20項目＋関連一次資料の限定確認。網羅的精読ではない','2章/LITERATURE_COMPARISON.csv'],
['12','新規性','PASS_WITH_LIMITS','指定cohort/支持/証拠対応の追加に限定。「初めて」の主張なし','6.6/貢献報告'],
['13','引用・参考文献','CONDITIONAL','比較文献7項目の書誌/確認範囲対応、旧原意図/未精読HOLD','文献台帳/ISSUE H04'],
['14','DOCX/PDF一致','CONDITIONAL',f'現行本文{auto["current_prose_paragraphs"]}段落と表451セルの正規化抽出一致、86OMML保持。Word実機はHOLD','DOCX_PDF_* /RENDER_RUN'],
['15','図表と本文参照','PASS_DISPLAY_SCOPE','新4図＋設定/入力/運用表、全118頁接触シート、代表頁拡大。大学体裁はHOLD','NEW_FIGURE_REGISTER/visual log']]
pd.DataFrame(audit,columns=['item','scope','judgment','evidence','locator']).to_csv(E/'ACADEMIC_AUDIT_15_ITEMS.csv',index=False)
write('STEP5_CLAIM_EVIDENCE_AUDIT.md',f'''# 最終学術監査

総合判定は **CONDITIONAL COMPLETE** である。保存証拠によるStep5再分析・改訂稿作成・監査は完了したが、全HOLD解消、Microsoft Word実機確認、大学提出版の完成を意味しない。同一エージェントの分離工程であり第三者査読ではない。

## 15項目の監査

{md(pd.DataFrame(audit,columns=['項目','対象','判定','証拠','位置']))}

## 主張と根拠

`evidence/CLAIM_EVIDENCE_MAP.csv` に11主要主張、計算式、元パス、Step5根拠、論文章を対応付けた。入力の正本は `ANALYSIS_INPUT_SHA256.csv` と `SCIENCE_INPUT_SHA256.csv`、全新規出力は `OUTPUT_SHA256_MANIFEST.csv` で固定する。表中の秒と百分率はCSVから作成し、高桁数値を測定精度とは扱わない。

## 問題・原因・修正・再検証

{md(pd.DataFrame(issues,columns=['ID','原因','箇所','修正/扱い','状態','再検証']))}

初回の報告作成で任意依存tabulateが未導入であったため標準的な文字列整形へ置換した。研究データや既存環境の変更は不要であった。図は初回の縮小可読性を確認して実寸に合わせて修正した。正しい数値を変えて見やすくしたのではなく、図中の字体/寸法のみを調整した。

## DOCX/PDFと保存内容

最終PDFは{auto['pages']}頁で、現行本文・文献/付録Aは31頁まで、元保全付録Bは32頁以降である。目次の10章項目はPDFの章開始頁へ照合した。183現行通常段落と451表セルを正規化抽出で照合した。抽出時に独立配置のminus/arrowが文字順へ影響したため、当該字形を比較正規化し、PDF22/27頁を拡大して符号の表示を確認した。TOC頁は独立に照合し、式は元86OMMLの保持・代表頁の表示を確認した。PDFとDOCXのbyte同一性を意味するものではない。

全118頁を10枚の接触シートで確認し、代表頁3/17/19/20/22/27/29等を図/本文/数式/引用の観点から確認した。ページ外テキストblock0、置換文字0である。図表のサイズ、表の継続と見出し、参考例注記は確認したが、大学の提出規定とMicrosoft Word固有の再組版/自動参照は未確認である。

元保全付録1,594blockのテキスト/数式数/画像数signatureと元の画像byte集合を保持し、86式を保存した。本文の差し替え箇所は `THESIS_CHANGELOG.csv`、旧保全対応はStep4の `THESIS_PRESERVED_CONTENT_AUDIT.csv` を継承する。旧記述に残るΔJ符号・407/53・旧定時率・Chen参考値を、現行結論へ復帰させない。

## 保全結果

開始台帳と読取入力を統合した{preservation['files_verified']:,}ファイルのうち{preservation['unchanged_files']:,}ファイルのSHA256が一致した。元原稿・Step1〜4・使用研究入力の不一致は0であり、13不一致はStep5の書込み対象外の既存ポスター作業ディレクトリに限定された。HEADとtracked差分は不変であるが、Step5外に新規未追跡ファイルも増えており、リポジトリ全体不変とは判定しない。外部変更の作成主体は本監査では確定せず、上書き・巻戻しは行わない。詳細は `evidence/PRESERVATION_RESULT.json`、`PRESERVATION_END_CHECK.csv` に保存した。03_data全rawファイルの全byte検査ではなく、一覧保全と使用入力のhash確認を実施した範囲である。
''')
completion=[
['1','秒・%の定量説明','PASS','平均+441.791秒/+22.244%、設定差を算出'],['2','分布・ばらつき','PASS','全階層全統計/460入力併記/4図/影響診断'],['3','運用成果との関係','PASS_WITH_LIMITS','保存静的ODの帰庫/最終顧客/余裕まで。実契約定時率は未同定'],['4','経路1条件','PASS_WITH_LIMITS','A〜E、支持不存在と取得を区別。C〜E実運用HOLD'],['5','経路2判断反映','PASS','Step4を変更せず記号感度/材料非依存DCを主とした'],['6','共通点と相違','PASS','比較表と考察。上流実行/証拠非対称性'],['7','学術的貢献','CONDITIONAL','関連一次資料との比較。網羅的精読/一部旧引用原意図は未解決'],['8','論文整合','PASS_WITH_SUBMISSION_HOLD','RQと章と結論を対応。Word/大学体裁は別途'],['9','主張と証拠','PASS','主要11主張と元データ/式/箇所を対応'],['10','保全','PASS_RESEARCH_SCOPE_WITH_EXTERNAL_CHANGES',str(preservation['unchanged_files'])+'一致。研究入力/原稿/Step1-4差0。対象外ポスター13変化と外部新規ファイルを記録']]
pd.DataFrame(completion,columns=['item','criterion','judgment','reason']).to_csv(O/'STEP5_COMPLETION_MATRIX.csv',index=False)
write('STEP5_FINAL_REPORT.md',f'''# Step5最終報告

## 1. 総合判定

**CONDITIONAL COMPLETE**。Task5-1〜5-8の保存証拠再分析、二経路の統合、独立Word/PDF改訂と監査を実施した。実運用・実材料等の科学的HOLDと、引用原意図/Word実機/大学体裁の提出上のHOLDを残す。修士論文の無条件の最終完成とは判定しない。

## 2. B系列の主な数値結果

ΔJ=J_candidate−J_greedy（正は悪化）である。

|指標|36,800保存計画|460入力の各80出力平均|
|---|---:|---:|
|平均符号付き差 秒|+441.790609|+441.790609|
|平均絶対差 秒|441.790609|441.790609|
|中央値 秒|0|7.473770|
|SD 秒|1,459.379051|622.305258|
|平均相対差 %|+22.243524|+22.243524|
|相対差中央値 %|0|0.634226|
|相対差SD ポイント|73.504767|31.345204|

全計画のP5/P95は0/4,508.770475秒、0/218.865155%。最大差9,483.990487秒・500.980544%。平均Jからの相対比28.471877%は個別率平均22.243524%とは別である。補助内訳は改善0、同等28,200（76.630435%）、悪化8,600（23.369565%）。独立標本数は36,800としない。

## 3. greedyとの解品質差の解釈

mirror5とactiveの6設定は各平均+1.040464秒/+0.065503%。Grover p2/p3は+1,766.046542/+1,762.035546秒、+88.887051/+88.668125%。R5 Grover p2は+5,983.706453秒/+292.076023%、入力間SD1,314.364537秒である。全体の正差総和の99.823367%がGrover2設定に集中する。

最大1入力の差総和寄与は1.139200%、上位5入力5.622822%、上位23入力21.644748%。単一入力の外れ値だけが平均を作った結果ではない。全体平均は8設定を等重み混合した保存設計の記述であり、量子手法一般の代表効果や因果効果ではない。候補はCPU上の量子アルゴリズム模擬、対照は古典反復greedyで、予算/出力規則の差が残る。

## 4. 定時配達率との関係

固定OD/共通開始原点/サービス102秒では帰庫差=ΔJで、平均+441.790609秒。最終顧客完了差の平均は+439.538924秒であり、180計画では負差となる。帰庫と配送完了は異なる。

候補の帰庫余裕最小7,435.747703秒。モデルの共通上限内遵守は両側100%、差0ポイントである。顧客時間窓なしBの上限遵守であり実契約定時率ではない。契約期限/実出発/取得総時間/採用記録は未同定で、実定時率はNULLのままである。閾値付近で差が成果に反映する条件式を示したが、新しい期限を置く実験はしていない。

## 5. 経路1の成立条件

A改善候補存在、B有限予算で取得、C全工程がH_plan以内、D可行かつ運用採用、E期限等の成果へ反映を区別した。mirror460はJ*_S=J_initial≥J_greedyで指定支持内Aが不成立。全順列では135入力により強い参照証拠、41に保存MIP条件付き証拠でgreedy超えの解があり、238は参照と同等、46は未証明である。Groverの不取得を単一原因へ帰属しない。C〜Eの実運用はHOLDである。

## 6. 経路2の成立条件

正の定義域/他条件固定の記号的感度と同じ部材会計ΔM=b−δを主に用いた。δ=bで相殺、δ>bで逆転。材料非依存DCの1000kg右微分平均は下/上Crrで2.368077/2.431780Wh/kg、軌跡間SD1.140334/1.167081。460対応軌跡、1000〜1250kg、同一凍結物理なら質量削減とDC削減の符号が一致する。Chen実用入力、T09未知BOM、完成pack・実車・量子材料は未検証であり、参考の具体的削減率を主効果としない。

## 7. 統合した研究上の発見

技術能力だけでは運用成果の符号と大きさを同定できず、比較基準と中間変換・採用/走行条件を確定する必要がある。本研究はこれを差分布、指定支持の不存在、帰庫/顧客時刻の相違、部材/DCモデルの成立範囲で具体化した。経路1は実行済みCPU模擬の比較、経路2は上流材料改善を未実証とする下流モデルという非対称性がある。共通構造のみを新規性としない。

## 8. 学術的貢献と新規性

実証的追加は指定cohortの秒/%分布・入力影響診断・支持証拠との対応、モデル内の質量/DC応答である。方法的特徴は主対照/支持/取得/時間/採用と、材料適格性/会計/DCを追跡可能に分けた点である。

Hadfield/Bärtschi/Palackalには支持・状態準備・解品質評価、Davis/FigliozziとFASTSimには運用/車両接続、Delgadoには量子電池物性/資源の先行例がある。書誌・DOI/URL・確認scope・差分は `STEP5_ACADEMIC_CONTRIBUTIONS.md` と `evidence/LITERATURE_COMPARISON.csv` に記録した。公開要旨等の限定確認であり、網羅的優先権や「初めて」は主張しない。

## 9. 修士論文改訂

来歴を確認したStep4全文版から、要旨・1.4目的/RQ・2.4文献比較・3.8方法・4章結果・6章統合考察・7章結論を改訂した。5章にT07/車両質量の採用条件を補い、Chen参考節の役割を維持した。主結果は符号付き/相対差、分布、入力単位、帰庫と配送完了差である。新4図と設定/分布/運用比較表、主張対応を追加した。参考文献にBrooker2015を追加しRobinson2008a/bを整形した。

最終Word/PDFは{auto['pages']}頁、現行主論証/文献/付録Aは31頁まで、保全付録Bは32頁以降である。旧保全1,594block、86式、元画像byteを保持した。PDF通常本文183段落/表451セルの正規化照合と全頁接触シート確認、代表頁拡大を実施した。PDF表示版はLibreOffice生成である。

## 10. 残存HOLD

- 46最適値未証明、41参照の外部証明、旧8設定と古典の予算/出力統制。
- H_plan・全工程時間・QPU資源、実採用/実出発、契約定時率、道路/需要の全再生成と受入。
- Chen実用full-cell入力、独立材料範囲、未知BOM、完成pack、量子→実材料、実車DC。既存道路受入FAILとT09_ROW183対向FAILは維持する。
- Papachristos旧引用原意図・原著未確認保存文献、Microsoft Word実機・大学提出体裁/自動目次/最終引用書式。

## 11. 保存先と保全

`{O}`。指定11成果物に加え、data/全件CSV・全階層統計、figures/PNG300dpi・PDF、scripts/再現コード、evidence/hash・主張・検算・問題対応、render/全頁画像・目次照合を保存した。

既存/読取入力{preservation['files_verified']:,}ファイル中{preservation['unchanged_files']:,}ファイルのSHA256一致、元原稿・元実験・Step1〜4・使用研究入力の不一致0、HEAD・tracked差分不変を確認した。対象外の既存ポスター13ファイルには開始後変更があり、Step5外の新規未追跡ファイルも記録したため、リポジトリ全体不変とは報告しない。これらを戻さず、Step5の書込みは専用ディレクトリに限定した。commit/pushは実施していない。保全範囲は台帳対象であり、使用しない全rawデータのbyte監査を実施したとはしない。

## 12. 修士論文完成までの残作業

提出に向けて必要なのは、大学様式とMicrosoft Word実機での組版/目次/相互参照確認、旧引用原意図と必要な原著内容の最終確認、保全付録を本冊/別冊のどちらで提出するかの確定である。科学的HOLDは、解除しない場合も結論の適用範囲と限界として維持する。実定時率や完成pack効果を追加して主張する場合には対応する独立証拠が不可欠であり、今回の改訂完了と区別する。

`STEP5_COMPLETION_MATRIX.csv` に10完了条件を個別判定した。10は研究対象の保全範囲に限定し外部同時変化を記録した。7は文献確認範囲、8は提出環境、3/4は実運用範囲の条件を伴うため、無条件COMPLETEを出さない。
''')
write('README.md','''# Step5成果物

入口はSTEP5_FINAL_REPORT.md、論文はTHESIS_STEP5_REVISED.docx / THESIS_STEP5_REVISED.pdfである。総合判定はCONDITIONAL COMPLETEであり、未検証科学事項と提出体裁のHOLDを残す。

再現順序はscripts/analyze.py → scripts/write_reports.py → scripts/verify_science.py → scripts/refine_figures.py → scripts/build_thesis.py → scripts/render_thesis.py → scripts/final_audit.py → scripts/close_step5.pyである。元実験の再探索ではなく保存データの再集計/検算である。既存Step5を上書き再実行する場合は新しい独立ディレクトリへscriptsと開始台帳を移し、入力/環境/出力の依存を確認する。現成果物の再実行を承認済み元版の書換えへ転用しない。

本文のΔJ=候補−greedyはStep1〜4の旧符号と逆である。旧付録Bは保全履歴として読み、現在の定義/採用値を復活させない。図はF1〜F4、数値正本はdata/、来歴/検算/学術監査はevidence/にある。SHA256出力一覧はOUTPUT_SHA256_MANIFEST.csvを参照する。
''')
# Seal outputs excluding transient renderer profile/cache and the manifest itself.
manifest=[]
for p in sorted(O.rglob('*')):
 if not p.is_file() or p.name in ['OUTPUT_SHA256_MANIFEST.csv','close.log'] or any(x in p.relative_to(O).parts for x in ['profile','cache','config','__pycache__']):continue
 manifest.append(dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
pd.DataFrame(manifest).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
print(json.dumps(dict(preservation=preservation,outputs=len(manifest),status='CONDITIONAL COMPLETE'),ensure_ascii=False))
