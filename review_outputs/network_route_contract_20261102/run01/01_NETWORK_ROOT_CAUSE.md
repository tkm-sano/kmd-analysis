# 道路不適合の原因と影響

## N0：正式保存網 — FAIL

実体 `/home/takuma/kmd-analysis/reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml`、SHA256 `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。XML version1.20はネットワーク形式であり、実行SUMO版とは別。保存command・config・binary台帳はSUMO1.24.0系を使用。完全な元OSMからの再生成は未検証。

外部laneの端点をjunction中心へ延長し長さも更新する `repair_network_geometry_lengths.py` が、内部laneの接続幾何を保ったまま適用された。XML接続IDが存在することと幾何連続は別である。config snapshotの長さ維持という説明と実際の長さ更新に来歴不一致があり、`MAX_GAP_ROOT_CAUSE_CASE.json` と保存変換report／実装を優先して記録した（完全再生成HOLD）。

独立に全468,439lane／598,016connectionを検査。接続primitiveの端点距離>1mは **563,513件**、52,603junctionに分布、最大 **97.0337281568m**。同一connectionから複数primitiveが生じるためconnection行数と同一の分母ではない。欠落lane参照0は接続の形式検査PASSに限る。

最大例：junction`448039303`、内部lane`:448039303_2_0`終端 `(14066.14,5435.71)` と外部lane`38093006_0`始端 `(14146.84,5381.83)`。run2では同じ位置で連続していた。N0の当該外部lane長158.816254m、旧run2長61.67m。原始記録510027を `N0_GAP_PRIMITIVES.csv.gz` で追跡できる。全件のfrom/next/to lane・junction・gapを保存した。

単なる表示差とは判定できない。保存AのPID`P_019e5c3c54c407bfcc2cbb7520d5456041ea980c62abf15533f1d29cc6e1830b`の軌跡で、1秒のXY移動弦長が速度×dtより1m以上長い区間を25件、最大超過25.752048m確認した (`SAVED_TRACE_DISCONTINUITY_READBACK.csv`)。これだけでnative速度が全件誤りとは言えないが、実空間で妥当な走行の受入証拠にはならない。

既存の完全入力A303＋追加15＋B37の全355経路、今回回収B2,323全経路に、外部経路と直接対応する不良primitiveが存在。各candidate/run/問題IDと影響junction数は `SAVED_RUN_NETWORK_EXPOSURE.csv`、`RECOVERED_B_NETWORK_EXPOSURE.csv`。これは全経路が衝突したという判定ではない。未回収Bの経路は検査不能HOLD。保存ODの算術的整合と地域道路としての妥当性を区別する。

## N1：既存B6候補 — 動的FAIL

実体 `/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/road_network_b6_priority_reacceptance_20261028/run01/candidates/B6_priority_repaired.net.xml`、SHA256 `2858d9e674ed819b94238da5e31ec9556e47f8867489d2e6641156eaff5b7c3b`。N0の単純な表示修正ではない。lefthandを明示し、外部形状・長さ、内部接続・信号を広く変更している。`NETWORK_ELEMENT_DIFF.csv.gz` は要素ID／変更前後内容ハッシュを保存。内部ID再採番があるので、同じ内部IDを同じmovementと決めつけない。

|要素|追加|変更|削除|
|---|---:|---:|---:|
|edge|5,703|53,839|973|
|lane|6,606|462,475|4,535|
|junction|2,357|99,127|286|
|connection|198,670|331,713|196,599|
|tlLogic|0|1,257|0|

幾何端点gap>1mは0、最大0.610328mで、この静的閾値のみPASS。完全な交差部安全性の証明ではない。保存native記録183件について、車体の前後端・幅から別の分離軸検査を行い、183/183で車体矩形の重なりを確認した。独立事故数や人身事故の実測値ではない。

|保存イベント原因|件数|
|---|---:|
|下流赤・queueにより内部lane内停止|150|
|短い下流出力の後部がjunctionを占有|2|
|上記占有からの内部foe閉塞連鎖|28|
|移動車両の残存クリアランス重なり|3|

TLSは `1063596961,1883302384,1910535633,256367939,8917306614` の5箇所、方向付きlink対8、順序を除くmovement対7。局所の信号・内部停止・車体占有が相互作用し、処理能力にも波及する。位置・車両・lane・時刻・sourceは `COLLISION_EVENT_CAUSES.csv`／`COLLISION_LANE_RECONSTRUCTION.csv`／`COLLISION_BODY_OVERLAP_INDEPENDENT.csv`。

runtime guardではcollision record183→0となるが、scheduled19,775に対してarrived9,181→8,584、異常停止388→410。保存最大phase保持3,411.5秒で、green配分・待ち・需要処理を同時に受入できない。XML requestのみの修正でもload90で43件残存。collisionを0にするだけでは採用条件を満たさない。

## 最小再現と限界

保存最小probeは予定540車両、最初の`probe:001`は940.5秒、TLS`256367939`、link11/6、lane`:256367939_11_0`／`:256367939_18_0`、被衝突側停止。`MINIMAL_REPLAY_EVIDENCE.json` に保存済みコマンド・binarySHA・入力hash・時刻整合を収録。保存observer replayは183イベントのsignatureを再現した。540車両probeが数学的な最小入力とは証明していない。2台へ縮小したwitnessはHOLD。

今回native再現0。原記録と独立幾何readbackで不採用を判断できるため再実行は不要。将来の局所診断は対象TLS・入力SHA・目的・件数を先に固定し、最大10回、各wall120秒でtimeout、超過時HOLD停止。保存コマンドを出力先そのままで実行しない。地域代表12問題へ拡大しない。

再検証入口：`diagnose_network.py`、`network_supplement.py`。出典SHAは `NETWORK_SOURCES.json`／`NETWORK_SUPPLEMENT_SOURCES.json`。新たなnative値を推定・補完していない。
