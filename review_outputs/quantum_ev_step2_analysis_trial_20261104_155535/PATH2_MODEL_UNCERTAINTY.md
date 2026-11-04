# モデル不確実性と適用範囲

T08主：gross20kWhから正負塗工材を設計し、cell other19kgとpack other15kgを固定、additionalを別項にする。usable18kWhは走行stockで質量設計へ代入しない。qLP171.875/qS195.959596は保持率基準逆算proxy、u/V/NP/活物質率等は仮定。保持率/ICEをuへ再度掛けない。完成パック実測値ではない。

T09補完：positive/negative coatings,Al,Cu,separator,liquidの既知subtotal。area/loading/porosity/密度transferでbが変わる。casing/tabs/foil margins/pack structureはNULL/変数delta。19+15kgのT08固定部材をT09subtotalへ加えて残差を埋めない。T09_ROW183の全面対向FAILは維持し、追加共通入力gridへ紛れ込ませない。

数値verification、実材料/セルのvalidation、実車DCのvalidationは別。今回の検査は凍結kernelと同一軌跡mass置換の再現、部材算術、ゼロ境界、構造感度。材料密度/電圧/利用率/形成/Li在庫/power/thermal/life/safetyの妥当性は未実証。

独立な49実験や920実車走行ではない。trajectory間分布、parameter範囲、未知部材境界、仮想group再標本化感度を区別する。未知部材やproxyに根拠のない確率分布・CIを与えない。Crr lower/upperは凍結モデルの二設定で95%確率区間ではない。

平坦、回生なし、補機・旋回除外、積載0、運転者55kg、rotational equivalent61kg、eta.9、dt1sを保持。区間総仕事を正値化し、massによるmask変化をbranch correctionへ入れる。末端未観測tailを0で埋めない。道路地域受入/実車外部妥当性と量子材料改善への帰属はHOLD。
