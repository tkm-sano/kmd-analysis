from evidence import *
t=time.monotonic();pp=rows(O/'DOCX_PARAGRAPHS.csv');changes=[]
def add(start,end,action,section,reason,draft,fig='',claims=''):
 x=pp[start];changes.append({'paragraph_index0_start':start,'paragraph_index0_end':end,'original_style':x['style'],'exact_anchor':x['text'][:150],'action':action,'proposed_section':section,'change_and_reason':reason,'draft_file_and_heading':draft,'figure_or_table_id':fig,'claim_ids':claims,'original_docx_sha256':sha(use(DOC)),'status':'PLANNED_NOT_EDITED'})
add(19,19,'KEEP_WITH_SCOPE_NOTE','目的','2経路と成立条件という目的は維持。量子優位実証を目的に追加しない。','07_THESIS_CONCLUSION_DRAFT.md','F3-1;F3-2')
add(21,27,'REVISE','目的・分析範囲','研究対象の広い概念範囲と、実際に定量評価したA/B/Cの範囲を分ける。両経路を実世界で一貫実証した印象を避ける。','04_THESIS_METHODS_DRAFT.md §3.1','T3-1','A01;B10;C06')
add(34,150,'HOLD_CITATIONS','2 先行研究','背景の8引用と末尾文献の対応、Faraji-Niri DOI、単位・用語を確認。章全体の引用の真偽を今回全面保証しない。','LITERATURE_VERIFICATION.csv')
add(174,176,'REPLACE','3.1 対象範囲','新全件結果と観測・導出・条件付き・未検証・不適合の証拠範囲を追加。','04_THESIS_METHODS_DRAFT.md §3.1','F3-1;F3-2')
add(177,184,'KEEP_AND_QUALIFY','3.2 道路網','N0受入FAILとN1動的FAILを維持。地域走行の主分析として受入れた道路網と読ませない。PLATEAU生成不足はHOLD。','04_THESIS_METHODS_DRAFT.md §3.1','T3-1')
add(185,193,'KEEP','3.3 需要生成','原資料の生成・需要PEと限界を維持。PEをkgに換算しない。現実確率標本という解釈を追加しない。','04_THESIS_METHODS_DRAFT.md §3.4')
add(194,200,'REPLACE_AND_MOVE_OLD','3.4 実験系列','旧465負荷・548入力・R4=99の補助系列を履歴付録へ。A78、現行B460、旧C460速度の相違を表3-1で明示。','04_THESIS_METHODS_DRAFT.md §3.4','T3-1','B07')
add(201,208,'REVISE','3.5 問題定式化','J+102n帰庫式は時間窓なしBに限定。Aはmax待機再帰を使う。DOCX内OMMLを保持して数式を置換・追加。','04_THESIS_METHODS_DRAFT.md §3.5・§3.8','F3-1','A05')
add(209,213,'KEEP_AND_DISTINGUISH','3.6 古典参照','初期解、mirror支持最小、旧CPU対応改善920行、global厳密407を区別。53を推定で埋めない。','04_THESIS_METHODS_DRAFT.md §3.6','T5-2','B03;B07')
add(214,228,'MOVE_OR_LABEL_OLD','3.7 旧量子方式','旧one-hot直接p1、圧縮Groverp1、局所ブロック方式は既存補助結果として付録へ整理。現行8設定のp2/p3・支持と混同しない。','04_THESIS_METHODS_DRAFT.md §3.13','T5-1')
add(229,233,'REPLACE_MAIN_AND_MOVE_HISTORY','3.8 固定ODによる採用政策・配送成果','現見出しはSUMO接続。旧native生成条件と作業完了候補は履歴付録へ移し、全件固定ODの正式計算を主節へ。stop endedを引渡し完了へ変換しない。','04_THESIS_METHODS_DRAFT.md §3.8','F3-1','A01..A07')
add(234,247,'KEEP_AND_COMPLETE','3.9 材料質量','T08/T09と未知部材の説明は維持し、パラメータ・既知差・完成packHOLDを新表へ整合。既存OMML数式を不足と誤判定しない。','04_THESIS_METHODS_DRAFT.md §3.9','F3-2;F5-6','C01;C03..C06')
add(248,260,'KEEP_AND_RECONCILE','3.10 Controlled-DC','凍結式を維持。合計後正値化、末端unknown、Crr envelopeと空荷境界を明記。T08/T09の量を分離。','04_THESIS_METHODS_DRAFT.md §3.10','F5-7;FA-1','C02;C04')
add(261,263,'UPDATE_ENVIRONMENT_SCOPE','3.11 環境','旧実験環境と今回の算術・描画環境を別表。未保存の全fit環境を現環境で補完しない。','04_THESIS_METHODS_DRAFT.md §3.11','T5-3','B08')
add(264,273,'REPLACE','3.12 評価と統計','固定有限cohort主・25群補助bootstrapを追加。旧の区間推定なしという文章は全件分析の補助区間と整合させる。検定は0。','04_THESIS_METHODS_DRAFT.md §3.12','TA-3','S01;S02')
add(274,279,'RESTRUCTURE','3.13 11月追加系列','旧11/1 swap460、CPU対照、全seed96600等を別版・補助として残す。今回8設定/36800主参照へ主節を更新。独自N1等の証拠記号と道路版N1の衝突に注意。','04_THESIS_METHODS_DRAFT.md §3.13;ALGORITHM_PROTOCOL_APPENDIX.md','F5-1;F5-3','B01..B08')
add(280,285,'UPDATE','4 再現性','4段階評価を維持。保存結果再現・入力再実行と原資料再生成・実世界妥当性を分離。以前の原稿編集のみという履歴を今回の全件算術と区別。','09_FINAL_QUALITY_REVIEW.md')
add(287,293,'REPLACE_MAIN_AND_MOVE_OLD','5.1 B','旧小規模直接・局所548結果を主8設定と混ぜず付録へ。407/53・全規模別結果と工程資源を追加。','05_THESIS_RESULTS_DRAFT.md §5.1','F5-1..F5-3;T5-1..T5-3','B01..B08')
add(294,295,'ADD_HEADING_AND_REPLACE','5.2 A（現状見出し欠落）','5.1内の旧A64/zero-departure proxyを独立5.2へ。3133秒は新固定OD、3099秒は旧native候補と明記し、後者を履歴付録へ。','05_THESIS_RESULTS_DRAFT.md §5.2','F5-4;F5-5;TA-1','A01..A07')
add(296,299,'REVISE','5.3 C','T08数値の精度・分母・T09未知183/FAIL1を整合。bridge既存probeを実packとしない。','05_THESIS_RESULTS_DRAFT.md §5.3','F5-6;F5-7;FA-1;T5-4','C01..C05')
add(300,305,'MOVE_TO_APPENDIX','5.4旧補助系列→付録','旧548局所、相互依存の外部検証、旧whole adjacent inactive、96600全対照seedを履歴別表へ。新5.4は補助不確実性と未評価を記す。','05_THESIS_RESULTS_DRAFT.md §5.4','TA-3','S01')
add(307,311,'REPLACE','6.1 配送計画','採用と固定OD時刻差、待機吸収の証拠、指標飽和を記載。Δ帰庫=Δ出発−ΔOD短縮は待機差0に限定し+Δ待機を追加。','06_THESIS_DISCUSSION_DRAFT.md §6.1','F5-4;F5-5','A04..A08')
add(312,318,'RELOCATE_AND_SCOPE','6.2 材料と成立境界','b−δの式は維持し材料節へ。旧枝導関数の特定数値・電圧閾値は今回結果にない補助履歴として出典を残す。新たな実車一般化にしない。','06_THESIS_DISCUSSION_DRAFT.md §6.2','F5-6;FA-1','C03;C04')
add(319,323,'REVISE','6.2 材料・DC','旧5経路の速度差・幾何診断を補助と区別。Bへ流用しない。既知/未知とT08簡略会計の限界を考察する。','06_THESIS_DISCUSSION_DRAFT.md §6.2','F3-2;F5-7','C01..C06')
add(324,327,'REPLACE_AND_ADD','6.3統合、6.4統計・外的妥当性','旧アーキテクチャ数値は旧系列付録。正の遅延nativeは未取得だが固定OD全件結果は新たにあると更新。H1〜H3・面接計画M0を実施済みにしない。','06_THESIS_DISCUSSION_DRAFT.md §6.3・§6.4','T3-1','B09;B10;C06;S01')
add(328,333,'REPLACE','7 結論','新全件数値と2経路の証拠到達段階に直接回答。量子優位、実配送、実EV、完成pack改善を主張しない。','07_THESIS_CONCLUSION_DRAFT.md','F3-1;F3-2','A08;B09;B10;C06')
add(334,397,'RECONCILE','参考文献','本文・末尾の双方向対応、年、著者、DOIを確認。Field/Welshを補助統計に追加。現在の出典記号と著者年引用を統一。','LITERATURE_VERIFICATION.csv')
add(398,413,'APPEND','付録A-1','新レビュー実パスと外部保全の非公開性を追記。元成果物を公開Git内と偽らない。','00_SOURCE_AND_RESULT_INVENTORY.md')
add(414,533,'RECONCILE','付録A-2 主張証拠','新26主張のclaim IDと旧証拠IDの対応を整理。既存IDを黙って異なる実験へ使い回さない。','02_CLAIM_EVIDENCE_MATRIX.md')
add(534,581,'APPEND','付録A-3 SHA','今回入力・生成コード・図表hashと参照リビジョンを追加。自己hash循環を避ける。','SHA256_MANIFEST.csv')
add(582,606,'APPEND','付録A-4 再生成','元科学runnerと今回描画・原稿生成を別の入口として列挙。図10点と表・全区間を付録へ。','09_FINAL_QUALITY_REVIEW.md','TA-1..TA-3;FA-1')
add(607,609,'KEEP_LABEL_OLD','付録A-5 旧局所','旧局所3seedの分母・compiled resourceを今回B8設定の保存資源に転用しない。','01_ACADEMIC_INTERPRETATION_REVIEW.md')
table('DOCX_INSERTION_MAPPING.csv',changes)
s=f'''# DOCX反映対応表（読み取り専用レビュー）

対象 `{DOC}`、SHA256 `{sha(DOC)}`。610段落・8表、段落番号は0始まりでありWordのページ番号ではない。段落番号は原DOCXのこのhashにのみ対応する。実編集ではexact_anchorを再照合してから適用する。OMML数式は別抽出で確認し、python-docxの本文文字が空という理由で「数式が欠落」と判断していない。

現稿は方法・結果・考察・結論を既に持つ。目的と既存の条件付き表現は維持し、主分析に変わった箇所を更新する。3.8は見出しから差し替え、現在欠落する5.2を見出し2で追加する。章2の一部はnormal styleであり、次回は見出しstyle・目次・相互参照を合わせて確認する。Wordを保存・変換・編集していないため、ページ内配置の受入はHOLDである。

'''
for x in changes:
 s+=f"## {x['proposed_section']}：{x['action']}\n\n- 原段落：{x['paragraph_index0_start']}〜{x['paragraph_index0_end']}（{x['original_style']}）。原文アンカー「{x['exact_anchor']}」。\n- 修正：{x['change_and_reason']}\n- 転記元：`{x['draft_file_and_heading']}`\n- 図表：{x['figure_or_table_id'] or 'なし'}。主張：{x['claim_ids'] or '構成・出典整理'}。\n\n"
