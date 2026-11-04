# Step 2統計方法（主解析実行前固定）

主対象は固定されたB460入力とC旧460軌跡の有限cohort。Bは25需要group→26parent→input→8設定→1fit→10測定rep、Cは軌跡内LP/S/2Crr/parameterを対応させる。無作為に抽出した配送母集団ではない。全て秒/kg/Wh/%を区別する。

B主ΔJ=JC−JQ、JCはStep1指定ITERATED_GREEDY_ADJACENT_SWAP、第二対照DEPHASED_RANDOM_SWAP。古典初期差は別列。raw sampled-bestを主とし、両方式で初期incumbent保持を揃える補助値はmin(initial,sampled)と別表記する。Fractionで比較しεJ=0。数値検算のfloat許容幅は目的値の同等閾値ではない。

設定/規模/対照ごとに、まずinput内10repを平均、次にinputを等重みで平均。目的/差の入力間分布にmedian/sampleSD(ddof1)/線形quantileIQR/min/maxを算定し、rep全行の記述とfit内SDは別列。改善・可行・最適一致の分母は予定rep、有効rep、厳密参照repを明示する。厳密値はTask2-1の監査で確定した集合のみ。既存407集合での旧計算再現を別に保存し、証明更新の影響を示す。未知値を0補完しない。

Bの不確実性は(1)input/fit固定・各input内10repの復元抽出10,000回seed20261104（測定乱数感度）、(2)25groupを25個復元抽出しgroup内全parent/input/設定を保持する10,000回seed20261102（仮想group母集団の感度）。後者は需要group間独立・交換可能性という仮定に条件付きで、実配送の校正済みCIではない。各scaleの有効group数とundefined再標本を併記。rep区間とgroup区間を足さない。測定10repのinput別取得確率には95% Wilson区間も示すが学習安定性の区間とは呼ばない。

追加統制実験は3診断input×16条件×2方法、学習seed97/cell（95%Wilson最大半幅0.10というprimary rep0取得確率の精度から設定）、測定10rep/fit×8192shots。学習fit間と測定rep内を区別。primary rep0の97独立学習/測定組のWilson区間、全10repを平均したfit-level値の記述、状態確率からのbest8192成功確率を区別する。旧cohort全体や大規模へ外挿しない。主要比較は事前指定greedyと対応DEPHASED、その他因子対比は機構診断。

Cは決定論的モデルの入力感度と構造依存性を中心とする。49点を独立nにせず、未知部材に確率分布を与えない。ΔE=ELP−ES、個別率100ΔE/ELPと総和比100ΣΔE/ΣELPを別に算定。軌跡分布とCrr/parameter範囲、未知部材境界、需要group感度を別表にする。共通Crr・軌跡・観測窓・凍結kernelを保持する。

統計的有意差検定は実施しない。p値・量子優位・任意0.25%削減を合否条件にしない。全設定と負/ゼロ結果を出力し、有利な条件だけを選ばない。図はCSVから作成し、フィット線/相関を因果効果と断定しない。

## 0件改善に対する補助的な条件付き上限（探索的追加）

観測0件の経験分布bootstrapは[0,0]に退化するため、将来の取得確率が0と解釈しない。input別Wilson(0/10)に加え、全てのinput/fitを固定したまま測定stream間が独立と仮定する補助上限を保存する。piをinput iの「8192shotsのbatchで改善解を得る確率」とすると、P(全0)=Π(1−pi)^10≤(1−平均pi)^(10N)。したがって観測0なら平均piの片側95%上限1−0.05^(1/(10N))を用い、観測が1件以上なら上限1とする手続きは不均一piにも保守的な被覆を持つ。この上限は同じ保存fit群の測定過程に条件付きで、学習や入力抽出の独立性を仮定するものではない。36,800行を無条件の独立したアルゴリズム実験と扱わない。独立stream仮定を置かなければinput別区間と有限cohort記述に限定する。
