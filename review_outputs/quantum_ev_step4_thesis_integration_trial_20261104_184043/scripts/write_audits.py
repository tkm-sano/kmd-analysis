from pathlib import Path
import pandas as pd,json,re,hashlib,collections,unicodedata
from docx import Document
from lxml import etree
O=Path(__file__).resolve().parents[1];R=O.parents[1];S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309'
def md(n,t):(O/n).write_text(t.strip()+'\n')
source=pd.read_csv(O/'ORIGINAL_THESIS_STRUCTURE.csv',keep_default_na=False);pres=pd.read_csv(O/'THESIS_PRESERVED_CONTENT_AUDIT.csv');claim=pd.read_csv(O/'CLAIM_ADOPTION_REVIEW.csv',keep_default_na=False);reg=pd.read_csv(O/'FIGURE_TABLE_REGISTER.csv');build=json.loads((O/'evidence/DOCX_BUILD.json').read_text());render=json.loads((O/'render/RENDER_RUN.json').read_text())
# Complete RQ-to-chapter mapping preserves RQI, rather than treating it as a new experiment.
pd.DataFrame([dict(RQ=a,question=b,method=c,results=d,discussion=e,conclusion=f,adoption='trial表現案・正式採否未決定') for a,b,c,d,e,f in [('RQ0','二経路の技術能力/適用/成立条件','3.1/3.12','4/5','6.5/6.9','7'),('RQ1','古典近似に対する解品質と時間条件','3.4–3.8/3.11','4.1–4.5','6.1–6.2/6.7','7'),('RQ2','連続設計入力から質量/DCへの伝達と消失','3.9–3.10','5.1–5.6','6.3–6.4/6.7','7'),('RQI','二経路の比較から得る接続条件の示唆','3.1/評価枠組み','4/5の条件台帳','6.5–6.9','7')]]).to_csv(O/'RQ_CHAPTER_ALIGNMENT.csv',index=False)
# All original and new changes receive a review recommendation; archival retention is not scientific adoption.
changes=[]
for x in pres.to_dict('records'):
 changes.append(dict(change_id=x['block_id'],origin='source block',classification=x['category'],action=x['action'],location=x['destination'],reason=x['reason'],scientific_judgment='NOT_A_NEW_EMPIRICAL_CLAIM',adoption_recommendation='A' if x['category']=='A' else 'B',formal_adoption='NOT_DECIDED'))