s+='''## 既存8表の扱い

|表index0|現内容|次回の扱い|
|---|---|---|
|0|旧系列のコホート表|表3-1へ更新し旧548等は履歴付録へ|
|1|需要生成|維持、PEと統計単位の説明を整合|
|2|材料パラメータ|維持、T08/T09別、未知と出典を追加|
|3|旧小規模直接比較|履歴付録へ移動、新B表5-1/5-2とは分ける|
|4|旧局所548結果|履歴付録へ、現行460へ転用しない|
|5|材料・DC|新表5-4とT09既知/未知を整合|
|6|11月補助方式|主8設定と別対照の範囲を明記して再編|
|7|旧局所最適一致|付録として維持、今回407分母と混ぜない|

全体の章・図表番号を確定した後、見出しstyle、図表キャプション、本文相互参照、目次、数式の添字、フォント、印刷幅をWord上で検証する。図のSVG/PDF単体受入とDOCX組版の受入を分ける。背景引用8件の照合、用語の「定時配達率」「モデル上の配達完了」「CPU工程時間」の統一をDOCX転記前に行う。
'''
doc('08_DOCX_INSERTION_MAP.md',s)
# Pin each original protocol and its source snapshot; no import/execution.
protos=[];snap=[]
for folder in ['mirror_family','grover_depth','active_adjacent_p3']:
 p=use(S/folder/'PROTOCOL.json');v=js(p);protos.append({'family':folder,'path':str(p),'sha256':sha(p),'configuration':v})
 for q in (S/folder/'SOURCE_SNAPSHOT').rglob('*.py'):
  use(q);snap.append({'family':folder,'path':str(q),'sha256':sha(q),'role':'READ_ONLY_IMPLEMENTATION_SNAPSHOT_NOT_EXECUTED'})
