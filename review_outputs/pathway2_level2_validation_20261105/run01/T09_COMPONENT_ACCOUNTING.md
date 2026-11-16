# T09部材会計の積算仕様

出典は[Argonne BatPaC v5.0 manual](https://publications.anl.gov/anlpubs/2022/07/176234.pdf)である。保存一次資料は`/home/takuma/kmd-analysis/review_outputs/pathway2_additional_data_review_20261105/run01/sources/BATPAC_NHTSA.pdf`であり、同一報告の米政府NHTSA公開版である。印刷頁とPDF通し頁を`T09_COMPONENT_REQUIREMENTS.csv`に併記した。原資料の式・設計固定値と、本研究で導いたSI体積質量恒等式を区別した。BatPaCワークブックの全計算を再実装したものではない。

対象LP/Sの部材質量は今回確定していない。`None`は未知であり0にしない。各部材は`PACK`又は`SYSTEM_EXTERNAL`に所属し、`coverage`で同じ物体の重複登録を拒否する。必要部材を省略した台帳は集計を拒否する。ただしこのチェックは宣言した分類内の完全性であり、設計BOM自体の完全性は別の工学レビューを要する。

実装は`scripts/components.py`である。外装は総展開面積×各層の面密度、箔余白は既計上塗工面積以外の箔面積×厚さ×密度、既知寸法のタブ/端子/板は体積×密度である。閉箱関数は外形体積−内形体積で角を一度だけ数える単位検算であり、対象の実パック形状を仮定しない。接続断面はBatPaC Eq5.53–5.55より、I²L/(Aσ)=ρAL Cp(dT/dt)から A=I/√[ρσCp(dT/dt)] と導ける。この熱的制約の設計最適化は未実装である。

BMSはTable7.2と§7.2/7.6から、m=1.3{1.1(0.040 nPCB+0.020 nASIC)+Σ n_j m_j} kgを実装した。BDU1個質量はmain contactor750g、aux180g、precharge90g、resistor185g、disconnect150g、service fuse80g、charger fuse24g、current sensor55gである。電圧/モジュール構成による除外、PCB数の主コンタクタ補正は入力側で確定させる。1PCBは常に正しいという意味ではない。モジュール管理46g/moduleは別計上、ガス放出5g/moduleも別物である。interface配線・センサをこの参照集約質量へさらに加算しない。

内部冷却板・伝導板・冷媒はパック側である。Table8.2の外部管理装置は1パックで冷却能力500/1000/3000/6000Wに対し2/3/5/7kgを選ぶ。関数は最小充足区分を選び、入力不明又は通常条件で6000Wを超えるとNoneを返す。急速充電指定の7kgは原資料の選択規則であり、熱的充足を検証した値ではない。複数パックの√N補正は仕様化のみで未実装である。Table8.4（p99/PDF118）では外部冷却管理の質量はbattery system側であり、pack側には入らない。熱管理装置の絶対7kgを材料差7kgと置くことはできない。加熱装置がBatPaC質量指標の対象外であることも、実物の質量0を意味しない。

`evidence/T09_SYNTHETIC_COMPONENT_RESULTS.csv`は各関数の人工幾何単位例である。外装0.1m²×(40µm×2700kg/m³+80µm×900kg/m³)=0.018kg、Cu余白0.003m²×10µm×8960kg/m³=0.0002688kg、Al矩形端子2個=0.005184kgである。これらは1つの製造可能なセル/パックBOMとして寸法整合させたものではない。台帳例は未知保持と会計境界のソフトウェア検証に限り、その既知小計をLP/SのKへ置換しない。未知部材・内部熱部材・保護部材は台帳でもNULLを維持する。

元T09のfoil_massが未塗工・端層を受け取る場合、新しいfoil_incrementを再加算してはならない。余剰注液も既存空隙充填量へ全注液量を重ねて加算しない。T08の固定34kg（100×0.19+15）にこれらを加えることもしない。T09完成パック質量はHOLDである。
