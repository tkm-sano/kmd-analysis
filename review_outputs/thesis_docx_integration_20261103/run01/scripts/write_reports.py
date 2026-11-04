from common import *
from importlib.metadata import version
import platform
before=js(O/'DOCX_STRUCTURE_BEFORE.json');after=js(O/'DOCX_STRUCTURE_AFTER.json');build=js(O/'BUILD_RUN.json');check=js(O/'INTEGRITY_RUN.json');run=js(O/'FINAL_RENDER_SELECTION.json')['run'];render=js(O/run/'RENDER_RUN.json');qa=js(O/run/'PAGE_QA_SUMMARY.json');accept=js(O/'VISUAL_ACCEPTANCE.json')
assert check['failures']==0 and accept['accepted_pages']==render['pages']
assert render['DOCX_sha256']==sha(OUT)
actual={
'I01':'目的段落19は維持し、見出し1.1に整理した。',
'I02':'段落27の後にA固定OD・B計画・C感度という実施範囲と未検証区間を追記した。',
'I03':'本文・元引用は維持。7背景引用を一次資料へ照合し参考文献を追加した。Papachristos2018のみHOLD。',
'I04':'3.1を更新して新表3-1を挿入。旧3.1本文・旧表0は付録BへXMLごと移動した。',
'I05':'3.2の地域・道路・位置・生成限界を維持し、N0/N1受入不成立、固定OD限定利用を追記した。',
'I06':'3.3需要生成・表1・元数式を維持し、既存表へ表3-2の題名を追加した。',
'I07':'3.4を現行A/B/Cの入力・親・需要群・版へ更新し、旧記述を付録Bへ保全した。',
'I08':'3.5の数理定義・数式を維持。J+102nは時間窓なしB、Aは3.8再帰という適用範囲を追加した。',
'I09':'3.6古典法と厳密参照を維持し、407/53・920旧補助対照の範囲を追加した。',
'I10':'Aの取得64/14を説明するone-hot・PUBO・ProtocolV2と原数式は本文に維持。旧no-window直接法・局所法のみ付録Bへ移動した。旧系列全てを一括で移す原案を実際の必要性に合わせて調整した。',
'I11':'3.8を固定OD再帰、D03期限、D10/D11政策、4arm、分母、仮想時間の区分へ置換し図3-1を挿入。旧native定義は付録Bへ移動した。',
'I12':'3.9を最新T08/T09の式・部材・未知質量へ更新。旧本文・パラメータ表・数式は付録Bへ保全し図3-2を挿入。新電解液式は同値な体積内訳で表示した。',
'I13':'3.10を凍結仕様の式・境界・欠測規則へ更新。旧式は付録Bへ保持し、元FREEZEは未変更。',
'I14':'3.11を現在Bの工程別時間・未保存資源とAの保存環境の区分へ更新。旧環境記述は付録B。',
'I15':'3.12を25群・10000回・1176補助区間・検定0・欠測区分へ更新。旧説明は付録B。',
'I16':'3.13をB現行8設定・支持・8192shot・10seed・時間scopeへ更新。旧11月補助方式は付録B、全設定所在はE.4。',
'I17':'第4章を4段階再現性、前段算術・独立照合と今回文書編集の分離へ更新。旧本文は付録B。',
'I18':'5.1にB全件結果、表5-1/2/3、図5-1/2を挿入。旧小規模直接・局所表は付録B。工程図は付録C.1へ。',
'I19':'欠落した5.2見出しを追加し、A2808判断・64機構比較・待機吸収・余裕を挿入。旧native3099秒は付録B、新固定OD3133秒と分離。',
'I20':'5.3にT08/T09/bridgeの条件付き結果、表5-4と図5-6/7を挿入。旧表5の全セルは付録Bへ。',
'I21':'5.4を補助区間と未評価へ更新。旧548・局所・96600全対照系列は付録Bへ。',
'I22':'6.1を採用・待機・飽和・規模・資源の考察へ更新。旧帰庫境界式を含む原文は付録B。',
'I23':'旧312〜318の材料境界・枝導関数等は付録Bへ保全。現在6.2にはb−δと条件付き解釈を配置した。',
'I24':'6.2を固定担持/面積、未知部材、固定速度DC、実EV未校正へ更新。旧補助5経路を主Bへ流用しない。',
'I25':'6.3統合と6.4統計・外的妥当性を追加し、旧アーキテクチャ資料と面接未実施状態を分離した。',
'I26':'第7章を新全件数値・到達段階・条件・限界へ更新。旧結論は付録Bへ保全。',
'I27':'旧参考文献の全段落・リンクを保持し、確認済み7背景文献とField/Welshを補足欄へ追加。Faraji DOIを別段落で追記。Papachristosの意図同定のみHOLD。',
'I28':'原付録A.1を維持し、現行主分析の所在・外部保全区分を新E.1へ追加した。',
'I29':'原付録A.2を維持し、現行26主張と採否・証拠の対応を新E.2および電子CSVへ追加した。',
'I30':'原付録A.3を維持し、現行主要CSVの完全SHAを付表E-1へ追加。統合コード・図・DOCXの台帳は今回レビューへ保存。',
'I31':'原付録A.4を維持し、新E.4へ主分析・図表・統合の入口を追加。全1176区間は電子付録として明示した。',
'I32':'原付録A.5の局所3seedと表7を維持。付表A-1の題名を追加し、現在Bの資源へ転用しない。'}
ex=rows(O/'INSERTION_EXECUTION.csv')
for x in ex:x['actual_edit_detail']=actual[x['integration_id']]
table('INSERTION_EXECUTION.csv',ex)
# Every original paragraph's new location, including archival material, is traceable.
from docx import Document
src=Document(SRC);out=Document(OUT);parents={p._p:i for i,p in enumerate(out.paragraphs)}
old_text={p.text for p in src.paragraphs if p.text}
table('ORIGINAL_TEXT_RETENTION.csv',[{'original_index0':i,'text':p.text,'retained_in_new_text':p.text in '\n'.join(q.text for q in out.paragraphs),'note':'冒頭4見出しは番号・章名を更新。その他は主本文または履歴付録に保全。'} for i,p in enumerate(src.paragraphs) if p.text])
md('00_SOURCE_INVENTORY.md',f'''# 統合入力と出力の所在

元文書 `{SRC}`、SHA256 `{sha(SRC)}`。統合出力 `{OUT}`、SHA256 `{sha(OUT)}`。元文書は未変更である。既存研究データ・コード・FREEZE・図表・前段報告の読取対象317ファイルをSOURCE_HASHES_BEFORE.csvへ固定し、SOURCE_PROTECTION_CHECKS.csvで一致を確認した。前段の図表・原稿142成果物と全件分析171成果物を、各台帳のhashで照合してから使用した。

|区分|入力|対応する記録|
|---|---|---|
|反映方針|thesis_results_interpretation_20261102/run01の00〜09、DOCX_INSERTION_MAPPING.csv|32件のアンカー照合とINSERTION_EXECUTION.csv|
|新原稿|04_THESIS_METHODS_DRAFT、05_THESIS_RESULTS_DRAFT、06_THESIS_DISCUSSION_DRAFT、07_THESIS_CONCLUSION_DRAFT|新本文と付録Bの旧原文移動|
|図|FIGURE_SOURCE_MAPPING.csv、figures/の既存PNG|FIGURE_INTEGRATION.csv、元SVG/PDFは未変更|
|表|tables/の既存CSVおよび元8表|TABLE_INTEGRATION.csv、全旧表XML一致|
|数値|no_sumo_full_analysis_20261102/run01のA/B/C主要CSV|凍結結果と少数の保存集計行のreadback。再求解なし|
|Controlled-DC|CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json|SHA維持。式・境界を転記|
|参考文献|元参考文献と一次資料書誌|REFERENCE_UPDATES.json（確認日2026-11-03）|

全パス・SHA256はSOURCE_HASHES_BEFORE.csvとOUTPUT_SHA256_MANIFEST.csvを参照する。原raw/snapshotの一部は外部保全領域にあり、公開Gitに全て含まれるとは記述しない。今回のレンダラー・Python補助ライブラリはreview内のrendering_tools/へローカル展開した。システムや研究コードへインストール・変更していない。
''')
s='# 32箇所の反映実施記録\n\n32件の元アンカーはすべて実DOCXと一致した。30件PASS、引用同定に関係するI03/I27の2件HOLDである。HOLDは同じPapachristos2018の1文献に由来し、数値の欠落ではない。実際の章構造に合わせ、Aの取得方法を本文維持する等、原案の一括移動を調整した。\n\n'
for x in ex:
 s+=f"## {x['integration_id']} {x['proposed_section']}：{x['execution_status']}\n\n- 元位置：段落{x['paragraph_index0_start']}〜{x['paragraph_index0_end']}（0始まり）。原文アンカー「{x['exact_anchor']}」。\n- 原案：{x['change_and_reason']}\n- 実施：{x['actual_edit_detail']}\n- 旧資料移動先：{x['old_material_destination']}。\n- 新原稿：{x['draft_file_and_heading']}。図表：{x['figure_or_table_id'] or 'なし'}。\n- 根拠：CLAIM_EVIDENCE_MAPPING.csvの{x['claim_ids'] or '構成・出典項目'}、元CSVと計算式・hash。\n\n"
