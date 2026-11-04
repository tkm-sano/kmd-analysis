# 道路修復の既往履歴と停止判断

**修士研究の主分析では、地域道路網の追加修復を停止し、案2へ移行する。** 道路FAILを解除する判断ではない。N0/N1は地域実験に不採用、N2は未構築を維持する。

## 既に試した方法

|段階|目的・実変更|保存検証結果・未解決|
|---|---|---|
|N0 run3|外部lane端点をjunction中心へ延長、長さ更新、内部幾何維持|1m超gap563,513、最大97.033728m。FAIL。静的OD費用自体もこの保存網由来|
|A rollback run2|延長前へ戻す|別SHA。左側通行・信号・端点適合が解決したわけではない|
|B LHT|CLIで左側通行を明示、旧TLS保持|旧phaseと新幾何の同時green foe不適合。設定ファイルのLHT指定が上書きされる初回失敗も保存|
|B2|左側幾何＋TLS再構築|残存8gap、信号4対、端点再対応等でFAIL。再生成controlはXML byte差と意味比較を区別|
|B3/B4|8gap局所修正、信号保護分離・G/gとresponse調整|局所改善。全網screen拡大で18対／12junctionをHOLDとして残した|
|B5|18対のfoes/response/intLanes、12TLSを個別保護green|静的回帰PASS、cycle282〜658秒。green比・容量・待ちと配送mappingは未受入|
|B6 priority|信号優先再受入|静的範囲PASS、動的保存183collision record。車体重なり独立照合183/183、5TLS・7順序なしmovement対|
|grouped run01/run02|競合group化でcycle短縮、制約追加|run01は282probe到達でもcollision2。run02静的回帰PASS／最終静的HOLD、動的未実施。両版を区別|
|body-clearance prototype|request6/7補正XML＋5TLS runtime guard|XMLだけのload90はcollision43。guard併用ではcollision0だがarrived9,181→8,584、異常停止388→410、最大phase保持3,411.5秒で運用FAIL|
|downstream control|space-only／clearance等の出力側占有制御|安全の一部改善と待ち・容量の両立が未成立。別背景需要の受入を実配送成功扱いしない|

各版の実ファイル・SHA・目的・変更・判定・参照先は `ROAD_NETWORK_VERSION_HISTORY.csv`、検証JSON・コードへの起点は `ROAD_HISTORY_EVIDENCE_FILES.csv`。直接読んだgeneration／acceptance／回帰報告を根拠に履歴を整理した。今回は新しい診断手法もnative試験も実行していない。

|版（複製control含む）|実ファイルSHA256|保存判定|
|---|---|---|
|B5_local_static.net (run01)|`3eb7d5c4646f310c93e22e11ae27e6837c1948ac909d0a560730b3c706c21f3a`|HOLD|
|B6_body_clearance_prototype.net (limited_fix)|`22b7e07366e8a5d80768948ad650a04f04db9aca0ccd03b1e79f0bb158a43b4d`|FAIL|
|B6_grouped_static.net (run01)|`6115064ae2c3271388ad3aa807482b42c68543db9761ee6001e36d423d8649e6`|FAIL|
|B6_grouped_static.net (run02)|`6a2d8a56141f9d0f2b8b54eb8926c2f8774e3fd3ead53f944af5c865b2bd9946`|HOLD|
|B6_priority_repaired.net (run01)|`2858d9e674ed819b94238da5e31ec9556e47f8867489d2e6641156eaff5b7c3b`|FAIL|
|B3_local_static.net (run01)|`e8de8ce0210b75117bcffc425e6a3139932bf874efc98f0e20e371844699adb8`|CONDITIONAL|
|B3_reproduced.net (run01)|`e8de8ce0210b75117bcffc425e6a3139932bf874efc98f0e20e371844699adb8`|CONDITIONAL|
|B4_local_static.net (run01)|`f17985b68514f4c1094a4aaa5da48ba53ab3eb76fefeb2926e2677bfe2e3141c`|HOLD|
|B4_reproduced.net (run01)|`f17985b68514f4c1094a4aaa5da48ba53ab3eb76fefeb2926e2677bfe2e3141c`|HOLD|
|A_rollback_run2.net (run01)|`4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f`|HOLD|
|B2_lht_tls_rebuilt.net (run01)|`e76525aec1c15ad5828586c360b0f059ac57813d0474f539ac16ea49ada46dc5`|FAIL|
|B2_reproduction.net (run01)|`d566da1ec8a050a321c560a43796a032cb1dfe73eb4558f0537882075d4c5c38`|FAIL|
|B_lht_rebuilt.net (run01)|`8431d7c6bed1f9e9af8f968441ac09c290cbf29b2975692636c2c46370dd1f7e`|FAIL|
|N0 (phase13_20260903_three_tier_completion)|`460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`|FAIL|

14実体に12異なるhash。B3/B4の再生成一致controlを独立修復成功数に数えない。B2 reproductionはbyte hashが異なるため元版と同一バイトとは呼ばず、保存canonical比較の範囲に限定する。

## OD・既存計画への影響

N1へ旧使用端点6,670roleを移すと958offsetが範囲外、範囲内でも5,700座標が0.1m超移動した。保存355経路すべてで固定lane0距離／自由流時間proxyが変化。新native ODが何秒変わるかは未計算。旧端点・OD・最適値・QAOA目的値の自動再利用は不可。全域mapping→全OD→参照値→計画妥当性→イベント→資源の再受入が必要となる。

地域代表試行はA/Bとも未実施、受入済み既存走行0。過去のprobeや背景交通stress試験を研究の代表配送試行と数えない。過去の衝突記録を独立した現実事故件数とも呼ばない。

## 停止理由と再開条件

研究目的は量子優位・実EV電費の実証ではなく、媒介と成立境界の解明である。計算取得→採用→出発・訪問順→固定OD成果、材料会計→固定速度DCの条件付き関係は地域網受入なしで検証可能。一方、実地域の信号・混雑・速度・電費を結論に必要とするなら修復を省略できない。

今回は前者へ対象を明示的に限定するため追加修復は不可欠ではない。案1は別研究工程として保留する。再開する場合は「現実の動的交通の何を検証するか」、対象5TLSの受入条件、mapping／全行列再計算、時間・人員予算を新計画で固定する。成功まで無制限修復を続けない。全域修復工期は未計測で数値予算HOLD。保存静的診断約73秒／3.04GBは、修復完了工期の見積値ではない。