for i,x in enumerate(pd.read_csv(O/'evidence/NEW_PARAGRAPHS.csv',keep_default_na=False).to_dict('records'),1):changes.append(dict(change_id=f'NEW{i:03d}',origin='new paragraph',classification='E',action='現行方針・結果・確認範囲を追加',location=x['section'],reason=x['text'][:160],scientific_judgment='CONDITIONAL',adoption_recommendation='B',formal_adoption='NOT_DECIDED'))
for id,reason in [('REWRITE_CH1','目的を寄与条件へ、定時率を主指標から除外'),('REWRITE_CH2','三領域と研究ギャップを再構成し原著確認範囲を明記'),('REWRITE_CH4_5','Δinitial中心から主greedy差へ更新し新統計・統制を追加'),('REWRITE_PATH2','Chen参考例を後置し解析感度/材料非依存DCを主にする'),('REWRITE_CONCLUSION','支持の不成立・収支・観測・未接続を分離')]:changes.append(dict(change_id=id,origin='chapter revision',classification='B',action='本文を改訂し旧文は付録Bに保全',location=id,reason=reason,scientific_judgment='CONDITIONAL',adoption_recommendation='B',formal_adoption='NOT_DECIDED'))
for i,txt in enumerate(['量子最適化一般に改善可能性はない','CPU時間をQPU時間とする','Chen逆算値を実用初回実測容量とする','約0.413%を実EV/量子改善とする','T09完成packを確定する','Wilson区間だけでp2有意優位とする','社会技術システム一般の法則を証明したとする'],1):changes.append(dict(change_id='REJECT'+str(i),origin='rejected interpretation',classification='D',action='採用しない解釈候補',location='全体',reason=txt,scientific_judgment='FAIL',adoption_recommendation='D',formal_adoption='NOT_DECIDED'))
pd.DataFrame(changes).to_csv(O/'THESIS_CHANGE_ADOPTION_MATRIX.csv',index=False)
md('THESIS_INTEGRATION_CHANGELOG.md',f'''# 全文統合の変更履歴
基準版は53a3abac…の11月3日統合原稿である。元ファイルは変更せずbyte同一コピーを保存した。
全935 body blockのうち、53を現行本文にXML再使用、794を保存付録Bへ移動、内容を持たない組版空段落88だけをtrialから省略した。全項目の原位置・理由をTHESIS_PRESERVED_CONTENT_AUDITに記録する。実質内容の無記録削除は行っていない。
地域・道路・建物、配送需要生成、訪問順数理、初期構成、厳密参照の求解過程、T09部材式、Controlled-DC式の詳細を保持した。旧one-hot、旧時間窓・採用政策、旧結果/考察、旧参考文献、付録A〜Eの再現資料は保全付録へ移した。保存章番号は元位置の識別であり現行章の採番ではない。
第1章は目的Bと二経路、第2章は社会技術/EV運用/量子応用の比較、第3章は主対照・反復・新統制・モデル式、第4章は経路計算、第5章は材料・車両、第6章は統合、第7章はRQへの回答へ再構成した。旧第4章の再現性管理は3.12と保存記録へ配置した。Step3の14頁を全文に置き換えず、既存86OMML・27表・19画像を全て残した。
新規に7図・7表を追加した。主ΔJはgreedy対照、414/46/41参照、97fit統制とCPU限定scopeを反映した。経路2は解析感度/一般相殺/材料非依存DCを主とし、LP/Sと既存数値走査を参考へ後置した。
スタイルはA4縦、標準行間を自動に調整した。初回レンダリングの原段落重なりを検出し、コピーしたpPrのexact行間をtrialだけでリセットした。原文字列/OMML/画像は変更していない。原表は幅を比例調整し行分割を許し、図は縦横比を保って縮小した。章レベル固定目次はPDFの実際の章開始ページと照合して更新した。
元書誌と背景のPapachristos等は保存する。新しい主論証は原著の確認範囲に限定し、書誌だけの確認を全文内容検証と呼ばない。正式採否は全変更について未決定である。
''')
md('ORIGINAL_VS_TRIAL_COMPARISON.md','''# 元原稿と統合trialの比較
|要素|元原稿|統合trial|
|---|---|---|
|目的/RQ|定時率・電力量と旧問い|目的B、RQ0/RQ1/RQ2/RQIを保持した意味対応|
|背景|社会課題・社会技術・萌芽技術|論理順を維持し、実証範囲へ接続。旧具体論点は保存|
|文献|広い技術/社会的文献と未同定引用|三領域と既存接続研究を整理。原著確認と書誌確認を分離|
|方法|詳細地域/需要/数理/旧政策/材料/DC|有効詳細を再使用、主greedy・追加統制・解析感度を追加|
|結果|旧A/B/C、初期差、407/53|B主差・0改善、414/46/41、新統制とCPUscope。一般質量/DCと参考例を分離|
|考察/結論|取得政策と旧材料境界中心|支持/取得/時間、設計/質量/DC、非対称な二経路の限定統合|
|図表/数式|19図・27表・86OMML|全保全＋新7図7表。旧番号は保存範囲で有効|
|参考文献/付録|既存書誌・A〜E再現資料|現行確認範囲付き参考文献、現行根拠A、元内容保全B|
保存移動と現在の科学的採用を区別する。空段落88の省略以外に内容を単純削除していない。元byteと全位置の対応が残る。
''')
md('STATISTICAL_INTERPRETATION_AUDIT.md','''# 統計解釈の監査
主Bの460問題・8設定・10測定は階層を持つ。36,800を独立問題とせず、10repを独立学習としない。保存bestの可行率とraw-shot可行率を分ける。入力内平均→規模内等重みと、測定内/入力間のSDを区別した。
独立学習97fitのprimary最適取得率とWilson区間は3診断入力/固定手続きの条件付き評価である。最適取得と主greedy超えは異なる。区間だけで設定差の有意性を宣言しない。旧設定の支持・予算・backend・出力規則が異なるためmixerや問題規模だけの因果効果へ帰属しない。
群再標本化は固定cohortに対する仮想群感度であり、実配送母集団の校正済みCIや数値近似/道路/材料/BOM誤差の範囲ではない。検定や量子優位の有意性を採用条件にしない。
経路2の解析感度は数式、49点等はChen依存の決定論的参考格子、460×2Crrは対応軌跡の物理条件である。920実車実験ではない。軌跡間SD、パラメータ範囲、未知質量、統計的感度を別にした。未証明46を補完せず、41の証明留保も残した。
''')
md('RESEARCH_CONTRIBUTION_REVIEW.md','''# 学術的貢献の審査
1. 指定460入力について、mirror支持の最良値と主古典対照を結び付けて不成立の証拠を示し、候補存在・取得・品質・時間を分けた事例的知見である。QAOA/支持/mixerという一般概念自体の発見とはしない。
2. T08の連続入力感度と未知追加部材の相殺、T09の会計構造、材料非依存DC質量応答を区別した。既存EVの費用/運用統合研究が存在することを認め、技術性能とシステム成果の接続を世界で初めて検討したとはいわない。
3. 二経路の異なる検証水準を保持して寄与条件と未接続を追跡可能にした方法的整理である。二事例から社会技術システム一般の法則や制度効果を証明しない。
以上は条件付き採用候補Bである。正式採用前に論文審査者が新規性の位置付けと文献精読範囲を確認する。改善の観測がないことを研究失敗として扱わない。
''')
md('STEP4_ACADEMIC_REVIEW.md','''# 分離工程による学術レビュー
本レビューは同一エージェント内の統合工程と監査工程を分けたもので、第三者査読や完全独立査読ではない。
目的B・定時率主指標除外・二経路の証拠非対称性・RQIの統合的意味を全章で確認した。旧の定時率やChen値が付録Bに残ることは履歴保全であり、主指標/確定入力の復活ではない。
主張31件の科学的判定と採用推奨を分離し、A2/B23/C6とした。未限定の量子不可能性/QPU速度/実EV効果/完成pack/有意層優位/社会一般法則という7候補解釈はFAIL、採用Dとして棄却した。元台帳にその誤文があったとする監査ではない。
数値は入力件数、主差、支持、取得率、414/46/41、解析偏微分、DC対応条件と参考境界を再照合した。保存計算の再現確認を現実妥当性としない。文献は原著を確認できた主張範囲へ限定し、書誌確認だけの資料・Papachristos原意図等はHOLDに残した。
原文の有効説明が省略で失われないよう全935blockを対応付けた。現行本文と保存付録の区別を各保存範囲に表示し、元86式/27表/19画像の保全を別検査する。表示監査では初回の行重なりと目次誤認を修正した。Microsoft Word実機と大学提出体裁は未確認である。
''')
md('WORD_COMPATIBILITY_HOLD.md','''# Word互換性のHOLD
DOCXはpython-docxで生成し、読み取り専用のLibreOffice24.2.7.2でPDFへ変換した。Microsoft Word実機での改頁、代替フォント、数式、目次フィールド更新は確認していない。確認済みとは報告しない。
章レベル目次はPDFページ照合済みの固定目次であり、Wordで自動更新する最終目次ではない。原数式86はOMMLで保持した。新しい感度式等は本文の数式文字列/表に示す。大学指定書式、図表の最終番号、引用書式、原稿の採否はStep5で確認する。
''')
# Citation occurrences, including historical text: flag ambiguous/metadata-only use rather than treating it as a new verified claim.
orig=Document(O/'sources/BASELINE_THESIS.docx');units=pd.read_csv(O/'CITATION_AUDIT.csv',keep_default_na=False);oc=[]
pat=re.compile(r'([A-ZÀ-ž][A-Za-zÀ-ž\-]+(?: et al\.| and [A-Z][A-Za-z\-]+| & [A-Z][A-Za-z\-]+)?)[\s（(,]+((?:19|20)\d{2})')
alias={'AI and Collaborators':'Google Quantum AI','Zini et al.':'Shokrian Zini','Laboratory':'Argonne'}
for i,p in enumerate(orig.paragraphs):
 if 370<=i<=444:continue
 for m in pat.finditer(p.text):
  name=alias.get(m[1],m[1]).split()[0];year=m[2];hits=units[units.original_text.str.contains(re.escape(name),case=False)&units.original_text.str.contains(year)]
  oc.append(dict(origin='original main → retained/main or historical appendix',paragraph_index=i,citation=m[0],matching_ids=';'.join(hits.reference_id),status='HOLD_ORIGINAL_INTENT' if name=='Papachristos' else 'MATCHED_WITH_STATED_SCOPE' if len(hits) else 'HOLD_NO_UNIQUE_MATCH'))
