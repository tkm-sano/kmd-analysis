# 追加QAOA統制実験結果

 事前仕様QAOA_CONTROLLED_EXPERIMENT_DESIGN.mdに基づき、3診断入力×支持2×初期2×mixer2×layer2×方法2=96cell、97独立学習start/cell、各10測定rep×8192shotsを実施した。合計9,312fit（QAOA4,656/DEPHASED4,656）、93,120測定rep。pilot288fitは別stream・主集計外。main wall=306.734秒、プロセスCPU=305.753秒。CPUの厳密順列部分空間モデルで、元staged8の再実行でもQPU実行でもない。

 97は最適取得率のprimary rep0に対する95% Wilson最大半幅0.10の精度から設定した。97×10を独立学習と数えない。学習seedはoptimizer初期角、測定seedは8192shot categorical抽出の別stream。同じ学習startを2方式で対応させ、それぞれ別に64評価上限で最適化した。exact期待値を用いるため学習時のshot noiseは扱わない。

 R1_020（4顧客、初期非最適）におけるQAOA結果：

 |support|initial_state|mixer|layers|primary_optimal_rep0_count|independent_learning_fits|primary_optimal_rep0_rate|primary_optimal_Wilson95_lower|primary_optimal_Wilson95_upper|mean_delta_J_initial_s|mean_delta_J_greedy_s|
|---|---|---|---|---|---|---|---|---|---|---|
|FULL_PERMUTATION|BASIS_INITIAL|GRAPH_SWAP|1|58|97|0.5979381|0.4984365|0.689978|7.468533|-5.021945|
|FULL_PERMUTATION|BASIS_INITIAL|GRAPH_SWAP|2|78|97|0.8041237|0.7142162|0.8708606|10.18553|-2.304944|
|FULL_PERMUTATION|BASIS_INITIAL|PROJECTOR|1|0|97|0|0|0.03809404|0|-12.49048|
|FULL_PERMUTATION|BASIS_INITIAL|PROJECTOR|2|6|97|0.06185567|0.02865489|0.1284378|0.6438391|-11.84664|
|FULL_PERMUTATION|UNIFORM_SUPPORT|GRAPH_SWAP|1|97|97|1|0.961906|1|12.41322|-0.07726069|
|FULL_PERMUTATION|UNIFORM_SUPPORT|GRAPH_SWAP|2|97|97|1|0.961906|1|12.49048|0|
|FULL_PERMUTATION|UNIFORM_SUPPORT|PROJECTOR|1|97|97|1|0.961906|1|12.49048|0|
|FULL_PERMUTATION|UNIFORM_SUPPORT|PROJECTOR|2|97|97|1|0.961906|1|12.49048|0|
|MIRROR_ORBIT|BASIS_INITIAL|GRAPH_SWAP|1|0|97|0|0|0.03809404|-8.233273|-20.72375|
|MIRROR_ORBIT|BASIS_INITIAL|GRAPH_SWAP|2|0|97|0|0|0.03809404|-2.694704|-15.18518|
|MIRROR_ORBIT|BASIS_INITIAL|PROJECTOR|1|0|97|0|0|0.03809404|0|-12.49048|
|MIRROR_ORBIT|BASIS_INITIAL|PROJECTOR|2|0|97|0|0|0.03809404|0|-12.49048|
|MIRROR_ORBIT|UNIFORM_SUPPORT|GRAPH_SWAP|1|0|97|0|0|0.03809404|0|-12.49048|
|MIRROR_ORBIT|UNIFORM_SUPPORT|GRAPH_SWAP|2|0|97|0|0|0.03809404|0|-12.49048|
|MIRROR_ORBIT|UNIFORM_SUPPORT|PROJECTOR|1|0|97|0|0|0.03809404|0|-12.49048|
|MIRROR_ORBIT|UNIFORM_SUPPORT|PROJECTOR|2|0|97|0|0|0.03809404|0|-12.49048|

 保存greedyは選択3入力で既に厳密最適のため、主ΔJの正改善は定義上不可能である。この負条件を保持した。R1_020のmirror支持は最適を含まず、full支持でもbasis-projector p1は0/97、uniform-projector p1は97/97。したがってfull supportだけで有限予算の成功は保証されない。layer差は同じ評価上限の局所最適化を含む結果で、global角度最適性やlayer一般則ではない。

 raw np.stdに1e-15秒級の丸めSDが残る77fitは、保存目的分数が全反復同一であることを確認しpublic summaryをSD0へ正規化した。raw実験CSVは変更せず、evidence/CONTROLLED_SD_NUMERICAL_REVIEW.csvに差を保存。

 同じ学習角度でDEPHASEDへ置換する4,656診断はQAOA_SAME_ANGLE_DEPHASING.csv。期待目的の干渉差を確認できる条件があるが、主指標は8192shot sampled-best対greedyであり、期待値の差と同じではない。別最適化DEPHASEDとの差はQAOA_CONTROLLED_PAIRED_CONTRASTS.csv。shots1/8/64/8192の解析的感度は37,248行、同じ最終状態の再利用で新しい独立実験とは数えない。

 新結果は全cell保持。初期incumbentの保持あり/なしを別列にした。rawが悪化しても初期解保持で悪化を防ぐことは定義上の選択効果で、量子による改善ではない。全shot histogramから最短解を独立再構成し、9,312fit×10測定の保存値と照合した。direct expmと固有分解、全支持可行性も検証した。

 旧Aの3/4顧客直接比較方針に合わせ本実験は3/4顧客のみ。新mixerはgraph Hamiltonianで、旧activeの逐次parity回路と同一ではない。小規模・選択入力の結果をn25/100/125や一般QAOAへ外挿しない。事前に固定した入力のうち都合の良いcellだけを結果として選んでいない。
