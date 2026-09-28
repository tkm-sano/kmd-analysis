# 現在の実行状況 — 複数台が必要な配送問題の検証 合格・完了 / 停止

研究タイトル：[正式な研究タイトル](RESEARCH_TITLE_AUTHORITY.md)。研究の問い・仮説：[研究の問いと仮説](RESEARCH_QUESTION_AND_HYPOTHESIS.md)。

N002/M2/TW-MODERATEの量子状態の検証に合格に続き、有限回測定の動作確認が合格。凍結完了規則に従い、複数台配送問題の総合判定=合格・完了（この問題例の計算基盤検証のみ）。

- [有限回測定の判定](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/FINITE_SHOT_DECISION.json)
- [複数台配送問題の総合判定](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/MEANINGFUL_MULTI_VEHICLE_OVERALL_DECISION.json)
- [監督停止記録](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/STOP.json)
- [科学会計](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/SCIENTIFIC_ACCOUNTING.json)
- [最終報告](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/FINAL_REPORT.md)
- [成果物一覧](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/ARTIFACT_MANIFEST.json)

実行識別子: 69e866bf-66fc-4f7f-b25d-19fd39136990。第2版の標本抽出監督入口を第一操作として起動、新規実行の許可確認 合格。乱数の種20260927。全状態ベクトル方式64回の測定×1 → 全状態ベクトル方式 判定 合格 → 行列積状態方式64回の測定×1 → 復号器・検証器・資源・時間・会計・保護ファイル監査合格 → 停止。

標本抽出予算2/2回の呼出し・128/128回の測定消費、残予約0。量子状態予算2/2消費は不変。量子状態再実行・量子状態・確率の出力・最適化処理・再試行・追加測定は0。既定実行制御は閉鎖、標本抽出予算は消費済みのため同じ入口の再実行は禁止。

全状態ベクトル方式・行列積状態方式とも実行可能な標本0・最適な標本0。経験分布間の全変動距離=1.0は診断専用であり合否条件ではない。不正符号化は修復・除外せず保存。起動から取得・検査までの処理全体は全状態ベクトル方式4.601901583秒、行列積状態方式4.528426863秒。監督停止時総時間19.695256364秒。監督終了後の読取り検証・本索引更新はこの測定値に含めない。

量子状態単位の整合性と標本抽出処理経路の検証完了を示す。量子優位性、省エネ、解品質、大規模や実量子処理装置での成立は主張しない。手法比較に用いる問題規模=未固定、本実験の第0段階=未許可。

次は別作業で手法比較に用いる問題規模を固定可能か判断するための証拠整理・候補規模選定のみ。今回その段階へ進まない。旧実行・判定の正本・旧未実行・旧第1版の実行不可・科学履歴は保持。
