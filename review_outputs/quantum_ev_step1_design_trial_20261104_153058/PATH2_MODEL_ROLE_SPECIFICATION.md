# T08/T09の役割と会計境界

T08を主、T09をモデル構造依存性の補完とする。根拠：T8/SCENARIOS.json、T08.json、SOURCE_SNAPSHOT/src/kmd_quantitative/material_ev/stage2/battery.py、T9/model.py・analyze.py・RUN_CONFIG.json・PACK_20KWH_SENSITIVITY.csv、BR/integrate.pyと部材境界表。

T08では総cell容量Q=Egross/V [Ah]、正極活物質mp=Q/(q u)、正極乾燥塗工材Mp=mp/fp、負極活物質mn=NP·Q/qn、負極塗工材Mn=mn/fn。Mpack=Mp+Mn+Ncell·mother+Mpack,other+Madditional。cell質量=(Mp+Mn)/Ncell+mother。100s1pは設計仮定で、sum cell Ahとpack terminal Ahを混同しない。

gross=20,000 Whは質量設計、usable=18,000 Whは運転stock。qLP=171.875、qS=195.959596 Ah/kg、u=1、V=3.5 V、NP=1.1、qn=360 Ah/kg、fp=.75、fn=.98、100cells×.19kg=19kg、pack other15kg、additional0。0.19kgは両極塗工材以外のcell固定部材の包括項であり、内訳を実測した値ではない。15kgも仮定である。additionalは他に入っていない材料固有追加部材のみ。

qLPは121/.704、qSは194/.99の保持率基準からの逆算proxy（保存丸め値を用いる）。半電池の初回実測比容量やgraphite full-cell性能とは区別。保持率・ICEを追加uと重複適用しない。温度、保持率の基準、Sの質量正規化、活性化履歴、実電圧、power/thermal/life/safety/formation/Li inventoryは未確認。条件付き伝達を計算できても実材料の適格性はHOLD。

T08出力LP96.14565479871602kg、S90.6973573836391kgは簡略モデル計算値。車両質量は元車両から旧電池質量を除いた非pack質量に置換packを加え、走行質量に運転者55kgを加える。保存Cでは非pack走行部分1043.888888888889kgが共通。車体自重にpackを二重加算しない。

T09は部材ごとに幾何を伝播する。face area=active mass/active loading、coating volume=solid volume/(1−porosity)、thickness=coating volume/face area。両面foil面積はface area/2（margin/端部未測定）、Al密度2699・Cu8960 kg/m³。separator面積=max(正負face area)、乾燥separator質量=面積×面密度。電解液は両極coating空隙＋separator空隙＋extra volumeへwettable/saturationと密度を適用する。保存モデルでは正極混合固体密度4458、負極2200、液密度1300kg/m³、separator厚25μm・porosity.41、wettable=saturation=1。密度の材料間transferは仮定として残す。

既知subtotalは正負塗工材＋Al＋Cu＋乾燥separator＋liquid。活物質とcoatingを二重加算しない。未知はcasing/tabs/foil margins/pack structureなど。complete_pack_mass_kgは全183行NULL。T08固定19+15kgをT09 subtotalへ足して完成packを推定しない。T09_ROW_183は全面対向の条件FAILを保持し、物理的に成立した候補として用いない。

共通は20kWh/18kWh、3.5V、LP/S proxy、N/Pと負極基礎値。異なるのは活物質率・loading・area policy・porosity・部材密度transfer・部材固定/幾何連動の扱い。正確な共通条件は行ごとに辞書と照合する。T08/T09絶対質量を完成パック同士として直接比較しない。T09はT08の実証的validationではなく、同じ入力変化でもモデル構造でbが変わることを示す補完モデル。

成立境界はPATH2_BOUNDARY_DEFINITION_TABLE.csv、B015/B051はevidence/T09_BOUNDARY_PAIR_LINKAGE.csvで元行に接続する。q/u/V連続分析や49点は決定論的な探索座標で、49独立実験ではない。全軌跡の正DC質量感度の保証は、指定質量区間とCrr条件内に限る。
