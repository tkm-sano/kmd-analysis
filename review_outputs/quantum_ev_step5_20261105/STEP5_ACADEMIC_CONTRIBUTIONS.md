# 学術的貢献と新規性の範囲

## 実証的貢献

実際に検証したのは、指定B系列の保存候補/古典greedyの同一入力対応と、符号付き差平均+441.790609秒、平均相対差+22.243524%、中央値・百分位・入力/設定別の分布である。平均/絶対差/百分率/平均J比の非同義性を実データで区別した。入力平均中央値7.473770秒と設定別平均、影響診断は、改善件数だけでは見えない悪化の局在を示す。新たなQPU効果の実証ではない。

460のmirror支持で改善候補不存在を確認した既存証拠を、有限予算での取得失敗と分けて採用した。固定ODでは帰庫差=ΔJであるが最終顧客完了差は異なり、対象共通上限内では遵守差0ポイントとなることを再集計した。実契約定時率の改善を実証したものではない。

経路2の主実証範囲は保存軌跡を用いたモデル内検算である。記号的感度、会計境界、1000〜1250kg/460軌跡での材料非依存DC応答を採用する。材料性能・完成packの効果としては主張しない。

## 方法的貢献

主対照、支持内最小、最適参照、取得確率、時間scope、計画採用、運用時刻を同一の成功指標へ混ぜず、追跡可能なファイル/式/判断へ対応させた事例評価に特徴がある。全36,800件を保持しつつ460入力とその親/group依存を明示した。材料側は入力来歴、数値整合、実用適格性、モデル帰結、実車validationを独立に審査した。一般的な統計手法や因果媒介概念自体を新規発明したとはいえない。

## 先行研究との比較

| reference_id | authors | year | title | DOI | URL | checked_scope | comparison |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L14 | Brian A. Davis; Miguel Figliozzi | 2013 | A methodology to evaluate the competitiveness of electric delivery trucks | 10.1016/j.tre.2012.07.003 | https://web.cecs.pdx.edu/~maf/publications.html | 著者大学サイト書誌＋既存原著要旨 | 経路/速度/電力/費用接続の先行例。統合構造自体の新規性を主張しない |
| OR02 | Bärtschi, A.; Eidenbenz, S. | 2020 | Grover Mixers for QAOA: Shifting Complexity from Mixer Design to State Preparation | 10.1109/QCE49297.2020.00020 | https://arxiv.org/abs/2006.00354 | v2公開要旨・書誌 | 全可行重ね合わせと状態準備は既知。全支持での取得成功と実用優位を同一視しない |
| OR03 | Hadfield, S.; Wang, Z.; O’Gorman, B.; Rieffel, E.G.; Venturelli, D.; Biswas, R. | 2019 | From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz | 10.3390/a12020034 | https://arxiv.org/abs/1709.03489 | v2公開要旨・書誌 | 可行部分空間mixerは既知。本研究は指定mirror460の不存在と主対照差を追加 |
| OR36 | Palackal, L.; Poggel, B.; Wulff, M.; Ehm, H.; Lorenz, J.M.; Mendl, C.B. | 2023 | Quantum-Assisted Solution Paths for the Capacitated Vehicle Routing Problem | 10.1109/QCE57702.2023.00080 | https://arxiv.org/abs/2304.09629 | v2公開要旨・書誌 | CVRP分解/TSPの解品質評価は先行例。本研究は全保存分布・入力依存・支持証明が対象 |
| OR37 | Delgado, A., et al. | 2022 | Simulating key properties of lithium-ion batteries with a fault-tolerant quantum computer | 10.1103/PhysRevA.106.032428 | https://arxiv.org/abs/2204.11890 | v2公開要旨・書誌 | 電池物性の耐故障量子計算/資源。実材料/実車効果の証拠ではない |
| OR28 | Chen, Q.; Pei, Y.; Chen, H.; Song, Y.; Zhen, L.; Xu, C.-Y.; Xiao, P.; Henkelman, G. | 2020 | Highly reversible oxygen redox in layered compounds enabled by surface polyanions | 10.1038/s41467-020-17126-3 | https://doi.org/10.1038/s41467-020-17126-3 | Step4保存原著Fig5g/方法。Step5 web再取得はエラー | 材料報告と逆算/実用採用を分離。科学的HOLD維持 |
| S5-L01 | Aaron Brooker; Jeffrey Gonder; Lijuan Wang; Eric Wood; Sean Lopp; Laurie Ramroth | 2015 | FASTSim: A Model to Estimate Vehicle Efficiency, Cost and Performance | 10.4271/2015-01-0973 | https://www.nrel.gov/docs/fy15osti/63623.pdf | 研究所公開原著p1要旨/モデル概略・書誌 | 走行cycle/物理モデルによる車両評価は既知。凍結DCの限定算術検証はFASTSim/実車validationと別 |

Hadfield et al.の可行部分空間、Bärtschi/Eidenbenzの状態準備、Palackal et al.の量子配送問題における可行性・解品質評価は先行している。本研究の追加部分は指定cohortの主greedy差分布と支持証拠の対応である。[Hadfield原著](https://arxiv.org/abs/1709.03489)、[Grover mixer原著](https://arxiv.org/abs/2006.00354)、[Palackal原著](https://arxiv.org/abs/2304.09629)。

Davis/Figliozziの経路・電力・費用接続とFASTSimのcycle/物理モデルは既存である。したがって「性能と運用を結んだ最初の研究」としない。本研究の凍結DCは補機・回生等を除くため、FASTSimの実車比較検証を本研究へ継承しない。[著者公開一覧](https://web.cecs.pdx.edu/~maf/publications.html)、[Brooker原著](https://www.nrel.gov/docs/fy15osti/63623.pdf)。

Delgado et al.は量子による電池物性評価の計算・資源を扱う。本研究はその上流計算を実行せず、材料側から質量/DCへ伝わる条件を分離する。[Delgado原著](https://arxiv.org/abs/2204.11890)。Chenの原著はStep4保存一次資料の該当実験のみを使用し、再取得失敗で採用判断を上書きしない。

## 理論的示唆と限界

対象事例では、上流技術の能力から成果の符号・大きさを直結して同定できず、比較基準と中間変換・採用条件が必要となる。これは社会技術システム評価への限定した解釈であり、一般理論の検証ではない。δ=bは会計恒等式、閾値内なら二値成果が変わらないことは閾値定義の帰結であり、それだけを新規性としない。

調査は既存Step4台帳20項目と関連一次資料の限定確認であり、網羅的systematic reviewではない。公開要旨/書誌の確認を全文精読完了と表現しない。「初めて」「世界初」「先例がない」は使用しない。旧Papachristos引用原意図と一部保存書誌/全文はHOLDであり、現行主張の支えには用いない。材料HOLDや実車/QPU未検証のままで、一般的量子優位を新規性に置くことはできない。
