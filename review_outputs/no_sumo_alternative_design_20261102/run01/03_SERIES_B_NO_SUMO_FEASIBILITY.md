# B：SUMOなし比較と電力量接続の限界

推奨 **B-E3：計画段階を主結論とする（CONDITIONAL GO）**。物理460入力、26親・25需要group、8設定×10測定repの36,800参照を保持する。R0…R5は78/78/78/78/78/70入力、配送先3/4/5/25/100/125。旧時間窓あり系列のR4=99、旧保存460軌跡と混同しない。

## 指標の可用性

|指標|元データ・計算|成立範囲と制限|
|---|---|---|
|目的値／OD時間|raw record、ALL_SEEDS、NPZ travelの訪問脚和（秒）|全36,800参照。今回再計算18経路のみ。実走行時間ではない|
|OD経路距離|NPZ distanceの脚和（m）|全460入力に行列あり、全参照で今後導出可能。edge列回復不要。SUMO走行距離と別名|
|帰庫時刻|出発0＋OD時間＋102n|固定ODで導出可能、顧客待機なし。既存帰庫期限32400は顧客時間窓ではない|
|厳密最適値|元REFERENCE／REFINED、R3 exact-integer DP|407入力で保存。53入力は未確定。メタデータ照合と極小3入力の独立最適値一致。全大規模証明の再実行はしていない|
|global gap・最適値一致|100(J−J*)/J*、完全一致|407入力×8×10=32,560参照が潜在分母。残り4,240を0gapにしない|
|orbit gap|mirror二値chain DPのorbit最小|限定支持上の最適性。global TSP最適値と分離|
|取得・実行可能性|raw status、route permutation／容量・帰庫domain証明、invalid raw samples|保存採用経路と8,192shot全試行の取得確率を区別。参照の存在だけで全shot成功率100%とはしない|
|初期解との比較|同一inputの保存classical initial route/cost|sampled-bestを主値とし、min(initial,sampled)は別のincumbent維持政策。悪化をminで隠さない|
|実CPU時間／RSS|FIT、RESULT、実行ログ、classical resources|fit／検証DP・MC／sampling／前処理を別境界。欠測を0秒にしない。QPU実測値ではない|
|seed変動|rep0…9と元SeedSequence状態|同じ学習結果からの測定変動。10独立学習・10物理問題とは呼ばない|
|qubit／layer／gate|protocol、snapshot、backend stats|mirrorの二値自由度floor(n/2)と物理qubitを区別。p2/p3は論理層。compiled回路深さ・native gate数がない設定はHOLD|
|shots|各protocolの8,192/rep|fitのCVAR1,024、Grover training65,536等と別計上。backend演算回数をhardware shotsと混ぜない|

|規模|厳密参照あり|未確定|
|---|---:|---:|
|R0|78|0|
|R1|78|0|
|R2|78|0|
|R3|78|0|
|R4|57|21|
|R5|38|32|

保存global-gap列のNULL8,310は、53入力×7設定×10とactiveの全列未保存4,600。activeの407入力分は原目的値と証明値から今後導出できるが、今回は全件補完していない。参照未証明の53はbest-knownや下界との偏差を別名で報告可能だが、厳密最適性gap・最適値一致率には含めない。

mirror5設定は固定非隣接swapの2^floor(n/2)支持でありn!全探索ではない。同じorbitの古典chain DPを比較対象に残す。Grover P2/P3は全順列の理想初期化を仮定し、n≤25ではDP、n>25では独立MC等によるCPU検証を用いる。active P3は3点angle grid・rank上限の近似MPS。これらのアーキテクチャ・支持・角度探索・誤差・資源が違うため、計算速度の単一順位を量子優位と解釈しない。

旧cpu-matched classical資料は別時期／設定の結果である。現行8設定のfit・検証・測定と同じ時間予算であることを確認するまで、CPU予算一致比較へ自動転用しない。compiled resource旧表も同様。`B_RESOURCE_FIELD_EXAMPLES.csv` は18例のfield所在・scope・NULLを示すだけで全件資源評価ではない。

