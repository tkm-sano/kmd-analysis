# Controlled-DC適用範囲

根拠：R/01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json、R/src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py:68–83（公開alias controlled_dc.pyでhash保護）、P/run_c.py、C_TRAJECTORY_READBACK.csv、T8/MATERIAL_ENERGY.csv、各保存trajectory manifest。

Cの古典460速度入力はmatched_classical_trajectories_20261007/MATCHED_CLASSICAL_CANONICAL_TRAJECTORIESの保存CSV.gz。道路交通シミュレーション由来のモデル速度であり実車センサ計測ではない。別にR0/R1量子経路の参照があり、C全readbackは重複を除く465軌跡。古典460だけを主要固定軌跡cohortとし、R0/R1のmethod参照を新しい独立軌跡として水増ししない。Bの新460問題とjoinして配送経路改善のDC効果を推定しない。

区間jはdt=1s、右端速度vj、ds=vj dt、Δv²=vj²−vj−1²。

|項|機械仕事 [J]|質量置換|
|---|---|---|
|W1|m g Crr(v,p) ds|走行質量mを置換|
|W2|.5 ρ CdA v² ds|同じ軌跡・空力仮定では不変|
|W3|.5 m Δv²|走行質量mを置換|
|W4|.5×61 Δv²|回転等価質量61kg固定|

E_DC=Σmax(W1+W2+W3+W4,0)/(3600η) [Wh]、η=.90。成分個別を正値化して足す式ではない。回生なし、平坦路、補機・旋回損失除外、積載0kg、運転者55kg。g9.80665、ρ1.2041、CdA1.175。Crr=.005+(.01+.0095(v_kmh/100)²)/p、lower p4.5bar・upper p2.6bar。Crr2条件は確率的な95%区間ではない。

同一trajectory SHA・観測区間・CrrでLP/Sのpack質量のみを置換する。車両構成や経路選択は共通。正値maskがmassで変わるため、成分寄与はbaseline正値maskでのW1〜W4差＋branch correctionの恒等式で扱う。W2/W4が同値でもmask変化の補正を省かない。

約0.413%は100Σ(ELP−ES)/ΣELP。今回の端点再集計はevidence/C_ENDPOINT_RATIO_READBACK.csv。個別削減率の平均は約0.4093/0.4104%で別の推定対象。いずれもモデル計算値で、測定電力量や量子由来材料改善効果ではない。Bの量子解品質差に乗じない。

末端1秒等の未観測tailは未補完、未知電力量を0としない。C_TRAJECTORY_READBACK.csvのterminal_gap_sとmanifestを保持する。保存道路の地域的受入/実運用妥当性FAIL/HOLDも維持。同一軌跡質量感度のverificationは実道路/実車validationを意味しない。