s+='''## 旧資料の保全と文書構造修正

旧本文は16ブロックを付録BへXML要素ごと移動し、原段落範囲と移動先をARCHIVED_ORIGINAL_BLOCKS.csvに保存した。旧8表・67数式・53ハイパーリンク・29ブックマークの要素または対応関係を保持した。4つの冒頭見出しは章番号・階層を整え、旧付録Aはそのまま維持した。新規脚注は追加していない。

初版で本文直下のブックマーク58境界要素を段落と同じ扱いで移動できていない問題を検出した。元29組の名前・IDを保ったまま、更新後の同じ主題または旧節の位置へ復元し、BOOKMARK_RETARGETING.csvへ記録した。captionの新bookmark名は一意にした。header/numberingのXML宣言・改行の再直列化は内容変更と分け、意味構造を照合した。初版の不適合記録はrevisions/v01_DOCX_INTEGRITY_CHECKS.csvに残した。

横向き4ページの追加によりセクションを1→9とした。元の本文ページ寸法・余白・空ヘッダーを保持し、ページ番号をフッターへ新規追加した。継続番号が途中で1へ戻る問題を修正した。新規数式19件はOMMLで追加し、空上限の非表示、正負添字のliteral指定、電解液式の同値分割を実施した。3.9節だけ段落間隔を調整し、3行のみの継続ページを解消した。原付録の証拠ID見出し（R07等）は説明文と同じページへ保持する設定を追加した。全て今回統合版への変更であり元DOCX・数値・モデルは未変更である。
'''
md('02_INSERTION_EXECUTION_LOG.md',s)
md('03_CONTENT_CONSISTENCY_REVIEW.md',f'''# 研究内容の整合性

判定：主要な方法・結果・考察・結論の対応はPASS、科学的主張は従来どおりCONDITIONALである。新規研究計算は0件である。前段の独立検証済みCSV・原稿・図表のhashを照合して転記し、保存集計行の単位・分母・比較方向を確認した。今回の文書完全性確認{check['checks']}項目は不一致0件（DOCX_INTEGRITY_CHECKS.csv）。

|系列|本文へ反映した定量値|解釈の制約|
|---|---|---|
|A|78問題、成功64/未取得14、36条件2808判断、9216arm。採用1344・切替1464・正の出発936。全定時率100%、対照差0pp。最小余裕3133.461531秒。|時間不変ODと102秒サービスのモデル完了。native SUMO・引渡し実測ではない。時刻差と定時率差を分け、飽和・待機吸収を考察。|
|B|460入力、8設定、10seed、36800参照。6設定は訪問順と目的値が初期解と一致。Grover P2/P3平均差+1765.006/+1760.995秒（460入力等重み）。参照407/未確定53。|支持・規模・予算・CPU工程を分離。R3〜R5平均悪化、小規模一部改善を併記。現行Bは全配送先を保持し旧局所法と区別。走行DC・定時率は未評価。|
|C|T08差5.448297415kg、下側DC差5941.555975Wh、加重0.412579010%。T09代表既知差9.722608121/5.977891152kg。183HOLD・1FAIL。|T08とT09を完成品比較にしない。旧460速度と現行B460を区別。δ=bで質量差消失、δ>bで逆転。量子材料改善と実EV性能は未実証。|

32件の実施内容と根拠は02、原稿の採否は前段の26主張に対応する。1,176区間は25需要群bootstrapの補助感度であり、同等性・実地域誤差の証拠にしない。固定期限を改善のために変えていない。HOLD/FAIL・未知・未取得を補完していない。

新しい電解液式の4行表示は、同じc/ρ×ε/(1−ε)とセパレータ空隙・追加液を体積内訳へ分けたものであり、新たな物性値・質量を計算したものではない。元の式とコードは変えていない。既存67数式は全てそのまま残し、現在の式と旧履歴の適用範囲を分けた。

統合後の旧本文も付録Bに残るため、旧表番号・旧「今回」という時点表現は付録冒頭で履歴と明示した。現在の主分析の結果として読む範囲を第3・5・6・7章へ限定した。参考文献の意図同定1件、実機回路資源・実交通・完成パックの未検証は残存し、全ての研究関係が実証済みとは記述しない。
''')
fig=rows(O/'FIGURE_INTEGRATION.csv');tb=rows(O/'TABLE_INTEGRATION.csv')
s='# 図表の反映\n\n元図10点のうち8点を本文、2点を付録Cへ配置した。数値内容を変更せず、4点をA4横向き、残る複数panelを拡大配置した。Word内は19画像、元SVG/PDFは保持した。キャプションは固定文字列で管理し、元原稿と同じくSEQ/REF自動番号は新設していない。全キャプション・本文参照・原図IDを対応付け、bookmarkを一意に付与した。\n\n'
for x in fig:s+=f"## {x['number']}（{x['figure_id']}）\n\n{x['title']}。配置：{x['placement']}。画像数：{x['embedded_images']}。\n\n{x['caption']}\n\n元画像 `{x['source_png']}` SHA256 `{x['source_sha256']}`。元CSV `{x['source_csv_paths']}`、SHA256 `{x['source_csv_sha256']}`。変換：{x['conversion']}。\n\n"
s+='## 表\n\n元8表のセル・XMLを全て保持し、新規19表を追加した（合計27表）。元需要表と旧局所表には題名だけを追加した。新表は繰返し見出し行と行内分割禁止を設定し、ページ跨ぎでヘッダーを再表示する。全1,176補助区間は電子付録S-1を明示し、本文の説明例のみを選び直した主結果として扱わない。\n\n'
for x in tb:s+=f"- {x['table_id']}：{x['title']}。{x['rows_excluding_header']}行×{x['columns']}列、出典：{x['source']}。{x['note']}\n"
s+='\n図のpanel切出し範囲とファイルはfigure_panels/と生成コードに残した。手作業による数値・軸・凡例変更は行っていない。原稿の本文参照は図3-1/2、図5-1/2/4/5/6/7、付図C-1/2へ正規化した。表示確認は05を参照する。\n'
md('04_FIGURE_AND_TABLE_INTEGRATION.md',s)
md('05_DOCX_VISUAL_QA.md',f'''# DOCX表示検証

最終版は `{O/run/(OUT.stem+'.pdf')}`、{render['pages']}ページである。LibreOffice24.2.7.2によるDOCXのレンダリングを行い、ページ別PNGと2ページ見開き画像を保存した。Microsoft Word実機の表示を確認したとは報告しない。変換wall {render['wall_s']:.3f}秒、子process最大RSS {render['RSS_bytes']}bytesである。Java警告はJava不使用のWriter PDF出力に関するもので、出力は正常に作成された。

{accept['accepted_pages']}ページすべてを画像で確認した。確認方法の区分と対象画像hashはVISUAL_PAGE_REVIEW.csv、全ページの自動検査は{run}/PAGE_AUTOMATIC_QA.csvを参照する。変更のない既読ページの受入引継ぎは画像hashの一致を条件とし、未閲覧ページを一括で閲覧済みにしていない。数式・図表・表分割の重要ページは個別PNGでも確認した。

|確認|最終結果|
|---|---|
|ページ外の文字・画像|0ページ|
|空白候補ページ|0ページ|
|Unicode置換文字|0ページ|
|画像の配置|19画像、元図10点の全panelを確認|
|ページ番号|全ページで連続番号を照合（PAGE_NUMBER_CHECKS.csv）|
|見出し・表|孤立見出し、主要表の不自然な分割、欠落をページ画像で確認|
|新規数式|空上限の四角、正負添字の赤いエラー記号を修正し再確認|
|原数式・脚注・リンク|67数式保持、脚注0→0、53リンク保持。数式はPDFとXMLを区別して照合|

## 修正履歴

- 初版：本文直下の29組のbookmarkを復元し、同じ主題または旧履歴へ再対応した。初版不適合と修正後検証をrevisions/へ保持した。
- 横向き切替：元sectPrの開始番号1の複写で番号が再開始したため、開始指定を外して連続番号とした。
- 数式：新規naryの空上限を非表示、単独正負添字をliteralに指定した。電解液の長式は同値な4行へ分けた。MATH_LAYOUT_FIXTURE.docx/pdf/pngは変換器の表示比較であり、科学実験ではない。
- 3.9節：最終3行だけの継続ページを避けるため新規段落間隔だけを調整し、再レンダリングした。本文フォント寸法と入力・数式の内容は維持した。
- 原付録：46ページ末尾でR07項目見出しが孤立するのを検出し、証拠ID見出しへkeep_with_nextを設定して再確認した。
- 図：横向き4ページとpanel拡大で可読性を確保し、元図の全panelと出典注記を維持した。

本文中の長い英語識別子・パスの改行、参考文献の表記統一等は次段階の可読性調整として残る。PDF確認はMicrosoft Wordのフォント置換・改ページを保証しないため、提出前にWord実機でも最終確認する。
''')
md('06_UNRESOLVED_ITEMS.md','''# 未解決事項

## 編集・引用

1. **HOLD：Papachristos（2018）の意図した文献の一意同定**。元本文の引用を保持した。Futures98:57–71（10.1016/j.futures.2018.02.006）と2018会議論文等は主旨が近く、元引用の識別子がないため推測で文献を追加していない。32対応中I03/I27の2件は同じ1文献のHOLDである。
2. 背景の他7引用は一次資料の書誌・該当主旨を照合して追加した。Faraji-Niri DOIはWRAP原著版から確認した。これは全文の全引用の完全検証や参考文献形式の統一を意味しない。省略著者・掲載情報等の既存記法は次段階で整理する。
3. **HOLD：Microsoft Word実機での最終組版**。LibreOfficeで全ページを確認し、構造と内容を照合した。Word固有のフォント置換・フィールド再評価・改ページは提出前に確認する。原稿に目次はなかったため今回も新設していない。必要なら次段階で規程に合わせて追加する。
4. 旧本文・旧表の履歴を付録Bに保全したため、重複・長さ・旧時点表現が残る。削除せず配置と意味を明示している。次段階で本文・補助資料の最終構成を判断する。

## 研究証拠（今回の編集では解消しない）

道路N0の幾何FAIL、N1の動的FAIL、正の遅延native未取得、Bの走行DC未評価、厳密参照53入力未確定、実機回路資源と統一当時環境の保存不足を維持する。T09完成パック183行HOLD、全面対向T09_ROW_183のFAILを維持する。量子材料解析による対象性能改善、対象EV校正・実車省電力・完成パック改善は未実証である。固定ODと固定速度の条件付き主張を越えて、文書編集によって確定させない。

数値・図表・単位・分母について、今回照合した主要箇所に未解決の不一致はない。これを研究全体の妥当性や現実への一般化が達成されたという意味に拡大しない。
''')
md('07_FINAL_GO_NO_GO.md',f'''# 統合原稿の進行判定

**CONDITIONAL GO：学術表現・可読性の全面修正へ進行可能。** 最新研究内容と図表のWord統合は完了し、元DOCXと317確認入力は不変である。32反映箇所は30PASS・2HOLD（同じ引用同定1件）である。HOLDを隠して提出可能な完成稿とは扱わない。

元8表と67数式・53リンク・29bookmarkを保持し、新規19表・19数式・19画像を追加した。元図10点は本文8・付録2である。最終DOCXは正常に読め、{render['pages']}ページのレンダリングを確認した。文書完全性{check['checks']}項目の不一致は0件である。数値・図表から元の分析CSV・式・コードへ追跡できる。

## 次段階の順序

1. Papachristos2018の元引用意図を確認し、引用・文献一覧を整合させる。確認できるまではHOLD表示を維持する。
2. 現行主分析と旧履歴の役割を維持しつつ、重複・独自略語・英語識別子・文献形式・説明順序を推敲する。数値・モデル・分母・条件を変更しない。
3. 図表参照、記号、節番号を整え、目次・大学指定様式が必要かを確認する。Word実機で全体表示とPAGEフィールドを再確認する。
4. 「定時率差0＝同等」「量子一般の優劣」「B省電力」「実EV・実pack改善」を結論へ追加しない。既存のHOLD/FAILは新工学証拠なしで解消しない。

研究内容の限定を保った編集作業には新しい科学実験は不要である。条件付きモデルの範囲を超えた実証主張には別の実験・工学データが必要であり、今回の次段階とは分ける。

出力： `{OUT}`、SHA256 `{sha(OUT)}`。元DOCX SHA256 `{sha(SRC)}`。表示用PDF・ページ画像は{run}/、コードはscripts/、全出典・生成物hashはOUTPUT_SHA256_MANIFEST.csvとSOURCE_PROTECTION_CHECKS.csvを参照する。新規SUMO・経路探索・QAOA・全件分析・元DOCX上書きは実施せず、この統合原稿の保存で停止する。
''')
# Reproducibility helpers and immutable inventory. Exclude local package tree/cache from research output enumeration.
dump('INTEGRATION_ENVIRONMENT.json',{'python':sys.version,'platform':platform.platform(),'python_docx':version('python-docx'),'lxml':version('lxml'),'Pillow':version('pillow'),'renderer':'LibreOffice24.2.7.2 locally extracted','rendered_final':run,'native_MS_Word_tested':False,'scientific_runs':0})
md('REPRODUCE.md','''# 再生成と検証

作業ディレクトリは/home/takuma/kmd-analysisである。既存の利用者ファイルを上書きしないため、新規review runへscripts/とREFERENCE_UPDATES.jsonを複製し、common.pyのOUTを別の新しい出力名へ設定する。元DOCXはSRCのまま読み取り専用にする。audit_before.pyは既存出力があると停止する。

1. audit_before.pyで元317資料と32アンカーを固定する。
2. ローカルレンダラーはrendering_tools/APT_URIS.txtとPACKAGES.jsonのhashを使いsetup_renderer.pyで展開する。RCとregistryの修正はローカル展開先に限る。補助Pythonライブラリはrendering_tools/pythonへ配置する。
3. integrate_docx.pyで新しい別名DOCXを作成する。元XMLの要素を本文または履歴付録へ保持する。
4. verify_integrity.pyで原数式・表・リンク・bookmark・OPC関係・source hashを照合する。
5. render_docx.pyとqa_pages.pyでPDFと全ページを生成し、実際に画像を確認する。write_reports.pyの受入記録は別途実施した目視の結果であり、コードを回すだけで新しい目視確認を主張しない。

原分析runnerは実行しない。DOCXのZIPタイムスタンプ等により全体のbyte hashが異なる場合もあるため、入力hashに加え、文書構造・元要素保全・転記値・描画結果を照合する。今回の実出力hashは各台帳に固定した。
''')
print(json.dumps({'reports':8,'output_sha256':sha(OUT),'pages':render['pages'],'insertion_PASS':30,'insertion_HOLD':2},ensure_ascii=False))
