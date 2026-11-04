# 追加計算の判断と実行

- 厳密：最初に53終了理由を監査。default SoPlex残差は証明へ採用せず、rational zero-tolerance pilot、厳密mincut separation pilotを実施。既存large95も検査して影響範囲を拡大。148独立LP、61等値証明（新7/旧54）、残る証拠クラス/上下界を保存。新規大規模整数branchingの一括実施は、既存主要ΔJに不要で分数DFJ pilotが残るため省略し、46HOLDを保持。単なるtimeoutとして省略したのではない。
- 既存統計：不要なQAOA/SUMO再実行をせず、保存NPZ/測定/古典経路から算術・統計・区間を計算。
- QAOA：支持/初期/mixer/pが旧群で同時変化するため統制追加を実施。実行前仕様とinput選択、Wilson精度から97learning、pilot288fit→resource gate→main9312fit。main wall=306.734s。全cell保持、取得改善をgateにしなかった。
- 時間：新fitに内訳をinstrument。greedy同入力291測定、warmup/pilot別。旧時間の不一致scopeは解消したふりをせず残した。
- T08/T09：既存49点だけではjoint u/V・会計構造依存を十分に表せないため、共通入力81格子/2policyとmass境界probeを追加。460保存trajectoryを使用し新SUMOは実行しなかった。model wall=60.362s。
- 走行条件：距離/再発進/速度/加速のcovariate quartile、対応Crr、group感度を計算。回生/補機/勾配等の物理境界は変更していない。

全新規コードはscripts/、実行CLI/seed/環境/原数値はexperiments/・evidence/・logs/。各仕様書にはpilot後の追加固定も実行順で記録した。pilot失敗を隠さず、数値・資源診断として保持している。