for p in (O/'drafts').glob('0[1-7]_*.md'):
 for m in pat.finditer(p.read_text()):oc.append(dict(origin='current draft '+p.name,paragraph_index='',citation=m[0],matching_ids='see LITERATURE_EVIDENCE_MATRIX author/year + stated scope',status='HOLD_ORIGINAL_INTENT' if 'Papachristos' in m[0] else 'SCOPE_RESTRICTED_REVIEW'))
pd.DataFrame(oc).to_csv(O/'CITATION_OCCURRENCES.csv',index=False)
# Trace current claims to actual current paragraph indices and scientific sources.
doc=Document(O/'THESIS_STEP4_INTEGRATED_TRIAL.docx');paragraphs=[];scope='front'
for i,p in enumerate(doc.paragraphs):
 if p.text=='付録B　元原稿の保全記録':break
 if p.style.name in ['Heading 1','Heading 2']:scope=p.text
 paragraphs.append(dict(index=i,section=scope,text=p.text))
keywords={'P1-D01':'主差ΔJ','P1-N01':'J*_S','P1-O01':'正改善は0','P1-O02':'5983.706','P1-O03':'Grover p2/p3','P1-S01':'matching-chain','P1-S02':'activeの3点grid','P1-C01':'58/97','P1-C02':'78/97','P1-C03':'基底初期0/97','P1-C04':'同角度','P1-T01':'34.643','P1-H01':'414','P2-D01':'材料性能値を使わない','P2-B01':'5.448297','P2-B02':'0.877094','P2-B03':'3.193156','P2-E01':'.412579','P2-E02':'.413590','P2-S01':'9.722608','P2-O01':'速度・加減速','P2-A01':'平坦','P2-H01':'量子物性予測','P2-A02':'偏微分','P2-A03':'ΔM=b−δ','P2-H02':'未採用','I01':'非対称','I02':'技術性能','L01':'Geels','H01':'実道路運用','H02':'合成'}
tr=pd.read_csv(O/'STEP3_TO_THESIS_EVIDENCE_MATRIX.csv',keep_default_na=False);out=[]
for x in tr.to_dict('records'):
 key=keywords[x['claim_id'][3:]];hits=[p for p in paragraphs if key in p['text']];x.update(current_paragraph_indices=';'.join(str(p['index']) for p in hits[:12]),matched_current_sections=';'.join(dict.fromkeys(p['section'] for p in hits[:12])),keyword=key,locator_status='PASS' if hits else 'HOLD_EXPLICIT_LOCATOR');out.append(x)
