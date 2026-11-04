# T08/T09・Controlled-DC監査

T08：Q=20000/V。正極活物質=Q/(q*u)、正極塗工材=Q/(q*u*0.75)、負極活物質=1.1Q/360、負極塗工材=1.1Q/(360*0.98)。100セルで両極塗工材を分割し、0.19kg/cellを一度加え、pack15kgとadditionalを一度加える。gross20kWhは質量設計、usable18kWhは運転stockであり交換しない。保持率・ICEを利用率へ重ねて適用しない。

T09：183行で正極・負極活物質／塗工材、Al/Cu foil、separator、liquidを独立Fraction式で1464照合した。Alはface area/2×厚さ×2699、Cuはface area/2×厚さ×8960、separatorは最大face area×面密度。液量は両極の空隙とseparator空隙とextraを明示して加算する。使用密度4458/2200/1300kg/m³と両面規約は元モデル入力であり独立計測値の妥当性まで保証しない。

完成packは全183行でNULL。casing/tabs/foil margins/pack structureが未測定であり、残差を埋めない。T09_ROW_183の全面対向条件FAILを保持する。正負面積の必要条件が十分な製造・安全条件とはいえない。T08の0.19kgや15kgをT09既知成分へ再加算しない。

T08とT09は同じ完成品の代替予測ではない。比較できるのは会計境界が一致する部材と、条件を明示した差の相殺式である。T08のpack総質量を実測完成packとして採用しない。

Controlled-DC：W1=m*g*Crr(v)*ds、W2=0.5*rho*CdA*v²*ds、W3=0.5*m*Δv²、W4=0.5*61*Δv²。各区間の合計を正値化して0.9で割る。個別成分の正値化ではない。W2/W4は質量置換で共通でも、正値区間maskは変わり得る。成分分解はbaseline正値maskとbranch補正の和であり、branchを省いた単純比例は一般には成立しない。

今回、T08古典920端点について公開凍結kernelと区分線形式を照合し、最大差2.73e-12Whであった。最初の保存軌跡について別のscalar和も両端点・両Crrで照合した。これは実装Verificationであり実車Validationではない。末端1秒の未観測電力量を補完していない。
