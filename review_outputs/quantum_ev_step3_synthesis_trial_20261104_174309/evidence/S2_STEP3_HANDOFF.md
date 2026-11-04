# Step 3引継ぎ：確定結果と根拠

独立Step2 trial。正式採用は未決定、Step3は未実行。原稿へ直接反映しない。

1. RQ1の主要結果はgreedy対照改善0/36,800、全best可行。初期対照との差と混同しない。規模/設定/反復/入力/seedが残るPATH1_PAIRED_COMPARISONS.csvと112行summaryを使う。主JCを結果を見て変更しない。
2. 厳密参照は414、46HOLD。新規証明7と既存証拠クラス（再列挙234・保存DP78・独立LP61・保存MIPのみ41）を併記。414全てを今回再求解したとは書かない。旧407との指標変化は専用impactCSV。
3. mirror orbit最小=初期を全460で新DP検証。active t0選択。支持制限による不成立と最適化失敗を区別し、Grover大規模悪化をQAOA一般の劣位へ拡張しない。
4. 新統制は3診断input×96方法cell、97learning/cell、10measurement/fit。R1_020 graph basis p1は58/97、p2は78/97、full-projector basis p1は0/97対uniform97/97。各Wilson区間とexact期待値学習の限定を示す。同角度DEPHASEDと別学習DEPHASEDを区別する。
5. CPU時間は新9,603パイプライン記録と旧scope別表。Q/dephased工程は対応、greedy1出力とQ10出力のtotalを公平な1計画speedupとしない。H_plan、QPU/compiled/physical resourcesは未確定。
6. T08主のb≈5.448kg、u*≈.877094、V*≈3.193156、DC総和比≈.412579/.413590%。個別率平均/SD、group感度、K_EM/K_Eqを区別。T09のb≈9.722608/5.977891kgは会計構造依存、完成packはNULL。
7. delta=bでmass/DCが消失し、両側で反転する指定モデル内条件と、1000〜1250kgの920軌跡/Crr正傾き確認を根拠にする。範囲外・回生/補機/勾配/積載変動へ外挿しない。

改善の定義からの同値を新実証と呼ばず、実験で確認した支持/初期/学習依存と、モデル上の感度・未接続を分離する。材料の量子由来改善と実道路運用改善は考察後段で未実証接続として扱う。全HOLD解消をStep3開始条件にせず、各主張の限定を保持する。

参照順：EXECUTIVE_SUMMARY.md → PATH1_STATISTICAL_REPORT.md / QAOA_CONTROLLED_EXPERIMENT_REPORT.md / PATH2_STATISTICAL_REPORT.md → 条件CSV → UNRESOLVED_ITEMS.md → FINAL_AUDIT_REPORT.md。図表はFIGURE_INDEX.csvから対応CSV/スクリプトを辿る。
