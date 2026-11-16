# Amazon原データの再集計

2026-11-05取得。[AWS登録](https://registry.opendata.aws/amazon-last-mile-challenges/)、[原route_data.json](https://amazon-last-mile-challenges.s3.us-west-2.amazonaws.com/almrrc2021/almrrc2021-data-training/model_build_inputs/route_data.json)。SHA256は `da3a5d4e73b683d756111f0d9e6d3f20eb8e82adf7c89ee6ee0cb2239abd2f38`、78,972,162 bytes。スクリプト `probes/amazon_stats.py`、結果 `probes/amazon_stats.json`。

|定義|ルート数|平均|最小|P10|P25|中央値|P75|P90|最大|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|type=Dropoffのみ|6112|146.991983|32|104|128|150|169|185|237|
|全stop（Dropoff+Station）|6112|147.991983|33|105|129|151|170|186|238|

分位点はNumPy既定のlinear補間。全6112ルートにStationがちょうど1つ。Dropoff総数898415。Station総数6112。論文表2の平均148.0・P10=105・P90=186は全stop集計と整合し、配送比較で1デポを除く補正が可能になった。

2018年の米国5都市（Seattle、Los Angeles、Austin、Chicago、Boston）の履歴。ルート実施日、出発、実績順序、推定道路時間、計画サービス時間を区別する。原データのStopは一配送世帯・住所と等価ではなく、論文§2.3によれば同じ荷物の再試行が別stopとして記録されることもある。packageデータ375MBは今回ダウンロードしておらず、ユニーク住所数や荷物個数分布を原ファイルから再集計したとはしない。論文表2の平均荷物238.5は別指標。

station×dateで観測されるrouteの最大数は56だったが、公開データは全営業所全車群を網羅すると確認できない。これを営業所配備56台・同時出発56台・一計画56台と読み替えない。荷物到着／確定時刻も提供schemaでは確認できず、計画の締切推定には使えない。

取得はus-west-2エンドポイントが遅く、代替エンドポイントも試行した。最終集計は上記SHAの完全JSONのみ使用。別ファイルは主データとして採用しない。論文本体はwebツールで§2・表1〜3を閲覧できたが、requestsでのローカル保存は403だった。このアクセス差を隠さず `sources/manifest.json` に残す。
