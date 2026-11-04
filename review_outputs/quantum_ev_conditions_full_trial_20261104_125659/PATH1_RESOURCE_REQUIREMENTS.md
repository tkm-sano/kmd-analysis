# 量子計算資源の確認範囲

|由来|確認できる条件|確認できない条件|
|---|---|---|
|符号化|旧正式小規模は位置表現n²二値変数（3/4で9/16）。B mirrorの有効二値方向はfloor(n/2)、支持2^floor(n/2)。Grover支持n!|支持サイズ・シミュレータ変数数を実機論理qubit数と同一視できない|
|アルゴリズム|B mirror p2、Grover p2/p3、active p3。8192shots/測定rep、10rep/fit。3680fitを一意に数える|全学習回路のshots総数・実optimizer反復・compiled回路深さとgate数の一貫した記録|
|計算アーキテクチャ|binary matching MPS、subset DP／certified MC、active-label MPS。保存backend two-site演算・bond等をscope別に追跡可能|backend演算をnative量子gateとみなす換算、DP/MCのCPU時間からQPU時間への換算|
|量子ハードウェア|本実験はCPU上の理想化・近似シミュレーション|ハードウェア接続、native gate set、compiled depth、noise、誤り訂正、論理／物理資源|

必要資源はアルゴリズム・符号化・許容誤差・サンプリング成功確率・ハードウェアに依存する。pは層数であり回路depthそのものではない。旧n²を現行全Bへ適用しない。n=125のmirror有効二値方向62という数を「62論理qubitで配送全探索」と表現するのは不適切である。

全順列を一意に表すための情報量下界ceil(log2(n!))は数学上書けるが、回路・補助qubit・実装コストを与えないため、本trialではハードウェア要求値として数値採用しない。誤り耐性物理資源を断定する根拠はない。Delgado等の材料計算の資源数を経路問題や本T08へ移植しない。