pd.DataFrame(out).to_csv(O/'SECTION_CLAIM_EVIDENCE_MAP.csv',index=False)
# Figure/table source and numerical correspondence audit, separately scoped for archived items.
fa=reg.copy();fa['numbering_status']='PASS_UNIQUE_CURRENT_OR_EXPLICIT_HISTORICAL_SCOPE';fa['unit_scope']='current values follow CSV; historical figures keep original units/numbering';fa['interpretation_status']=fa.scope.map(lambda s:'CONDITIONAL;Chen reference where labelled' if s=='current' else 'HISTORICAL_NOT_CURRENT_ADOPTION');fa['source_status']=fa.source.map(lambda s:'PASS' if Path(str(s)).is_file() else 'LOCATOR_IN_STATED_SOURCE');fa.to_csv(O/'FIGURE_TABLE_AUDIT.csv',index=False)
# Structural source paragraph classification and section revision map.
sp=source.merge(pres,on='block_id');sp.to_csv(O/'ORIGINAL_TO_REVISED_SECTION_MAP.csv',index=False)
# Residual holds are visible and preserved.
md('UNRESOLVED_ITEMS.md','''# 未解決HOLD・既存FAIL
- 原稿の正式承認権威と全変更の正式採否は未決定。本trialで代行しない。
- 厳密参照46未証明、保存MIPのみ41の外部証明、raw-shot可行率一部、旧8設定の予算・出力規則の統制。
- H_plan、前後処理/転送等を含む実運用総時間、QPU/native compile/物理qubit、未見問題への一般化。
- Chen保持試験の分母/実用full-cell入力採用、材料の独立実用範囲、設計依存部材と未知BOM、完成pack、量子→実材料、実車DC/道路運用。
- 元需要生成器・原統計の全採用セル・道路変換全連鎖・地域受入。旧道路受入FAILとT09_ROW183対向条件FAILを維持する。
- Papachristos2018の元引用意図。Futures候補は同定できたが自動置換しない。原著未確認の保存引用と一部書誌再取得失敗はCITATION_AUDITに残す。全47項目の内容を精読完了したとはいわない。
- Microsoft Word実機、提出体裁、自動目次/相互参照・引用書式の最終整形。旧番号は保存付録内だけ有効である。
HOLDの解消と統合trialの作成完了を区別する。科学的な未解決を削除・推測で補完しない。
''')
md('STEP5_HANDOFF.md','''# Step5最終査読への引継ぎ
最初にSOURCE_THESIS_AUTHORITY、CLAIM_ADOPTION_REVIEW、THESIS_CHANGE_ADOPTION_MATRIX、FINAL_AUDIT_REPORTを読む。正式採否は研究者が判断する。独立Word/PDFと元原稿の差を確認し、採用する変更だけを将来の独立コピーへ反映する。現時点で正式原稿への反映は未実施である。
優先事項は、①目的/RQ0・1・2・Iの採用文言、②主greedy対照と支持/取得/予算/出力規則、③414/46/41とCPUscope、④T08主・T09補完とChen参考の明確な分離、⑤原著確認の範囲とPapachristosの元意図、⑥保存付録Bの提出版への収録範囲、⑦Word実機と大学体裁である。
旧内容を本文へ自動復帰させない。特に定時率、旧主Δinitial、旧407/53、約0.413%の代表効果扱いを復活させない。原86式/27表/19図を保全したことと、それらの旧結論を現在の研究成果として採用することは異なる。
研究貢献は指定入力の支持不成立証拠、モデル伝達・消失の条件、証拠非対称性の比較に限定する。未知BOMや実車/量子材料/制度のHOLDを消さない。文献の内容確認を広げる場合は原著locatorを追加し、書誌の実在確認だけを内容PASSにしない。
本文・参考文献/現行付録・保存付録の量と役割は明示してある。提出版で保存付録を別冊へ移す案は可能だが、元blockへの対応・原DOCX・全履歴は必ず保持する。commit/push/公開は本trialの範囲ではない。
''')
md('EXECUTIVE_SUMMARY.md',f'''# Step4全文統合trial
内容保全の基準は11月3日のtmp_RsrchMstrDc_1026_results_integrated.docxであり、正式版の再認定はしない。31主張にA2/B23/C6の採用推奨を付け、科学的判定と分離した。
元935blockは53本文再使用、794保存付録移動、88組版空段落省略とした。全86OMML、27表、19画像を保全し、7図7表を追加した。背景・文献・方法・経路別結果・統合考察・結論・要旨を目的Bで整合させた。Step3の14頁を全文代替にはしていない。
経路1は主greedyへの正改善0、mirror支持の不成立、取得と品質/時間の別条件を反映した。経路2は解析感度・一般収支・材料非依存DCを主とし、Chen逆算値と約0.413%等を参考へ後置した。
DOCXからPDFをレンダリングし、現在{render['pages']}ページ、26画像・34表である。旧内容は保存付録であり現行採用と区別する。原著の限定確認と書誌照合を分け、Papachristos/Word実機等のHOLDを保持した。正式採用・原稿反映・commit/push/公開は未実施である。
''')
md('README.md','''# KMD修士研究 Step4：独立全文統合trial
最初にEXECUTIVE_SUMMARY.md、SOURCE_THESIS_AUTHORITY.md、FINAL_AUDIT_REPORT.mdを参照する。原稿はTHESIS_STEP4_INTEGRATED_TRIAL.docx、表示PDFは同名.pdf、全文はTHESIS_FULL_TEXT.mdである。
原稿は現行主論証、確認範囲付き参考文献、現行根拠付録A、元原稿保全付録Bを区別する。旧記述を現行採用と読まない。採用審査はCLAIM_ADOPTION_REVIEW.csvとTHESIS_CHANGE_ADOPTION_MATRIX.csv、原稿の全位置対応はORIGINAL_THESIS_STRUCTURE.csv/THESIS_PRESERVED_CONTENT_AUDIT.csv、主張の元データ対応はSECTION_CLAIM_EVIDENCE_MAP.csvに保存する。
文献の確認範囲はLITERATURE_EVIDENCE_MATRIX.csv/BIBLIOGRAPHY_VERIFICATION.csv/CITATION_AUDIT.csv、数値・統計・図表・表示は各AUDITに記録した。すべての成果物とスクリプトはOUTPUT_SHA256_MANIFEST.csvを参照する。再現入力の版と保全はSOURCE_BASELINE_SHA256.csv、evidence内の台帳を参照する。
既存ファイルを変更せず、新規大規模計算を行わない。正式採用、元原稿への反映、commit/push/公開は未実施である。Step5の優先事項はSTEP5_HANDOFF.mdに記録した。
''')
pd.DataFrame([dict(task='4-'+str(i),execution='COMPLETE',scientific_judgment='CONDITIONAL',deliverables=s) for i,s in enumerate(['基準候補7版・935block・内容保全','31主張の科学/採用推奨分離','三領域文献/ギャップ/原著確認範囲','目的B・RQ0/1/2/I・章整合','全文DOCX/PDF/図表/変更履歴','数値/統計/書誌/表示監査','分離工程レビュー/採否資料/Step5'],1)]).to_csv(O/'STEP4_COMPLETION_MATRIX.csv',index=False)
print('Audit documents written; citations',len(oc),'source ledger',len(pres),'claims',len(claim))