dump('ALGORITHM_PROTOCOLS_PINNED.json',protos);table('ALGORITHM_SOURCE_SNAPSHOTS.csv',snap)
ps='# アルゴリズム設定の再実行用付録\n\n以下は元凍結PROTOCOL.jsonを読み取った設定である。今回再学習や回路計算は行っていない。FIT.jsonごとの選択角度・精度・seed・training pool hashはB_RESOURCES_PER_FIT.csvのfit_source_pathから参照できる。全fitの値を単一の推定値に置き換えない。元コードのSHA256はALGORITHM_SOURCE_SNAPSHOTS.csv。ファイルが外部保全にある点は公開再現性の制約である。\n\n'
for x in protos:ps+=f"## {x['family']}\n\n`{x['path']}` SHA256 `{x['sha256']}`\n\n```json\n{json.dumps(x['configuration'],ensure_ascii=False,indent=2)}\n```\n\n"
ps+='''## 本文3.13へ追加する説明

mirrorは経路位置iとn−1−iの互いに素なpartial swapを二値の向きへ同型変換した支持を用いる。各入力の元有向OD費用を整数Decimal演算で二値chainの単項・二体項へ折り込み、同支持の古典chain-DP最小を対照とする。単一基底初期状態では第1位相が大域位相となるためγ1=0であり、COHERENT2/4は2/4初期状態を用いる。層数2、角度範囲・開始格子・COBYLA最大評価数は上記固定設定に従う。CVAR学習は1024shotと共通乱数を使い、最終8192shotの測定とは分ける。全件のtraining_mode99と代表点に限る追加学習seedを混合しない。

Groverは理想的な全順列一様初期状態とn!支持のモデルを用い、主cohortでは既存65536費用の学習poolを保持する。p=2/3、解析的な最後のβと2開始点のCOBYLA、最大68固有評価という固定予算である。n≤25の最終検証は保存complex subset-DP、n>25は別一様MCの共通prefixと事前3精度を用いる。学習・最終検証・Born測定の乱数を区別し、global角度最適を証明したとはしない。

activeはgammas=[0,0.009,0.017]、base betas=[0.07,0.09,0.11]とし、betaをt∈{0,0.5,1}で尺度変更する3点gridで保守的な期待費用上界を選ぶ。連続最適化や全角度最適を主張しない。rank64のactive-label MPSとtruncation誤差条件は元コード・PROTOCOLの通りである。これらのソフトウェア上の状態表現の大きさを、そのまま実装済み量子ハードウェア資源に読み替えない。
'''
doc('ALGORITHM_PROTOCOL_APPENDIX.md',ps)
finish('INSERTION',t,{'mapped_sections':len(changes),'protocols':len(protos),'source_snapshot_files':len(snap),'docx_written':False})