## 経路回復の偏り

2,323 ORIGINAL_RECOVERED、2旧cache同一性HOLD、2,662 PARTIAL。元OD脚同一性カバー24,333/36,800=66.122283%、構造入力unionカバー24,493/36,800=66.557065%。地域受入0を保持。

保存目的値・gapの分布を全参照と回復群／非回復群で記述した。親、需要group、設定、rep、問題、訪問順hash別の記録は `B_RECOVERY_BIAS_DESCRIPTIVE.csv`。平均値は保存参照の反復加重記述で、独立標本平均や一般化効果量ではない。

|規模|群|参照数|保存目的値平均秒|保存gap有効n|保存gap平均%|
|---|---|---:|---:|---:|---:|
|R0|ORIGINAL_RECOVERED|5680|1155.809|4970|0.00000|
|R0|NOT_ORIGINAL_RECOVERED|560|1153.120|490|0.00000|
|R1|ORIGINAL_RECOVERED|5440|1204.084|4760|0.01563|
|R1|NOT_ORIGINAL_RECOVERED|800|1124.908|700|0.00000|
|R2|ORIGINAL_RECOVERED|5200|1247.527|4550|0.07966|
|R2|NOT_ORIGINAL_RECOVERED|1040|1094.913|910|0.04722|
|R3|ORIGINAL_RECOVERED|3372|1781.419|2952|12.88905|
|R3|NOT_ORIGINAL_RECOVERED|2868|1680.992|2508|13.26519|
|R4|ORIGINAL_RECOVERED|2401|3278.986|1470|74.38460|
|R4|NOT_ORIGINAL_RECOVERED|3839|3129.505|2520|68.50477|
|R5|ORIGINAL_RECOVERED|2240|3708.839|1260|85.12460|
|R5|NOT_ORIGINAL_RECOVERED|3360|3586.281|1400|85.73810|

回復率はR0約91.0%に対しR4約38.5%、R5=40%。同一規模でも目的値分布が異なる。gap平均は厳密参照のある7設定の保存欄のみなので欠測分母も明示した。回復は無作為抽出ではなく保全履歴と共有脚に依存する。回復subsetを全460の代表とみなさず、回復脚を必要としない目的値・OD距離比較は**全入力を維持**する。coverageで重み補正すれば偏りが消えるという仮定も置かない。

## 電力量の3案

|案|成立性|必要仮定・費用|推奨|
|---|---|---|---|
|B-E1 保存速度＋Controlled-DC|HOLD|現行計画の完全run条件・軌跡対応と道路受入が未成立。旧460を流用不可|Bの主比較には使わない|
|B-E2 OD・距離の解析推定|CONDITIONAL設計可能、現時点主結果HOLD|共通mass、速度・加減速・停止、損失・時間の解釈を新モデルで仮定。追加パラメータ感度が必要|独立補助分析として必要時のみ|
|B-E3 計画段階まで|CONDITIONAL GO|保存数理問題・算法範囲を明示。計画→DCは未検証|主分析に採用|

同じ20m／4秒でも、合成速度2系列はDC20.441059Whと20.269854Whとなった (`B_ENERGY_NONIDENTIFICATION_FIXTURES.csv`、fixture質量1,200kg)。ODのD/Tだけでは加減速・正値化・空気抵抗を同定できない。これはBの推定電費ではなく非一意性の例である。

B-E2を後で行うなら、区間ごとの一定速度D/Tだけで停止損失まで復元したとはしない。速度profileと停止／再発進規則を先に固定した合成モデル、または平坦・端点静止等の条件付き抵抗仕事下界を新IDで設計する。距離に比例する下界の改善は実DCの改善順位を保証しない。旧空荷1,155kgは候補にとどまり、現行B主質量はHOLD。PEをkgへ換算しない。凍結Controlled-DCの式を改変せず、新合成入力／別解析モデルと明示する。

Bには顧客ready/dueを追加しない。別根拠のない顧客定時配達率は算出しない。計画時間・距離と配送電力量の接続を検証済みに見せない。
