# 公開全電池ケースの選定

主検算は[Zhang et al.]( https://www.nature.com/articles/s41467-026-75101-w)のH-SCLMR/黒鉛全電池である。Source Data `RATE2026_DATA.xlsx`、`Figure S17`のA:B（形成1）、C:D（形成2）を採用する。SI Fig.S17a（PDF18頁）に形成2サイクル、0.1C、30°Cの対応がある。Methods Electrochemical measurements（本文PDF9–10頁）に全電池形成窓1.8–4.75V、2回、1C=250mA/g、黒鉛、N/P≈1.2、正極担持11mg/cm²がある。形成1と形成2は同系列の観測であり、独立標本ではない。

[元xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-75101-w/MediaObjects/41467_2026_75101_MOESM5_ESM.xlsx)の放電枝から容量と平均電圧を同時に取る。容量は正極活物質基準、電圧は黒鉛全電池端子間である。CR2032実験系列に属する全電池であり、同論文のLi金属対極パウチ試験とは区別する。H-SCLMRのHは本論文の処理でありChenのS-200ではない。LP/Sの性能値としての適用は不可である。

正極配合80:8:2:10の全電池への対応とN/Pの形成後有効容量基準は別記されていない。したがってqとVの共同実測スナップショットに、fp=0.8の条件付き対応、T08有効N/P=1.2の仮定、移用qn=360Ah/kgを付けた仮想設計である。完全実測入力の完成パックを構成したとは判定しない。厚電極90%配合の無条件転用は行わない。

補助検算は[Song et al. Fig.4](https://www.nature.com/articles/s41467-026-76366-x)のprotocol4320、45°C、66mA/g（0.33C）、2.0–4.3Vの黒鉛全電池である。[元xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-76366-x/MediaObjects/41467_2026_76366_MOESM3_ESM.xlsx)の`Figure 4`、AY:AZ（BoL放電）、BK:BL（EoL放電）を採用する。本文Fig.4キャプション（PDF6頁）でBoL=形成後の通常1サイクル、EoL=150サイクルと特定できる。SI Fig.S9（PDF11頁）も窓・レートを補助する。形成データとは混合しない。

Songは配合非公開、N/P定義温度に本文45°C/Methods35°C、小型セル表記1Ah/1.5Ahの不一致がある。Q–V数値積分の補助に限定し、Zhangとの共同T08入力や独立反復には使用しない。代表Q–Vとサイクル容量系列の同一試料・同一記録であることも未確認である。

除外した候補は、Song Fig.S8（25°Cだが特定サイクル不明）、Fig.S7b（対Li/Li+電位との対応不十分）、Zhang SCLMR/PCLMR形成曲線（原データ上端約4.8VとMethods全電池窓4.75Vの差がある）である。これらを推測で修正しない。

Zhang原図S17aの縦軸下限2.0Vに対しxlsx放電下端は1.8Vである。下端はMethodsとは整合するが、原図から低電圧末尾の完全一致は確認できない。平均電圧の独立した本文公表値もない。検算は公開数値の再現を意味し、図形と原測定の完全な同一性を保証しない。`evidence/PUBLICATION_ALIGNMENT.csv`に条件付き整合性と未解決点を記録した。
