# 経路1：比較対象

監査元はP/B_PLAN_REFERENCES_36800.csv、B_CLASSICAL_INITIAL_BASELINES.csv、B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv、B_EXACT_REFERENCE_COVERAGE.csv、S各PROTOCOL.jsonとSOURCE_SNAPSHOT。独立算術検査はevidence/NUMERICAL_CHECKS.csv。保存表の件数をそのまま引用せず460元NPZ・測定JSONへ照合した。

|規模|顧客数|入力数|厳密参照あり|未証明|古典初期解|古典近似|
|---|---:|---:|---:|---:|---:|---|
|R0|3|78|78|0|78|2法×78|
|R1|4|78|78|0|78|2法×78|
|R2|5|78|78|0|78|2法×78|
|R3|25|78|78|0|78|2法×78|
|R4|100|78|57|21|78|2法×78|
|R5|125|70|38|32|70|2法×70|
|計|—|460|407|53|460|920行|

時間窓なし・単一車両・全顧客デポ発着。目的Jは有向OD旅行時間総和（秒）、サービス時間は目的へ加えない。制約は全顧客の順列、需要合計≤216 PE、J+102n≤32,400秒。32,400秒は帰庫制約であり計算予算ではない。旧凍結Aの時間窓/99顧客やCの旧460軌跡とは別母集団。

8設定はmirror5（MEAN_P2、CVAR10_P2、CVAR01_P2、COHERENT2_P2、COHERENT4_P2）、GROVER_P2、GROVER_P3、ACTIVE_ADJACENT_P3_GRID。各460入力で10測定rep、36,800保存計画、3,680 fit。各repは8,192 shotsからのraw sampled-bestであり、初期解とのminを採用しない。

mirror：対称位置のpartial-SWAP、p2、支持2^floor(n/2)、奇数中央固定。COHERENTは初期状態2/4、他は1。MEANとCVaR(α=.10/.01)は学習目的が異なるが最終解品質は同じOD秒で評価する。Grover：全n!支持、一様順列初期状態、p2/p3、65,536学習cost pool。active：隣接parity SWAP p3、t={0,.5,1}の限定grid、初期経路からの局所支持。支持・初期状態・探索予算・近似精度が異なるため、群間差をmixerだけの因果効果としない。

|対照|役割と採用仕様|利用可能性・制約|
|---|---|---|
|古典近似|主対照JCはITERATED_GREEDY_ADJACENT_SWAPを事前指定。DEPHASED_RANDOM_SWAPは第二の近似対照として別々に表示。2法の結果を見て有利な方を選ばない|全規模460入力ずつ。元比較は旧swap実験へのCPU合わせであり現行staged8への予算合わせではない。入力hashと目的値は共通、解品質比較は条件付き、時間公平性HOLD|
|古典初期解|Jinitial。全460の補助対象。初期解が強いことと主近似対照で勝てることを区別|元RESULTで初期経路・評価・構築時間保存。近似改善処理を含む完成対照と同一視しない|
|全問題厳密最適値|J*。共通gap・一致率の参照、実用近似の代替にしない|407のみ。53は最適性未証明、HOLD。詳細はPATH1_REFERENCE_COVERAGE.csv|
|同じmirror支持のchain-DP最適値|探索支持の診断。全順列J*とは別。古典に対する量子優位の証拠にはしない|mirror5の同支持比較。初期目的とorbit最適値が一致する保存結果を確認する対象|

初期解の生成は元unified_no_windowsの保存RESULTSを上流とし、旧whole_rosterのRESULTへ転記されている。古典近似は同じ初期経路を基にした局所探索・脱位相ランダムswap（S/SOURCE_SNAPSHOTおよびcpu_matched_classical_swapsの凍結コード）。厳密値を初期解やQAOAの学習に漏らさず、評価参照に限る。

主比較は同一input SHA・目的・制約・サービス条件をjoin時に必須検査する。現行8設定のCPU予算統制がない既存JC比較は「保存条件での品質比較」と明記し、総時間/速度優位を付けない。Step2の新規統制比較で公平性を補う。

初期解の実装詳細：unified_no_windows/SOURCE_SNAPSHOT/src/kmd_quantitative/routing/solver.py:19–73では、earliest-due nearest・ready-class nearest・期限順挿入の3構成候補から選び、relocateと有向reversalを最大3sweep行う。古典近似の原経路920件は今回すべて元NPZで目的・制約・初期経路を照合済み（evidence/CLASSICAL_APPROXIMATION_ROUTE_CHECK.csv）。表だけから可行性を推測していない。

出力方針の差も保持する：保存古典近似は共通初期解をincumbentに含み、Q側の主保存値はraw sampled-bestである。したがって既存比較はこの出力規則の差も含む条件付き比較。Step2では初期解保持あり/なしを両方式で揃えた補助比較を別に設計し、raw値は置換しない。初期解保持の差を量子状態操作の効果へ帰属しない。
