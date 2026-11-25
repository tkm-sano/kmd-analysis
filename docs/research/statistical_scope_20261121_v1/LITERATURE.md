# 学術的根拠と本研究の設計判断

確認日：2026-11-21。一次文献・著者公開原著・公式ハンドブックを対象とした。文献を根拠とする一般事項と、今回ユーザーが承認した研究方針を区別する。文献から本研究の正式J、許容MCSE、SESOIを導いてはいない。

| 文献・参照URL | 確認できた事項 | 本研究での使用・限界 |
|---|---|---|
| Cumming, Fidler & Vaux (2007), [Error bars in experimental biology](https://pmc.ncbi.nlm.nih.gov/articles/PMC2064100/), DOI 10.1083/jcb.200611141 | Table 1等でSDは観測値のばらつき、SEは平均の不確かさとして区別。バーの種類・標本単位の明記が必要。 | 結果図にSDを使用し、平均の有限反復誤差と区別する根拠。検定を行わないことや本研究のJをこの論文が指示しているわけではない。本文確認後の再アクセスではreCAPTCHAを確認。 |
| Bartz-Beielstein et al. (2020), [Benchmarking in Optimization: Best Practice and Open Issues, arXiv:2007.03488v2](https://arxiv.org/html/2007.03488v2) | §6.2.2の記述統計に平均・中央値・最小最大・四分位数・SDが挙げられる。要約だけで分布全体を説明できない点にも注意がある。 | 記述統計と分布可視化を併用する根拠。§6.3では確認的分析も扱っており、検定廃止自体は本研究の承認済み設計判断。 |
| Krzywinski & Altman (2014), [Visualizing samples with box plots](https://www.nature.com/articles/nmeth.2813), DOI 10.1038/nmeth.2813 | 出版者の検索索引に含まれるPDF本文で中央値・四分位数・IQR・1.5IQR型の外れ値表示を確認。[PubMed書誌](https://pubmed.ncbi.nlm.nih.gov/24645192/)と[著者書誌](https://mk.bcgsc.ca/points-of-significance/bibliography.mhtml)も確認。 | 出版者HTML/PDF直接取得はcookie/IDP遷移で不能。全文を直接取得したとは主張しない。箱ひげ定義の直接参照可能な裏付けには次のNISTも使用する。少数観測では生データ点とJを併記する。 |
| NIST/SEMATECH, [Engineering Statistics Handbook §1.3.3.7 Box Plot](https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm) | 中央値・四分位数の箱、fences型の1.5IQRと外れ値の表現を確認。単純な最小最大型とは区別されている。 | 本研究はユーザー指定の1.5IQR型。境界ちょうどをひげ範囲に含めるのは今回の明示仕様であり、NIST本文のgreater/smaller表現と同じだと偽らない。四分位補間type 7も再現性のための本研究の実装選択。 |
| Morris, White & Crowther (2019), [Using simulation studies to evaluate statistical methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/), DOI 10.1002/sim.8086 | §5.2/Table 6は反復平均に関するMonte Carlo SEを扱い、§5.3は反復数とMonte Carlo精度の設計を扱う。独立反復で平均のMCSEはs/√J。 | 同文献は既知のデータ生成過程から統計的方法の性能を調べる研究。本研究は固定配送問題に対する確率的最適化実行で、需要生成反復とは異なる。有限反復誤差の評価原理を適用することは本研究の設計判断。文献の検定・検出力・被覆率設計を移植しない。 |

## 指定URLの確認不能

ユーザー指定のSpringer URL `https://link.springer.com/book/10.1007/978-3-030-75519-9` は、出版社ページ・DOI等から対象書誌を確認できなかった。誤りだと断定せず、確認不能として保存する。同題・著者・2020年が確認できた著者原著のarXiv版を根拠として使用した。[書誌・版履歴](https://arxiv.org/abs/2007.03488)には2020-07-07初版、2020-12-16改訂v2が記録される。指定Springer書籍を確認済みとして引用しない。

## 本研究が決めた事項

検定・有意性判定・MDE・検出力設計を正式範囲から除外すること、平均±1SDで統一すること、MCSEを内部J評価に限ることは、上記文献から必然的に導かれる結論ではなく、今回のユーザー承認による研究設計である。SDバーの重なりから有意性を読まない。MCSEを小さくするだけで配送問題への一般化や実運行の可行性は証明されない。
