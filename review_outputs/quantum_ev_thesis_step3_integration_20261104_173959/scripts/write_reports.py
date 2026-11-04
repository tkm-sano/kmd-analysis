from pathlib import Path
import csv,json,shutil,hashlib,re
O=Path(__file__).resolve().parents[1];R=O.parents[1];S=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535'
def md(name,text):(O/name).write_text(text.strip()+'\n')
def csvout(name,rows):
 with(O/name).open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
claims=[]
def cl(id,text,status,kind,files,locator,scope,limit,where):
 paths=[S/f for f in files.split(';')] if files else []
 assert all(p.is_file()for p in paths),(id,paths)
 claims.append(dict(claim_id=id,claim=text,judgment=status,evidence_type=kind,source_paths=';'.join(map(str,paths)),source_sha256=';'.join(hashlib.sha256(p.read_bytes()).hexdigest()for p in paths),row_or_calculation=locator,scope=scope,limitations=limit,thesis_location=where))
cl('P1-01','460入力×8設定×10測定、36,800保存bestは可行、主greedyへの正改善0件','PASS','保存測定・有理数再計算','PATH1_PAIRED_COMPARISONS.csv;PATH1_INPUT_CONFIG_STATISTICS.csv','classical_baseline=ITERATED_GREEDY_ADJACENT_SWAP;DeltaJ=JC−JQ;original NPZとFraction照合','時間窓なしB、保存bestの有限cohort','raw全shot、未見入力、量子計算一般には適用しない','3.4–3.8;5.1')
cl('P1-02','R5 Grover p2の入力平均−5983.706453s、入力間sample SD1314.364537s','PASS','対応記述統計','PATH1_INPUT_CONFIG_STATISTICS.csv;PATH1_STATISTICAL_RESULTS.csv','R5/GROVER_P2/主greedy、10測定を入力内平均後70入力等重み','保存70入力','70×10を700独立入力にしない','5.1;図5-1')
cl('P1-03','需要group再標本化感度区間−6516.668692〜−5515.460176s','CONDITIONAL','補助再標本化','PATH1_UNCERTAINTY_INTERVALS.csv;STATISTICAL_METHODS.md','10,000 resamples/PCG64 seed20261102、group再標本化を独立再現','保存需要群と手順','実配送母平均の信頼区間ではない','3.8;5.1')
cl('P1-04','参照414、未証明46、414の内41は保存MIP等値証拠に条件付き','CONDITIONAL','参照証拠層別','EXACT_REFERENCE_STATUS.csv;EXACT_REFERENCE_STATISTICAL_IMPACT.csv','234列挙+78保存整数DP+61独立有理双対+41保存MIP=414','460入力','373強化参照と41条件付き参照を区別','3.6;5.2;表5-2')
cl('P1-05','独立有理数双対によって旧未証明53中7入力を追加証明','PASS','独立双対・巡回路等値検算','EXACT_REFERENCE_RECHECK_RESULTS.csv;EXACT_REFERENCE_BOUND_COMPARISON.csv','R4_021,030;R5_019,024,052,062,063;dual feasible and objective=valid witness','指定7保存入力','新しいsolverによる再求解ではない','3.6;5.2')
cl('P1-06','旧53入力はSCIP optimal終了後も保存下界と巡回路有理目的値に不一致','PASS','保存終了状態診断','EXACT_REFERENCE_FAILURE_AUDIT.md;EXACT_REFERENCE_RECHECK_RESULTS.csv','statusおよびexact witness/bound差の保存監査','旧53入力','単純なタイムアウトとしない','3.6;5.2')
cl('P1-07','追加統制は3診断入力・合計96条件・9,312fit・93,120測定','PASS','raw出力照合','experiments/QAOA_MAIN_FITS.csv;experiments/QAOA_MAIN_MEASUREMENTS.csv','96×97;各fit10測定×8192shots;全raw histogramのbestを独立再構成','指定3小規模入力、CPU exact期待値','97learningと10measurement streamを区別','3.12;5.3')
cl('P1-08','R1_020全支持・基底・graph p1=58/97,p2=78/97','PASS','取得件数とWilson算術','QAOA_CONTROLLED_CELL_SUMMARY.csv;experiments/QAOA_MAIN_MEASUREMENTS.csv','primary rep0、Wilson 95%p1[49.8437,68.9978]%,p2[71.4216,87.0861]%','指定入力/開始角分布/8192shots','主greedyが既に最適。外部母集団や優位性の証明ではない','5.3;表5-3;図5-2')
cl('P1-09','取得確率の差を主greedyへの解品質改善と読み替えない','PASS','指標定義・対照の最適性','QAOA_CONTROLLED_EXPERIMENT_REPORT.md;QAOA_CONTROLLED_CELL_SUMMARY.csv','3診断入力のgreedy目的値=global optimum、ΔJ≤0','指定目的関数と3入力','干渉の一般的効用・不可能性は導かない','5.3;6.2')
cl('P1-10','9603工程記録、固定4顧客例Q34.643ms/D35.014ms中央値','PASS','CPU実測の再集計','PATH1_RUNTIME_RESULTS.csv;PATH1_RUNTIME_PROTOCOL.md','R1_001/FULL_PERMUTATION/UNIFORM_SUPPORT/PROJECTOR/p2/97 each,total wall ms','学習+10測定の指定CPUパイプライン','import/initialgeneration/転送/queue除外、greedy出力数相違','3.11;5.4;図5-3')
cl('P1-11','運用計画時間条件τ_total≤H_plan','CONDITIONAL','適用条件の定義','STEP2_CONTRIBUTION_CONDITIONS_SUMMARY.md','必要な全工程と運用締切を含める','計画適用の前提としての条件式','H_plan未設定、数値閾値未同定。十分条件ではない','3.11;6.2')
cl('P1-12','H_plan・実出発・配送成果への計測接続','HOLD','未検証','UNRESOLVED_ITEMS.md','H05','対象業務','32400s帰庫期限を代用しない','5.7;6.6')
cl('P1-13','QPU実機時間・物理量子ビット・量子優位性を実証した','NOT CLAIMED','対象外への帰属','UNRESOLVED_ITEMS.md','H06/CPUとQPUの区別','本研究の実証範囲外','CPU模擬・未コンパイルから断定しない','3.7;5.4;7')
cl('P2-01','T08相殺境界5.448297415kg、u*=.877094072、V*=3.193155684V','CONDITIONAL','固定設計・材料換算','PATH2_BOUNDARY_ANALYSIS.csv;PATH2_SENSITIVITY_SUMMARY.csv','Eg20kWh、q参照値、V3.5/u1;一変数境界は他条件固定','T08簡略会計、検証入力範囲','完成packの実測値・量子材料改善ではない','3.9;5.5–5.6')
cl('P2-02','460軌跡×2CrrのDC総和比0.412579010/0.413590412%','CONDITIONAL','保存速度・凍結DCモデル','PATH2_OPERATION_CONDITION_ANALYSIS.csv;PATH2_SENSITIVITY_RESULTS.csv','T08 LP対S endpoint;100ΣΔE/ΣELP','共通旧古典460速度・固定物理','実EVの電力量・新Bルートの効果ではない','5.5;表5-5')
cl('P2-03','個別DC削減率平均.409329419/.410435042%、SD.012172392/.012017831pp','CONDITIONAL','軌跡間記述統計','PATH2_OPERATION_CONDITION_ANALYSIS.csv','個別率の算術平均・sample SD、460/各Crr','保存軌跡の決定論的モデル','総和比と個別平均を区別、SD単位pp','5.5;表5-5')
cl('P2-04','T09既知部材差9.722608121/5.977891152kg','CONDITIONAL','構造依存既知小計','PATH2_BOUNDARY_ANALYSIS.csv;PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','固定担持/固定面積、代表B015/B051','T09部材会計','T08との完成pack性能比較をしない','5.6;表5-6;図5-4')
cl('P2-05','T09完成パック質量はNULLのまま保持','HOLD','未知BOM','UNRESOLVED_ITEMS.md;PATH2_MODEL_UNCERTAINTY.md','H09;183詳細入力のnullを検算','未知外装/タブ/余白/BMS/構造等','T08固定34kgを重ねて補わない','3.9;5.6;6.3')
cl('P2-06','指定会計でΔM=b−δ、δ=b消失、δ>b逆転','CONDITIONAL','数学的恒等式とモデル境界','PATH2_BOUNDARY_ANALYSIS.csv','b=MLP,known−MS,known;δ=MS,unknown−MLP,unknown','指定部材会計、固定他条件','δが実測されたことを意味しない','3.13;5.6;6.3')
cl('P2-07','固定物理・検証1000〜1250kgで920軌跡条件のDC質量傾きは正','CONDITIONAL','Controlled-DCの質量感度','PATH2_OPERATION_CONDITION_ANALYSIS.csv','全920正、最小0.827572648Wh/kg;正値化は合計後','保存速度460×2Crrと凍結物理','回生/勾配/補機/末端/実車へ外挿しない','5.6;6.3')
cl('P2-08','距離・再発進・速度とDC差の相関は運転介入の因果効果ではない','CONDITIONAL','保存軌跡の分布・相関','PATH2_OPERATION_PAIRED_FEATURES.csv;PATH2_OPERATION_STRATA.csv','同一軌跡対応、規模・群交絡を留保','旧速度の分布','走行要因の独立操作実験なし','3.13;5.6;図5-5')
cl('P2-09','量子計算が実材料を改善し実EVのDC削減を実現した','NOT CLAIMED','帰属未検証','UNRESOLVED_ITEMS.md','H08,H10,H11,H12','本研究の実証外','ChenのDFT・halfcell実験と量子計算を混同しない','3.9;6.3;7')
cl('S3-01','両経路の能力・適用・成果を分け媒介条件を比較する','CONDITIONAL','今回新たに作成した統合解釈','CONTRIBUTION_CONDITION_TABLE.csv;STEP3_HANDOFF.md','今回第6章の比較表とRQ回答；Step2はStep3未実行','固定された二経路の分析構造','社会技術システム全体の転換・普及を実証しない','2.4;6;7')
cl('S3-02','社会制度・市場・普及過程全体を再現・実証した','NOT CLAIMED','研究境界','UNRESOLVED_ITEMS.md','本研究は設計運用条件B中心、導入普及条件Aは内生化なし','研究目的の範囲外','MLP/TISを定量実装したとは主張しない','1.3;2.4;6.5–6.6;7')
csvout('CLAIM_EVIDENCE_LEDGER.csv',claims)
# user can follow original requirement filename too; same exact content, explicit alias.
shutil.copyfile(O/'CLAIM_EVIDENCE_LEDGER.csv',O/'CLAIM_EVIDENCE_MATRIX.csv')
changes=[
('要旨・第1章','改善・旧指標と条件評価が併存','寄与成立・不成立・消失/逆転、RQ0–RQ3、主指標から定時率除外','最新研究方針と結果の非優位性を整合','ABSTRACT;CHAPTER1'),
('旧2.1','一般理論・EV研究混在','一般理論→2.1、EV物流→2.3','説明対象を分離','L01–L03,L11,L13–L15'),
('旧2.2','量子ELSI・社会影響','問題設定に必要な不確実性のみ2.1へ圧縮','未モデル化の普及過程を実証扱いしない','L04,L05'),
('旧2.3','量子アーキテクチャ・FTQC','3.7/3.11の実装と資源境界へ','CPUとQPU資源を区別','ALGORITHM source snapshots;T04'),
('旧2.4','技術成果と利用','新2.1/2.4の能力・成果・媒介関係へ','レビュー中心問いを明示','L01,L06–L09'),
('旧2.5','QAOA等アルゴリズム','3.7、旧one-hotは付録B.1へ','主系列と旧系列を混ぜない','T01–T03;原218–225'),
('旧2.6','配送・電池技術','一般物流→2.3、材料設計→方法3.9','一般研究と本研究固有式の分離','L13–L15;T05,T06'),
('旧2.7','モデルの一般論・実施法','一般論→2.1.3、実施→3/4章','妥当性と算術再現を区別','L06;凍結DC'),
('旧2.8','旧位置づけ','新2.4.1–2.4.4・横断表2-1','A普及/制度とB設計/運用の区別','文献台帳13主要文献'),
('第3章','407参照、初期対照の主差、旧資源等','主greedyとΔJ、414/41/46、統計単位、96統制条件、工程、T08/T09/固定DC','現行解析との不整合解消、既存数式保持','Step2各protocol;原方法OMML'),
('第4章','旧全件監査・原稿統合','既存全件検証、Step2、新Step3の別工程','Step2がStep3完了と誤記しない','STEP3_HANDOFF;今回検算'),
('第5章','旧407/53・旧統計・旧図表','検証済36800、R5、414/41/46、統制・時間・質量/DC境界','結果中心、解釈は第6章へ','P1/P2 claim ledger'),
('第6章','旧条件考察','6.1–6.6の新Step3統合、二経路比較、社会技術的範囲','技術能力から成果への未接続を見える形にする','S3-01;表6-1'),
('第7章','旧結論と数値','RQ0–RQ3へ暫定回答、実証/条件/未検証を分離','非優位性を結果として保持','全主要主張'),
('参考文献','旧73書誌段落、同定HOLDを含む','13主要＋10技術、旧73は処置台帳と元原稿に保全','未同定Papachristosを新論証から外す、類似文献補填なし','LITERATURE_SELECTION_LEDGER'),
('付録','重複した旧章・図表・数式','A根拠ID/B旧A仕様/C全48設定/D管理範囲','主系列を混同せず現行方法42OMML保持、歴史的44は原DOCX保存','DOCX_BUILD_LEDGER;数式監査')]
csvout('CHAPTER_STRUCTURE_COMPARISON.csv',[dict(chapter=a,before=b,after=c,reason=d,evidence=e)for a,b,c,d,e in changes])
md('CHAPTER_STRUCTURE_COMPARISON.md','# 更新前後の章・節構成\n\n'+'\n\n'.join(f'## {a}\n\n変更前：{b}。\n\n変更案：{c}。\n\n理由：{d}。根拠：{e}。'for a,b,c,d,e in changes))
md('STEP3_INTEGRATED_DISCUSSION.md','# 今回実施したStep 3の範囲\n\nStep 2のSTEP3_HANDOFFはStep 3未実行と明記している。本報告の考察は今回新規作成した解釈であり、新しい量子性能や実車効果の実験ではない。\n\n'+(O/'drafts/CHAPTER6.md').read_text()+'\n\n## RQへの回答\n\n'+(O/'drafts/CHAPTER7.md').read_text())
md('WORD_CHANGELOG.md','''# Word変更履歴

元原稿はsources/ORIGINAL_THESIS.docxへbyte同一コピーした。元のstyles、テーマ、フォント宣言、関係部品をベースに独立DOCXを作成した。既存原稿は上書きしていない。

第1・2・4〜7章を整合的に改稿し、第3章は対象地域・需要・数理問題・材料・Controlled-DCの既存XMLを再使用した。旧one-hotと固定OD政策を付録Bへ移した。本文42個の原OMMLを維持し、新規3式は編集可能なOMMLとして追加した。旧付録にのみある44式は重複・歴史的仕様として元DOCXへ保全し、新本文に無条件で再掲していない。照合結果はDOCUMENT_AUDIT.jsonを参照する。

再配置に伴い原p210の3.8節参照を付録B.2、p225の現行8設定参照を3.7節、p233の旧「主指標」を「この旧系列の補助指標」へ変更した。旧図3-1を図B-1へ改番した。原図3-2と需要表3-2は保持した。コピーした内容の版はDOCX_BUILD_LEDGER.jsonの原段落indexで追跡する。

既存9sectionの縦横混在から、改訂本文と付録をA4縦に統一した。既存1inch余白、ArialおよびArial Unicode MS宣言、既存見出しstyleを維持した。新図6点と新しい編集可能な表10点を配置した。段落間隔を直接指定して日本語の行重なりを防ぎ、表には繰返し見出しと行分割禁止を設定した。自動採番を偽装せず、図表は手動一意番号・bookmark・本文内リンク、数式は既存OMMLと新3式の番号を管理した。目次は章レベルの固定見出し一覧で、未更新のページ番号を載せていない。

原脚注の有無・関係部品・外部ハイパーリンク・既存数式・全画像は文書監査で確認した。元原稿に存在しない脚注を新設していない。Wordネイティブアプリでの最終表示は未実施であり、LibreOfficeのPDFと全ページ画像で確認した。フォント代替によるWordとの改ページ差は残る。

文献訂正はBIBLIOGRAPHIC_CORRECTIONS.mdに記録する。L14誤取得資料は使用前に棄却し、正しいタイトルの著者公開版を採用した。Papachristos（2018）は同定不足のため新論証には使用せず原引用を元DOCXに保全した。
''')
md('SOURCE_FIELD_SEMANTICS.md','''# Step 2の保存列名に関する注意

追加統制実験の集計列exact_success_probability_best8192は、controlled_qaoa.pyの実装では主greedyより厳密に小さいcostの確率質量から算定されている。列名だけからglobal最適解取得確率と解釈してはならない。今回の最適解取得率はraw測定のprimary_rep0_optimalを独立に再構成して用いた。

この違いは3診断入力では特に重要である。主greedyが既に最適であるため、厳密改善の確率は0であっても、最適解を取得する確率は0とは限らない。保存出力を変更せず、本文・図5-2・表5-3の意味を取得件数とWilson区間へ固定した。

旧主系列のDEPHASED_RANDOM_SWAPと、新統制の層ごとの別学習脱位相対照は異なる対照である。同角度の脱位相診断と、別学習後の比較も区別した。
''')
holds=[
('H01','46入力の最適参照未証明','全460のglobal gap/一致率を確定できない','ゼロ許容の整数・有理数最適証明。大規模再求解は今回不要'),
('H02','保存MIP等値41の外部証明未実施','414参照を全件独立証明と呼べない','外部VIPR等。373強化参照感度を併記'),
('H03','旧8設定と古典の予算完全統制なし','公平な総性能順位を結論にできない','同支持・出力数・全工程予算を合わせた将来試験'),
('H04','未見入力・全量学習安定性','3診断入力の97学習の外へ取得率を一般化できない','独立入力/開始分布・学習shot noiseの検証'),
('H05','H_plan/真の全工程取得時間/運用時刻','計算時間による実出発・配送成果効果未同定','業務締切と全工程の測定。32400秒を代用しない'),
('H06','QPU/コンパイル/物理資源','CPU模擬から実機条件を確定できない','回路・compile・誤りモデル・実機計測'),
('H07','旧raw shotの可行率一部未保存','best可行と全shot可行を同一視できない','保存sampleの範囲を限定した将来監査'),
('H08','半電池参照から実用fullcellへの移行','入力qと利用率・電圧が実用条件で同時成立するか未検証','形成・Li在庫・密度・寿命・安全等の独立根拠'),
('H09','T09未知BOM/完成パック質量','既知差bを完成pack軽量化へ無条件帰属不可','外装/タブ/箔余白/冷却/BMS/構造の設計・実測；NULL保持'),
('H10','量子計算から実材料改善への接続','条件付きDC差を量子達成効果とできない','計算精度と材料設計・試作結果の独立接続'),
('H11','地域道路受入/実車/新B→走行DC','実EV削減率・地域因果効果を実証できない','道路受入と車両校正、Bの軌跡への別接続'),
('H12','未観測末端・除外物理','全行程・回生/補機/勾配/積載変化へ外挿不可','別モデルとして検証；凍結Controlled-DCは変更しない'),
('H13','主要候補L12の一次本文確認','主要レビューから除外し新論証に使っていない','一次論文本文確認。被引用数だけで採用しない'),
('H14','Papachristos2018の原引用意図','旧同定HOLDは未解消','研究者の原引用根拠確認。似た同年論文で補填しない'),
('H15','Wordネイティブ表示と研究者による採否','LibreOffice表示とWord表示の完全同一は未保証','MS Wordで表示・リンク・改ページを確認し個別採否を判断'),
('H16','原資料→地域網/需要の完全再生成','保存結果算術PASSを研究全体再現PASSとできない','旧原表セル・中間parquet・生成器・処理順等を回収')]
csvout('HOLD_REGISTER.csv',[dict(id=a,item=b,impact=c,next_work=d)for a,b,c,d in holds])
md('HOLD_UNRESOLVED_ITEMS.md','# 残存HOLDと影響\n\n'+'\n\n'.join(f'## {a}　{b}\n\n影響：{c}。次の作業：{d}。'for a,b,c,d in holds)+'\n\n道路受入不成立とT09 row183の全面対向条件不適合を肯定的結果へ変更していない。現在の主要主張判定はPASS/CONDITIONAL/HOLD/NOT CLAIMEDである。\n\nStep 2のH13（原稿統合・採用）は、今回独立原稿を作成した部分のみ実施済みであり、正式採用は未決定である。')
shutil.copyfile(O/'HOLD_UNRESOLVED_ITEMS.md',O/'UNRESOLVED_ITEMS.md')
phases=[('Phase1','実施','元908段落/27表/19画像/86OMMLの構造、版と原hashを確認','ORIGINAL_STRUCTURE.csv;CHAPTER_STRUCTURE_COMPARISON.csv'),('Phase2','条件付きで実施','13主要文献を一次資料の確認範囲付き採用、単一DB基準、旧引用再配置','LITERATURE_SELECTION_LEDGER.csv;drafts/CHAPTER2.md'),('Phase3','実施','保存データの461450項目検算、不一致0。原データと報告値を対応','NUMERICAL_AUDIT_CHECKS.csv;CLAIM_EVIDENCE_LEDGER.csv'),('Phase4','実施','Step2根拠から新規Step3考察・経路比較・RQ回答','STEP3_INTEGRATED_DISCUSSION.md'),('Phase5','実施','要旨/1章/方法/結果/考察/結論/参考文献/付録を整合','THESIS_SECTIONS_TRIAL.md;WORD_CHANGELOG.md'),('Phase6','条件付きで実施','独立DOCX/PDF/ページ画像とXML・数値・保全監査、ネイティブWord確認HOLD','THESIS_UPDATED_STEP3.docx;FINAL_AUDIT_REPORT.md')]
csvout('TASK_COMPLETION_MATRIX.csv',[dict(phase=a,status=b,work=c,outputs=d)for a,b,c,d in phases])
md('ADOPTION_REVIEW.md','''# 採用判断のための推奨（正式採否ではない）

A：採用候補は、主36,800計画の非改善、階層的統計単位、ΔJ符号、414/41/46の参照層別、保存数値に一致した図表、CPU測定の範囲表記である。確認範囲を明記した文献再構成と、主張・根拠の対応も採用候補である。

B：条件付き採用候補は、T08/T09の指定部材会計、保存速度のDC感度、相殺・逆転の境界、group補助感度区間、新しいStep3の媒介条件比較である。材料・車両・道路・未知BOM・外部参照証明の留保を本文と同時に採用する必要がある。

C：再検討候補は、原Papachristos引用、L12本文、未見入力への取得率一般化、H_planとQPU資源、T09完成packと実車校正である。今回はこれらを確定結果として扱わない。

D：採用非推奨は、量子優位性達成、量子計算による実材料性能改善、実EVの電力量削減実証、社会技術システム全体の転換実証、T08とT09の完成pack直接順位、36800を独立入力数とする区間推定である。

既存原稿からの具体的変更はCHAPTER_STRUCTURE_COMPARISON.csv、主張別の範囲と根拠はCLAIM_EVIDENCE_LEDGER.csvへ対応する。新たな価値は、技術能力から成果への未検証接続と、条件内の成立/消失/逆転を同じ枠組みで説明した点にある。解取得率が高まっても既に最適な対照を上回れないこと、既知部材の軽量化が未知部材差で相殺されることを、異なる機構として比較した。新しい一般法則の因果実証を主張するものではない。
''')
md('REPRODUCIBILITY_REPORT.md','''# 再現性報告

この改訂は新しい科学実験を実施していない。scripts/audit_evidence.pyは元入力・保存測定・保存証明を読み、461450検査項目を照合した。実行時間は22.30秒、seedを伴う新計算は既存group再標本化の独立再現（PCG64 seed20261102、10000回）である。solver・量子学習・SUMO・実機実験は実行していない。検査項目数は科学的標本数ではない。

主要手順はaudit_evidence.py（検算）、build_tables_figures.py（既存統計から図表）、build_docx.py（原DOCX XML＋改稿本文）、render_docx.sh（PDF）、inspect_render.py（全ページ画像）、audit_document.py（文書監査）である。.conda/bin/python -Bで実行し、追加Python cacheを元研究へ書かない。図表はPNGに加え作成可能なPDF/SVG、表はCSVと編集可能なWord表を保存した。

文献のOpenAlex JSONと一次資料はsources/literatureへ取得日時付きで保存した。台帳は実際の巻年を用い、原著の確認範囲を示す。最初の取得失敗・誤取得を隠さず保存し、成功したretryと正しい一次資料だけを根拠にした。fetch系スクリプトは取得作業の記録であり、将来のネットワーク応答・被引用数は同一とは保証しない。凍結したCSV/JSONが今回の版を定める。

文書生成は原stylesと選択した原XMLを使う。表示検証には既存保全LibreOffice runtimeとPyMuPDFを読み取り利用し、profile/cache/PDF/画像は今回ディレクトリ内へ保存した。Microsoft Wordのネイティブ表示は未確認である。原ファイル同一性はSOURCE_PRESERVATION_REPORT.json、追跡ファイルはTRACKED_PRESERVATION_REPORT.jsonを参照する。

保存結果の算術再現と、原資料からの再生成・現実妥当性を分ける。ローカル外部保全領域へ依存する入力を含み、公開cloneだけで研究全体を再現できるとは主張しない。原地域網・需要の再生成と実車校正はHOLDを維持する。
''')
md('README.md',f'''# 修士論文 Step3統合・独立改訂

対象：{R/'tmp_RsrchMstrDc_1026_results_integrated.docx'}。
元SHA256：53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99f。
保存先：{O}。

目的は、第2章の文献調査、Step2の検証済み結果、新たなStep3統合考察を論文全体へ反映することである。定時配達率を主指標とせず、量子優位性と実材料・実EV効果を断定しない。正式採否は研究者に委ねる。commit/push/公開/外部送信は行っていない。

最初にTHESIS_UPDATED_STEP3.docxとrender/THESIS_UPDATED_STEP3.pdfを参照する。研究上・表示上の留保はFINAL_AUDIT_REPORT.md、HOLD_UNRESOLVED_ITEMS.mdを参照する。

## 成果物対応

- 独立原稿：THESIS_UPDATED_STEP3.docx、THESIS_SECTIONS_TRIAL.md、drafts/。
- 章構成の更新前後：CHAPTER_STRUCTURE_COMPARISON.md/.csv。
- 文献採否と被引用数：LITERATURE_SELECTION_LEDGER.csv、LITERATURE_CROSS_COMPARISON.csv、ORIGINAL_REFERENCE_DISPOSITION.csv、BIBLIOGRAPHIC_CORRECTIONS.md、sources/literature/。
- 主要主張と一次成果物：CLAIM_EVIDENCE_LEDGER.csv（CLAIM_EVIDENCE_MATRIX.csvは同内容の別名）。
- 今回の新Step3：STEP3_INTEGRATED_DISCUSSION.md、ADOPTION_REVIEW.md。
- Word変更：WORD_CHANGELOG.md、DOCX_BUILD_LEDGER.json、DOCUMENT_AUDIT.json。
- 図表：TABLES.json、FIGURES.json、FIGURE_SELECTION.csv、figures/、tables/。
- 検算：NUMERICAL_AUDIT_RESULT.json、NUMERICAL_AUDIT_CHECKS.csv、logs/、scripts/。
- 入力一覧：INPUT_FILE_LEDGER.csv（原パス・SHA256・役割・採否範囲）。
- 監査・HOLD：FINAL_AUDIT_REPORT.md、REPRODUCIBILITY_REPORT.md、HOLD_REGISTER.csv、UNRESOLVED_ITEMS.md。
- 作業状況：TASK_COMPLETION_MATRIX.csv（今回依頼の6Phase）。
- 保全：sources/ORIGINAL_THESIS.docx、GIT_STATUS_START/END.txt、SOURCE_PRESERVATION_REPORT.json、TRACKED_PRESERVATION_REPORT.json。

元原稿から再使用した本文方法42OMMLと元図2点を保持し、旧の重複・歴史的仕様は原DOCXへ保全した。新たに追加した6図・10表の範囲、再構成・移動・除外の理由を台帳で追跡できる。全11表のうち1表は元需要表、全8画像のうち2画像は元図である。

HOLDが残ることと編集作業の実施を区別する。科学的妥当性をファイル生成だけで完了とは判断しない。本成果物は独立した1回のtrialであり、正式な研究成果への採用・統合は未実施である。
''')
print('reports saved',len(claims),'claims',len(changes),'changes',len(holds),'holds')
