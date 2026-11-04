# Step 2 総合監査

**総合判定：TRIAL COMPLETE。研究解釈CONDITIONAL。Task2-1〜2-6は全て作業上COMPLETE。**

このtrialは計画だけではなく、元入力照合、既存統計評価、追加有理数LP、追加QAOA統制、CPU時間、T08/T09感度・走行条件、図表、根拠台帳を実行した。HOLD解消や量子優位性を完了条件にしていない。

## 実行結果と根拠

- Task2-1：旧欠測53はR4=21/R5=32、全てoptimal終了後のExactBound/Witness微小不一致。53の元LP係数/索引/solution/log、全large148モデル、234小規模全列挙、78保存128bit DPの入力/整数scale/実行binary/source/witnessを監査。148を独立有理数LPで再検査し61の等値証明（既存54＋新規7）。新規=R4_021, R4_030, R5_019, R5_024, R5_052, R5_062, R5_063。参照414、残46HOLD。旧407への反例0。41は保存MIP等値のみの条件付き証拠で外部VIPRなし。上下界の証拠強度を分離した。
- Task2-2：B460入力×8設定×10測定=36,800、PKと原NPZ/測定JSONを照合。主greedy正改善0件、全best可行。2対照対応73,600行、input設定対照7,360行、summary112行、interval672行。mean/median/SD/IQR/min/max/取得率/gapと分母を保存。exact414/欠測46を分離し旧407結果も残した。測定10repを独立学習としない。
- Task2-3：小規模3診断input、96cell、97学習start/cell、10測定/fit×8192shots、9,312fit/93,120測定。全条件を保持。R1_020で制限支持最適取得0、全支持でも初期/mixer/layer/最適化に依存。同角度脱位相4,656診断、測定予算感度37,248行。主greedyに正改善はない。direct expm/確率正規化/全支持可行性/shot histogramからのbest再構成を照合。raw std丸め77fitは目的分数一致からpublic SD0へ正規化、raw実験保持。
- Task2-4：旧3680fit/初期460/近似920をscope別集計、新fit9312と新greedy291の計9,603pipeline時間を計測。1thread/同core条件、warmup/pilot別、wall/CPU/内訳。Q/dephasedは対応するがgreedy1出力対Q10出力等の差を明記。H_plan/QPU/compiled/物理資源は未確定。
- Task2-5：旧C460trajectory×2Crr、144parameter case=132,480行、T09共通入力162行。T08主のb≈5.448297kg、u*≈.877094、V*≈3.193156、DC総和比.412579/.413590%を検証。共通fixed/追加unknown/u/V/geometryと運転covariate依存を分析。920のDC(m)正傾きを1000〜1250kgに確認し、delta=bでmass/DC差ゼロ。T09完成packはNULL。
- Task2-6：両経路の条件台帳23行、claim台帳26行を分類。定義/モデル内同値と新しい観測依存を区別。Step3へ使用できる数値・限定・根拠を保存し、統合考察自体は実行していない。

NUMERICAL_VERIFICATION.csvは今回371,371検査行、最終FAIL0。検査行数は独立実験数ではない。CLAIM_EVIDENCE_MATRIX.csvのFAILはQPU時間読み替え・完成pack断定・任意成功基準という棄却解釈を示し、計算失敗を隠してPASSへ変えたものではない。

## 統計と解釈

主DeltaJはgreedy−Q。初期差は補助、最適参照は共通J*。input内10rep→input等重み、25group感度と固定fit測定感度を分離。group区間は実配送母集団の校正済みCIではない。ゼロ改善bootstrapの[0,0]を将来確率0とせず、Wilsonと条件付き測定stream上限を併記。新97はexact期待値・random-start条件の学習反復で、旧10測定とは別。

mirror support最小=初期は全460で新しい独立matching DPを検算したため、支持内改善余地がない不成立条件として使用可。full supportだけでは初期状態/最適化/有限shotsの条件を満たさない。期待値の干渉差をsampled-best対古典近似の改善へ置換しない。

T08モデル計算と材料proxy/仮定、T09既知subtotalとunknown BOM、CPU実測とシミュレーション・bootstrap感度を区別。zero effectはdelta=b、任意0.25%は成功基準不採用。旧Aの時間窓/定時率、旧Cの速度460と新B460、B100顧客と旧99を混合しない。実材料の量子改善・実道路運用改善・実機量子優位は未実証。

## 保全と版

開始HEAD `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`、remoteは`https://github.com/tkm-sano/kmd-analysis.git`。Step1成果物とその読取元を開始hashで照合し、追加元LP/log/solution/DP/sourceを読取前にpinした。SOURCE_PROVENANCE.csvの旧入力/旧trial/コード11,337件は全て終了hash一致、Git追跡100件も全一致。広い既存227,866ファイルのsize/mtime検査は変更0・欠落0（全バイト監査ではなく環境/第三者ツールを除外）。trial外Git変化追加0/除去0、tracked diffは開始時と同一。

新trial内の中間派生物/コードの使用時hashはSOURCE_HISTORY.csv、最終コード版はCODE_SHA256.csv。生成中に更新した派生表を旧研究ファイルの保全対象と混同していない。旧データ・コード・既存trial・DOCXを変更せず、commit/push/公開/正式原稿反映を行っていない。新規SUMOは0、追加計算は本trialで事前仕様/数値/資源gateを固定して実行した範囲だけ。

## 成果物と残課題

必要37ファイルと4図ディレクトリを確認。CSV由来図は18組のPNG/PDF、FIGURE_INDEX.csvに出典/再生成scriptを記録。画像の内部表示点検とCSV対応を確認したが、外部第三者査読を受けたとはしない。

HOLDはUNRESOLVED_ITEMS.mdのH01〜H13。厳密46、保存MIP外部証明41、旧staged8予算、未見入力/学習、H_plan/総計画時間、QPU/compiled、raw-invalid一部、材料full-cell、未知BOM、量子材料改善、道路/実車/B→DC、tail/除外物理、正式採用を保持する。旧道路受入FAIL・T09_ROW183対向FAILも維持。

Step3はSTEP3_HANDOFF.mdの確定結果と限定を使って統合考察を開始できる。本成果物は独立した1回のStep2 trialであり、正式採用・研究成果への統合・原稿への反映は未実施。
