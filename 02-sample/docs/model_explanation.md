# モデルの数式表現

本研究のモデルは、量子計算条件が材料探索性能を改善し、それが軽量化率、燃費・電費、一般化交通費を通じて都市への流入就業者数に影響するという二段階構造をとる。推定対象として観測データから直接識別するのは一般化交通費弾力性であり、量子計算の効果そのものは文献に基づく技術シナリオとして外生的に与える。

## 1. 記号

起点地域を $r$、都市を $j$、産業群を $g$、問題類型を $p$、技術シナリオを $s \in \{\mathrm{low},\mathrm{base},\mathrm{high}\}$ とする。$Y_{rjg}$ は起点地域 $r$ から都市 $j$ への産業群 $g$ の流入就業者数であり、$C_{rj}$ は一般化交通費、$A_{rj}$ は起終点対の自動車依存度である。

## 2. 材料探索性能差

問題類型 $p$ と産業群 $g$ ごとに、古典条件と量子条件を比較する。まず、計算削減比、時間短縮比、候補生成効率比を定義する。

$$
R^{\mathrm{cost}}_{gp}
=
\frac{\mathrm{classical\_cost\_index}_{gp}}
{\mathrm{quantum\_cost\_index}_{gp}}
$$

$$
R^{\mathrm{time}}_{gp}
=
\frac{\mathrm{classical\_time\_hours}_{gp}}
{\mathrm{quantum\_time\_hours}_{gp}}
$$

$$
R^{\mathrm{yield}}_{gp}
=
\frac{
\mathrm{quantum\_valid\_candidates}_{gp}/\mathrm{quantum\_cost\_index}_{gp}
}{
\mathrm{classical\_valid\_candidates}_{gp}/\mathrm{classical\_cost\_index}_{gp}
}
$$

品質閾値を満たす場合を $Q_{gp}=1$、満たさない場合を $Q_{gp}=\lambda$ とし、$0 \leq \lambda < 1$ とする。また、量子アルゴリズム利用可能性を $a_{gp}$ とする。すると、品質調整済み改善度は

$$
\mathrm{QAG}_{gp}
=
a_{gp} \, Q_{gp}
\exp\!\left(
\omega_1 \log R^{\mathrm{cost}}_{gp}
+
\omega_2 \log R^{\mathrm{time}}_{gp}
+
\omega_3 \log R^{\mathrm{yield}}_{gp}
\right)
$$

と表せる。ここで $\omega_1,\omega_2,\omega_3$ は重みであり、$\omega_1+\omega_2+\omega_3=1$ とする。

## 3. 産業群レベルへの集約

各問題類型の改善度を文献重み $w_{gp}$ で加重平均し、産業群レベルの材料探索改善度 $G_g$ を定義する。

$$
G_g
=
\frac{\sum_p w_{gp} \mathrm{QAG}_{gp}}
{\sum_p w_{gp}}
$$

## 4. 軽量化率・燃費改善率・一般化交通費

産業群 $g$ の改善度 $G_g$ を、工学的制約を組み込んだ翻訳関数 $f_g^{(s)}(\cdot)$ により軽量化率へ変換する。

$$
L_g^{(s)} = f_g^{(s)}(G_g),
\qquad
0 \leq L_g^{(s)} \leq \overline{L}_g
$$

ここで $\overline{L}_g$ は産業群 $g$ における到達可能な最大軽量化率である。軽量化率を燃費・電費改善率へ変換する関数を $h_g(\cdot)$ とすると、

$$
\eta_g^{(s)} = h_g\!\left(L_g^{(s)}\right)
$$

となる。起終点対 $(r,j)$ における古典条件のエネルギー費用を $E_{rj}^{C}$ とすると、量子条件のエネルギー費用は

$$
E_{rjg}^{Q,(s)}
=
E_{rj}^{C}\left(1-\eta_g^{(s)}\right)
$$

である。したがって、古典条件と量子条件の一般化交通費はそれぞれ

$$
C_{rj}^{C} = T_{rj} + N_{rj} + E_{rj}^{C}
$$

$$
C_{rjg}^{Q,(s)} = T_{rj} + N_{rj} + E_{rjg}^{Q,(s)}
$$

と表される。ここで $T_{rj}$ は時間費用、$N_{rj}$ は非エネルギー運行費用である。

## 5. 都市流入就業者数の重力モデル

起点地域 $r$、都市 $j$、産業群 $g$ を単位とし、一般化交通費に対する流入就業者数の弾力性を PPML 重力モデルで推定する。

$$
\mathbb{E}[Y_{rjg}\mid X]
=
\exp\!\left(
\alpha_{rg}
+
\delta_{jg}
+
\beta_g \log C_{rj}
+
\rho_g A_{rj}\log C_{rj}
\right)
$$

ここで、$\alpha_{rg}$ は起点地域×産業群固定効果、$\delta_{jg}$ は都市×産業群固定効果、$\beta_g$ は一般化交通費の基礎的弾力性、$\rho_g$ は自動車依存度による追加的感応度である。

このとき、起終点対 $(r,j)$ における実効的な一般化交通費弾力性は

$$
\varepsilon_{rjg}
=
\beta_g + \rho_g A_{rj}
$$

と解釈できる。

## 6. 反実仮想計算

推定された係数 $\hat{\alpha}_{rg}, \hat{\delta}_{jg}, \hat{\beta}_g, \hat{\rho}_g$ を用いて、古典条件と量子条件の予測流入就業者数を計算する。

$$
\hat{Y}_{rjg}^{C}
=
\exp\!\left(
\hat{\alpha}_{rg}
+
\hat{\delta}_{jg}
+
\hat{\beta}_g \log C_{rj}^{C}
+
\hat{\rho}_g A_{rj}\log C_{rj}^{C}
\right)
$$

$$
\hat{Y}_{rjg}^{Q,(s)}
=
\exp\!\left(
\hat{\alpha}_{rg}
+
\hat{\delta}_{jg}
+
\hat{\beta}_g \log C_{rjg}^{Q,(s)}
+
\hat{\rho}_g A_{rj}\log C_{rjg}^{Q,(s)}
\right)
$$

したがって、量子条件がもたらす流入就業者数の差は

$$
\Delta Y_{rjg}^{(s)}
=
\hat{Y}_{rjg}^{Q,(s)} - \hat{Y}_{rjg}^{C}
$$

であり、都市別・産業群別の差は

$$
\Delta Y_{jg}^{(s)}
=
\sum_r \Delta Y_{rjg}^{(s)}
$$

によって得られる。

## 7. 不確実性評価

不確実性は二層で評価する。第一に、PPML 推定量についてブートストラップにより統計的不確実性を評価する。第二に、$\mathrm{QAG}_{gp}$、軽量化率変換関数、燃費・電費換算関数について、低位・基準・高位の三シナリオを設定し、文献仮定の不確実性を評価する。最終的には両者を統合し、$\Delta Y_{jg}^{(s)}$ の区間として示す。

## 8. 解釈

本モデルで観測データから直接推定されるのは、一般化交通費弾力性 $\beta_g$ と、その自動車依存度による変化 $\rho_g$ である。これに対し、量子計算条件の効果は、$\mathrm{QAG}_{gp}$ から一般化交通費差を構成する技術シナリオとして外生的に与えられる。したがって、最終結果は量子計算の直接因果効果ではなく、文献拘束的技術仮定を接続した静学的反実仮想差分として解釈される。
