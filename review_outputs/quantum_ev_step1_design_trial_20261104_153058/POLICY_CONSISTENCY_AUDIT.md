# 方針整合性監査

総合CONDITIONAL：新しい評価仕様は研究者方針に整合するが、既存正式文書・原稿に旧目的が残る。本作業は一切書き換えない。

検出根拠はevidence/POLICY_OCCURRENCES.csv（実パス、行、見出し、原文抜粋）。DOCXは本文・表内を含むXML段落番号pNをevidence/*TEXT.txtに保存した。単語の存在だけを違反とせず、その記述の役割を判別する。

|箇所|旧方針の残存とtrial修正案|判定|
|---|---|---|
|R/README.md 冒頭・研究目的・3経路と二つの成果|表題に定時配達率、目的に需要充足と電力量の両立、旧3経路と面接中心が残る。将来採用時は二経路の寄与条件と本trial RQ対応へ置換提案|現方針との整合FAIL、原本保全PASS|
|R/docs/research/RESEARCH_DESIGN_SUMMARY.md §1/§2/§5/§7|旧RQ/H1〜H3・面接工程・成果構成に定時配達率。現行の研究工程と同一視しない。履歴版を保持して採用後の版更新候補|CONDITIONAL|
|R/docs/research/EXPERT_INTERVIEW_PROTOCOL.md、回答票、分析ガイド|目的・指標・方法の旧面接記録。主研究方法として再採用しない。旧版・未実施状態を明示する候補|CONDITIONAL|
|R/tmp_RsrchMstrDc_1026_results_integrated.docx 序論・問い・方法・結果・考察および付録|序論で定時配達率をサービス水準とする記述が存在。現行A/B/Cの第5章と旧節の付録保存を区別する。目的/RQ/方法/結果見出し/考察主張を本trialに対応させる編集候補を記録。旧A数値や付録を削除しない|CONDITIONAL、未統合|
|R/tmp_RsrchMstrDc_1026_revised.docx / revisions/v07_results_integrated.docx|別候補として抽出・hash保存。mtime順だけで正式最新版を決めない|正式採用版HOLD|
|T/THESIS_TRIAL.docx、T/THESIS_SECTIONS_TRIAL.md|寄与条件中心の独立原稿案。定時率の除外や限界への言及は許容。最新の独立trialであり正式原稿ではない|PASS（位置付け）|
|P/stage0.py、P/FROZEN_PROTOCOL.json、P/statistics_tables.py|Aの主指標PE定時率と旧符号JQ−Jinitialが凍結されている。Pを改変せずStep2で別仕様として再出力|PASS（履歴維持）、流用時CONDITIONAL|
|T/PATH2_BOUNDARY_RESULTS.csv|0.1/0.25/0.4/0.5%はARBITRARY_ILLUSTRATIVE_TARGET。研究の成否判定に用いず、ゼロ境界を主とする|PASS（区別が必要）|

最新原稿の扱い：11月3日の統合記録に対応するルートresults_integratedを正式側の作業候補、11月4日のT/THESIS_TRIALを最新の独立案として両方確認した。版はevidence/MANUSCRIPT_VERSIONS.jsonとSOURCE_PROVENANCE.csvで識別。正式採用を本監査では決めない。

元データにon_time列が残ること、限界で定時配達率を説明することは方針違反ではない。未実証接続を実証結果として記載すること、CPU時間をQPU時間へ読み替えること、任意削減率を成功基準にすることはFAIL。

正式側統合DOCXの具体位置はevidence/POLICY_CLASSIFIED_LOCATORS.csv：目的・指標p11/p23/p27/p45、方法p281、結果p444、考察・限界p856/p1284、旧節・付録p1026/p1180/p1260/p1268/p2319。段落番号は表内も含むXML順でWord画面上の段落番号とは異なる。ルート統合版とv07はバイトhashは異なるが、今回抽出した全文（表内含む）は一致した。正式原稿の採用版を自動決定した意味ではない。
