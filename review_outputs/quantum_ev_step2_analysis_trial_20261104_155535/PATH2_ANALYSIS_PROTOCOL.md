# 経路2実行前仕様

T08主、T09構造補完。元SCENARIOS/凍結Controlled-DCを保持する。q49点は既存171.875〜195.959596を再評価。u=0.8..1の9点、V=3.0..3.8の9点の共通格子81点と、共通固定部材17/34/51kg、追加部材差delta=b−1,b,b+1kgをモデル診断として追加する。これらの範囲は旧感度probeに対応する設計範囲で、実現確率や成功基準ではない。

全C古典460trajectory×2Crrを対応保持。各trajectoryからE(m)=sum max(alpha*m+beta,0)/etaの区分線形式を構築し、凍結kernel端点で照合する。q/u/V/fixed/deltaによるmassからDCを計算する。モデル出力であり測定値ではない。既存49点を49独立実験としない。

改善伝達率は新たに二つの定義を明記する：(1)相対走行質量削減に対する相対DC削減の比K_EM=(DeltaE/E_LP)/(DeltaM/m_LP)。DeltaM=0ではNULL。(2)qのみ変えた時の相対有効容量変化に対する相対DC削減K_Eq=(DeltaE/E_LP)/((q*u−qLP)/qLP)。q/u/V等が同時変化する条件には単一因果効果として適用しない。両者はモデル上の無次元伝達比で、量子による実現性能ではない。

ゼロ境界はDeltaM=b−delta=0。u/V/qの境界式を既存値と照合する。T09は既知部材subtotalの同一会計境界でq/u/Vを共通にする追加算術を行う。fixed_loadingとfixed_area_LPの二policy、LP/Sの共通入力を固定し、unknown BOMはNULLのまま、delta軸で境界表示する。T09_ROW183の対向FAILは採用しない。

走行条件は距離・再発進回数・moving平均速度・正加速dv2和の分布を保存し、説明変数だけのquartile分類で層別する。相関は記述、規模/parent/groupで交絡し得る。Crr2条件は軌跡内対応差とする。25group bootstrap10000 seed20261102は任意の補助group感度として端点総和比だけに付す。未知材料/BOMの確率分布は導入しない。
