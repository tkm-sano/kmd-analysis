# Current execution — meaningful multi-vehicle validation PASS / COMPLETE / STOP

研究タイトル：[正式タイトル](RESEARCH_TITLE_AUTHORITY.md)。研究の問い・仮説：[正本](RESEARCH_QUESTION_AND_HYPOTHESIS.md)。

N002/M2/TW-MODERATEのstate-level PASSに続き、finite-shot smokeがPASS。凍結completion ruleに従い、MEANINGFUL_MULTI_VEHICLE_OVERALL=PASS / COMPLETE（このinstanceの計算基盤検証のみ）。

- [finite-shot判定](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/FINITE_SHOT_DECISION.json)
- [総合判定](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/MEANINGFUL_MULTI_VEHICLE_OVERALL_DECISION.json)
- [監督STOP receipt](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/STOP.json)
- [科学会計](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/SCIENTIFIC_ACCOUNTING.json)
- [最終報告](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/FINAL_REPORT.md)
- [成果物manifest](reproducibility/outputs/traffic_simulation/r24_meaningful_multi_vehicle_finite_shot/20260928_v1/ARTIFACT_MANIFEST.json)

run_id: 69e866bf-66fc-4f7f-b25d-19fd39136990。v2 sampling監督入口を第一操作として起動、fresh admission PASS。seed20260927。Dense64 shots×1 → Dense gate PASS → MPS64 shots×1 → decoder・validator・資源・時間・会計・保護ファイル監査PASS → STOP。

sampling予算2/2 calls・128/128 shots消費、残予約0。state予算2/2消費は不変。state再実行・state/probability export・optimizer・retry・追加shotsは0。既定guardはCLOSED、sampling予算は消費済みのため同じ入口の再実行は禁止。

Dense/MPSともfeasible0・optimal0。empirical histogram TVD=1.0はDIAGNOSTIC_ONLYであり合否条件ではない。不正符号化は修復・除外せず保存。full-callはDense4.601901583秒、MPS4.528426863秒。監督STOP時総時間19.695256364秒。監督終了後の読取り検証・本索引更新はこの測定値に含めない。

state-level整合性とsampling処理経路の検証完了を示す。量子優位性、省エネ、解品質、大規模や実QPUでの成立は主張しない。METHOD_COMPARISON_SCALE=NOT_FROZEN、Main S0=NOT_AUTHORIZED。

次は別taskでMETHOD_COMPARISON_SCALEをfreeze可能か判断するための証拠整理・候補規模選定のみ。今回その段階へ進まない。旧authority・旧NOT_EXECUTED・旧V1 BLOCKED・科学履歴は保持。
